import asyncio
import json
import logging
import math
import random  # Added for variety in course selection if needed
import statistics
from collections import defaultdict
from typing import Any, List, Dict, Set, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.database.database import Program, Course
from data.logic.availability import predict_availability

# from data.logic.scheduler import TermData # Explicitly import if not part of SchedulerResult module easily

from data.parser.parser_utils import (
    flatten_requisites_to_list,
    parse_prerequisites,
    parse_corequisites,
    filter_parsed_requisites,
)

logger = logging.getLogger(__name__)


# Pydantic models
class TermData(
    BaseModel
):  # This was already defined, ensure it matches SchedulerResult's expectations
    courses: List[str] = []
    credits: int = 0
    difficulty_sum: float = 0.0


class SchedulerResult(BaseModel):
    schedule: Dict[str, TermData]  # Maps term name ("Fall 2025") to TermData
    score: float  # Lower is better fit to curve?
    is_complete: bool
    warnings: List[str] = []
    rank: int = 0


class Requirement(BaseModel):
    kind: str  # "COURSE", "COURSE_CATEGORY"
    value: str  # Course code or category name
    credits: int = 0
    difficulty: float = 0.0
    priority: float = 0.0


class TermRequisiteData(BaseModel):
    requirement: List[Requirement] = []
    credits: int = 0
    difficulty_sum: float = (
        0.0  # Sum of difficulties of REQUIREMENTS (courses or estimated for categories)
    )

    def is_empty(self):
        return not self.requirement


class SchedulerSkeletonResult(BaseModel):
    schedule: Dict[
        str, TermRequisiteData
    ]  # Maps term name ("Fall 2025") to TermRequisiteData
    score: float  # Lower is better
    is_complete: bool
    warnings: List[str] = []


# Helper functions
async def load_program_data(program_code: str, db: AsyncSession) -> Optional[Program]:
    """Loads program requirements from the DB."""
    try:
        result = await db.execute(select(Program).where(Program.code == program_code))
        program = result.scalars().first()
        if program:
            logger.info(f"Loaded program data for {program_code}")
        else:
            logger.warning(f"Program data not found for {program_code}")
        return program
    except Exception as e:
        logger.error(f"Error loading program data for {program_code}: {e}")
        return None


async def load_course_data_lookups(db: AsyncSession) -> Dict[str, Dict]:
    """
    Loads all course data into lookup dictionaries for efficient access.
    Includes credits, difficulty, path length, availability info, and
    stores RAW prerequisite/corequisite strings for later parsing if needed.
    """
    lookup = {}
    try:
        stmt = select(Course)
        result = await db.execute(stmt)
        all_courses = result.scalars().all()
        for course in all_courses:
            lookup[course.course_code] = {
                "credits": course.credits or 0,
                "difficulty": course.difficulty or 0,
                "highest_ancestor": course.highest_ancestor or 0,
                "prerequisites_raw": course.prerequisites,
                "corequisites_raw": course.corequisites,
                "last_Fall": course.last_Fall or 0,
                "last_Spring": course.last_Spring or 0,
                "last_FirstSummer": course.last_FirstSummer or 0,
                "last_SecondSummer": course.last_SecondSummer or 0,
                "last_ExtendedSummer": course.last_ExtendedSummer or 0,
            }
        logger.info(f"Loaded lookup data for {len(lookup)} courses.")
    except Exception as e:
        logger.error(f"Error loading course lookup data: {e}")
        return {}
    return lookup


