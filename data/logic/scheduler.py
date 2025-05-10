import asyncio
import json
import logging
import math
import statistics
from typing import List, Dict, Set, Optional, Tuple, Literal
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


# Pydantic models
class TermData(BaseModel):
    courses: List[str] = []
    credits: int = 0
    difficulty_sum: float = 0.0


class SchedulerResult(BaseModel):
    schedule: Dict[str, TermData]  # Maps term name ("Fall 2025") to TermData
    score: float  # Lower is better fit to curve?
    is_complete: bool
    warnings: List[str] = []
    rank: int = 0


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
        stmt = select(Course)  # Select all columns needed
        result = await db.execute(stmt)
        all_courses = result.scalars().all()
        for course in all_courses:
            lookup[course.course_code] = {
                "credits": course.credits or 0,
                "difficulty": course.difficulty or 0,  # Calculated previously
                "highest_ancestor": course.highest_ancestor
                or 0,  # Calculated previously
                "prerequisites_raw": course.prerequisites,  # Store raw string
                "corequisites_raw": course.corequisites,  # Store raw string
                # Add last_term info for availability checks
                "last_Fall": course.last_Fall or 0,
                "last_Spring": course.last_Spring or 0,
                "last_FirstSummer": course.last_FirstSummer or 0,
                "last_SecondSummer": course.last_SecondSummer or 0,
                "last_ExtendedSummer": course.last_ExtendedSummer or 0,
            }
        logger.info(f"Loaded lookup data for {len(lookup)} courses.")
    except Exception as e:
        logger.error(f"Error loading course lookup data: {e}")
        return {}  # Return empty on error
    return lookup


def generate_terms(
    start_year: int,
    start_term: str,
    end_year: int,
    end_term: str,
    summer_pref: str,
    specific_summers: Optional[List[int]],
) -> List[Tuple[str, int]]:
    """Generates a list of (term_type, year) tuples for scheduling."""
    terms = []
    # Ensure canonical term names match availability function and Course columns
    term_order = ["Spring", "FirstSummer", "SecondSummer", "ExtendedSummer", "Fall"]
    try:
        current_term_index = term_order.index(start_term)
    except ValueError:
        logger.error(f"Invalid start_term provided: {start_term}")
        return []

    current_year = start_year

    # Loop logic needs refinement to handle end condition correctly
    while True:
        term_type = term_order[current_term_index]
        year_to_schedule = current_year

        # Check end condition BEFORE adding
        if year_to_schedule > end_year or (
            year_to_schedule == end_year
            and term_order.index(term_type) > term_order.index(end_term)
        ):
            break  # Stop if we've passed the target grad term

        is_summer = "Summer" in term_type
        include_term = True

        if is_summer:
            if summer_pref == "None":
                include_term = False
            elif summer_pref == "Specific":
                # Summer sessions belong to the ACADEMIC year that started the previous Fall
                academic_year_start = (
                    year_to_schedule if term_type != "Fall" else year_to_schedule + 1
                )
                if (
                    specific_summers is None
                    or academic_year_start not in specific_summers
                ):
                    include_term = False
            # If summer_pref == "All", include_term remains True

        if include_term:
            terms.append((term_type, year_to_schedule))

        # Move to next term/year
        current_term_index += 1
        if current_term_index >= len(term_order):
            current_term_index = 0
            current_year += 1  # Increment year only after Fall

        # Add safety break (e.g., max number of terms)
        if len(terms) > 50:  # Prevent infinite loops if end condition is tricky
            logger.error("Exceeded maximum scheduling terms limit.")
            break

    return terms


