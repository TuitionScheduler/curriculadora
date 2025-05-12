import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from collections import defaultdict
from data.database.database import Course, Program
from data.parser.requisite_parser import (
    parse_prerequisites,
    parse_corequisites,
    lexer,
)

logger = logging.getLogger(__name__)
_path_cache = {}


def get_highest_ancestor(
    db_session: Session, program_courses_and_tech_union: list
) -> tuple:
    """
    Fetches highest ancestor and course with the highest ancestor in the program.
    """
    print(program_courses_and_tech_union)
    courses_with_ancestors_list = (
        db_session.query(Course)
        .distinct(Course.course_code)
        .filter(Course.course_code.in_(program_courses_and_tech_union))
        .order_by(desc(Course.highest_ancestor))
        .limit(1)
        .all()
    )
    print(courses_with_ancestors_list)
    if not courses_with_ancestors_list:
        return (0, "")
    course_with_highest_ancestor = courses_with_ancestors_list[0]
    course_code = course_with_highest_ancestor.course_code
    highest_ancestor = course_with_highest_ancestor.highest_ancestor
    return (highest_ancestor, course_code)


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
    )

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


def filter_parsed_requisites(req_dict: dict | None) -> dict | None:
    if not req_dict or not isinstance(req_dict, dict):
        return None

    req_type = req_dict.get("type")

    if req_type == "COURSE":
        return req_dict
    elif req_type in [
        "AND",
        "OR",
        "ANDOR",
        "FOR",
    ]:
        original_conditions = req_dict.get("conditions", [])
        if not isinstance(original_conditions, list):
            return None
        filtered_conditions = []
        for condition in original_conditions:
            filtered_condition = filter_parsed_requisites(condition)
            if filtered_condition:
                filtered_conditions.append(filtered_condition)
        if not filtered_conditions:
            return None
        elif len(filtered_conditions) == 1:
            return filtered_conditions[0]
        else:
            return {"type": req_type, "conditions": filtered_conditions}
    else:
        return None


def _extract_course_dependencies(req_dict: dict) -> set:
    """
    Helper to recursively find only COURSE codes mentioned as actual dependencies
    in a parsed requisite dictionary, pruning non-course requirements.
    """
    deps = set()
    if not isinstance(req_dict, dict):
        return deps

    req_type = req_dict.get("type")

    if req_type == "COURSE":
        # Found a course requirement, extract and format its code.
        course_val = req_dict.get("value", "")
        if isinstance(course_val, str):
            deps.add(course_val.replace(" ", ""))  # Format code (remove spaces)
        # Handle rare cases where parser might nest COURSE types
        elif isinstance(course_val, dict) and course_val.get("type") == "COURSE":
            nested_val = course_val.get("value", "")
            if isinstance(nested_val, str):
                deps.add(nested_val.replace(" ", ""))

    elif req_type in ["AND", "OR", "ANDOR", "FOR"]:
        # For logical operators, recurse on the contained conditions.
        conditions = req_dict.get("conditions", [])
        if isinstance(conditions, list):
            for condition in conditions:
                # Recursively call to find course dependencies within sub-conditions.
                deps.update(_extract_course_dependencies(condition))

    elif req_type in [
        "CREDITS_TO_GRADUATION_REQUIREMENT",
        "GRADUATION_STATUS_REQUIREMENT",
        "ENGLISH_LEVEL_REQUIREMENT",
        "CREDITS_WITH_PATTERN_REQUIREMENT",
        "COURSES_WITH_PATTERN_REQUIREMENT",
        "YEAR_REQUIREMENT",
        "EXAM_REQUIREMENT",
        "UNKNOWN",
        "DEPARTMENT_REQUIREMENT",
        "PROGRAM_REQUIREMENT",
        "DIRECTOR_APPROVAL",
    ]:
        pass
    return deps


def build_reverse_dependency_maps(all_reqs: dict) -> tuple[dict, dict]:
    # Use defaultdict(set) to automatically handle new keys and prevent duplicates
    prereq_needed_by_map_set = defaultdict(set)
    coreq_needed_by_map_set = defaultdict(set)

    total = len(all_reqs)
    count = 0
    for course_code_needing, req_info in all_reqs.items():
        # Find course codes mentioned in the prerequisites of course_code_needing
        prereq_deps = _extract_course_dependencies(req_info.get("prerequisites", {}))
        for needed_course in prereq_deps:
            needed_course_no_space = needed_course.replace(" ", "")
            # Add course_code_needing to the set for the needed_course
            prereq_needed_by_map_set[needed_course_no_space].add(course_code_needing)

        # Find course codes mentioned in the corequisites of course_code_needing
        coreq_deps = _extract_course_dependencies(req_info.get("corequisites", {}))
        for needed_course in coreq_deps:
            needed_course_no_space = needed_course.replace(" ", "")
            # Add course_code_needing to the set for the needed_course
            coreq_needed_by_map_set[needed_course_no_space].add(course_code_needing)

        count += 1
        if count % 100 == 0 or count == total:
            print(f"DB Task: Processed reverse deps for {count}/{total} courses...")

    # Convert sets to sorted lists for consistent JSON output
    prereq_map_list = {k: sorted(list(v)) for k, v in prereq_needed_by_map_set.items()}
    coreq_map_list = {k: sorted(list(v)) for k, v in coreq_needed_by_map_set.items()}

    print("DB Task: Finished building reverse dependency maps.")
    return prereq_map_list, coreq_map_list