def check_requisites_recursive(req_dict: dict, completed_courses: Set[str]) -> bool:
    """Checks if parsed requisites (filtered for courses) are met by the completed set."""
    if not req_dict or not isinstance(
        req_dict, dict
    ):  # Base case: empty or invalid req is met
        return True

    req_type = req_dict.get("type")

    if req_type == "COURSE":
        course_code = req_dict.get("value", "").replace(" ", "")
        return course_code in completed_courses
    elif req_type == "AND":
        conditions = req_dict.get("conditions", [])
        if not conditions:
            return True  # Empty AND is true
        return all(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "OR":
        conditions = req_dict.get("conditions", [])
        if not conditions:
            return False  # Empty OR is false
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "ANDOR":  # Usually A Y/O B -> A or B or (A and B)
        conditions = req_dict.get("value", [])
        if not isinstance(conditions, list) or not conditions:
            return False  # Invalid or empty ANDOR
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif (
        req_type == "FOR"
    ):  # e.g. "6 credits FOR MATE" - applies to a category, not a direct course pre/co-req
        logger.debug(
            f"Encountered 'FOR' type during requisite check, treating as met: {req_dict}"
        )
        return True  # In course-based pre/co-req checks, this type doesn't block.
    else:
        logger.warning(
            f"Unexpected node type in check_requisites_recursive: {req_type} for {req_dict}"
        )
        return False  # Fail safe


def get_course_category(
    course_code: str,
    required_course_codes: set[str],
    technical_course_codes: set[str],
    group_sociohumanistics: bool = False,
) -> str:  # Return type changed to str, will return "free" as default
    if course_code in required_course_codes:
        return "required"

    # Important: A course can be technical in nature but also specifically required.
    # The "technical" category here implies it's being considered as an elective choice from the technical pool.
    # If it's NOT in required_course_codes but IS in technical_course_codes, it's a technical elective.
    if (
        course_code in technical_course_codes
    ):  # And implicitly not in required_course_codes due to above check if used sequentially
        return "technical"

    prefix = course_code[:4]
    category = None  # Only used for disambiguating sociohumanistics
    # General Education / Other Categories
    if prefix == "EDFI":
        return "kinesiology"
    if prefix == "INGL":
        return "english"
    if prefix == "ESPA":
        return "spanish"
    if prefix in [
        "HUMA",
        "FILO",
        "ARTE",
        "LITE",
        "MUSI",
        "TEAT",
        "FRAN",
        "ITAL",
        "ALEM",
        "LATI",
    ]:
        category = "humanities"
    if prefix in ["CISO", "CIPO", "SOCI", "ECON", "PSIC", "HIST", "GEOG", "ANTR"]:
        category = "social"
    if category:
        return "sociohumanistics" if group_sociohumanistics else category

    return "free"  # Default category if none of the above match


def get_course_priority(category: str) -> float:
    PRIORITY_MAP = {
        "required": 1.0,
        "techniucal": 2.0,
        "english": 3.0,
        "spanish": 3.0,
        "humanities": 4.0,
        "social": 4.0,
        "sociohumanistics": 4.0,
        "free": 5.0,
        "kinesiology": 6.0,
    }
    return PRIORITY_MAP.get(
        category, 5.0
    )  # Default to "free" priority for unknown categories


def get_next_term(current_term: str, current_year: int) -> Dict[str, Any]:
    current_term_lower = current_term.lower()
    TERMS = ["spring", "firstsummer", "secondsummer", "fall"]

    try:
        current_term_index = TERMS.index(current_term_lower)
    except ValueError:
        logger.error(
            f"Invalid current_term '{current_term}' provided to get_next_term."
        )
        raise ValueError(f"Unknown term: {current_term}")

    next_term_index = (current_term_index + 1) % len(TERMS)
    next_term_name = TERMS[next_term_index]

    next_year = current_year
    # Year increments if we are moving from Fall (last term in sequence) to Spring (first term in sequence)
    if current_term_index == (len(TERMS) - 1):
        next_year = current_year + 1

    return {"term": next_term_name, "year": next_year}


def _is_program_complete_v2(
    program_reqs: Program,
    current_taken_courses: Set[str],
    course_lookups: Dict[str, Dict],
    program_specific_required_codes: Set[str],
    program_technical_elective_pool: Set[str],
) -> bool:
    """
    Checks if all program requirements (specific courses and category credits) are met.
    """
    # 1. Check all specific required courses
    if not program_specific_required_codes.issubset(current_taken_courses):
        missing_specific = program_specific_required_codes - current_taken_courses
        logger.debug(
            f"Program completion check: Incomplete. Missing specific courses: {missing_specific}"
        )
        return False

    # 2. Check credit categories
    credits_met_for_category = defaultdict(int)
    for course_code in current_taken_courses:
        # Only count courses NOT in program_specific_required_codes towards category credits.
        # Assumes specific courses fulfill their role and don't double-count for general categories.
        if course_code not in program_specific_required_codes:
            category = get_course_category(
                course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
            )
            # `get_course_category` will return "technical" if course_code is in program_technical_elective_pool (and not specific).
            # It will return "free" or other gen-ed categories otherwise.
            # "required" category courses are handled by the specific check above.

            course_data = course_lookups.get(course_code)
            if course_data:
                credits_met_for_category[category] += course_data["credits"]
            else:
                logger.warning(
                    f"Program completion check: Course {course_code} not in lookups during credit sum."
                )

    target_category_credits = {
        "english": program_reqs.english or 0,
        "spanish": program_reqs.spanish or 0,
        "humanities": program_reqs.humanities or 0,
        "social": program_reqs.social or 0,
        "technical": program_reqs.technical
        or 0,  # Credits from the technical_elective_pool
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }

    for cat, required_val in target_category_credits.items():
        if credits_met_for_category[cat] < required_val:
            logger.debug(
                f"Program completion check: Incomplete. Category '{cat}': {credits_met_for_category[cat]}/{required_val} credits."
            )
            return False

    # Check sociohumanistics requirement (sum of humanities and social credits met)
    if program_reqs.sociohumanistics and program_reqs.sociohumanistics > 0:
        total_huma_social_met = (
            credits_met_for_category["humanities"] + credits_met_for_category["social"]
        )
        if total_huma_social_met < (program_reqs.sociohumanistics or 0):
            logger.debug(
                f"Program completion check: Incomplete. Sociohumanistics: {total_huma_social_met}/{program_reqs.sociohumanistics} credits."
            )
            return False

    logger.debug("Program completion check: All requirements appear to be met.")
    return True


# --- Start improved functions ---


async def generate_semester(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    term: str,
    year: int,
    taken_courses_set: Set[str],
    target_difficulty: float,
    credit_limits: Dict,  # {"min": x, "max": y}
    db_session: AsyncSession,
) -> tuple[TermRequisiteData, bool]:

    try:
        required_courses_req_data_json = json.loads(program_reqs.courses or "{}")
        # tech_electives_req_data_json = json.loads(program_reqs.technical_courses or "{}") # Not directly used here beyond defining the pool
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse program course JSON for {program_reqs.code} in generate_semester: {e}"
        )
        raise

    program_specific_required_codes = set(required_courses_req_data_json.keys())
    # Pool of codes ALLOWED for technical electives (used by get_course_category & _is_program_complete_v2)
    program_technical_elective_pool = set(
        json.loads(program_reqs.technical_courses or "{}").keys()
    )

    current_semester_requirements_pool: List[Requirement] = []

    # 1. Add specific required courses to the pool if eligible
    remaining_specific_course_codes = (
        program_specific_required_codes - taken_courses_set
    )
    for course_code in remaining_specific_course_codes:
        course_data = course_lookups.get(course_code)
        if not course_data:
            logger.warning(
                f"Course {course_code} (required) not in course_lookups. Skipping."
            )
            continue

        prereqs_raw = course_data.get("prerequisites_raw")
        if prereqs_raw:
            parsed_prereqs = parse_prerequisites(prereqs_raw)
            filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
            if not check_requisites_recursive(filtered_prereqs, taken_courses_set):
                logger.info(
                    "Prerequisites not met for course %s. Skipping.",
                    course_code,
                )
                continue

        if not await predict_availability(course_code, term, db_session):
            continue

        # Category for a specific required course is "required"
        category_for_priority = get_course_category(
            course_code,
            program_specific_required_codes,
            program_technical_elective_pool,
            group_sociohumanistics=False,
        )
        current_semester_requirements_pool.append(
            Requirement(
                kind="COURSE",
                value=course_code,
                credits=course_data["credits"],
                priority=get_course_priority(category_for_priority),
                difficulty=course_data["difficulty"],
            )
        )

    # 2. Calculate and add category requirements (COURSE_CATEGORY)
    target_category_credits_map = {
        "english": program_reqs.english or 0,
        "spanish": program_reqs.spanish or 0,
        "humanities": program_reqs.humanities or 0,
        "social": program_reqs.social or 0,
        "sociohumanistics": program_reqs.sociohumanistics or 0,
        "technical": program_reqs.technical or 0,
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }
    credits_already_met_for_category = defaultdict(int)
    for (
        taken_course_code
    ) in taken_courses_set:  # Iterate over courses taken *before* this semester
        if (
            taken_course_code not in program_specific_required_codes
        ):  # Only non-specific courses count towards categories
            cat = get_course_category(
                taken_course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
            )
            # `cat` will be "technical", "humanities", "free", etc. but not "required".
            credits_already_met_for_category[cat] += course_lookups[taken_course_code][
                "credits"
            ]

    for (
        category_name,
        total_target_credits_for_category,
    ) in target_category_credits_map.items():
        needed_credits = (
            total_target_credits_for_category
            - credits_already_met_for_category[category_name]
        )
        if needed_credits <= 0:
            continue

        num_3_credit_chunks = needed_credits // 3
        remaining_offshoot_credits = needed_credits % 3
        cat_priority = get_course_priority(category_name)
        # Estimated difficulty for category slots
        est_difficulty = 2.5 if category_name not in ["technical", "required"] else 3.0

        for _ in range(num_3_credit_chunks):
            current_semester_requirements_pool.append(
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category_name,
                    credits=3,
                    priority=cat_priority,
                    difficulty=est_difficulty,
                )
            )
        if remaining_offshoot_credits > 0:
            current_semester_requirements_pool.append(
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category_name,
                    credits=remaining_offshoot_credits,
                    priority=cat_priority,
                    difficulty=est_difficulty,
                )
            )

    current_semester_requirements_pool.sort(
        key=lambda r: (r.priority, abs(r.difficulty - target_difficulty))
    )

    # 3. Select requirements for the semester
    proposed_semester_data = TermRequisiteData()
    courses_added_this_term_codes = (
        set()
    )  # For co-requisite checks within this semester

    eligible_reqs_copy = list(current_semester_requirements_pool)  # Iterate over a copy

    while proposed_semester_data.credits < credit_limits["max"] and eligible_reqs_copy:
        selected_req_obj = None
        selected_req_idx = -1

        for i, req_candidate in enumerate(eligible_reqs_copy):
            if (
                proposed_semester_data.credits + req_candidate.credits
                > credit_limits["max"]
            ):
                continue

            if req_candidate.kind == "COURSE":
                course_code_cand = req_candidate.value
                course_cand_data = course_lookups[course_code_cand]

                coreqs_raw = course_cand_data.get("corequisites_raw")
                if coreqs_raw:
                    parsed_coreqs = parse_corequisites(coreqs_raw)
                    filtered_coreqs = filter_parsed_requisites(parsed_coreqs)
                    # Co-reqs check against (taken before this term) + (already added to this term)
                    if not check_requisites_recursive(
                        filtered_coreqs,
                        taken_courses_set.union(courses_added_this_term_codes),
                    ):
                        logger.debug(
                            f"Course {course_code_cand} co-reqs not met for {term} {year}. Skipping."
                        )
                        continue

                selected_req_obj = req_candidate
                selected_req_idx = i
                break

            elif (
                req_candidate.kind == "COURSE_CATEGORY"
            ):  # No co-reqs for category placeholders
                selected_req_obj = req_candidate
                selected_req_idx = i
                break

        if selected_req_obj:
            proposed_semester_data.requirement.append(selected_req_obj)
            proposed_semester_data.credits += selected_req_obj.credits
            proposed_semester_data.difficulty_sum += selected_req_obj.difficulty

            if selected_req_obj.kind == "COURSE":
                courses_added_this_term_codes.add(selected_req_obj.value)

            eligible_reqs_copy.pop(selected_req_idx)  # Remove from consideration
        else:
            break  # No suitable requirement found

    # 4. Validate credit limits and determine program completion status
    # Allow empty semester only if min_credits is 0 or program is already complete.
    is_empty_and_min_is_zero = (
        proposed_semester_data.is_empty() and credit_limits["min"] == 0
    )

    if (
        not is_empty_and_min_is_zero
        and proposed_semester_data.credits < credit_limits["min"]
    ):
        # Check if program is complete; if so, being under min might be ok for the last semester.
        temp_taken_for_final_check = taken_courses_set.union(
            courses_added_this_term_codes
        )
        is_prog_complete_now = _is_program_complete_v2(
            program_reqs,
            temp_taken_for_final_check,
            course_lookups,
            program_specific_required_codes,
            program_technical_elective_pool,
        )
        if (
            not is_prog_complete_now
        ):  # If not complete and under min credits (and not empty with min_credits=0)
            warning_msg = (
                f"Term {term} {year}: Generated semester has {proposed_semester_data.credits} credits, "
                f"less than min ({credit_limits['min']}), and program is not yet complete."
            )
            logger.warning(warning_msg)
            raise ValueError(warning_msg)  # Critical failure to form a valid semester

    # `is_program_finished_bool` reflects if the program *would be* complete
    # assuming the specific courses from this semester are taken and category slots are eventually filled.
    tentative_all_taken_courses = taken_courses_set.union(courses_added_this_term_codes)
    is_program_finished_bool = _is_program_complete_v2(
        program_reqs,
        tentative_all_taken_courses,
        course_lookups,
        program_specific_required_codes,
        program_technical_elective_pool,
    )

    return proposed_semester_data, is_program_finished_bool


