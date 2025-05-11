import asyncio
import json
import logging
import math
import random
import statistics
from collections import defaultdict
from typing import Any, List, Dict, Set, Optional, Tuple, Literal

# from data.models import course # Assuming this import is not strictly needed for the provided snippet
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
    import os
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/scheduler.log"),
        ],
    )

equivalences_dict = {
    "INGE3016": {
        "CIIC3015",
    },
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

    def __hash__(self):
        # Hash based on kind, value, and credits for uniqueness in exclusion lists
        # Difficulty and priority are for sorting/selection, not fundamental identity for exclusion
        return hash((self.kind, self.value, self.credits))

    def __eq__(self, other):
        if not isinstance(other, Requirement):
            return NotImplemented
        return (self.kind, self.value, self.credits) == (
            other.kind,
            other.value,
            other.credits,
        )


class TermRequisiteData(BaseModel):
    requirement: List[Requirement] = []
    credits: int = 0
    difficulty_sum: float = 0.0

    def is_empty(self):
        return not self.requirement


class SchedulerSkeletonResult(BaseModel):
    schedule: Dict[
        str, TermRequisiteData
    ]  # Represents the skeletons that led to successful resolution
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
        all_courses_db = result.scalars().all()  # Renamed to avoid conflict
        for course_db_obj in all_courses_db:
            lookup[course_db_obj.course_code] = {
                "credits": course_db_obj.credits or 0,
                "difficulty": course_db_obj.difficulty or 0,
                "highest_ancestor": course_db_obj.highest_ancestor or 0,
                "prerequisites_raw": course_db_obj.prerequisites,
                "corequisites_raw": course_db_obj.corequisites,
                "last_Fall": course_db_obj.last_Fall or 0,
                "last_Spring": course_db_obj.last_Spring or 0,
                "last_FirstSummer": course_db_obj.last_FirstSummer or 0,
                "last_SecondSummer": course_db_obj.last_SecondSummer or 0,
                "last_ExtendedSummer": course_db_obj.last_ExtendedSummer or 0,
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
    elif req_type == "ANDOR":  # Assuming OR of (possibly complex) conditions
        conditions = req_dict.get(
            "value", []
        )  # Or "conditions" based on your parser's output
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
        return False  # Fail safe for unknown types


def get_course_category(
    course_code: str,
    required_course_codes: set[str],
    technical_course_codes: set[str],
    group_sociohumanistics: bool = False,
) -> str:
    # This function is typically called for non-program-specific courses when determining category fulfillment.
    if course_code in required_course_codes:
        # This case should ideally be filtered out before calling, if purpose is category fulfillment.
        # For priority setting of specific courses, it's fine.
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
    ]
    social_prefixes = ["CISO", "CIPO", "SOCI", "ECON", "PSIC", "HIST", "GEOG", "ANTR"]

    if prefix in humanities_prefixes:
        category = "humanities"
    elif prefix in social_prefixes:
        category = "social"

    if category:
        return "sociohumanistics" if group_sociohumanistics else category
    return "free"  # Default to free if no other category matches


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
    return PRIORITY_MAP.get(category, 5.0)  # Default priority for unknown categories


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
    if current_term_index == (
        len(TERMS) - 1
    ):  # Moving from Fall to Spring (last term in list)
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
    for course_code_val in current_taken_courses:
        if course_code_val not in program_specific_required_codes:
            category = get_course_category(
                course_code_val,
                program_specific_required_codes,
                program_technical_elective_pool,
                group_sociohumanistics=program_reqs.sociohumanistics > 0,
            )
            course_data = course_lookups.get(course_code_val)
            if course_data:
                credits_met_for_category[category] += course_data["credits"]
            else:
                logger.warning(
                    f"{context_message}: Course {course_code_val} not in lookups during credit sum."
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
        if required_val > 0 and credits_met_for_category[cat] < required_val:
            logger.info(
                f"{context_message}: Category '{cat}' incomplete: "
                f"{credits_met_for_category[cat]}/{required_val} credits."
            )
            all_direct_categories_met = False  # Log all missing, don't return early

    if not all_direct_categories_met:
        return False

    logger.info(f"{context_message}: All requirements appear to be met.")
    return True


async def generate_semester(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    term: str,
    year: int,
    resolved_courses_before_this_term: Set[str],
    category_credits_met_by_prior_resolved_courses: Dict[str, int],
    target_difficulty: float,
    credit_limits: Dict,  # Base credit limits
    db_session: AsyncSession,
    exclusion_list: Optional[List[Requirement]] = None,
) -> tuple[
    TermRequisiteData, bool
]:  # Returns (TermSkeleton, EstimatedProgramCompletionAfterThisSkeleton)

    current_credit_limits = credit_limits.copy()  # Use a copy to modify for summer
    if term.lower().endswith("summer"):
        current_credit_limits = {"min": 0, "max": 6}  # Override for summer terms

    term_id_str = f"{term.capitalize()} {year}"
    logger.info(
        f"--- Generating semester skeleton for: {term_id_str} (Iterative Method) ---"
    )
    if exclusion_list:
        logger.debug(
            f"  Exclusion list for this generation attempt ({len(exclusion_list)} items): {[f'{r.kind}:{r.value}({r.credits}cr)' for r in exclusion_list[:5]]}{'...' if len(exclusion_list) > 5 else ''}"
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
        program_specific_required_codes - resolved_courses_before_this_term
    )
    for course_code in remaining_specific_course_codes:
        course_data = course_lookups.get(course_code)
        if not course_data:
            logger.warning(
                f"{term_id_str}: Course {course_code} (required) not in lookups. Skipping."
            )
            continue

        # Create a representative Requirement to check against exclusion list
        # Priority/difficulty aren't part of exclusion identity here
        req_obj_for_exclusion_check = Requirement(
            kind="COURSE", value=course_code, credits=course_data["credits"]
        )
        if (
            exclusion_list and req_obj_for_exclusion_check in exclusion_list
        ):  # Relies on Requirement.__eq__
            logger.debug(
                f"  {term_id_str}: Specific course {course_code} is in exclusion list for this attempt. Skipping."
            )
            continue

        prereqs_raw = course_data.get("prerequisites_raw")
        if prereqs_raw:
            try:
                parsed_prereqs = parse_prerequisites(prereqs_raw)
                filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
                if not check_requisites_recursive(
                    filtered_prereqs, resolved_courses_before_this_term
                ):
                    logger.debug(
                        f"{term_id_str}: Prerequisites not met for specific course {course_code}. Skipping."
                    )
                    continue
            except Exception as parse_exc:
                logger.error(
                    f"{term_id_str}: Error parsing/filtering prereqs for {course_code}: {parse_exc}. Skipping."
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

    # 2. Calculate and add category requirements (COURSE_CATEGORY) placeholders
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

    for (
        category_name,
        total_target_credits_for_cat,
    ) in target_category_credits_map.items():
        if total_target_credits_for_cat == 0:
            continue

        credits_from_prior_resolved = (
            category_credits_met_by_prior_resolved_courses.get(category_name, 0)
        )
        needed_credits_for_placeholders = (
            total_target_credits_for_cat - credits_from_prior_resolved
        )

        if needed_credits_for_placeholders <= 0:
            continue

        # Common credits for placeholders are 3, then remaining.
        # This could be made more flexible (e.g. allow 1, 2 credit placeholders too)
        num_3_credit_chunks = needed_credits_for_placeholders // 3
        remaining_offshoot_credits = needed_credits_for_placeholders % 3

        cat_priority = get_course_priority(category_name)
        est_difficulty = (
            2.5 if category_name not in ["technical", "required"] else 3.0
        )  # Generic estimate

        for _ in range(num_3_credit_chunks):
            req_placeholder = Requirement(
                kind="COURSE_CATEGORY", value=category_name, credits=3
            )
            if exclusion_list and req_placeholder in exclusion_list:
                logger.debug(
                    f"  {term_id_str}: Category placeholder {category_name} (3cr) in exclusion list. Skipping for this attempt."
                )
                continue
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
            req_placeholder = Requirement(
                kind="COURSE_CATEGORY",
                value=category_name,
                credits=remaining_offshoot_credits,
            )
            if exclusion_list and req_placeholder in exclusion_list:
                logger.debug(
                    f"  {term_id_str}: Category placeholder {category_name} ({remaining_offshoot_credits}cr) in exclusion list. Skipping for this attempt."
                )
                continue
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

    # 3. Select requirements for the semester from the pool
    proposed_semester_data = TermRequisiteData()
    specific_courses_added_this_term_skeleton = (
        set()
    )  # For co-req checks within this term's skeleton

    eligible_reqs_copy = list(current_semester_requirements_pool)
    while (
        proposed_semester_data.credits < current_credit_limits["max"]
        and eligible_reqs_copy
    ):
        selected_req_obj = None
        selected_req_idx = -1

        for i, req_candidate in enumerate(eligible_reqs_copy):
            # Note: Exclusion check was done when building the pool. If it were done here,
            # it would be `if exclusion_list and req_candidate in exclusion_list: continue`

            if (
                proposed_semester_data.credits + req_candidate.credits
                > current_credit_limits["max"]
            ):
                continue

            if req_candidate.kind == "COURSE":
                course_code_cand = req_candidate.value
                course_cand_data = course_lookups.get(
                    course_code_cand
                )  # Should exist if in pool
                if not course_cand_data:
                    continue

                coreqs_raw = course_cand_data.get("corequisites_raw")
                if coreqs_raw:
                    try:
                        parsed_coreqs = parse_corequisites(coreqs_raw)
                        filtered_coreqs = filter_parsed_requisites(parsed_coreqs)
                        # Co-reqs check: (resolved before this term) + (specifics added to THIS term's skeleton so far)
                        co_req_check_set = resolved_courses_before_this_term.union(
                            specific_courses_added_this_term_skeleton
                        )
                        if not check_requisites_recursive(
                            filtered_coreqs, co_req_check_set
                        ):
                            logger.debug(
                                f"{term_id_str}: Course {course_code_cand} co-reqs not met for skeleton. Skipping."
                            )
                            continue
                    except Exception as parse_exc:
                        logger.error(
                            f"{term_id_str}: Error parsing/filtering coreqs for {course_code_cand} in skeleton: {parse_exc}. Skipping."
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
            proposed_semester_data.requirement.append(selected_req_obj)
            proposed_semester_data.credits += selected_req_obj.credits
            proposed_semester_data.difficulty_sum += selected_req_obj.difficulty
            if selected_req_obj.kind == "COURSE":
                specific_courses_added_this_term_skeleton.add(selected_req_obj.value)
            eligible_reqs_copy.pop(selected_req_idx)
        else:
            logger.debug(
                f"{term_id_str}: No more eligible requirements found or fit credit limits for skeleton."
            )
            break

    logger.info(
        f"{term_id_str}: Proposed skeleton: {len(proposed_semester_data.requirement)} items, {proposed_semester_data.credits}cr."
    )

    # 4. Estimate program completion based on this new skeleton term
    # Specific courses: (resolved before this term) + (specifics planned in THIS term's skeleton)
    all_specifics_in_skeleton_so_far = resolved_courses_before_this_term.union(
        specific_courses_added_this_term_skeleton
    )
    all_specific_courses_covered_estimate = program_specific_required_codes.issubset(
        all_specifics_in_skeleton_so_far
    )

    # Category credits: (met by prior resolved courses) + (placeholders planned in THIS term's skeleton)
    all_category_credits_covered_estimate = True
    current_term_category_credits_planned_in_skeleton = defaultdict(int)
    for req_item in proposed_semester_data.requirement:
        if req_item.kind == "COURSE_CATEGORY":
            current_term_category_credits_planned_in_skeleton[
                req_item.value
            ] += req_item.credits

    for cat_name, target_credits in target_category_credits_map.items():
        if target_credits == 0:
            continue

        total_cat_covered_estimate = category_credits_met_by_prior_resolved_courses.get(
            cat_name, 0
        ) + current_term_category_credits_planned_in_skeleton.get(cat_name, 0)
        if total_cat_covered_estimate < target_credits:
            all_category_credits_covered_estimate = False
            logger.debug(
                f"{term_id_str}: Skeleton completion estimate: Category '{cat_name}' estimated coverage {total_cat_covered_estimate}/{target_credits}."
            )
            # Don't break, log all category shortfalls for estimate

    program_would_be_complete_estimate = (
        all_specific_courses_covered_estimate and all_category_credits_covered_estimate
    )
    logger.info(
        f"{term_id_str}: Skeleton completion estimate (based on this term's plan): {program_would_be_complete_estimate}"
    )

    # Validate credit limits for the generated skeleton term
    min_credits_for_term = current_credit_limits.get(
        "min", 1 if not term.lower().endswith("summer") else 0
    )
    is_empty_and_min_is_zero = (
        proposed_semester_data.is_empty() and min_credits_for_term == 0
    )

    if (
        not is_empty_and_min_is_zero
        and proposed_semester_data.credits < min_credits_for_term
    ):
        if (
            not program_would_be_complete_estimate
        ):  # If program not estimated complete by this skeleton AND under min credits
            warning_msg = (
                f"Term {term_id_str}: Generated semester skeleton has {proposed_semester_data.credits} credits, "
                f"less than min ({min_credits_for_term}), and program skeleton is not yet estimated complete."
            )
            logger.warning(warning_msg)
            raise ValueError(
                warning_msg
            )  # This is a critical failure for this skeleton generation attempt
        else:  # Program estimated complete by this skeleton, but this (likely final) term is under min_credits. Might be acceptable.
            logger.info(
                f"{term_id_str}: Semester credits ({proposed_semester_data.credits}) below min ({min_credits_for_term}), but program skeleton IS estimated complete. Allowing."
            )

    return proposed_semester_data, program_would_be_complete_estimate


async def resolve_single_semester_skeleton(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    term_skeleton_data: TermRequisiteData,  # The skeleton for the current semester only
    term_key: str,  # e.g., "Fall 2024"
    taken_courses_before_this_term: Set[
        str
    ],  # All courses resolved successfully in previous iterations
    db_session: AsyncSession,
    program_specific_required_codes: Set[str],
    program_technical_elective_pool: Set[str],
) -> Tuple[
    Optional[TermData], List[Requirement]
]:  # (ResolvedTermData or None, List of FAILED Requirement objects from skeleton)

    logger.info(f"--- Resolving skeleton for single semester: {term_key} ---")
    resolved_term_data = TermData()
    courses_resolved_this_term_set = (
        set()
    )  # Tracks courses added (specific or category-filled) within this term
    failed_requirements_in_skeleton: List[Requirement] = (
        []
    )  # Stores Requirement objects from term_skeleton_data that fail

    term_name_parts = term_key.split()
    current_term_name_for_api = term_name_parts[0].lower()  # e.g., "fall"
    # current_term_year_for_api = int(term_name_parts[1]) # Not directly used by predict_availability

    # 1. Process "COURSE" requirements from the skeleton (these are specific courses)
    for req in term_skeleton_data.requirement:
        if req.kind == "COURSE":
            course_code = req.value
            if (
                course_code in taken_courses_before_this_term
                or course_code in courses_resolved_this_term_set
            ):
                logger.warning(
                    f"  {term_key}: Course {course_code} (from skeleton) is a duplicate or already taken/resolved this term. Skipping in resolution."
                )
                # This implies an issue in skeleton generation if it plans already taken/planned courses.
                # Or, if a category was resolved to this specific course earlier in THIS term's resolution.
                # For now, we assume it's okay to skip if already handled.
                continue

            course_info = course_lookups.get(course_code)
            if not course_info:
                logger.error(
                    f"  {term_key}: Course {course_code} (from skeleton) missing from lookups. CANNOT RESOLVE THIS REQUIREMENT."
                )
                failed_requirements_in_skeleton.append(
                    req
                )  # Add the problematic skeleton Requirement
                continue

            # Optional: Re-validate availability/requisites here for robustness, though skeleton should be pre-validated.
            # For now, assume skeleton's specific courses are valid w.r.t. pre-reqs/availability. Co-reqs are trickier.
            # Co-req check (if needed): against taken_courses_before_this_term + courses_resolved_this_term_set

            resolved_term_data.courses.append(course_code)
            resolved_term_data.credits += course_info["credits"]
            resolved_term_data.difficulty_sum += course_info["difficulty"]
            courses_resolved_this_term_set.add(course_code)

    # 2. Resolve "COURSE_CATEGORY" requirements from the skeleton
    for req in term_skeleton_data.requirement:  # Iterate again for categories
        if req.kind == "COURSE_CATEGORY":
            category_to_fill = req.value
            credits_for_slot = req.credits
            logger.debug(
                f"  {term_key}: Attempting to resolve category '{category_to_fill}' for {credits_for_slot}cr (Req object: {req})"
            )

            candidate_pool: List[str] = []
            # Build candidate_pool (similar to original resolve_category_requirements logic)
            if category_to_fill == "technical":
                for c_code in program_technical_elective_pool:
                    if (
                        c_code not in program_specific_required_codes
                    ):  # Must be an elective, not a specific req
                        candidate_pool.append(c_code)
            else:  # For gen-ed categories (english, spanish, humanities, social, free, kinesiology)
                for c_code, c_lookup_data in course_lookups.items():
                    if c_code in program_specific_required_codes:
                        continue  # Cannot use a specific program req to fill gen-ed

                    # Determine actual category of candidate (without grouping sociohumanistics for this matching part)
                    actual_course_cat = get_course_category(
                        c_code,
                        program_specific_required_codes,
                        program_technical_elective_pool,
                        group_sociohumanistics=False,  # Match against base categories first
                    )
                    # If program groups socio, and category_to_fill is "sociohumanistics", adjust matching
                    is_socio_target = (
                        category_to_fill == "sociohumanistics"
                        and program_reqs.sociohumanistics > 0
                    )

                    match_condition = False
                    if is_socio_target:  # Target is "sociohumanistics" (grouped)
                        if (
                            actual_course_cat == "humanities"
                            or actual_course_cat == "social"
                        ):
                            match_condition = True
                    elif (
                        actual_course_cat == category_to_fill
                    ):  # Target is specific (e.g. "humanities", "english")
                        match_condition = True

                    if category_to_fill == "free":  # Free can be many things
                        # A "free" elective should not be a course from the technical elective pool
                        # unless technical elective requirements are already satisfied (more complex check).
                        # Simpler: if it's in tech pool, it's for tech credits.
                        # Also, should not be from other defined categories if they are still needed.
                        # For now: truly "free" means its actual_course_cat is 'free'.
                        if (
                            actual_course_cat == "free"
                        ):  # only pick courses categorized as 'free'
                            match_condition = True
                        else:  # if trying to fill 'free' but course is e.g. 'humanities', don't use it for free unless huma is full
                            match_condition = False  # Stricter 'free' interpretation

                    if match_condition:
                        # Additional check: a gen-ed category should not be filled by a course from the technical elective pool
                        # unless that's explicitly allowed or tech electives are already full.
                        if c_code not in program_technical_elective_pool:
                            candidate_pool.append(c_code)
                        # else: logger.debug(f"    {term_key}: Candidate {c_code} in tech pool, not using for non-tech '{category_to_fill}'.")

            random.shuffle(candidate_pool)
            found_match_for_category_req = False
            for cand_course_code in candidate_pool:
                # Basic checks for candidate viability
                if (
                    cand_course_code in taken_courses_before_this_term
                    or cand_course_code in courses_resolved_this_term_set
                ):  # Already taken or added this term
                    continue

                cand_course_data = course_lookups.get(cand_course_code)
                if not cand_course_data:
                    continue  # Should not happen if pool is from course_lookups

                if (
                    cand_course_data["credits"] != credits_for_slot
                ):  # Simplification: exact credit match for placeholder
                    continue

                is_available = await predict_availability(
                    cand_course_code, current_term_name_for_api, db_session
                )
                if not is_available:
                    continue

                # Check Prerequisites (against courses taken *before* this term)
                prereqs_r = cand_course_data.get("prerequisites_raw")
                if prereqs_r:
                    try:
                        parsed_pr = parse_prerequisites(prereqs_r)
                        filtered_pr = filter_parsed_requisites(parsed_pr)
                        if not check_requisites_recursive(
                            filtered_pr, taken_courses_before_this_term
                        ):
                            continue
                    except Exception as parse_exc:
                        logger.error(
                            f"    {term_key}: Error parsing/filtering prereqs for candidate {cand_course_code}: {parse_exc}. Skipping."
                        )
                        continue

                # Check Co-requisites (against (taken before this term) + (all courses resolved in *this* term so far))
                coreqs_r = cand_course_data.get("corequisites_raw")
                if coreqs_r:
                    try:
                        parsed_co = parse_corequisites(coreqs_r)
                        filtered_co = filter_parsed_requisites(parsed_co)
                        # Co-req check set includes courses already resolved in this term
                        co_req_check_set = taken_courses_before_this_term.union(
                            courses_resolved_this_term_set
                        )
                        if not check_requisites_recursive(
                            filtered_co, co_req_check_set
                        ):
                            continue
                    except Exception as parse_exc:
                        logger.error(
                            f"    {term_key}: Error parsing/filtering coreqs for candidate {cand_course_code}: {parse_exc}. Skipping."
                        )
                        continue

                # If all checks pass, select this candidate
                logger.debug(
                    f"    {term_key}: Selected candidate {cand_course_code} for category '{category_to_fill}' ({credits_for_slot}cr)"
                )
                resolved_term_data.courses.append(cand_course_code)
                resolved_term_data.credits += cand_course_data["credits"]
                resolved_term_data.difficulty_sum += cand_course_data["difficulty"]
                courses_resolved_this_term_set.add(
                    cand_course_code
                )  # Add to set for this term's co-req checks
                found_match_for_category_req = True
                break  # Move to next category requirement in this term's skeleton

            if not found_match_for_category_req:
                msg = f"  {term_key}: Could not resolve category placeholder '{req.value}' ({req.credits} cr). No suitable candidate found."
                logger.warning(msg)
                failed_requirements_in_skeleton.append(
                    req
                )  # Add the skeleton Requirement object that failed

    if failed_requirements_in_skeleton:
        # If any requirement (COURSE or COURSE_CATEGORY) from the skeleton failed to be processed/resolved,
        # then this resolution attempt for the semester has failed.
        return None, failed_requirements_in_skeleton

    # If all requirements from the skeleton were processed successfully (either added or resolved):
    logger.info(
        f"Successfully resolved semester {term_key}. Courses: {resolved_term_data.courses}, Credits: {resolved_term_data.credits}"
    )
    return resolved_term_data, []


async def generate_sequence(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    start_term_name: str,
    start_year: int,
    initial_taken_courses_set: Set[str],
    credit_limits: Dict,  # e.g. {"min": 12, "max": 18} for Fall/Spring
    db_session: AsyncSession,
    max_terms: int = 15,
    max_resolution_attempts_per_semester: int = 3,
) -> Tuple[Optional[SchedulerResult], Optional[SchedulerSkeletonResult]]:

    logger.info(
        f"--- Starting Iterative Schedule Sequence Generation for Program {program_reqs.code} ---"
    )
    logger.info(
        f"Start: {start_term_name.capitalize()} {start_year}, Initial courses: {len(initial_taken_courses_set)}"
    )
    if logger.isEnabledFor(logging.DEBUG) and initial_taken_courses_set:
        logger.debug(
            f"Initial taken courses sample: {list(initial_taken_courses_set)[:5]}"
        )
    logger.info(
        f"Credit limits (base): {credit_limits}, Max terms: {max_terms}, Max resolution attempts/semester: {max_resolution_attempts_per_semester}"
    )

    # Stores the final successfully resolved schedule term by term
    final_resolved_schedule_map: Dict[str, TermData] = {}
    # Stores the skeleton that *led* to a successful resolution for each term
    final_successful_skeletons_map: Dict[str, TermRequisiteData] = {}

    # Tracks all *actually resolved* courses, including initial ones, as the sequence progresses
    globally_resolved_and_taken_courses = initial_taken_courses_set.copy()

    sequence_generation_warnings: List[str] = []
    is_program_fully_resolved = False  # Tracks if the *resolved* program is complete

    main_current_term = start_term_name.lower()
    main_current_year = start_year
    DEFAULT_TARGET_DIFFICULTY = 3.0  # Could be made dynamic or program-specific

    try:
        prog_courses_json = json.loads(program_reqs.courses or "{}")
        prog_tech_electives_json = json.loads(program_reqs.technical_courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"CRITICAL: Failed to parse program JSON for {program_reqs.code} at sequence start: {e}"
        )
        # Cannot proceed without program structure
        return None, None

    p_specific_req_codes = set(prog_courses_json.keys())
    p_tech_elective_pool = set(prog_tech_electives_json.keys())

    # Initial check: Is the program already complete with the provided courses?
    if _is_program_complete_v2(
        program_reqs,
        globally_resolved_and_taken_courses,
        course_lookups,
        p_specific_req_codes,
        p_tech_elective_pool,
        "Initial check",
    ):
        logger.info(
            f"Program {program_reqs.code} is ALREADY COMPLETE with provided initial courses."
        )
        res = SchedulerResult(
            schedule={},
            score=0,
            is_complete=True,
            warnings=["Program already complete."],
        )
        skel_res = SchedulerSkeletonResult(
            schedule={},
            score=0,
            is_complete=True,
            warnings=["Program already complete."],
        )
        return res, skel_res

    # Main loop: iterate through terms up to max_terms
    for term_count in range(max_terms):
        term_id_str = f"{main_current_term.capitalize()} {main_current_year}"
        logger.info(
            f"--- Processing Term {term_count + 1}/{max_terms}: {term_id_str} ---"
        )

        # Check for program completion *before* attempting to schedule this new term
        if _is_program_complete_v2(
            program_reqs,
            globally_resolved_and_taken_courses,
            course_lookups,
            p_specific_req_codes,
            p_tech_elective_pool,
            f"Pre-check for {term_id_str}",
        ):
            logger.info(
                f"Program RESOLVED and complete before term {term_id_str} was needed."
            )
            is_program_fully_resolved = True
            break  # Exit term loop, program is complete

        # Reset exclusion list for each new semester's attempts
        current_semester_exclusion_list: List[Requirement] = []
        semester_successfully_resolved_and_added = False

        # Calculate category credits met by *actually resolved non-specific* courses so far
        # This is passed to generate_semester to inform placeholder generation
        category_credits_met_by_resolved_courses = defaultdict(int)
        for course_code_val in globally_resolved_and_taken_courses:
            if (
                course_code_val not in p_specific_req_codes
            ):  # Only non-specific courses count towards these categories
                category = get_course_category(
                    course_code_val,
                    p_specific_req_codes,
                    p_tech_elective_pool,
                    group_sociohumanistics=program_reqs.sociohumanistics > 0,
                )
                course_data_lookup = course_lookups.get(course_code_val)
                if course_data_lookup:
                    category_credits_met_by_resolved_courses[
                        category
                    ] += course_data_lookup["credits"]

        # Inner loop: attempts to generate and resolve the current semester
        for attempt in range(max_resolution_attempts_per_semester):
            logger.info(
                f"  Attempt {attempt + 1}/{max_resolution_attempts_per_semester} for {term_id_str} (Skeleton Generation & Resolution)"
            )

            # 1. Generate skeleton for the current semester attempt
            current_semester_skeleton: Optional[TermRequisiteData] = None
            skeleton_estimates_program_complete = False
            try:
                current_semester_skeleton, skeleton_estimates_program_complete = (
                    await generate_semester(
                        program_reqs=program_reqs,
                        course_lookups=course_lookups,
                        term=main_current_term,
                        year=main_current_year,
                        resolved_courses_before_this_term=globally_resolved_and_taken_courses,
                        category_credits_met_by_prior_resolved_courses=category_credits_met_by_resolved_courses,
                        target_difficulty=DEFAULT_TARGET_DIFFICULTY,
                        credit_limits=credit_limits,
                        db_session=db_session,
                        exclusion_list=current_semester_exclusion_list,
                    )
                )
            except (
                ValueError
            ) as e:  # Critical failure in skeleton generation (e.g., min credits not met for non-final)
                msg = f"  {term_id_str}, Attempt {attempt+1}: Skeleton generation critically failed. Reason: {e}. Aborting this semester's attempts."
                logger.warning(msg)
                sequence_generation_warnings.append(msg)
                # This semester cannot be planned; break from attempts loop. Outer logic will stop sequence.
                break

            if (
                current_semester_skeleton.is_empty()
                and not skeleton_estimates_program_complete
            ):
                logger.warning(
                    f"  {term_id_str}, Attempt {attempt+1}: Generated skeleton is empty, and program not estimated complete by skeleton. Resolution may fail or be trivial."
                )
                # This might not be fatal yet, but if it continues, the semester will fail.

            # 2. Resolve the generated skeleton for this single semester
            resolved_term_data_current_sem, failed_reqs_from_resolution = (
                await resolve_single_semester_skeleton(
                    program_reqs,
                    course_lookups,
                    current_semester_skeleton,
                    term_id_str,
                    globally_resolved_and_taken_courses.copy(),  # Pass a copy for safety
                    db_session,
                    p_specific_req_codes,
                    p_tech_elective_pool,
                )
            )

            if (
                resolved_term_data_current_sem is not None
                and not failed_reqs_from_resolution
            ):
                # Resolution SUCCESSFUL for this attempt
                logger.info(
                    f"  {term_id_str}, Attempt {attempt+1}: Successfully generated and resolved semester."
                )
                final_resolved_schedule_map[term_id_str] = (
                    resolved_term_data_current_sem
                )
                final_successful_skeletons_map[term_id_str] = (
                    current_semester_skeleton  # Store skeleton that worked
                )

                # Update globally tracked resolved courses
                for c_code in resolved_term_data_current_sem.courses:
                    globally_resolved_and_taken_courses.add(c_code)

                semester_successfully_resolved_and_added = True
                break  # Break from resolution_attempts_per_semester loop (SUCCESS for this semester)
            else:
                # Resolution FAILED for this attempt
                logger.warning(
                    f"  {term_id_str}, Attempt {attempt+1}: Failed to resolve semester. Failed skeleton reqs: {[f'{r.kind}:{r.value}({r.credits}cr)' for r in failed_reqs_from_resolution]}"
                )
                sequence_generation_warnings.append(
                    f"Resolution failed for {term_id_str} (attempt {attempt+1})."
                )

                # Add unique failed requirements to exclusion list for the next attempt for this semester
                for freq in failed_reqs_from_resolution:
                    if (
                        freq not in current_semester_exclusion_list
                    ):  # Relies on Requirement.__eq__ and __hash__
                        current_semester_exclusion_list.append(freq)

                if attempt + 1 == max_resolution_attempts_per_semester:
                    logger.error(
                        f"  {term_id_str}: All {max_resolution_attempts_per_semester} generation/resolution attempts failed for this semester."
                    )
                    sequence_generation_warnings.append(
                        f"All generation/resolution attempts failed for {term_id_str}."
                    )
                    # Outer logic will handle stopping sequence generation.

        # After all attempts for the current semester:
        if not semester_successfully_resolved_and_added:
            # If semester could not be processed after all attempts (either skeleton gen failed critically or all resolution attempts failed)
            logger.error(
                f"Failed to schedule or resolve {term_id_str} after all attempts. Stopping sequence generation."
            )
            sequence_generation_warnings.append(
                f"Could not process {term_id_str}. Sequence generation halted."
            )
            is_program_fully_resolved = False  # Ensure this reflects failure
            break  # Break from the main term_count loop (stop generating further terms)

        # If semester was successful, advance to the next term
        next_term_info = get_next_term(main_current_term, main_current_year)
        main_current_term = next_term_info["term"]
        main_current_year = next_term_info["year"]

    # After the main term_count loop (either completed max_terms, or broke due to completion/failure)
    else:  # This 'else' block executes if the term_count loop completed without a 'break'
        # This means max_terms were processed. Check final completion status.
        if not _is_program_complete_v2(
            program_reqs,
            globally_resolved_and_taken_courses,
            course_lookups,
            p_specific_req_codes,
            p_tech_elective_pool,
            f"Post max_terms ({max_terms}) check",
        ):
            msg = f"Sequence generation reached max_terms ({max_terms}) but program is NOT fully resolved."
            logger.warning(msg)
            sequence_generation_warnings.append(msg)
            is_program_fully_resolved = False
        else:
            logger.info(
                f"Sequence generation reached max_terms ({max_terms}) and program IS fully resolved."
            )
            is_program_fully_resolved = True

    # Final check for overall program completion status if not determined by an earlier break
    # This handles cases where the loop might have broken due to other reasons than explicit completion check.
    if not is_program_fully_resolved:  # If not True from loop logic, do a final check
        is_program_fully_resolved = _is_program_complete_v2(
            program_reqs,
            globally_resolved_and_taken_courses,
            course_lookups,
            p_specific_req_codes,
            p_tech_elective_pool,
            "Final overall completion status check",
        )

    # Construct final result objects
    schedule_score = float(
        len(final_resolved_schedule_map)
    )  # Simple score: number of terms in the schedule

    final_skel_result = SchedulerSkeletonResult(
        schedule=final_successful_skeletons_map,  # Skeletons that led to success
        score=schedule_score,
        is_complete=is_program_fully_resolved,  # Skeleton's completeness tied to resolved result's completeness
        warnings=list(set(sequence_generation_warnings)),  # Unique warnings
    )

    final_resolved_result = SchedulerResult(
        schedule=final_resolved_schedule_map,
        score=schedule_score,  # Score could be more sophisticated
        is_complete=is_program_fully_resolved,
        warnings=list(set(sequence_generation_warnings)),  # Share warnings
    )

    if not is_program_fully_resolved:
        logger.warning(
            f"Program {program_reqs.code} sequence generation finished, BUT THE PROGRAM IS NOT COMPLETE."
        )
    else:
        logger.info(
            f"Program {program_reqs.code} sequence generation finished successfully, and THE PROGRAM IS COMPLETE."
        )

    return final_resolved_result, final_skel_result
