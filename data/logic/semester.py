import asyncio
import json
import logging
import math
import random
import statistics
from collections import defaultdict
from typing import Any, List, Dict, Set, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.database.database import Program, Course
from data.logic.availability import predict_availability

from data.parser.parser_utils import (
    flatten_requisites_to_list,
    parse_prerequisites,
    parse_corequisites,
    filter_parsed_requisites,
)

logger = logging.getLogger(__name__)
# Configure basic logging if not already configured by the application
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# Pydantic models
class TermData(BaseModel):
    courses: List[str] = []
    credits: int = 0
    difficulty_sum: float = 0.0


class SchedulerResult(BaseModel):
    schedule: Dict[str, TermData]
    score: float
    is_complete: bool
    warnings: List[str] = []
    rank: int = 0


class Requirement(BaseModel):
    kind: str
    value: str
    credits: int = 0
    difficulty: float = 0.0
    priority: float = 0.0


class TermRequisiteData(BaseModel):
    requirement: List[Requirement] = []
    credits: int = 0
    difficulty_sum: float = 0.0

    def is_empty(self):
        return not self.requirement


class SchedulerSkeletonResult(BaseModel):
    schedule: Dict[str, TermRequisiteData]
    score: float
    is_complete: bool
    warnings: List[str] = []


# Helper functions
async def load_program_data(program_code: str, db: AsyncSession) -> Optional[Program]:
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
    if not req_dict or not isinstance(req_dict, dict):
        return True

    req_type = req_dict.get("type")

    if req_type == "COURSE":
        course_code = req_dict.get("value", "").replace(" ", "")
        return course_code in completed_courses
    elif req_type == "AND":
        conditions = req_dict.get("conditions", [])
        if not conditions:
            return True
        return all(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "OR":
        conditions = req_dict.get("conditions", [])
        if not conditions:
            return False
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "ANDOR":
        conditions = req_dict.get("value", [])
        if not isinstance(conditions, list) or not conditions:
            return False
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "FOR":
        logger.debug(
            f"Encountered 'FOR' type during requisite check, treating as met: {req_dict}"
        )
        return True
    else:
        logger.warning(
            f"Unexpected node type in check_requisites_recursive: {req_type} for {req_dict}"
        )
        return False


def get_course_category(
    course_code: str,
    required_course_codes: set[str],
    technical_course_codes: set[str],
    group_sociohumanistics: bool = False,
) -> str:
    if course_code in required_course_codes:
        return "required"
    if course_code in technical_course_codes:
        return "technical"

    prefix = course_code[:4]
    category = None
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
    return "free"


def get_course_priority(category: str) -> float:
    PRIORITY_MAP = {
        "required": 1.0,
        "technical": 2.0,
        "english": 3.0,
        "spanish": 3.0,  # Corrected typo "techniucal"
        "humanities": 4.0,
        "social": 4.0,
        "sociohumanistics": 4.0,
        "free": 5.0,
        "kinesiology": 6.0,
    }
    return PRIORITY_MAP.get(category, 5.0)


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
    if not program_specific_required_codes.issubset(current_taken_courses):
        missing_specific = program_specific_required_codes - current_taken_courses
        logger.debug(
            f"Program completion check: Incomplete. Missing specific courses: {missing_specific}"
        )
        return False

    credits_met_for_category = defaultdict(int)
    for course_code in current_taken_courses:
        if course_code not in program_specific_required_codes:
            category = get_course_category(
                course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
            )
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
        "technical": program_reqs.technical or 0,
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }

    all_categories_met = True
    for cat, required_val in target_category_credits.items():
        if credits_met_for_category[cat] < required_val:
            logger.debug(
                f"Program completion check: Category '{cat}' incomplete: "
                f"{credits_met_for_category[cat]}/{required_val} credits."
            )
            all_categories_met = False
    if not all_categories_met:
        return False

    if program_reqs.sociohumanistics and program_reqs.sociohumanistics > 0:
        total_huma_social_met = (
            credits_met_for_category["humanities"] + credits_met_for_category["social"]
        )
        if total_huma_social_met < (program_reqs.sociohumanistics or 0):
            logger.debug(
                f"Program completion check: Incomplete. Sociohumanistics: "
                f"{total_huma_social_met}/{program_reqs.sociohumanistics} credits."
            )
            return False

    logger.info("Program completion check: All requirements appear to be met.")
    return True