async def resolve_category_requirements(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    initial_taken_courses: Set[str],
    schedule_skeleton: SchedulerSkeletonResult,
    db_session: AsyncSession,
    program_specific_required_codes: Set[str],  # Passed in for consistency
    program_technical_elective_pool: Set[str],  # Passed in for consistency
) -> SchedulerResult:

    resolved_schedule_map: Dict[str, TermData] = {}  # term_key -> TermData (resolved)
    final_warnings = list(schedule_skeleton.warnings)  # Copy warnings from skeleton

    # Tracks all courses assigned throughout the resolution process, term by term
    # Starts with courses taken before the skeleton begins.
    globally_resolved_and_taken_courses = initial_taken_courses.copy()

    term_order_map = {"spring": 0, "firstsummer": 1, "secondsummer": 2, "fall": 3}
    try:
        sorted_term_keys = sorted(
            schedule_skeleton.schedule.keys(),
            key=lambda tk: (int(tk.split()[1]), term_order_map[tk.split()[0].lower()]),
        )
    except Exception as e:  # Fallback if term keys are malformed
        logger.error(
            f"Error sorting term keys '{list(schedule_skeleton.schedule.keys())}': {e}. Using unsorted."
        )
        sorted_term_keys = list(schedule_skeleton.schedule.keys())

    for term_key in sorted_term_keys:
        term_skeleton_data = schedule_skeleton.schedule[
            term_key
        ]  # This is TermRequisiteData
        current_term_resolved_termdata = (
            TermData()
        )  # This will be the resolved TermData

        # Courses taken *before* this specific term (initial + previous resolved terms)
        taken_courses_before_this_term = globally_resolved_and_taken_courses.copy()

        # Courses added within *this* term, for co-req checks among them
        courses_resolved_this_term_set = set()

        term_name_parts = term_key.split()
        current_term_name_for_api = term_name_parts[0]  # e.g. "Fall"
        current_term_year_for_api = int(term_name_parts[1])

        # 1. Process concrete "COURSE" requirements first for this term
        for req in term_skeleton_data.requirement:
            if req.kind == "COURSE":
                course_code = req.value
                if (
                    course_code in globally_resolved_and_taken_courses
                    or course_code in courses_resolved_this_term_set
                ):
                    logger.warning(
                        f"Course {course_code} in term {term_key} seems to be a duplicate or already taken. Skipping."
                    )
                    continue

                course_info = course_lookups.get(course_code)
                if not course_info:
                    logger.error(
                        f"Course {course_code} from skeleton not in lookups for term {term_key}. Cannot resolve."
                    )
                    final_warnings.append(
                        f"Error: Course {course_code} (skeleton) missing from lookups for {term_key}."
                    )
                    continue

                current_term_resolved_termdata.courses.append(course_code)
                current_term_resolved_termdata.credits += course_info["credits"]
                current_term_resolved_termdata.difficulty_sum += course_info[
                    "difficulty"
                ]
                courses_resolved_this_term_set.add(course_code)

        # 2. Resolve "COURSE_CATEGORY" requirements
        for req in term_skeleton_data.requirement:
            if req.kind == "COURSE_CATEGORY":
                category_to_fill = req.value
                credits_for_slot = req.credits

                candidate_pool: List[str] = []
                if category_to_fill == "technical":
                    # Technical electives must come from the program's defined pool
                    # And must not be a course already designated as a specific program requirement
                    for c_code in program_technical_elective_pool:
                        if c_code not in program_specific_required_codes:
                            candidate_pool.append(c_code)
                else:  # For humanities, social, english, spanish, free, kinesiology
                    for c_code, c_lookup_data in course_lookups.items():
                        # Must not be a specifically required course for the program
                        if c_code in program_specific_required_codes:
                            continue

                        actual_course_cat = get_course_category(
                            c_code,
                            program_specific_required_codes,
                            program_technical_elective_pool,
                        )

                        if category_to_fill == "free":
                            # "Free" electives can be anything not specifically required.
                            # It could even be a technical course if not needed for technical credits.
                            pass  # No further category filtering for "free"
                        else:  # Specific categories (humanities, social, etc.)
                            if actual_course_cat != category_to_fill:
                                continue
                            # Additionally, ensure a non-technical category is not filled by a designated technical elective
                            if c_code in program_technical_elective_pool:
                                continue  # e.g. don't use a tech pool course for "humanities"

                        candidate_pool.append(c_code)

                random.shuffle(candidate_pool)  # For variety in selection

                found_match_for_category = False
                for cand_course_code in candidate_pool:
                    if (
                        cand_course_code in globally_resolved_and_taken_courses
                        or cand_course_code in courses_resolved_this_term_set
                    ):
                        continue  # Already taken or assigned in this term

                    cand_course_data = course_lookups[cand_course_code]
                    if (
                        cand_course_data["credits"] != credits_for_slot
                    ):  # Simplification: exact credit match
                        continue

                    if not await predict_availability(
                        cand_course_code,
                        current_term_name_for_api,
                        db_session,
                    ):
                        continue

                    # Check Prerequisites (against courses taken *before* this term)
                    prereqs_r = cand_course_data.get("prerequisites_raw")
                    if prereqs_r:
                        parsed_pr = parse_prerequisites(prereqs_r)
                        filtered_pr = filter_parsed_requisites(parsed_pr)
                        if not check_requisites_recursive(
                            filtered_pr, taken_courses_before_this_term
                        ):
                            continue

                    # Check Co-requisites (against (taken before this term) + (all courses resolved in *this* term so far))
                    coreqs_r = cand_course_data.get("corequisites_raw")
                    if coreqs_r:
                        parsed_co = parse_corequisites(coreqs_r)
                        filtered_co = filter_parsed_requisites(parsed_co)
                        co_req_check_set = taken_courses_before_this_term.union(
                            courses_resolved_this_term_set
                        )
                        if not check_requisites_recursive(
                            filtered_co, co_req_check_set
                        ):
                            continue

                    # If all checks pass, select this course
                    current_term_resolved_termdata.courses.append(cand_course_code)
                    current_term_resolved_termdata.credits += cand_course_data[
                        "credits"
                    ]
                    current_term_resolved_termdata.difficulty_sum += cand_course_data[
                        "difficulty"
                    ]
                    courses_resolved_this_term_set.add(cand_course_code)
                    found_match_for_category = True
                    break  # Move to next category requirement

                if not found_match_for_category:
                    final_warnings.append(
                        f"Term {term_key}: Could not resolve category '{category_to_fill}' ({credits_for_slot} cr)."
                    )

        resolved_schedule_map[term_key] = current_term_resolved_termdata
        # Update globally tracked courses with those resolved in this term
        globally_resolved_and_taken_courses.update(courses_resolved_this_term_set)

    # Determine final completion status based on all resolved courses
    is_schedule_truly_complete = _is_program_complete_v2(
        program_reqs,
        globally_resolved_and_taken_courses,
        course_lookups,
        program_specific_required_codes,
        program_technical_elective_pool,
    )

    return SchedulerResult(
        schedule=resolved_schedule_map,
        score=schedule_skeleton.score,  # Score could be re-evaluated based on resolved data
        is_complete=is_schedule_truly_complete,
        warnings=final_warnings,
    )