def flatten_requisites_to_list(req_dict: dict | None) -> list[str]:
    course_codes = set()  # Use a set to automatically handle duplicates

    def find_courses_recursive(sub_dict: dict | None):
        """Inner recursive helper function."""
        # Base case: If input is not a dictionary, stop recursion for this branch.
        if not sub_dict or not isinstance(sub_dict, dict):
            return

        req_type = sub_dict.get("type")

        if req_type == "COURSE":
            # If it's a course node, extract the code.
            course_val = sub_dict.get("value", "")
            if isinstance(course_val, str):
                # Add the formatted code (no spaces) to the set.
                course_codes.add(course_val.replace(" ", ""))
            # Handle potential rare nested COURSE types if parser creates them
            elif isinstance(course_val, dict) and course_val.get("type") == "COURSE":
                nested_val = course_val.get("value", "")
                if isinstance(nested_val, str):
                    course_codes.add(nested_val.replace(" ", ""))

        elif req_type in ["AND", "OR", "ANDOR", "FOR"]:  # Check for logical operators
            # If it's a logical operator, recurse on its conditions.
            conditions = sub_dict.get("conditions", [])
            if isinstance(conditions, list):
                for condition in conditions:
                    find_courses_recursive(condition)  # Recursive call

        # Implicitly ignore all other types (EXAM, YEAR, DIRECTOR_APPROVAL etc.)
        # by not having specific elif clauses for them and not recursing.

    # Start the recursive process with the initial dictionary
    find_courses_recursive(req_dict)

    # Return a sorted list of the unique course codes found
    return sorted(list(course_codes))


def calculate_longest_path(
    course_code: str, all_parsed_reqs: dict, visited: set
) -> int:
    """
    Recursively calculates the longest prerequisite path (number of course dependencies)
    for a given course code, using pre-parsed prerequisites.
    Returns 0 for base cases (no course prerequisites).
    Returns -1 if a cycle is detected.
    """
    course_code = course_code.replace(" ", "")  # Ensure consistent formatting

    # Handle edge cases like empty string if possible
    if not course_code:
        return 0

    # Check cache first
    if course_code in _path_cache:
        return _path_cache[course_code]

    # Cycle detection
    if course_code in visited:
        # Log only once per detected cycle start if desired
        # logger.warning(f"Cycle detected for longest path calc involving: {course_code}")
        return -1  # Indicate cycle

    visited.add(course_code)

    parsed_prereqs = all_parsed_reqs.get(course_code)

    # Base case: Course not in our lookup or has no prerequisites dictionary
    if not parsed_prereqs:
        visited.remove(course_code)
        _path_cache[course_code] = 0
        return 0

    # Get DIRECT COURSE dependencies using the flatten function
    # Requires flatten_requisites_to_list to be defined/imported
    course_deps = flatten_requisites_to_list(parsed_prereqs)

    # Base case: Prerequisites exist but contain no actual COURSE dependencies
    if not course_deps:
        visited.remove(course_code)
        _path_cache[course_code] = 0
        return 0

    # Recursive step
    max_dep_path = -1  # Initialize to -1 to handle cycles correctly

    for dep_code in course_deps:
        # Pass a *copy* of the visited set down the recursion path
        dep_path = calculate_longest_path(dep_code, all_parsed_reqs, visited.copy())

        # Only consider valid, non-cyclic paths for the maximum length
        if dep_path != -1:
            max_dep_path = max(max_dep_path, dep_path)

    visited.remove(course_code)  # Remove self AFTER exploring children

    # If max_dep_path is still -1, it means all paths from here led to cycles
    if max_dep_path == -1:
        result = -1
    else:
        # The path length is 1 (representing the step from dependency to current)
        # plus the maximum path length found among its valid dependencies.
        result = 1 + max_dep_path

    _path_cache[course_code] = result  # Cache the result
    return result


def calculate_all_course_paths(all_parsed_reqs: dict) -> dict:
    """
    Calculates the longest prerequisite path for all courses provided in the
    all_parsed_reqs dictionary.
    Args:
        all_parsed_reqs: Dict mapping course_code -> parsed_prerequisite_dict.
    Returns:
        Dict mapping course_code -> longest_path_length (int, -1 for cycles).
    """
    logger.info("Calculating longest prerequisite paths for all courses...")
    global _path_cache
    _path_cache = {}  # Reset cache for a full run
    course_path_lengths = {}
    total_codes = len(all_parsed_reqs)
    processed_codes = 0

    # Calculate path for each course code we have prerequisites for
    for course_code in list(all_parsed_reqs.keys()):  # Use list for safe iteration
        if course_code not in _path_cache:  # Check cache before calculation
            visited_nodes = set()  # Reset visited set for each top-level call
            length = calculate_longest_path(course_code, all_parsed_reqs, visited_nodes)
            # The result is stored in the cache inside the function call
        # Ensure the entry exists in the final result dict, retrieving from cache
        course_path_lengths[course_code] = _path_cache[course_code]

        processed_codes += 1
        if processed_codes % 100 == 0 or processed_codes == total_codes:
            logger.info(
                f"Calculated paths for {processed_codes}/{total_codes} unique codes."
            )

    logger.info("Finished calculating all prerequisite paths.")
    return course_path_lengths