async def generate_semester(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    term: str,
    year: int,
    # This set includes:
    # 1. Courses initially taken by the student.
    # 2. Specific 'COURSE' type requirements planned in previous skeleton terms.
    taken_or_planned_specific_courses_set: Set[str],
    # This dict tracks credits for 'COURSE_CATEGORY' requirements
    # planned (but not yet resolved to specific courses) in previous skeleton terms.
    prior_category_credits_planned_in_skeleton: Dict[str, int],
    target_difficulty: float,
    credit_limits: Dict,
    db_session: AsyncSession,
) -> tuple[TermRequisiteData, bool]:
    term_id_str = f"{term.capitalize()} {year}"
    logger.info(f"--- Generating semester skeleton for: {term_id_str} ---")
    logger.debug(
        f"Received {len(taken_or_planned_specific_courses_set)} taken/planned specific courses: {taken_or_planned_specific_courses_set if len(taken_or_planned_specific_courses_set) < 10 else '...'}"
    )
    logger.debug(
        f"Received prior category credits planned in skeleton: {prior_category_credits_planned_in_skeleton}"
    )

    try:
        required_courses_req_data_json = json.loads(program_reqs.courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse program course JSON for {program_reqs.code} in generate_semester: {e}"
        )
        raise

    program_specific_required_codes = set(required_courses_req_data_json.keys())
    program_technical_elective_pool = set(
        json.loads(program_reqs.technical_courses or "{}").keys()
    )

    current_semester_requirements_pool: List[Requirement] = []

    # 1. Add specific required courses to the pool if eligible
    remaining_specific_course_codes = (
        program_specific_required_codes - taken_or_planned_specific_courses_set
    )
    logger.debug(
        f"{term_id_str}: Remaining specific required courses to consider: {remaining_specific_course_codes}"
    )

    for course_code in remaining_specific_course_codes:
        course_data = course_lookups.get(course_code)
        if not course_data:
            logger.warning(
                f"{term_id_str}: Course {course_code} (required) not in course_lookups. Skipping."
            )
            continue

        prereqs_raw = course_data.get("prerequisites_raw")
        if prereqs_raw:
            parsed_prereqs = parse_prerequisites(prereqs_raw)
            filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
            # Check against courses already taken/planned (specifics) before this term
            if not check_requisites_recursive(
                filtered_prereqs, taken_or_planned_specific_courses_set
            ):
                logger.debug(
                    f"{term_id_str}: Prerequisites not met for specific course {course_code}. Skipping."
                )
                continue

        is_available = await predict_availability(course_code, term, db_session)
        if not is_available:
            logger.debug(
                f"{term_id_str}: Specific course {course_code} predicted unavailable. Skipping."
            )
            continue

        category_for_priority = get_course_category(
            course_code,
            program_specific_required_codes,
            program_technical_elective_pool,
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
    logger.debug(
        f"{term_id_str}: Added {len([r for r in current_semester_requirements_pool if r.kind == 'COURSE'])} specific courses to consideration pool."
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
    logger.debug(
        f"{term_id_str}: Target category credits from program: {target_category_credits_map}"
    )

    # Credits for categories met by *actual courses taken or planned as specific requirements*
    # (i.e., from taken_or_planned_specific_courses_set)
    credits_met_by_actual_courses_for_category = defaultdict(int)
    for taken_course_code in taken_or_planned_specific_courses_set:
        if (
            taken_course_code not in program_specific_required_codes
        ):  # Only non-specific courses count towards general categories
            cat = get_course_category(
                taken_course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
            )
            if taken_course_code in course_lookups:  # Ensure course exists in lookups
                credits_met_by_actual_courses_for_category[cat] += course_lookups[
                    taken_course_code
                ]["credits"]
            else:
                logger.warning(
                    f"{term_id_str}: Course {taken_course_code} from 'taken_or_planned_specific_courses_set' not in lookups during category credit calculation."
                )

    logger.debug(
        f"{term_id_str}: Credits met by actual taken/planned courses for categories: {dict(credits_met_by_actual_courses_for_category)}"
    )
    logger.debug(
        f"{term_id_str}: Credits accounted for by prior skeleton category placeholders: {dict(prior_category_credits_planned_in_skeleton)}"
    )

    for (
        category_name,
        total_target_credits_for_category,
    ) in target_category_credits_map.items():
        credits_from_actual_taken = credits_met_by_actual_courses_for_category[
            category_name
        ]
        credits_from_prior_skeleton = prior_category_credits_planned_in_skeleton.get(
            category_name, 0
        )

        total_credits_accounted_for = (
            credits_from_actual_taken + credits_from_prior_skeleton
        )
        needed_credits = total_target_credits_for_category - total_credits_accounted_for

        logger.debug(
            f"{term_id_str}: Category '{category_name}': Target={total_target_credits_for_category}, ActualTakenMet={credits_from_actual_taken}, PriorSkeletonMet={credits_from_prior_skeleton}, Needed={needed_credits}"
        )

        if needed_credits <= 0:
            continue

        num_3_credit_chunks = needed_credits // 3
        remaining_offshoot_credits = needed_credits % 3
        cat_priority = get_course_priority(category_name)
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
    logger.debug(
        f"{term_id_str}: Total items in requirements pool (specifics + categories) before sorting: {len(current_semester_requirements_pool)}"
    )

    current_semester_requirements_pool.sort(
        key=lambda r: (r.priority, abs(r.difficulty - target_difficulty))
    )

    # 3. Select requirements for the semester
    proposed_semester_data = TermRequisiteData()
    courses_added_this_term_codes = set()

    eligible_reqs_copy = list(current_semester_requirements_pool)
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
                    # Co-reqs check: (taken before this term overall) + (specific courses already added to this term's skeleton)
                    if not check_requisites_recursive(
                        filtered_coreqs,
                        taken_or_planned_specific_courses_set.union(
                            courses_added_this_term_codes
                        ),
                    ):
                        logger.debug(
                            f"{term_id_str}: Course {course_code_cand} co-reqs not met. Skipping for this term."
                        )
                        continue
                selected_req_obj = req_candidate
                selected_req_idx = i
                break
            elif req_candidate.kind == "COURSE_CATEGORY":
                selected_req_obj = req_candidate
                selected_req_idx = i
                break

        if selected_req_obj:
            logger.debug(
                f"{term_id_str}: Selecting requirement: {selected_req_obj.kind} {selected_req_obj.value} ({selected_req_obj.credits}cr)"
            )
            proposed_semester_data.requirement.append(selected_req_obj)
            proposed_semester_data.credits += selected_req_obj.credits
            proposed_semester_data.difficulty_sum += selected_req_obj.difficulty
            if selected_req_obj.kind == "COURSE":
                courses_added_this_term_codes.add(selected_req_obj.value)
            eligible_reqs_copy.pop(selected_req_idx)
        else:
            logger.debug(
                f"{term_id_str}: No more eligible requirements found or credit limit nearly reached."
            )
            break

    logger.info(
        f"{term_id_str}: Proposed semester skeleton: {len(proposed_semester_data.requirement)} items, {proposed_semester_data.credits} credits."
    )
    for req_item in proposed_semester_data.requirement:
        logger.debug(
            f"  - Skeleton Item: {req_item.kind} {req_item.value} ({req_item.credits}cr)"
        )

    # 4. Validate credit limits and determine program completion status
    is_empty_and_min_is_zero = (
        proposed_semester_data.is_empty() and credit_limits["min"] == 0
    )

    # Tentative set of specific courses if this semester's specific courses are taken
    tentative_all_specific_courses = taken_or_planned_specific_courses_set.union(
        courses_added_this_term_codes
    )

    # For _is_program_complete_v2, we need to simulate that category placeholders are filled.
    # This is tricky. _is_program_complete_v2 works on *actual resolved courses*.
    # The `program_would_be_complete` flag from generate_semester is more of an estimate.
    # Let's define `program_would_be_complete` based on whether all *specific* courses are covered
    # AND all *category credit targets* are covered by the sum of:
    #   1. Actual taken courses (from `taken_or_planned_specific_courses_set` that are not program specific)
    #   2. Category placeholders from prior skeleton terms (`prior_category_credits_planned_in_skeleton`)
    #   3. Category placeholders from this current term's skeleton (`proposed_semester_data` for `COURSE_CATEGORY`)

    temp_all_taken_or_planned_specifics = taken_or_planned_specific_courses_set.union(
        courses_added_this_term_codes
    )

    # Check if all specific courses are covered by this point
    all_specific_courses_covered = program_specific_required_codes.issubset(
        temp_all_taken_or_planned_specifics
    )

    # Check if all category credits are covered by placeholders and actuals
    all_category_credits_covered = True
    current_term_category_credits_planned = defaultdict(int)
    for req in proposed_semester_data.requirement:
        if req.kind == "COURSE_CATEGORY":
            current_term_category_credits_planned[req.value] += req.credits

    for cat_name, target_credits in target_category_credits_map.items():
        met_by_actuals = credits_met_by_actual_courses_for_category[cat_name]
        met_by_prior_skeleton = prior_category_credits_planned_in_skeleton.get(
            cat_name, 0
        )
        met_by_current_skeleton = current_term_category_credits_planned[cat_name]
        total_covered_for_cat = (
            met_by_actuals + met_by_prior_skeleton + met_by_current_skeleton
        )
        if total_covered_for_cat < target_credits:
            all_category_credits_covered = False
            logger.debug(
                f"{term_id_str}: Program completion estimate: Category '{cat_name}' still needs {target_credits - total_covered_for_cat} credits."
            )
            break

    program_would_be_complete_estimate = (
        all_specific_courses_covered and all_category_credits_covered
    )
    logger.info(
        f"{term_id_str}: Program completion estimate (skeleton based): {program_would_be_complete_estimate} (Specifics covered: {all_specific_courses_covered}, Categories covered: {all_category_credits_covered})"
    )

    if (
        not is_empty_and_min_is_zero
        and proposed_semester_data.credits < credit_limits["min"]
    ):
        if (
            not program_would_be_complete_estimate
        ):  # If not complete and under min credits
            warning_msg = (
                f"Term {term_id_str}: Generated semester skeleton has {proposed_semester_data.credits} credits, "
                f"less than min ({credit_limits['min']}), and program skeleton is not yet complete."
            )
            logger.warning(warning_msg)
            raise ValueError(warning_msg)  # Critical failure

    return proposed_semester_data, program_would_be_complete_estimate


async def resolve_category_requirements(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    initial_taken_courses: Set[str],
    schedule_skeleton: SchedulerSkeletonResult,
    db_session: AsyncSession,
    program_specific_required_codes: Set[str],
    program_technical_elective_pool: Set[str],
) -> SchedulerResult:
    logger.info("--- Resolving Category Requirements for Skeleton ---")
    resolved_schedule_map: Dict[str, TermData] = {}
    final_warnings = list(schedule_skeleton.warnings)
    globally_resolved_and_taken_courses = initial_taken_courses.copy()

    term_order_map = {"spring": 0, "firstsummer": 1, "secondsummer": 2, "fall": 3}
    try:
        sorted_term_keys = sorted(
            schedule_skeleton.schedule.keys(),
            key=lambda tk: (int(tk.split()[1]), term_order_map[tk.split()[0].lower()]),
        )
    except Exception as e:
        logger.error(
            f"Error sorting term keys '{list(schedule_skeleton.schedule.keys())}': {e}. Using unsorted."
        )
        sorted_term_keys = list(schedule_skeleton.schedule.keys())

    for term_key in sorted_term_keys:
        logger.info(f"Resolving term: {term_key}")
        term_skeleton_data = schedule_skeleton.schedule[term_key]
        current_term_resolved_termdata = TermData()
        taken_courses_before_this_term = globally_resolved_and_taken_courses.copy()
        courses_resolved_this_term_set = set()

        term_name_parts = term_key.split()
        current_term_name_for_api = term_name_parts[0]
        current_term_year_for_api = int(term_name_parts[1])

        # 1. Process concrete "COURSE" requirements first
        for req in term_skeleton_data.requirement:
            if req.kind == "COURSE":
                course_code = req.value
                if (
                    course_code in globally_resolved_and_taken_courses
                    or course_code in courses_resolved_this_term_set
                ):
                    logger.warning(
                        f"Course {course_code} in term {term_key} (skeleton) is duplicate/already taken. Skipping."
                    )
                    continue
                course_info = course_lookups.get(course_code)
                if not course_info:
                    msg = f"Error: Course {course_code} (skeleton) missing from lookups for {term_key}."
                    logger.error(msg)
                    final_warnings.append(msg)
                    continue

                logger.debug(f"  Adding specific course from skeleton: {course_code}")
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
                logger.debug(
                    f"  Attempting to resolve category '{category_to_fill}' for {credits_for_slot}cr"
                )

                candidate_pool: List[str] = []
                if category_to_fill == "technical":
                    for c_code in program_technical_elective_pool:
                        if c_code not in program_specific_required_codes:
                            candidate_pool.append(c_code)
                    logger.debug(
                        f"    Technical elective candidate pool (size {len(candidate_pool)}): {candidate_pool[:10]}{'...' if len(candidate_pool)>10 else ''}"
                    )
                else:
                    for c_code, c_lookup_data in course_lookups.items():
                        if c_code in program_specific_required_codes:
                            continue
                        actual_course_cat = get_course_category(
                            c_code,
                            program_specific_required_codes,
                            program_technical_elective_pool,
                        )
                        if category_to_fill == "free":
                            pass
                        else:
                            if actual_course_cat != category_to_fill:
                                continue
                            if c_code in program_technical_elective_pool:
                                continue
                        candidate_pool.append(c_code)
                    # logger.debug(f"    Gen-Ed '{category_to_fill}' candidate pool (size {len(candidate_pool)}): {candidate_pool[:10]}{'...' if len(candidate_pool)>10 else ''}")

                random.shuffle(candidate_pool)
                found_match_for_category = False
                for cand_course_code in candidate_pool:
                    if (
                        cand_course_code in globally_resolved_and_taken_courses
                        or cand_course_code in courses_resolved_this_term_set
                        or cand_course_code not in course_lookups
                    ):
                        # logger.debug(f"    Skipping candidate {cand_course_code} (already taken/resolved this term).")
                        continue

                    cand_course_data = course_lookups[cand_course_code]
                    if cand_course_data["credits"] != credits_for_slot:
                        # logger.debug(f"    Skipping candidate {cand_course_code} (credit mismatch: {cand_course_data['credits']} vs {credits_for_slot}).")
                        continue

                    is_available = await predict_availability(
                        cand_course_code, current_term_name_for_api, db_session
                    )
                    if not is_available:
                        # logger.debug(f"    Skipping candidate {cand_course_code} (predicted unavailable).")
                        continue

                    prereqs_r = cand_course_data.get("prerequisites_raw")
                    if prereqs_r:
                        parsed_pr = parse_prerequisites(prereqs_r)
                        filtered_pr = filter_parsed_requisites(parsed_pr)
                        if not check_requisites_recursive(
                            filtered_pr, taken_courses_before_this_term
                        ):
                            # logger.debug(f"    Skipping candidate {cand_course_code} (prereqs not met).")
                            continue
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
                            # logger.debug(f"    Skipping candidate {cand_course_code} (coreqs not met).")
                            continue

                    logger.debug(
                        f"    Selected {cand_course_code} for category '{category_to_fill}'"
                    )
                    current_term_resolved_termdata.courses.append(cand_course_code)
                    current_term_resolved_termdata.credits += cand_course_data[
                        "credits"
                    ]
                    current_term_resolved_termdata.difficulty_sum += cand_course_data[
                        "difficulty"
                    ]
                    courses_resolved_this_term_set.add(cand_course_code)
                    found_match_for_category = True
                    break

                if not found_match_for_category:
                    msg = f"Term {term_key}: Could not resolve category '{category_to_fill}' ({credits_for_slot} cr)."
                    logger.warning(msg)
                    final_warnings.append(msg)

        resolved_schedule_map[term_key] = current_term_resolved_termdata
        globally_resolved_and_taken_courses.update(courses_resolved_this_term_set)
        logger.info(
            f"Finished resolving term {term_key}. Courses: {current_term_resolved_termdata.courses}, Credits: {current_term_resolved_termdata.credits}"
        )
        logger.debug(
            f"  Globally resolved/taken courses count: {len(globally_resolved_and_taken_courses)}"
        )

    is_schedule_truly_complete = _is_program_complete_v2(
        program_reqs,
        globally_resolved_and_taken_courses,
        course_lookups,
        program_specific_required_codes,
        program_technical_elective_pool,
    )
    logger.info(
        f"Final program completion status after resolution: {is_schedule_truly_complete}"
    )
    if not is_schedule_truly_complete:
        logger.warning("Program is NOT complete after resolving the skeleton.")
        # The _is_program_complete_v2 function already logs details on what's missing.

    return SchedulerResult(
        schedule=resolved_schedule_map,
        score=schedule_skeleton.score,
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
    logger.info(
        f"--- Starting Schedule Sequence Generation for Program {program_reqs.code} ---"
    )
    logger.info(
        f"Start: {start_term_name.capitalize()} {start_year}, Initial courses: {len(initial_taken_courses_set)}"
    )
    logger.debug(
        f"Initial taken courses: {initial_taken_courses_set if len(initial_taken_courses_set) < 10 else 'first 10...'}"
    )
    logger.info(f"Credit limits: {credit_limits}, Max terms: {max_terms}")

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

    p_specific_req_codes = set(prog_courses_json.keys())
    p_tech_elective_pool = set(prog_tech_electives_json.keys())
    logger.debug(
        f"Program specific required codes ({len(p_specific_req_codes)}): {list(p_specific_req_codes)[:10]}{'...' if len(p_specific_req_codes)>10 else ''}"
    )
    logger.debug(
        f"Program technical elective pool ({len(p_tech_elective_pool)}): {list(p_tech_elective_pool)[:10]}{'...' if len(p_tech_elective_pool)>10 else ''}"
    )

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

    # Accumulates SPECIFIC 'COURSE' type requirements planned in the skeleton so far,
    # PLUS the initial_taken_courses_set.
    cumulative_specific_courses_taken_or_planned_in_skeleton = (
        initial_taken_courses_set.copy()
    )

    # Accumulates credits for 'COURSE_CATEGORY' requirements planned in the skeleton so far.
    # Key: category_name (e.g., "english"), Value: total credits planned for this category in skeleton.
    cumulative_category_credits_planned_in_skeleton = defaultdict(int)

    generated_skeleton_map: Dict[str, TermRequisiteData] = {}
    sequence_generation_warnings: List[str] = []
    is_skeleton_estimated_complete = False
    DEFAULT_TARGET_DIFFICULTY = 3.0  # Could be made dynamic based on user preferences

    for term_count in range(max_terms):
        term_id_str = f"{main_current_term.capitalize()} {main_current_year}"
        logger.info(
            f"Generating skeleton for term {term_count + 1}/{max_terms}: {term_id_str}"
        )

        try:
            term_plan_data, program_would_be_complete_estimate = (
                await generate_semester(
                    program_reqs=program_reqs,
                    course_lookups=course_lookups,
                    term=main_current_term,
                    year=main_current_year,
                    taken_or_planned_specific_courses_set=cumulative_specific_courses_taken_or_planned_in_skeleton,
                    prior_category_credits_planned_in_skeleton=cumulative_category_credits_planned_in_skeleton,  # Pass the accumulated category credits
                    target_difficulty=DEFAULT_TARGET_DIFFICULTY,
                    credit_limits=credit_limits,
                    db_session=db_session,
                )
            )
        except ValueError as e:
            msg = f"Sequence generation halted: generate_semester failed for {term_id_str}. Reason: {e}"
            logger.error(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_estimated_complete = False
            break

        if term_plan_data.is_empty() and not program_would_be_complete_estimate:
            msg = f"Sequence generation halted: No courses/requirements could be scheduled for {term_id_str} via skeleton, but program skeleton not yet estimated complete."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_estimated_complete = False
            break

        generated_skeleton_map[term_id_str] = term_plan_data

        # Update cumulative trackers based on the just-planned term's skeleton
        for req in term_plan_data.requirement:
            if req.kind == "COURSE":
                cumulative_specific_courses_taken_or_planned_in_skeleton.add(req.value)
            elif req.kind == "COURSE_CATEGORY":
                cumulative_category_credits_planned_in_skeleton[
                    req.value
                ] += req.credits

        logger.debug(
            f"After {term_id_str} skeleton: Cumulative specific courses planned: {len(cumulative_specific_courses_taken_or_planned_in_skeleton)}"
        )
        logger.debug(
            f"After {term_id_str} skeleton: Cumulative category credits planned: {dict(cumulative_category_credits_planned_in_skeleton)}"
        )

        is_skeleton_estimated_complete = program_would_be_complete_estimate
        if is_skeleton_estimated_complete:
            logger.info(
                f"Skeleton generation for {program_reqs.code} estimates program completion after {term_id_str}."
            )
            break

        next_term_info = get_next_term(main_current_term, main_current_year)
        main_current_term = next_term_info["term"]
        main_current_year = next_term_info["year"]
    else:  # max_terms reached
        if not is_skeleton_estimated_complete:
            msg = f"Sequence generation for {program_reqs.code} reached max_terms ({max_terms}) without estimating skeleton completion."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)

    skeleton_score_val = float(len(generated_skeleton_map))
    final_skeleton_result = SchedulerSkeletonResult(
        schedule=generated_skeleton_map,
        score=skeleton_score_val,
        is_complete=is_skeleton_estimated_complete,  # This is the estimate from skeleton phase
        warnings=sequence_generation_warnings,
    )

    if (
        not generated_skeleton_map
        and not is_skeleton_estimated_complete
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
        return None, final_skeleton_result

    logger.info(
        f"--- Skeleton Generation Complete for {program_reqs.code}. Is Skeleton Estimated Complete: {is_skeleton_estimated_complete} ---"
    )
    if not is_skeleton_estimated_complete:
        logger.warning(
            f"Skeleton for {program_reqs.code} is NOT marked as complete. Proceeding to resolution phase anyway."
        )
    for term_key, term_req_data in final_skeleton_result.schedule.items():
        logger.debug(f"  Skeleton Term {term_key}: {term_req_data.credits}cr")
        for req_item in term_req_data.requirement:
            logger.debug(
                f"    - {req_item.kind} {req_item.value} ({req_item.credits}cr)"
            )

    resolved_final_result = await resolve_category_requirements(
        program_reqs=program_reqs,
        course_lookups=course_lookups,
        initial_taken_courses=initial_taken_courses_set,  # Start resolution with only the truly initial courses
        schedule_skeleton=final_skeleton_result,
        db_session=db_session,
        program_specific_required_codes=p_specific_req_codes,
        program_technical_elective_pool=p_tech_elective_pool,
    )
    logger.info(
        f"--- Schedule Sequence Generation and Resolution Finished for Program {program_reqs.code} ---"
    )
    return resolved_final_result, final_skeleton_result
