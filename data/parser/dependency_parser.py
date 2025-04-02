import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from data.database.database import Course
from data.parser.requisite_parser import (
    parse_prerequisites,
    parse_corequisites,
    lexer,
)

logger = logging.getLogger(__name__)


# --- Pre-computation ---
def load_and_parse_all_course_reqs(db_session: Session) -> dict:
    """
    Queries all courses, parses their requisites, and returns a lookup dictionary.
    """
    all_reqs = {}
    print("DB Task: Loading and parsing requisites for all courses...")
    # Query distinct course codes first to avoid parsing duplicates from different terms unnecessarily.
    # Or query latest term/year only if that is sufficient.
    latest_courses = (
        db_session.query(Course)
        .distinct(Course.course_code)
        .order_by(Course.course_code, desc(Course.year), desc(Course.term))
        .all()
    )  # Adjust query strategy if needed.

    count = 0
    for course_db_entry in latest_courses:
        course_code = course_db_entry.course_code
        prereq_str = course_db_entry.prerequisites
        coreq_str = course_db_entry.corequisites
        parsed_prereqs = {}
        parsed_coreqs = {}
        try:
            lexer.lineno = 1  # Reset lexer state.
            parsed_prereqs = parse_prerequisites(prereq_str or "") or {}
        except Exception as e:
            # Log potentially less noisily during bulk processing.
            logger.warning(
                f"Pre-parse failed for prereqs of {course_code}: '{prereq_str}'. Error: {e}"
            )
            pass  # Store empty dict on failure.
        try:
            lexer.lineno = 1  # Reset lexer state.
            parsed_coreqs = parse_corequisites(coreq_str or "") or {}
        except Exception as e:
            logger.warning(
                f"Pre-parse failed for coreqs of {course_code}: '{coreq_str}'. Error: {e}"
            )
            pass  # Store empty dict on failure.

        all_reqs[course_code] = {
            "prerequisites": parsed_prereqs,
            "corequisites": parsed_coreqs,
        }
        count += 1
        if count % 100 == 0:  # Print progress periodically.
            print(f"DB Task: Parsed requisites for {count} courses...")

    print(f"DB Task: Finished parsing requisites for {count} unique courses.")
    return all_reqs


# --- Tree Building ---


def _extract_course_dependencies(req_dict: dict) -> set:
    """Helper to recursively find all course codes mentioned in a parsed req dict."""
    deps = set()
    if not isinstance(req_dict, dict):
        return deps

    req_type = req_dict.get("type")

    if req_type == "COURSE":
        # Ensure value is extracted correctly, handling potential space.
        course_val = req_dict.get("value", "")
        if isinstance(course_val, str):
            deps.add(course_val.replace(" ", ""))  # Format code.
        elif (
            isinstance(course_val, dict) and course_val.get("type") == "COURSE"
        ):  # Handle nested COURSE if parser does that.
            nested_val = course_val.get("value", "")
            if isinstance(nested_val, str):
                deps.add(nested_val.replace(" ", ""))

    elif req_type in ["AND", "OR", "ANDOR", "FOR"]:
        conditions = req_dict.get("conditions", [])
        if isinstance(conditions, list):
            for condition in conditions:
                deps.update(_extract_course_dependencies(condition))
    # Handle other types like CREDITS_WITH_PATTERN if they can contain course codes.
    elif req_type == "CREDITS_WITH_PATTERN_REQUIREMENT":
        patterns = req_dict.get("patterns", [])
        # Assuming patterns might be actual course codes in some cases.
        for pattern in patterns:
            # Very basic check if it looks like a course code.
            if (
                isinstance(pattern, str)
                and len(pattern) >= 7
                and pattern[:4].isalpha()
                and pattern[4:].isdigit()
            ):
                deps.add(pattern.replace(" ", ""))

    return deps


# Cache to store already computed trees for performance.
_tree_cache = {}


def build_dependency_tree(course_code: str, all_reqs: dict, visited: set) -> dict:
    """
    Recursively builds a dependency tree for a given course code.
    """
    course_code = course_code.replace(" ", "")  # Ensure consistent formatting.

    # Check cache.
    if course_code in _tree_cache:
        return _tree_cache[course_code]

    # Cycle detection.
    if course_code in visited:
        logger.warning(f"Cycle detected involving course: {course_code}")
        return {"code": course_code, "cycle_detected": True}

    visited.add(course_code)

    req_info = all_reqs.get(course_code, {"prerequisites": {}, "corequisites": {}})
    parsed_prereqs = req_info.get("prerequisites", {})
    parsed_coreqs = req_info.get("corequisites", {})

    prereq_deps = _extract_course_dependencies(parsed_prereqs)
    coreq_deps = _extract_course_dependencies(parsed_coreqs)
    all_direct_deps = prereq_deps.union(coreq_deps)

    dependency_trees = []
    if all_direct_deps:
        for dep_code in sorted(list(all_direct_deps)):  # Sort for consistent output.
            # Recursive call - pass a copy of visited set for this path.
            dep_tree = build_dependency_tree(dep_code, all_reqs, visited.copy())
            dependency_trees.append(dep_tree)

    result_node = {
        "code": course_code,
        "prerequisites": parsed_prereqs,
        "corequisites": parsed_coreqs,
        "dependencies": dependency_trees,  # Store sub-trees here.
    }

    # Store in cache before returning.
    _tree_cache[course_code] = result_node
    return result_node


# --- Main Function to Generate Trees for a Program List ---
def generate_program_dependency_trees(course_list: list, all_reqs: dict) -> list:
    """
    Generates dependency trees for a list of course codes using pre-parsed reqs.
    """
    program_trees = []
    global _tree_cache  # Access the global cache.
    _tree_cache = (
        {}
    )  # Clear cache for each new program/list if desired, or keep global.

    if not course_list:
        return []

    for course_code in course_list:
        # Reset visited set for each top-level course to allow shared dependencies.
        visited_nodes = set()
        tree = build_dependency_tree(course_code, all_reqs, visited_nodes)
        program_trees.append(tree)

    return program_trees
