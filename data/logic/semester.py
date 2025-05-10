import asyncio
import json
import logging
import math
import statistics
from collections import defaultdict
from typing import List, Dict, Set, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.database.database import Program, Course
from data.logic.availability import predict_availability
from data.logic.scheduler import SchedulerResult
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


class Requirement(BaseModel):
    kind: str  # "COURSE", "COURSE_CATEGORY"
    value: str  # Course code or category name
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
    schedule: Dict[str, TermRequisiteData]  # Maps term name ("Fall 2025") to TermData
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
    course_code: str, required_course_codes: set[str], technical_course_codes: set[str]
) -> Optional[str]:
    if course_code in required_course_codes:
        return "required"
    elif course_code in technical_course_codes:
        return "technical"

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
        return "social"

    # If it doesn't match specific categories, consider it 'free'
    return "free"


def get_course_priority(category: str):
    # Check priority in priority map
    PRIORITY_MAP = {
        "required": 1,
        "technical": 2,
        "humanities": 4,
        "social": 4,
        "free": 5,
        "kinesiology": 6,
        "english": 3,
        "spanish": 3,
    }
    return PRIORITY_MAP.get(category, 5)  # Default priority 5 for unknown/free


def get_next_term(current_term: str, current_year: int) -> Dict:
    current_term = current_term.lower()

    # Get next term from list
    TERMS = ["spring", "firstsummer", "secondsummer", "fall"]
    current_term_index = TERMS.index(current_term)
    next_term_index = (current_term_index + 1) % 4
    next_term = TERMS[next_term_index]

    # Determine whether year changes
    next_year = current_year if next_term_index != 0 else current_year + 1

    # Return next term and year as a dictionary
    return {"term": next_term, "year": next_year}


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
) -> tuple[TermRequisiteData, bool]:  # returns if we finished or not
    # Find all the requirements of the program
    program = program_reqs
    warnings = []
    # Load and parse program requirements JSON
    try:
        required_courses_req_data = json.loads(program_reqs.courses or "{}")
        tech_electives_req_data = json.loads(program_reqs.technical_courses or "{}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse program course JSON for {program_reqs.code}: {e}"
        )
        raise

    # Sets for required course codes and for technical electives pool
    required_course_codes = set(required_courses_req_data.keys())
    technical_elective_pool = set(tech_electives_req_data.keys())

    # Calculate remaining courses and credits
    remaining_required_set = required_course_codes - taken_courses_set
    missing_requirements = {
        Requirement(
            kind="COURSE",
            value=course_code,
            credits=course_lookups[course_code]["credits"],
            priority=get_course_priority(
                get_course_category(
                    course_code, required_course_codes, technical_elective_pool
                )
            ),
            difficulty=course_lookups[course_code]["difficulty"],
        )
        for course_code in remaining_required_set
    }
    reqs_to_remove = set()
    # discard the ones we know we can't take
    for requirement in missing_requirements:
        parsed_prereqs = required_courses_req_data.get(requirement.value, {}).get(
            "prerequisites", {}
        )
        # Check Prereqs (against courses completed *before* this term)
        if not check_requisites_recursive(parsed_prereqs, taken_courses_set):
            reqs_to_remove.add(requirement)
        # Check Availability
        if not await predict_availability(requirement.value, term, year, db_session):
            reqs_to_remove.add(requirement)  # Maybe disable this if it's not reliable?

    missing_requirements.difference_update(reqs_to_remove)
    # Convert to list to append elements and sort
    missing_requirements = list(missing_requirements)

    # Augment the remaining course list with some fabricated template courses
    total_elective_credits = {
        "english": program_reqs.english or 0,
        "spanish": program_reqs.spanish or 0,
        "humanities": program_reqs.humanities or 0,
        "social": program_reqs.social or 0,
        "sociohumanistics": program_reqs.sociohumanistics or 0,
        "technical": program_reqs.technical or 0,
        "free": program_reqs.free or 0,
        "kinesiology": program_reqs.kinesiology or 0,
    }
    remaining_elective_credits = defaultdict(int)
    for course_code in taken_courses_set:
        category = get_course_category(
            course_code, required_course_codes, technical_elective_pool
        )
        if category not in ["required", "techincal"]:
            credits = course_lookups[course_code]["credits"]
            remaining_elective_credits[category] -= credits

    for category, remaining_creds in remaining_elective_credits.items():
        if remaining_creds <= 0:
            continue
        num_3_credit_chunks = remaining_creds // 3
        offshoot_creds = remaining_creds % 3

        # Add 3-credit category requirements
        for _ in range(num_3_credit_chunks):
            missing_requirements.append(
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category,
                    credits=3,
                    priority=get_course_priority(
                        category,
                        required_course_codes,
                        technical_elective_pool,
                    ),
                    difficulty=2.5,  # Placeholder average difficulty
                )
            )
        # Add remaining offshoot credit category requirement
        if offshoot_creds > 0:
            missing_requirements.append(
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category,
                    credits=offshoot_creds,
                    priority=get_course_priority(
                        category,
                        required_course_codes,
                        technical_elective_pool,
                    ),
                    difficulty=2.5,  # Placeholder
                )
            )
    # Sort these based on our priority and target difficulty
    missing_requirements.sort(
        key=lambda x: (
            x.priority,
            abs(x.difficulty - target_difficulty),
        )
    )

    proposed_semester = TermRequisiteData()
    while proposed_semester.credits < credit_limits["max"]:
        # pick course, from front of queue (Q)
        # repeat until loop is done
        # Add your implementation here
        pass

    # if we aren't able to get between min and max, throw
    if proposed_semester.credits < credit_limits["min"]:
        raise ValueError("Unable to generate a semester within the credit limits.")
    return proposed_semester