def check_requisites_recursive(req_dict: dict, completed_courses: Set[str]) -> bool:
    """Checks if parsed requisites (filtered for courses) are met by the completed set."""
    # Assumes req_dict is the *filtered* structure containing only COURSE and logical ops
    if not req_dict or not isinstance(req_dict, dict):
        return True  # Treat empty/invalid requirement as met

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
            return False  # Empty OR is false (cannot satisfy)
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "ANDOR":
        # "A Y/O B" usually means A OR B OR Both. Functionally equivalent to OR for checking completion.
        logger.debug(f"Treating ANDOR node as OR for requirement check: {req_dict}")
        # Check parser output: does it use "conditions" or "value"? Your parser uses "value" for this rule.
        conditions = req_dict.get("value", [])  # Use "value" based on p_andor_group
        if not isinstance(conditions, list):
            return False  # Invalid structure
        if not conditions:
            return False  # Empty ANDOR cannot be satisfied
        # Must satisfy ANY condition recursively
        return any(
            check_requisites_recursive(cond, completed_courses) for cond in conditions
        )
    elif req_type == "FOR":
        # The 'FOR' (PARA) node usually describes *what* a requirement applies to
        # (e.g., '6 credits FOR MATE'), not a condition checked against completed courses.
        # This type should ideally be filtered out by filter_parsed_requisites before checking.
        # If it appears here, it means the requirement structure isn't purely course-based.
        # We treat it as met in the context of checking *course* prerequisites.
        logger.info(
            f"Encountered 'FOR' type during requisite check, treating as met: {req_dict}"
        )
        return True
    else:
        # This case shouldn't be reached if input is pre-filtered correctly
        logger.warning(
            f"Unexpected node type in check_requisites_recursive: {req_type}"
        )
        return False  # Fail safe on unexpected types


def get_course_category(
    course_code: str, department: Optional[str], program_info: Program
) -> Optional[str]:
    """
    Tries to determine the elective category of a course based on code/dept.
    NEEDS SIGNIFICANT CUSTOMIZATION for UPRM structure.
    Returns category name (lowercase matching remaining_elective_credits keys) or None.
    """
    prefix = course_code[:4]

    if prefix == "EDFI":
        return "kinesiology"
    if prefix == "INGL":
        return "english"
    if prefix == "ESPA":
        return "spanish"
    # Humanities prefixes
    if prefix in [
        "HUMA",
        "FILO",
        "ARTE",
        "LITE",
        "MUSI",
        "TEAT",
        "FREN",
        "ITAL",
        "ALEM",
        "LATI",
    ]:
        # Check if it's maybe required by the program first?
        # if course_code in required_codes_from_program: return None
        return "humanities"
    # Example Social Science Prefixes (add ALL relevant ones)
    if prefix in ["CISO", "CIPO", "SOCI", "ECON", "PSIC", "HIST", "GEOG", "ANTR"]:
        # Check if it's maybe required by the program first?
        # if course_code in required_codes_from_program: return None
        return "social"

    # If it doesn't match specific categories, consider it 'free'
    # BUT exclude courses that are part of the *program's required courses*
    # We need access to the required course list here if possible.
    # Let's assume for now, if not categorized above, it *could* be free.
    # The calling function will need to verify it's not a required course.
    return "free"
    # Return None if it cannot be categorized or is a required course handled elsewhere?
    # return None


