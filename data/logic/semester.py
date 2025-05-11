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
    parse_prerequisites,
    parse_corequisites,
    filter_parsed_requisites,
)

logger = logging.getLogger(__name__)
# Configure basic logging if not already configured by the application
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,  # Set to DEBUG for most verbose output
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Output to console
            logging.FileHandler("scheduler.log"),  # Output to file
        ],
    )

equivalences_dict = {
    "INGE3016": set("CIIC3015"),
}


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
    is_complete: bool  # This reflects the skeleton's *estimate* of completion
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
        if course_code in equivalences_dict:
            options = equivalences_dict[course_code].union({course_code})
            return any(option in completed_courses for option in options)
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
    if (
        course_code in technical_course_codes
    ):  # Assumes this is checked after required_course_codes
        return "technical"

    prefix = course_code[:4]
    category = None  # Default
    if prefix == "EDFI":
        return "kinesiology"
    if prefix == "INGL":
        return "english"
    if prefix == "ESPA":
        return "spanish"

    # Handle humanities and social categories
    humanities_prefixes = [
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
    ]  # FRAN for French
    social_prefixes = ["CISO", "CIPO", "SOCI", "ECON", "PSIC", "HIST", "GEOG", "ANTR"]

    if prefix in humanities_prefixes:
        category = "humanities"
    elif prefix in social_prefixes:
        category = "social"

    if category:
        return "sociohumanistics" if group_sociohumanistics else category
    return "free"