async def generate_sequence(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    start_term_name: str,
    start_year: int,
    initial_taken_courses_set: Set[str],
    credit_limits: Dict,
    db_session: AsyncSession,
    max_terms: int = 15,
) -> Tuple[Optional[SchedulerResult], Optional[SchedulerSkeletonResult]]:

    main_current_term = start_term_name.lower()
    main_current_year = start_year

    try:
        prog_courses_json = json.loads(program_reqs.courses or "{}")
        prog_tech_electives_json = json.loads(program_reqs.technical_courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Critical: Failed to parse program JSON for {program_reqs.code} at sequence start: {e}"
        )
        return None, None

    # These are needed by helper functions and should be derived once at this level.
    p_specific_req_codes = set(prog_courses_json.keys())
    p_tech_elective_pool = set(prog_tech_electives_json.keys())

    # Check if program is already complete with the initial set of taken courses
    if _is_program_complete_v2(
        program_reqs,
        initial_taken_courses_set,
        course_lookups,
        p_specific_req_codes,
        p_tech_elective_pool,
    ):
        logger.info(
            f"Program {program_reqs.code} is already complete with provided initial courses."
        )
        skel_res = SchedulerSkeletonResult(
            schedule={},
            score=0,
            is_complete=True,
            warnings=["Program already complete."],
        )
        resolved_res = SchedulerResult(
            schedule={},
            score=0,
            is_complete=True,
            warnings=["Program already complete."],
        )
        return resolved_res, skel_res

    # This set accumulates *specific courses* identified by `generate_semester` calls.
    # It's used as input for `taken_courses_set` in subsequent `generate_semester` calls.
    current_cumulative_specific_courses = initial_taken_courses_set.copy()

    generated_skeleton_map: Dict[str, TermRequisiteData] = {}
    sequence_generation_warnings: List[str] = []

    is_skeleton_complete = (
        False  # Tracks if the skeleton generation loop thinks it completed the program
    )
    # Target difficulty for each semester; could be made more dynamic.
    DEFAULT_TARGET_DIFFICULTY = 3.0

    for _ in range(max_terms):  # Loop to generate semesters
        term_id_str = f"{main_current_term.capitalize()} {main_current_year}"

        try:
            # `generate_semester` gets the set of specific courses taken up to *before* the current term.
            # It returns the planned requirements for the term and whether the program *would be* complete
            # if those requirements (including specific courses and category placeholders) are met.
            term_plan_data, program_would_be_complete = await generate_semester(
                program_reqs=program_reqs,
                course_lookups=course_lookups,
                term=main_current_term,
                year=main_current_year,
                taken_courses_set=current_cumulative_specific_courses,  # Pass specific courses accumulated so far
                target_difficulty=DEFAULT_TARGET_DIFFICULTY,
                credit_limits=credit_limits,
                db_session=db_session,
            )
        except ValueError as e:  # Raised by generate_semester (e.g. credit limits)
            msg = f"Sequence generation halted: generate_semester failed for {term_id_str}. Reason: {e}"
            logger.error(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_complete = (
                False  # Program definitely not complete if a semester fails
            )
            break  # Stop generating more terms

        if term_plan_data.is_empty() and not program_would_be_complete:
            # If generate_semester returns an empty plan AND doesn't think the program is complete,
            # it means no valid courses/requirements could be scheduled for this term, and we're stuck.
            msg = f"Sequence generation halted: No courses could be scheduled for {term_id_str}, but program not yet complete."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_complete = False
            break

        generated_skeleton_map[term_id_str] = term_plan_data

        # Update `current_cumulative_specific_courses` with *specific courses* from the just-planned term
        for req in term_plan_data.requirement:
            if req.kind == "COURSE":
                current_cumulative_specific_courses.add(req.value)

        is_skeleton_complete = (
            program_would_be_complete  # Update overall completion status
        )
        if is_skeleton_complete:
            logger.info(
                f"Skeleton generation for {program_reqs.code} indicates program completion after {term_id_str}."
            )
            break  # Program requirements are covered by the skeleton

        # Advance to the next term
        next_term_info = get_next_term(main_current_term, main_current_year)
        main_current_term = next_term_info["term"]
        main_current_year = next_term_info["year"]
    else:  # max_terms reached without `is_skeleton_complete` becoming True
        if not is_skeleton_complete:
            msg = f"Sequence generation for {program_reqs.code} reached max_terms ({max_terms}) without completing the skeleton."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)

    # Create the SchedulerSkeletonResult
    skeleton_score_val = float(
        len(generated_skeleton_map)
    )  # Simple score: number of terms

    final_skeleton_result = SchedulerSkeletonResult(
        schedule=generated_skeleton_map,
        score=skeleton_score_val,
        is_complete=is_skeleton_complete,  # Reflects if skeleton structure covers all requirements
        warnings=sequence_generation_warnings,
    )

    # If the skeleton map is empty AND the program wasn't complete initially AND the skeleton isn't marked complete,
    # it means a failure occurred very early or nothing could be scheduled.
    # The initial completion check handles the "already complete" case.
    if (
        not generated_skeleton_map
        and not is_skeleton_complete
        and not _is_program_complete_v2(
            program_reqs,
            initial_taken_courses_set,
            course_lookups,
            p_specific_req_codes,
            p_tech_elective_pool,
        )
    ):
        logger.warning(
            f"No schedule skeleton generated for {program_reqs.code}, and program was not initially complete. Resolution will be skipped."
        )
        return (
            None,
            final_skeleton_result,
        )  # Return skeleton (possibly empty with warnings) and None for resolved

    # Resolve category requirements in the generated skeleton
    logger.info(f"Resolving category requirements for program {program_reqs.code}...")
    resolved_final_result = await resolve_category_requirements(
        program_reqs=program_reqs,
        course_lookups=course_lookups,
        initial_taken_courses=initial_taken_courses_set,  # Crucially, pass the original set here
        schedule_skeleton=final_skeleton_result,
        db_session=db_session,
        program_specific_required_codes=p_specific_req_codes,  # Pass derived sets
        program_technical_elective_pool=p_tech_elective_pool,
    )

    return resolved_final_result, final_skeleton_result