async def resolve_category_requirements(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    taken_courses: Set[str],
):

    pass


async def generate_sequence(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    start_term: str,
    start_year: int,
    taken_courses_set: Set[str],
    # target_difficulty: float,
    credit_limits: Dict,  # {"min": x, "max": y}
    db_session: AsyncSession,
) -> Tuple[SchedulerResult, SchedulerSkeletonResult]:
    # start at term year
    current_term, current_year = start_term, start_year
    # propose a semester
    proposed_semester = await generate_semester(
        program_reqs=program_reqs,
        course_lookups=course_lookups,
        term=current_term,
        year=current_year,
        taken_courses_set=taken_courses_set,
        target_difficulty=3,
        credit_limits=credit_limits,
        db_session=db_session,
    )
    proposed_curricular_sequence = SchedulerResult()
    proposed_curricular_skeleton = SchedulerSkeletonResult()
    while not proposed_semester.is_empty():

        pass

    # Find suggested courses to replace category requirements (this should be another function)
    # update taken courses
    # advance to next term year
    # propose a semester
    # return results and verify completion
    pass


# --- End improved functions ---


"""
async def generate_semester(
    program_reqs: Program,
    course_lookups: Dict[str, Dict],
    term: str,
    year: int,
    taken_courses_set: Set[str],
    target_difficulty: float,
    credit_limits: Dict,  # {"min": x, "max": y}
    db_session: AsyncSession,
) -> TermRequisiteData:
    # Find all the requirements of the program
    program = program_reqs
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
        raise

    required_course_codes = set(required_courses_req_data.keys())
    # Pool of codes ALLOWED for technical electives
    technical_elective_pool = set(tech_electives_req_data.keys())

    remaining_required_set = required_course_codes - taken_courses_set

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
    # Augment the remaining course list with some fabricated template courses
    # Me when I commit scooter ankle *dab*
    # Bitches go to Spain just to party
    missing_requirements = {
        Requirement(
            kind="COURSE",
            value=course_code,
            credits=course_lookups[course_code]["credits"],
            priority=get_course_priority(course_code),
            difficulty=course_lookups[course_code]["difficulty"],
        )
        for course_code in remaining_required_set
    }
    reqs_to_remove = set()
    # discard the ones we know we can't take
    for requirement in missing_requirements:
        parsed_prereqs = required_courses_req_data.get(requirement.value, {}).get(
            "prerequisites", {}
        )
        # Check Prereqs (against courses completed *before* this term)
        if not check_requisites_recursive(parsed_prereqs, taken_courses_set):
            reqs_to_remove.add(requirement)
        # Check Availability
        if not await predict_availability(requirement.value, term, year, db_session):
            reqs_to_remove.add(requirement)  # Maybe disable this if it's not reliable?

    missing_requirements.difference_update(reqs_to_remove)
    for category, remaining_creds in remaining_elective_credits.items():
        offshoot_creds = remaining_creds % 3
        missing_requirements.extend(
            [
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category,
                    credits=3,
                    priority=3.5,
                    difficulty=2.5,
                )
            ]
            * remaining_creds
            // 3
        )
        if offshoot_creds > 0:
            missing_requirements.append(
                Requirement(
                    kind="COURSE_CATEGORY",
                    value=category,
                    credits=offshoot_creds,
                    priority=3.5,
                    difficulty=2.5,
                )
            )
        # sort these based on our priority and target difficulty
        missing_requirements.sort(
            key=lambda x: (
                x.priority,
                abs(x.difficulty - target_difficulty),
            )
        )

        proposed_semester = TermRequisiteData()
        while proposed_semester.credits < credit_limits["max"]:
            # pick course, from front of queue (Q)
            # repeat until loop is done
            pass
        # if we aren't able to get between min and max, throw
        return proposed_semester
    
        
async def generate_sequence(
    # TODO
):
    # start at term year
    # propose a semester
    # While propose semester is not empty:
    # Find suggested courses to replace category requirements (this should be another function)
    # update taken courses
    # advance to next term year
    # propose a semester
    # return results and verify completion
    return 0
"""