def score_schedule(schedule_details: List[TermData], target_curve: str) -> float:
    """
    Scores a generated schedule based on how well it fits the target difficulty curve.
    Lower scores indicate a better fit. Uses difficulty per credit for normalization.
    Normalizes Increasing/Decreasing violation counts by the number of term transitions.

    Args:
        schedule_details: List of TermData objects, ordered chronologically.
        target_curve: "Flat", "Increasing", or "Decreasing".

    Returns:
        A float score. Returns 0.0 for perfect fit or trivial cases (<=1 term).
        Returns float('inf') if target_curve is invalid.
    """
    # Extract difficulty per credit for terms with actual credits scheduled
    difficulty_per_credit = []
    for term in schedule_details:
        if term.credits > 0:
            # Calculate difficulty density for the term
            difficulty_per_credit.append(term.difficulty_sum / term.credits)
        # We ignore terms with 0 credits for curve fitting

    num_valid_terms = len(difficulty_per_credit)

    # Handle edge cases: If 0 or 1 term has credits, it perfectly fits any curve.
    if num_valid_terms <= 1:
        return 0.0  # Best possible score

    # Scoring logic
    score = float("inf")  # Default to worst score
    num_transitions = num_valid_terms - 1

    if target_curve == "Flat":
        # Use variance - lower is better. Variance is inherently an average measure.
        try:
            score = statistics.variance(difficulty_per_credit)
        except statistics.StatisticsError:
            score = 0.0

    elif target_curve == "Increasing":
        violations = 0
        for i in range(num_transitions):
            # Penalize if current term difficulty/credit is higher than next (a decrease)
            if (
                difficulty_per_credit[i] > difficulty_per_credit[i + 1] + 1e-9
            ):  # Tolerance
                violations += 1
        # Normalize violation count by number of transitions
        score = float(violations) / num_transitions

    elif target_curve == "Decreasing":
        violations = 0
        for i in range(num_transitions):
            # Penalize if current term difficulty/credit is lower than next (an increase)
            if (
                difficulty_per_credit[i] < difficulty_per_credit[i + 1] - 1e-9
            ):  # Tolerance
                violations += 1
        # Normalize violation count by number of transitions
        score = float(violations) / num_transitions

    else:
        logger.warning(f"Unknown target_curve: {target_curve}. Returning max score.")
        # score remains float('inf')

    return score