def get_course_priority(category: str) -> float:
    PRIORITY_MAP = {
        "required": 1.0,
        "technical": 2.0,
        "english": 3.0,
        "spanish": 3.0,
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
    if current_term_index == (len(TERMS) - 1):  # Moving from Fall to Spring
        next_year = current_year + 1
    return {"term": next_term_name, "year": next_year}


def _is_program_complete_v2(
    program_reqs: Program,
    current_taken_courses: Set[str],
    course_lookups: Dict[str, Dict],
    program_specific_required_codes: Set[str],
    program_technical_elective_pool: Set[str],
    context_message: str = "Program completion check",
) -> bool:
    if not program_specific_required_codes.issubset(current_taken_courses):
        missing_specific = program_specific_required_codes - current_taken_courses
        logger.info(
            f"{context_message}: Incomplete. Missing specific courses ({len(missing_specific)}): {list(missing_specific)[:5]}{'...' if len(missing_specific) > 5 else ''}"
        )
        return False

    credits_met_for_category = defaultdict(int)
    for course_code in current_taken_courses:
        if (
            course_code not in program_specific_required_codes
        ):  # Non-specific courses count towards gen-ed/electives
            # Determine category without grouping sociohumanistics for accumulation
            category = get_course_category(
                course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
                group_sociohumanistics=program_reqs.sociohumanistics > 0,
            )
            course_data = course_lookups.get(course_code)
            if course_data:
                credits_met_for_category[category] += course_data["credits"]
            else:
                logger.warning(
                    f"{context_message}: Course {course_code} not in lookups during credit sum."
                )

    target_category_credits = {
        "english": program_reqs.english or 0,
        "spanish": program_reqs.spanish or 0,
        "humanities": program_reqs.humanities or 0,
        "social": program_reqs.social or 0,
        "sociohumanistics": program_reqs.sociohumanistics or 0,
        "technical": program_reqs.technical or 0,
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }

    all_direct_categories_met = True
    for cat, required_val in target_category_credits.items():
        if (
            required_val > 0 and credits_met_for_category[cat] < required_val
        ):  # Only check if target > 0
            logger.info(
                f"{context_message}: Category '{cat}' incomplete: "
                f"{credits_met_for_category[cat]}/{required_val} credits."
            )
            all_direct_categories_met = (
                False  # Don't return early, log all missing categories
            )

    if not all_direct_categories_met:
        return False

    logger.info(f"{context_message}: All requirements appear to be met.")
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
    if term.lower().endswith("summer"):
        credit_limits = {"min": 0, "max": 6}
    term_id_str = f"{term.capitalize()} {year}"
    logger.info(f"--- Generating semester skeleton for: {term_id_str} ---")
    logger.debug(
        f"{term_id_str}: Received {len(taken_or_planned_specific_courses_set)} taken/planned specific courses. Sample: {list(taken_or_planned_specific_courses_set)[:5]}"
    )
    logger.debug(
        f"{term_id_str}: Received prior category credits planned in skeleton: {prior_category_credits_planned_in_skeleton}"
    )

    try:
        required_courses_req_data_json = json.loads(program_reqs.courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"{term_id_str}: Failed to parse program course JSON for {program_reqs.code}: {e}"
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
    logger.info(
        f"{term_id_str}: Considering {len(remaining_specific_course_codes)} remaining specific required courses: {list(remaining_specific_course_codes)[:20]}{'...' if len(remaining_specific_course_codes)>20 else ''}"
    )
    specific_courses_added_to_pool_count = 0
    for course_code in remaining_specific_course_codes:
        course_data = course_lookups.get(course_code)
        if not course_data:
            logger.warning(
                f"{term_id_str}: Course {course_code} (required) not in course_lookups. Skipping."
            )
            continue

        prereqs_raw = course_data.get("prerequisites_raw")
        if prereqs_raw:
            try:
                parsed_prereqs = parse_prerequisites(prereqs_raw)
                # Assuming filter_parsed_requisites might take these, adjust if signature differs
                filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
            except Exception as parse_exc:
                logger.error(
                    f"{term_id_str}: Error parsing/filtering prereqs for {course_code}: {parse_exc}. Skipping."
                )
                continue

            if not check_requisites_recursive(
                filtered_prereqs, taken_or_planned_specific_courses_set
            ):
                logger.debug(
                    f"{term_id_str}: Prerequisites not met for specific course {course_code}. Skipping."
                )
                continue

        # Availability check now uses term name and db_session (predict_availability was updated)
        is_available = await predict_availability(course_code, term, db_session)
        if not is_available:
            logger.debug(
                f"{term_id_str}: Specific course {course_code} predicted unavailable. Skipping."
            )
            continue

        category_for_priority = get_course_category(  # Used for priority, not for general category fulfillment here
            course_code,
            program_specific_required_codes,
            program_technical_elective_pool,
            group_sociohumanistics=program_reqs.sociohumanistics > 0,
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
        specific_courses_added_to_pool_count += 1
    logger.debug(
        f"{term_id_str}: Added {specific_courses_added_to_pool_count} specific courses to consideration pool."
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
        f"{term_id_str}: Target category credits from program (for placeholders): {target_category_credits_map}"
    )

    credits_met_by_actual_courses_for_category = defaultdict(int)
    for taken_course_code in taken_or_planned_specific_courses_set:
        # Only non-program-specific courses count towards general category fulfillment.
        if taken_course_code not in program_specific_required_codes:
            cat = get_course_category(
                taken_course_code,
                program_specific_required_codes,
                program_technical_elective_pool,
                group_sociohumanistics=program_reqs.sociohumanistics > 0,
            )
            if taken_course_code in course_lookups:
                credits_met_by_actual_courses_for_category[cat] += course_lookups[
                    taken_course_code
                ]["credits"]
            else:  # Should not happen if taken_or_planned_specific_courses_set is derived from course_lookups based items
                logger.warning(
                    f"{term_id_str}: Course {taken_course_code} from 'taken_or_planned' set not in lookups during category credit calc."
                )

    logger.debug(
        f"{term_id_str}: Credits for categories met by actual (non-specific required) taken/planned courses: {dict(credits_met_by_actual_courses_for_category)}"
    )
    logger.info(
        f"{term_id_str}: Credits for categories accounted for by prior skeleton category placeholders: {dict(prior_category_credits_planned_in_skeleton)}"
    )

    category_placeholders_added_count = 0
    for (
        category_name,
        total_target_credits_for_cat,
    ) in target_category_credits_map.items():
        if total_target_credits_for_cat == 0:
            continue  # Skip if category not required

        credits_from_actual_taken_non_specific = (
            credits_met_by_actual_courses_for_category[category_name]
        )
        credits_from_prior_skeleton_placeholders = (
            prior_category_credits_planned_in_skeleton.get(category_name, 0)
        )

        total_credits_accounted_for = (
            credits_from_actual_taken_non_specific
            + credits_from_prior_skeleton_placeholders
        )
        needed_credits_for_placeholders = (
            total_target_credits_for_cat - total_credits_accounted_for
        )

        logger.info(
            f"{term_id_str}: Category '{category_name}': Target={total_target_credits_for_cat}, ActualNonSpecificMet={credits_from_actual_taken_non_specific}, PriorSkeletonMet={credits_from_prior_skeleton_placeholders}, NeedPlaceholdersFor={needed_credits_for_placeholders}"
        )

        if needed_credits_for_placeholders <= 0:
            continue

        num_3_credit_chunks = needed_credits_for_placeholders // 3
        remaining_offshoot_credits = needed_credits_for_placeholders % 3
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
            category_placeholders_added_count += 1
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
            category_placeholders_added_count += 1
    logger.info(
        f"{term_id_str}: Added {category_placeholders_added_count} category placeholders to pool. Total items in pool before sort: {len(current_semester_requirements_pool)}"
    )

    current_semester_requirements_pool.sort(
        key=lambda r: (r.priority, abs(r.difficulty - target_difficulty))
    )

    # 3. Select requirements for the semester
    proposed_semester_data = TermRequisiteData()
    # Tracks specific courses added to THIS semester's skeleton, for co-req checks within this term
    specific_courses_added_this_term_skeleton = set()

    eligible_reqs_copy = list(current_semester_requirements_pool)
    while proposed_semester_data.credits < credit_limits["max"] and eligible_reqs_copy:
        selected_req_obj = None
        selected_req_idx = -1

        for i, req_candidate in enumerate(eligible_reqs_copy):
            if (
                proposed_semester_data.credits + req_candidate.credits
                > credit_limits["max"]
            ):
                continue  # Would exceed max credits

            if req_candidate.kind == "COURSE":
                course_code_cand = req_candidate.value
                course_cand_data = course_lookups[
                    course_code_cand
                ]  # Should exist if added to pool
                coreqs_raw = course_cand_data.get("corequisites_raw")
                if coreqs_raw:
                    try:
                        parsed_coreqs = parse_corequisites(coreqs_raw)
                        filtered_coreqs = filter_parsed_requisites(parsed_coreqs)
                    except Exception as parse_exc:
                        logger.error(
                            f"{term_id_str}: Error parsing/filtering coreqs for {course_code_cand}: {parse_exc}. Considering co-reqs not met."
                        )
                        continue  # Skip if parsing fails

                    # Co-reqs check: (all taken/planned specific courses before this term) + (specific courses already added to THIS term's skeleton)
                    co_req_check_set = taken_or_planned_specific_courses_set.union(
                        specific_courses_added_this_term_skeleton
                    )
                    if not check_requisites_recursive(
                        filtered_coreqs, co_req_check_set
                    ):
                        logger.debug(
                            f"{term_id_str}: Course {course_code_cand} co-reqs not met with {len(co_req_check_set)} courses. Skipping for this term's skeleton."
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
            logger.debug(
                f"{term_id_str}: Selecting requirement for skeleton: {selected_req_obj.kind} {selected_req_obj.value} ({selected_req_obj.credits}cr)"
            )
            proposed_semester_data.requirement.append(selected_req_obj)
            proposed_semester_data.credits += selected_req_obj.credits
            proposed_semester_data.difficulty_sum += selected_req_obj.difficulty
            if selected_req_obj.kind == "COURSE":
                specific_courses_added_this_term_skeleton.add(selected_req_obj.value)
            eligible_reqs_copy.pop(selected_req_idx)
        else:
            logger.debug(
                f"{term_id_str}: No more eligible requirements found that fit credit limit or meet co-reqs."
            )
            break

    logger.info(
        f"{term_id_str}: Proposed semester skeleton: {len(proposed_semester_data.requirement)} items, {proposed_semester_data.credits} credits."
    )
    if logger.isEnabledFor(logging.DEBUG):
        for req_item in proposed_semester_data.requirement:
            logger.debug(
                f"  - Skeleton Item: {req_item.kind} {req_item.value} ({req_item.credits}cr)"
            )

    # 4. Estimate program completion based on this new skeleton term

    # All specific courses taken/planned up to and INCLUDING this term's skeleton
    all_specifics_in_skeleton_so_far = taken_or_planned_specific_courses_set.union(
        specific_courses_added_this_term_skeleton
    )
    all_specific_courses_covered_estimate = program_specific_required_codes.issubset(
        all_specifics_in_skeleton_so_far
    )
    if not all_specific_courses_covered_estimate:
        missing_s = program_specific_required_codes - all_specifics_in_skeleton_so_far
        logger.debug(
            f"{term_id_str}: Skeleton completion estimate: Still missing {len(missing_s)} specific courses like {list(missing_s)[:3]}"
        )

    all_category_credits_covered_estimate = True
    current_term_category_credits_planned = defaultdict(int)
    for req in proposed_semester_data.requirement:
        if req.kind == "COURSE_CATEGORY":
            current_term_category_credits_planned[req.value] += req.credits

    for cat_name, target_credits in target_category_credits_map.items():
        if target_credits == 0:
            continue
        met_by_actuals_non_specific = credits_met_by_actual_courses_for_category[
            cat_name
        ]
        met_by_prior_skeleton_placeholders = (
            prior_category_credits_planned_in_skeleton.get(cat_name, 0)
        )
        met_by_current_term_placeholders = current_term_category_credits_planned[
            cat_name
        ]
        total_cat_covered_estimate = (
            met_by_actuals_non_specific
            + met_by_prior_skeleton_placeholders
            + met_by_current_term_placeholders
        )

        if total_cat_covered_estimate < target_credits:
            all_category_credits_covered_estimate = False
            logger.debug(
                f"{term_id_str}: Skeleton completion estimate: Category '{cat_name}' estimated coverage {total_cat_covered_estimate}/{target_credits}."
            )

    program_would_be_complete_estimate = (
        all_specific_courses_covered_estimate
        and all_category_credits_covered_estimate
        # and socio_met_estimate
    )
    logger.info(
        f"{term_id_str}: Program completion estimate (skeleton based): {program_would_be_complete_estimate}"
    )

    # Validate credit limits
    is_empty_and_min_is_zero = (
        proposed_semester_data.is_empty() and credit_limits.get("min", 0) == 0
    )
    if (
        not is_empty_and_min_is_zero
        and proposed_semester_data.credits < credit_limits.get("min", 1)
    ):  # default min 1 if not specified
        if (
            not program_would_be_complete_estimate
        ):  # If not complete AND under min credits (and not an allowed empty sem)
            warning_msg = (
                f"Term {term_id_str}: Generated semester skeleton has {proposed_semester_data.credits} credits, "
                f"less than min ({credit_limits.get('min',1)}), and program skeleton is not yet estimated complete."
            )
            logger.warning(warning_msg)  # This is a critical failure for this term
            raise ValueError(warning_msg)
        else:  # Program is estimated complete, but this last semester is under min_credits. Might be acceptable.
            logger.info(
                f"{term_id_str}: Semester credits ({proposed_semester_data.credits}) below min ({credit_limits.get('min',1)}), but program skeleton IS estimated complete. Allowing."
            )

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
    final_warnings = list(
        schedule_skeleton.warnings
    )  # Start with warnings from skeleton phase

    # Tracks all courses assigned throughout the resolution process, term by term,
    # starting with courses taken before the skeleton begins.
    globally_resolved_and_taken_courses = initial_taken_courses.copy()
    logger.debug(
        f"Resolution starting with {len(globally_resolved_and_taken_courses)} initial_taken_courses."
    )

    term_order_map = {"spring": 0, "firstsummer": 1, "secondsummer": 2, "fall": 3}
    try:
        sorted_term_keys = sorted(
            schedule_skeleton.schedule.keys(),
            key=lambda tk: (
                int(tk.split()[1]),
                term_order_map.get(tk.split()[0].lower(), 99),
            ),  # Use 99 for unknown sort last
        )
    except Exception as e:  # Fallback if term keys are malformed
        logger.error(
            f"Error sorting term keys '{list(schedule_skeleton.schedule.keys())}' for resolution: {e}. Using unsorted."
        )
        sorted_term_keys = list(schedule_skeleton.schedule.keys())

    for term_key in sorted_term_keys:
        logger.info(f"Resolving term: {term_key}")
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
        current_term_name_for_api = term_name_parts[
            0
        ].lower()  # ensure lowercase for predict_availability
        current_term_year_for_api = int(term_name_parts[1])

        # 1. Process concrete "COURSE" requirements first for this term
        for req in term_skeleton_data.requirement:
            if req.kind == "COURSE":
                course_code = req.value
                # Check if already resolved globally or in this term (shouldn't happen if skeleton is clean)
                if (
                    course_code in globally_resolved_and_taken_courses
                    or course_code in courses_resolved_this_term_set
                ):
                    logger.warning(
                        f"{term_key}: Course {course_code} (from skeleton) seems to be a duplicate or already taken/resolved. Skipping in resolution."
                    )
                    continue

                course_info = course_lookups.get(course_code)
                if not course_info:
                    msg = f"Error: Course {course_code} (from skeleton) missing from lookups for {term_key}. Cannot resolve."
                    logger.error(msg)
                    if msg not in final_warnings:
                        final_warnings.append(msg)
                    continue

                logger.debug(
                    f"  {term_key}: Adding specific course from skeleton: {course_code}"
                )
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
                    f"  {term_key}: Attempting to resolve category '{category_to_fill}' for {credits_for_slot}cr"
                )

                candidate_pool: List[str] = []
                if category_to_fill == "technical":
                    # Technical electives must come from the program's defined pool
                    # And must not be a course already designated as a specific program requirement
                    for c_code in program_technical_elective_pool:
                        if (
                            c_code not in program_specific_required_codes
                        ):  # Ensure it's a true elective
                            candidate_pool.append(c_code)
                    logger.debug(
                        f"    {term_key}: Technical elective candidate pool (size {len(candidate_pool)}): {candidate_pool[:10] if candidate_pool else 'Empty'}{'...' if len(candidate_pool)>10 else ''}"
                    )
                else:  # For humanities, social, english, spanish, free, kinesiology
                    for c_code, c_lookup_data in course_lookups.items():
                        if c_code in program_specific_required_codes:
                            continue  # Cannot use a specific req to fill a gen-ed category here

                        # Determine actual category of candidate (without grouping sociohumanistics)
                        actual_course_cat = get_course_category(
                            c_code,
                            program_specific_required_codes,
                            program_technical_elective_pool,
                            group_sociohumanistics=program_reqs.sociohumanistics > 0,
                        )

                        if category_to_fill == "free":
                            # "Free" electives can be anything not specifically required by program,
                            # and not part of the technical pool (unless no technical credits are needed, then it's truly free).
                            # Simplification: if it's in tech pool, it's not "free" unless tech credits are full.
                            # For now, allow any non-specific, non-technical-pool course for "free".
                            if actual_course_cat not in [
                                "required",
                                "technical",
                            ]:  # Allow if its category is not "required" or "technical"
                                candidate_pool.append(c_code)
                        else:  # Specific categories (humanities, social, etc.)
                            if actual_course_cat == category_to_fill:
                                # Additionally, ensure a non-technical category is not filled by a designated technical elective
                                # unless that technical elective is truly 'free' because technical credits are already met.
                                # This is complex. Simpler: if it's in tech pool, it's for tech credits first.
                                if c_code not in program_technical_elective_pool:
                                    candidate_pool.append(c_code)
                                # else:
                                # logger.debug(f"    {term_key}: Candidate {c_code} is in tech pool, not using for '{category_to_fill}'.")
                    if (
                        logger.isEnabledFor(logging.DEBUG)
                        and category_to_fill != "technical"
                    ):
                        logger.debug(
                            f"    {term_key}: Gen-Ed '{category_to_fill}' candidate pool (size {len(candidate_pool)}): {candidate_pool[:10] if candidate_pool else 'Empty'}{'...' if len(candidate_pool)>10 else ''}"
                        )

                random.shuffle(candidate_pool)  # For variety in selection
                found_match_for_category = False
                for cand_course_code in candidate_pool:
                    # Check if already taken globally or resolved in this term, or not in lookups
                    if cand_course_code in globally_resolved_and_taken_courses:
                        continue  # logger.debug(f"    Skipping candidate {cand_course_code} (globally taken/resolved).");
                    if cand_course_code in courses_resolved_this_term_set:
                        continue  # logger.debug(f"    Skipping candidate {cand_course_code} (resolved this term).");
                    if (
                        cand_course_code not in course_lookups
                    ):  # Should not happen if pool is from course_lookups
                        logger.warning(
                            f"    {term_key}: Candidate {cand_course_code} from pool not in lookups. Skipping."
                        )
                        continue

                    cand_course_data = course_lookups[cand_course_code]
                    if (
                        cand_course_data["credits"] != credits_for_slot
                    ):  # Simplification: exact credit match
                        # logger.debug(f"    Skipping candidate {cand_course_code} (credit mismatch: {cand_course_data['credits']} vs {credits_for_slot}).")
                        continue

                    is_available = await predict_availability(
                        cand_course_code,
                        current_term_name_for_api,
                        db_session,
                    )
                    if not is_available:
                        # logger.debug(f"    Skipping candidate {cand_course_code} (predicted unavailable for {current_term_name_for_api} {current_term_year_for_api}).")
                        continue

                    # Check Prerequisites (against courses taken *before* this term)
                    prereqs_r = cand_course_data.get("prerequisites_raw")
                    if prereqs_r:
                        try:
                            parsed_pr = parse_prerequisites(prereqs_r)
                            filtered_pr = filter_parsed_requisites(parsed_pr)
                        except Exception as parse_exc:
                            logger.error(
                                f"    {term_key}: Error parsing/filtering prereqs for {cand_course_code}: {parse_exc}. Skipping."
                            )
                            continue
                        if not check_requisites_recursive(
                            filtered_pr, taken_courses_before_this_term
                        ):
                            # logger.debug(f"    Skipping candidate {cand_course_code} (prereqs not met against {len(taken_courses_before_this_term)} courses).")
                            continue

                    # Check Co-requisites (against (taken before this term) + (all courses resolved in *this* term so far))
                    coreqs_r = cand_course_data.get("corequisites_raw")
                    if coreqs_r:
                        try:
                            parsed_co = parse_corequisites(coreqs_r)
                            filtered_co = filter_parsed_requisites(parsed_co)
                        except Exception as parse_exc:
                            logger.error(
                                f"    {term_key}: Error parsing/filtering coreqs for {cand_course_code}: {parse_exc}. Skipping."
                            )
                            continue
                        co_req_check_set = taken_courses_before_this_term.union(
                            courses_resolved_this_term_set
                        )
                        if not check_requisites_recursive(
                            filtered_co, co_req_check_set
                        ):
                            # logger.debug(f"    Skipping candidate {cand_course_code} (coreqs not met against {len(co_req_check_set)} courses).")
                            continue

                    logger.debug(
                        f"    {term_key}: Selected {cand_course_code} for category '{category_to_fill}' ({credits_for_slot}cr)"
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
                    break  # Move to next category requirement in this term

                if not found_match_for_category:
                    msg = f"Term {term_key}: Could not resolve category '{category_to_fill}' ({credits_for_slot} cr). No suitable candidate found."
                    logger.warning(msg)
                    if msg not in final_warnings:
                        final_warnings.append(msg)

        resolved_schedule_map[term_key] = current_term_resolved_termdata
        # Update globally tracked courses with those resolved in this term
        globally_resolved_and_taken_courses.update(courses_resolved_this_term_set)

        logger.info(
            f"Finished resolving term {term_key}. Courses: {current_term_resolved_termdata.courses}, Credits: {current_term_resolved_termdata.credits}"
        )
        logger.debug(
            f"  Globally resolved/taken courses count after {term_key}: {len(globally_resolved_and_taken_courses)}"
        )

    # Determine final completion status based on all resolved courses
    is_schedule_truly_complete = _is_program_complete_v2(
        program_reqs,
        globally_resolved_and_taken_courses,
        course_lookups,
        program_specific_required_codes,
        program_technical_elective_pool,
        context_message="Final program completion check after resolution",
    )
    logger.info(
        f"Final program completion status after resolution: {is_schedule_truly_complete}"
    )
    if not is_schedule_truly_complete:
        logger.warning(
            "Program is NOT complete after resolving the skeleton. Check debug logs from 'Final program completion check' for details."
        )

    return SchedulerResult(
        schedule=resolved_schedule_map,
        score=schedule_skeleton.score,  # Score could be re-evaluated based on resolved data if desired
        is_complete=is_schedule_truly_complete,
        warnings=list(set(final_warnings)),  # Unique warnings
    )


async def generate_sequence(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    start_term_name: str,
    start_year: int,
    initial_taken_courses_set: Set[str],
    credit_limits: Dict,
    db_session: AsyncSession,
    max_terms: int = 15,  # Default max terms if not specified
) -> Tuple[Optional[SchedulerResult], Optional[SchedulerSkeletonResult]]:

    logger.info(
        f"--- Starting Schedule Sequence Generation for Program {program_reqs.code} ---"
    )
    logger.info(
        f"Start: {start_term_name.capitalize()} {start_year}, Initial courses: {len(initial_taken_courses_set)}"
    )
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            f"Initial taken courses ({len(initial_taken_courses_set)}): {list(initial_taken_courses_set)[:10]}{'...' if len(initial_taken_courses_set)>10 else ''}"
        )
    logger.info(f"Credit limits: {credit_limits}, Max terms: {max_terms}")

    main_current_term = start_term_name.lower()
    main_current_year = start_year

    try:
        prog_courses_json = json.loads(program_reqs.courses or "{}")
        prog_tech_electives_json = json.loads(program_reqs.technical_courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"CRITICAL: Failed to parse program JSON for {program_reqs.code} at sequence start: {e}"
        )
        return None, None  # Cannot proceed

    p_specific_req_codes = set(prog_courses_json.keys())
    p_tech_elective_pool = set(prog_tech_electives_json.keys())
    if logger.isEnabledFor(logging.DEBUG):
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
        "Initial check",
    ):
        logger.info(
            f"Program {program_reqs.code} is ALREADY COMPLETE with provided initial courses."
        )
        skel_res = SchedulerSkeletonResult(
            schedule={},
            score=0,
            is_complete=True,
            warnings=["Program already complete."],
        )
        # For already complete, resolved result is same as skeleton (empty schedule)
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
    cumulative_category_credits_planned_in_skeleton = defaultdict(int)

    generated_skeleton_map: Dict[str, TermRequisiteData] = {}
    sequence_generation_warnings: List[str] = []

    is_skeleton_estimated_complete = (
        False  # Tracks if the skeleton generation loop thinks it completed the program
    )
    DEFAULT_TARGET_DIFFICULTY = 3.0  # Could be made dynamic

    for term_count in range(max_terms):  # Loop to generate skeleton terms
        term_id_str = f"{main_current_term.capitalize()} {main_current_year}"
        logger.info(
            f"--- Attempting skeleton for term {term_count + 1}/{max_terms}: {term_id_str} ---"
        )

        try:
            term_plan_data, program_would_be_complete_estimate = (
                await generate_semester(
                    program_reqs=program_reqs,
                    course_lookups=course_lookups,
                    term=main_current_term,
                    year=main_current_year,
                    taken_or_planned_specific_courses_set=cumulative_specific_courses_taken_or_planned_in_skeleton,
                    prior_category_credits_planned_in_skeleton=cumulative_category_credits_planned_in_skeleton,
                    target_difficulty=DEFAULT_TARGET_DIFFICULTY,
                    credit_limits=credit_limits,
                    db_session=db_session,
                )
            )
        except (
            ValueError
        ) as e:  # Raised by generate_semester (e.g. credit limits not met for non-final term)
            msg = f"Sequence generation HALTED: generate_semester failed for {term_id_str}. Reason: {e}"
            logger.error(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_estimated_complete = (
                False  # Program definitely not complete if a semester fails to form
            )
            break  # Stop generating more terms for skeleton

        if term_plan_data.is_empty() and not program_would_be_complete_estimate:
            # If generate_semester returns an empty plan AND doesn't think the program is complete,
            # it means no valid courses/requirements could be scheduled for this term, and we're stuck.
            msg = f"Sequence generation HALTED: No courses/requirements could be scheduled for {term_id_str} (empty skeleton term), but program skeleton not yet estimated complete."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)
            is_skeleton_estimated_complete = False
            break

        generated_skeleton_map[term_id_str] = term_plan_data

        # Update cumulative trackers based on the just-planned term's skeleton
        new_specifics_this_term = 0
        new_cat_credits_this_term = defaultdict(int)
        for req in term_plan_data.requirement:
            if req.kind == "COURSE":
                if (
                    req.value
                    not in cumulative_specific_courses_taken_or_planned_in_skeleton
                ):
                    cumulative_specific_courses_taken_or_planned_in_skeleton.add(
                        req.value
                    )
                    new_specifics_this_term += 1
            elif req.kind == "COURSE_CATEGORY":
                cumulative_category_credits_planned_in_skeleton[
                    req.value
                ] += req.credits
                new_cat_credits_this_term[req.value] += req.credits

        logger.debug(
            f"After {term_id_str} skeleton: Added {new_specifics_this_term} new specific courses. Total specifics planned: {len(cumulative_specific_courses_taken_or_planned_in_skeleton)}"
        )
        if new_cat_credits_this_term:
            logger.debug(
                f"After {term_id_str} skeleton: Added category credits: {dict(new_cat_credits_this_term)}. Total category credits planned: {dict(cumulative_category_credits_planned_in_skeleton)}"
            )

        is_skeleton_estimated_complete = (
            program_would_be_complete_estimate  # Update overall completion status
        )
        if is_skeleton_estimated_complete:
            logger.info(
                f"Skeleton generation for {program_reqs.code} ESTIMATES program completion after {term_id_str}."
            )
            break  # Program requirements are covered by the skeleton (estimated)

        # Advance to the next term
        next_term_info = get_next_term(main_current_term, main_current_year)
        main_current_term = next_term_info["term"]
        main_current_year = next_term_info["year"]
    else:  # max_terms reached without `is_skeleton_estimated_complete` becoming True
        if not is_skeleton_estimated_complete:
            msg = f"Sequence generation for {program_reqs.code} reached max_terms ({max_terms}) without ESTIMATING skeleton completion."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)

    # Create the SchedulerSkeletonResult
    skeleton_score_val = float(
        len(generated_skeleton_map)
    )  # Simple score: number of terms

    final_skeleton_result = SchedulerSkeletonResult(
        schedule=generated_skeleton_map,
        score=skeleton_score_val,
        is_complete=is_skeleton_estimated_complete,  # Reflects if skeleton structure *estimates* it covers all requirements
        warnings=list(set(sequence_generation_warnings)),  # Unique warnings
    )

    # Log details of the generated skeleton, especially if not complete
    logger.info(
        f"--- Skeleton Generation Phase Complete for {program_reqs.code}. Is Skeleton Estimated Complete: {is_skeleton_estimated_complete} ---"
    )
    if not final_skeleton_result.schedule and not is_skeleton_estimated_complete:
        logger.warning(
            f"No skeleton terms were generated for {program_reqs.code}, and skeleton is not estimated complete."
        )
    elif (
        logger.isEnabledFor(logging.DEBUG) or not is_skeleton_estimated_complete
    ):  # Log full skeleton if debug or incomplete
        logger.info("Full Generated Skeleton:")
        for term_key_log, term_req_data_log in final_skeleton_result.schedule.items():
            logger.info(
                f"  Skeleton Term {term_key_log}: {term_req_data_log.credits}cr, {len(term_req_data_log.requirement)} items"
            )
            for req_item_log in term_req_data_log.requirement:
                logger.info(
                    f"    - Requirement: {req_item_log.kind} {req_item_log.value} ({req_item_log.credits}cr, Prio:{req_item_log.priority}, Diff:{req_item_log.difficulty})"
                )

    if not generated_skeleton_map and not is_skeleton_estimated_complete:
        # This implies the program wasn't initially complete and no skeleton could be formed.
        if not _is_program_complete_v2(
            program_reqs,
            initial_taken_courses_set,
            course_lookups,
            p_specific_req_codes,
            p_tech_elective_pool,
            "Check before skipping resolution",
        ):
            logger.warning(
                f"No schedule skeleton generated for {program_reqs.code}, and program was not initially complete. RESOLUTION WILL BE SKIPPED."
            )
            return (
                None,
                final_skeleton_result,
            )  # Return skeleton (possibly empty with warnings) and None for resolved

    # Proceed to resolve category requirements in the generated skeleton
    resolved_final_result = await resolve_category_requirements(
        program_reqs=program_reqs,
        course_lookups=course_lookups,
        initial_taken_courses=initial_taken_courses_set,  # Resolution starts from original taken set
        schedule_skeleton=final_skeleton_result,
        db_session=db_session,
        program_specific_required_codes=p_specific_req_codes,
        program_technical_elective_pool=p_tech_elective_pool,
    )

    logger.info(
        f"--- Schedule Sequence Generation and Resolution Finished for Program {program_reqs.code} ---"
    )
    return resolved_final_result, final_skeleton_result