# Core scheduling heuristic
async def generate_schedule_heuristic(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    start_year: int,
    start_term: str,
    end_year: int,
    end_term: str,
    taken_courses_set: Set[str],
    credit_limits: Dict,  # {"min": x, "max": y}
    summer_pref: str,
    specific_summers: Optional[List[int]],
    difficulty_curve: str,
    db_session: AsyncSession,  # For availability checks
    num_schedules_to_generate: int = 1,
) -> List[SchedulerResult]:
    """
    Generates one or more potential schedules using heuristics.
    Returns a list of SchedulerResult objects, sorted by score.
    """
    warnings = []
    # Load and Parse Program Requirements JSON
    try:
        # This contains {"CODE": {"prerequisites": {...}, "corequisites": {...}, "prereq_for": [], "coreq_for": []}}
        # The prerequisites/corequisites here SHOULD BE THE FILTERED versions
        required_courses_req_data = json.loads(program_reqs.courses or "{}")
        tech_electives_req_data = json.loads(program_reqs.technical_courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse program course JSON for {program_reqs.code}: {e}"
        )
        return []  # Cannot proceed without this data

    required_course_codes = set(required_courses_req_data.keys())
    # Pool of codes ALLOWED for technical electives
    technical_elective_pool = set(tech_electives_req_data.keys())

    remaining_required_set = required_course_codes - taken_courses_set
    required_course_codes = set(json.loads(program_reqs.courses or "{}").keys())

    remaining_elective_credits = {
        "english": program_reqs.english or 0,
        "spanish": program_reqs.spanish or 0,
        "humanities": program_reqs.humanities or 0,
        "social": program_reqs.social or 0,
        "sociohumanistics": program_reqs.sociohumanistics
        or 0,  # May need specific logic if used
        "technical": program_reqs.technical or 0,
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }

    # Initial decrement based on already taken courses
    for course_code in taken_courses_set:
        if course_code in required_course_codes:
            continue  # Handled by set difference
        course_info = course_lookups.get(course_code, {})
        category = get_course_category(
            course_code, course_info.get("department"), program_reqs
        )
        if category and category in remaining_elective_credits:
            remaining_elective_credits[category] -= course_info.get("credits", 0)
            remaining_elective_credits[category] = max(
                0, remaining_elective_credits[category]
            )

    # Make a copy for this specific schedule attempt
    current_remaining_electives = remaining_elective_credits.copy()

    # Generate Terms
    term_tuples = generate_terms(
        start_year, start_term, end_year, end_term, summer_pref, specific_summers
    )
    if not term_tuples:
        logger.error("No terms available for scheduling.")
        warnings.append(
            "No terms available for scheduling based on start/end dates and summer preferences."
        )
        # Return empty list with warning
        return [
            SchedulerResult(
                schedule={}, score=float("inf"), is_complete=False, warnings=warnings
            )
        ]

    generated_schedules = []

    # Loop to generate multiple variations (optional, start with 1)
    for attempt in range(num_schedules_to_generate):
        logger.info(f"Generating schedule attempt #{attempt+1}...")
        # Initialize state for this attempt
        schedule: Dict[str, TermData] = {
            f"{t[0]} {t[1]}": TermData() for t in term_tuples
        }
        completed_courses = taken_courses_set.copy()
        current_remaining_required = remaining_required_set.copy()
        current_remaining_electives = (
            remaining_elective_credits.copy()
        )  # Generic counts
        attempt_warnings = []
        is_valid_schedule = True

        # Scheduling Loop per Term
        for term_type, year in term_tuples:
            term_key = f"{term_type} {year}"
            schedule[term_key] = TermData()
            courses_added_this_term: Set[str] = (
                set()
            )  # Track courses added in *this specific term* for coreq checks

            # Loop to fill the term
            while schedule[term_key].credits < credit_limits["max"]:
                candidates = []

                # Find eligible required courses
                for course_code in list(current_remaining_required):
                    # Basic info lookup
                    course_info = course_lookups.get(course_code)
                    if not course_info:
                        continue  # Skip if basic info missing

                    # Get FILTERED requisites from the program data
                    parsed_prereqs = required_courses_req_data.get(course_code, {}).get(
                        "prerequisites", {}
                    )
                    parsed_coreqs = required_courses_req_data.get(course_code, {}).get(
                        "corequisites", {}
                    )

                    # Check Prereqs (against courses completed *before* this term)
                    if not check_requisites_recursive(
                        parsed_prereqs, completed_courses
                    ):
                        continue

                    # # Check Coreqs (against completed + already added *this term*)
                    # if not check_requisites_recursive(
                    #     parsed_coreqs, completed_courses.union(courses_added_this_term)
                    # ):
                    #     continue

                    # Check Availability
                    if not await predict_availability(
                        course_code, term_type, year, db_session
                    ):
                        continue

                    # Add as candidate if all checks pass
                    candidates.append(
                        {
                            "code": course_code,
                            "type": "Required",  # Mark type
                            "priority": 1,  # Highest priority
                            "parsed_prereqs": parsed_prereqs,
                            "parsed_coreqs": parsed_coreqs,
                            "difficulty": course_info.get("difficulty", 0),
                            "longest_path": course_info.get("highest_ancestor", 0),
                            "credits": course_info.get("credits", 0),
                            "coreqs_list": list(
                                flatten_requisites_to_list(parsed_coreqs)
                            ),
                        }
                    )

                needed_electives = {
                    cat: creds
                    for cat, creds in current_remaining_electives.items()
                    if creds > 0
                }

                if needed_electives:
                    # Check TECHNICAL electives from the POOL first if needed
                    if "technical" in needed_electives:
                        for (
                            course_code
                        ) in (
                            technical_elective_pool
                        ):  # Check courses from the defined pool
                            if (
                                course_code in completed_courses
                                or course_code in courses_added_this_term
                                or course_code in required_course_codes
                            ):
                                continue

                            course_info = course_lookups.get(course_code)
                            if not course_info:
                                continue

                            # Get reqs (ideally pre-parsed into course_lookups or parse raw here)
                            # Let's assume we parse the raw string from the main lookup now
                            prereq_str = course_info.get("prerequisites_raw", "")
                            coreq_str = course_info.get("corequisites_raw", "")
                            try:
                                parsed_prereqs = (
                                    filter_parsed_requisites(
                                        parse_prerequisites(prereq_str or "")
                                    )
                                    or {}
                                )
                                parsed_coreqs = (
                                    filter_parsed_requisites(
                                        parse_corequisites(coreq_str or "")
                                    )
                                    or {}
                                )
                            except Exception:
                                continue  # Skip if parse fails

                            if not check_requisites_recursive(
                                parsed_prereqs, completed_courses
                            ):
                                continue
                            # if not check_requisites_recursive(
                            #     parsed_coreqs,
                            #    completed_courses.union(courses_added_this_term),
                            # ):
                            #    continue
                            if not await predict_availability(
                                course_code, term_type, year, db_session
                            ):
                                continue
                            # Add as technical elective candidate (fulfilling the 'technical' credit need)
                            candidates.append(
                                {
                                    "code": course_code,
                                    "type": "ElectiveTechnical",
                                    "category": "technical",
                                    "priority": 2,  # Assign priority for technical electives
                                    "parsed_prereqs": parsed_prereqs,
                                    "parsed_coreqs": parsed_coreqs,
                                    "difficulty": course_info.get("difficulty", 0),
                                    "longest_path": course_info.get(
                                        "highest_ancestor", 0
                                    ),
                                    "credits": course_info.get("credits", 0),
                                    "coreqs_list": list(
                                        flatten_requisites_to_list(parsed_coreqs)
                                    ),
                                }
                            )

                    # Find OTHER Generic Electives (Hum, Soc, Free, Kin, Eng, Spa)
                    for course_code, course_info in course_lookups.items():
                        # Skip if already handled or in the technical pool (to avoid adding as 'free' if it's a tech option)
                        if (
                            course_code in completed_courses
                            or course_code in courses_added_this_term
                            or course_code in required_course_codes
                            or course_code in technical_elective_pool
                        ):
                            continue
                        category = get_course_category(
                            course_code, course_info.get("department"), program_reqs
                        )

                        # Check if this category is needed generically
                        if (
                            not category
                            or category == "technical"
                            or category not in needed_electives
                        ):
                            continue
                        prereq_str = course_info.get("prerequisites_raw", "")
                        coreq_str = course_info.get("corequisites_raw", "")
                        try:
                            parsed_prereqs = (
                                filter_parsed_requisites(
                                    parse_prerequisites(prereq_str or "")
                                )
                                or {}
                            )
                            parsed_coreqs = (
                                filter_parsed_requisites(
                                    parse_corequisites(coreq_str or "")
                                )
                                or {}
                            )
                        except Exception:
                            # If parsing fails for an elective, maybe skip it
                            continue

                        # Check Prereqs
                        if not check_requisites_recursive(
                            parsed_prereqs, completed_courses
                        ):
                            continue
                        # Check Coreqs
                        # if not check_requisites_recursive(
                        #     parsed_coreqs,
                        #     completed_courses.union(courses_added_this_term),
                        # ):
                        #     continue
                        # Check Availability
                        if not await predict_availability(
                            course_code, term_type, year, db_session
                        ):
                            continue

                        # Determine priority
                        priority_map = {
                            "sociohumanistics": 4,
                            "humanities": 4,
                            "social": 4,
                            "free": 5,
                            "kinesiology": 6,
                            "english": 3,
                            "spanish": 3,
                        }
                        priority = priority_map.get(category, 5)

                        # Add as elective candidate
                        candidates.append(
                            {
                                "code": course_code,
                                "type": "Elective",  # Mark type
                                "category": category,  # Store which category it fulfills
                                "priority": priority,
                                "parsed_prereqs": parsed_prereqs,
                                "parsed_coreqs": parsed_coreqs,
                                "difficulty": course_info.get("difficulty", 0),
                                "longest_path": course_info.get("highest_ancestor", 0),
                                "credits": course_info.get("credits", 0),
                                "coreqs_list": list(
                                    flatten_requisites_to_list(parsed_coreqs)
                                ),
                            }
                        )

                if not candidates:
                    break  # No more eligible candidates this term

                # Prioritize and select
                def sort_key(c):
                    # Sort based on difficulty curve preference
                    # Higher difficulty is prioritized for 'Decreasing', lower for 'Increasing'
                    diff_val = c["difficulty"]
                    sort_difficulty = (
                        -diff_val
                        if difficulty_curve == "Decreasing"
                        else diff_val if difficulty_curve == "Increasing" else 0
                    )
                    # Example sort: Priority ASC -> Longest Path DESC -> Difficulty (curve-based) -> Credits DESC (tie-breaker)
                    return (
                        c["priority"],
                        -c["longest_path"],
                        sort_difficulty,
                        -c["credits"],
                    )

                candidates.sort(key=sort_key)

                # Select best candidate respecting credit limits and coreqs
                course_to_add_data = None
                coreqs_to_add_data = []
                added_this_pass = False
                possible_to_add_more = False  # Flag to see if we skipped due to credits but could add later

                for cand in candidates:
                    cand_code = cand["code"]
                    cand_credits = cand["credits"]
                    cand_coreqs_list = cand["coreqs_list"]
                    estimated_total_credits = schedule[term_key].credits + cand_credits
                    potential_coreqs_info = (
                        []
                    )  # Store coreq details {code, credits, difficulty}

                    # Check if corequisites can also be added simultaneously
                    can_add_coreqs = True
                    for coreq_code in cand_coreqs_list:
                        if coreq_code == cand_code:
                            continue
                        if (
                            coreq_code in completed_courses
                            or coreq_code in courses_added_this_term
                        ):
                            continue

                        coreq_info = course_lookups.get(coreq_code)
                        if not coreq_info:
                            can_add_coreqs = False
                            break  # Coreq info missing

                        coreq_credits = coreq_info.get("credits", 0)
                        # Get FILTERED coreq requisites from program data or lookup
                        coreq_parsed_prereqs = required_courses_req_data.get(
                            coreq_code, {}
                        ).get(
                            "prerequisites", {}
                        )  # Or tech_courses_data
                        coreq_parsed_coreqs = required_courses_req_data.get(
                            coreq_code, {}
                        ).get(
                            "corequisites", {}
                        )  # Or tech_courses_data

                        if not check_requisites_recursive(
                            coreq_parsed_prereqs, completed_courses
                        ):
                            can_add_coreqs = False
                            break
                        if not check_requisites_recursive(
                            coreq_parsed_coreqs,
                            completed_courses.union(courses_added_this_term).union(
                                {cand_code}
                            ),
                        ):
                            can_add_coreqs = False
                            break
                        if not await predict_availability(
                            coreq_code, term_type, year, db_session
                        ):
                            can_add_coreqs = False
                            break

                        estimated_total_credits += coreq_credits
                        potential_coreqs_info.append(
                            {
                                "code": coreq_code,
                                "credits": coreq_credits,
                                "difficulty": coreq_info.get("difficulty", 0),
                                "type": (
                                    "Required"
                                    if coreq_code in current_remaining_required
                                    else "Elective"
                                ),  # Mark type
                            }
                        )

                    if not can_add_coreqs:
                        continue  # Skip candidate if coreqs unmet

                    # Check if fits within max credits
                    if estimated_total_credits <= credit_limits["max"]:
                        # Found a valid selection
                        course_to_add_data = cand
                        coreqs_to_add_data = potential_coreqs_info
                        added_this_pass = True
                        break  # Select this candidate and its coreqs
                    else:
                        # Could potentially add this later if smaller courses are added first
                        possible_to_add_more = True

                # Update term schedule and state
                if course_to_add_data:
                    all_courses_to_schedule_now = [
                        course_to_add_data
                    ] + coreqs_to_add_data
                    for course_data in all_courses_to_schedule_now:
                        code = course_data["code"]
                        if (
                            code not in courses_added_this_term
                        ):  # Avoid double adding if a course is coreq for multiple others
                            schedule[term_key].courses.append(code)
                            schedule[term_key].credits += course_data["credits"]
                            schedule[term_key].difficulty_sum += course_data[
                                "difficulty"
                            ]
                            courses_added_this_term.add(code)
                            if course_data["type"] == "Required":
                                current_remaining_required.discard(code)
                if added_this_pass and course_to_add_data:
                    all_courses_to_schedule_now = [
                        course_to_add_data
                    ] + coreqs_to_add_data
                    for course_data in all_courses_to_schedule_now:
                        code = course_data["code"]
                        credits = course_data["credits"]
                        if code not in courses_added_this_term:
                            schedule[term_key].courses.append(code)
                            schedule[term_key].credits += credits
                            schedule[term_key].difficulty_sum += course_data[
                                "difficulty"
                            ]
                            courses_added_this_term.add(code)

                            course_type = course_data["type"]
                            primary_category = course_data.get("category")
                            if course_type == "Required":
                                current_remaining_required.discard(code)
                            elif course_type == "ElectiveTechnical":
                                # Decrement the generic 'technical' credit count because it was chosen for this purpose
                                if current_remaining_electives["technical"] > 0:
                                    decrement = min(
                                        credits,
                                        current_remaining_electives["technical"],
                                    )
                                    current_remaining_electives[
                                        "technical"
                                    ] -= decrement
                            elif course_data["type"] == "Elective":
                                if (
                                    primary_category
                                    and primary_category in current_remaining_electives
                                    and current_remaining_electives[primary_category]
                                    > 0
                                ):
                                    decrement = min(
                                        credits,
                                        current_remaining_electives[primary_category],
                                    )
                                    current_remaining_electives[
                                        primary_category
                                    ] -= decrement
                                else:
                                    # This shouldn't happen if candidate finding is correct, but log if it does
                                    logger.warning(
                                        f"Scheduled elective {code} for category {primary_category} but no credits were needed."
                                    )
                else:
                    # No candidate could be added in this pass (either none eligible or all too large)
                    break  # Stop filling this term

            # Term validation
            if (
                schedule[term_key].credits < credit_limits["min"]
                and term_key != f"{end_term} {end_year}"
            ):  # Allow last term to be low
                warning_msg = f"Warning: Term {term_key} has only {schedule[term_key].credits} credits (min: {credit_limits['min']})."
                logger.warning(warning_msg)
                attempt_warnings.append(warning_msg)
                # Should this invalidate the schedule? Depends on strictness.

            # Update completed courses AFTER the term is fully scheduled
            completed_courses.update(courses_added_this_term)

        # Final validation and scoring for the attempt
        if current_remaining_required or any(
            v > 0 for v in current_remaining_electives.values()
        ):  # Checks technical, hum, soc, free, etc.
            is_valid_schedule = False
            final_warning = f"Attempt #{attempt+1}: Schedule incomplete. Remaining: {current_remaining_required}, Electives: {current_remaining_electives}"
            logger.warning(final_warning)
            attempt_warnings.append(final_warning)
        else:
            is_valid_schedule = True  # All requirements seem met

        # Format schedule details IN CHRONOLOGICAL ORDER for scoring function
        ordered_schedule_details = []
        for term_type, year in term_tuples:  # Use the generated term order
            term_key = f"{term_type} {year}"
            # Get the TermData object created earlier for this term
            term_data = schedule.get(term_key)
            if (
                term_data
            ):  # Should always exist if term_tuples was used to init schedule
                ordered_schedule_details.append(term_data)
            else:
                # This case indicates an issue with schedule dictionary keys vs term_tuples
                logger.error(
                    f"Mismatch: Term key {term_key} not found in generated schedule dict."
                )

        # Call the scoring function
        calculated_score = score_schedule(ordered_schedule_details, difficulty_curve)
        logger.info(
            f"Attempt #{attempt+1}: Score = {calculated_score:.4f}, Complete = {is_valid_schedule}"
        )

        generated_schedules.append(
            SchedulerResult(
                schedule=schedule,
                score=calculated_score,
                is_complete=is_valid_schedule,
                warnings=attempt_warnings,
            )
        )

    # Rank Schedules: prioritize complete schedules, then by score (lower is better)
    generated_schedules.sort(key=lambda x: (not x.is_complete, x.score))

    # Optionally assign ranks after sorting
    for i, result in enumerate(generated_schedules):
        result.rank = i + 1

    return generated_schedules
