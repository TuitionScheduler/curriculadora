import json
import sys
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from data.database.database import Base, Program, Course
from data.input_files.programs_metadata import PROGRAMS_METADATA
from data.parser.requisite_parser import (
    parse_prerequisites,
    parse_corequisites,
    lexer,
)
from data.parser.parser_utils import (
    get_highest_ancestor,
    load_and_parse_all_course_reqs,
    build_reverse_dependency_maps,
    filter_parsed_requisites,
)


def main():
    engine = create_engine("sqlite:///data/database/courses.db", echo=False)

    # Create the tables if they do not exist (safe for existing tables).
    Base.metadata.create_all(engine)

    # Create a session factory.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    try:
        # --- Pre-computation Steps ---
        all_course_requisites = load_and_parse_all_course_reqs(db_session)
        # Build the reverse dependency maps AFTER getting all parsed reqs
        prereq_for_map, coreq_for_map = build_reverse_dependency_maps(
            all_course_requisites
        )
        # --- End Pre-computation ---

        num_rows_deleted = db_session.query(Program).delete()
        print(
            f"DB Task: Deleted {num_rows_deleted} existing records from the 'programs' table."
        )
        print("DB Task: Starting database insertion.")
        count = 0
        for program_code in PROGRAMS_METADATA:
            program_info = PROGRAMS_METADATA.get(program_code)
            if not program_info or not isinstance(program_info, dict):
                print(f"DB Task: Skipping entry, invalid data for key: {program_code}")
                continue
            program_name = program_info.get("name")
            program_degree_type = program_info.get("degree_type")
            program_credits = program_info.get("credits")
            courses_list = program_info.get("courses", []) or []
            program_english = program_info.get("english")
            program_spanish = program_info.get("spanish")
            program_humanities = program_info.get("humanities")
            program_social = program_info.get("social")
            program_sociohumanistics = program_info.get("sociohumanistics")
            program_technical = program_info.get("technical")
            tech_courses_list = program_info.get("technical_courses", []) or []
            program_free = program_info.get("free")
            program_kinesiology = program_info.get("kinesiology")

            # Process courses list
            enhanced_courses_dict = {}
            if courses_list:
                for course_code_str in courses_list:
                    course_code_str_no_space = course_code_str.replace(" ", "")
                    course_db_entry = (
                        db_session.query(Course)
                        .filter(Course.course_code == course_code_str_no_space)
                        .order_by(desc(Course.year), desc(Course.term))
                        .first()
                    )

                    parsed_prereqs = {}
                    parsed_coreqs = {}
                    if course_db_entry:
                        prereq_str = course_db_entry.prerequisites
                        coreq_str = course_db_entry.corequisites
                        try:
                            lexer.lineno = 1
                            parsed_prereqs = parse_prerequisites(prereq_str or "") or {}
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Prereq parse failed for {course_code_str}: Error: {e}"
                            )
                            parsed_prereqs = {"error": "parsing failed"}
                        try:
                            lexer.lineno = 1
                            parsed_coreqs = parse_corequisites(coreq_str or "") or {}
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Coreq parse failed for {course_code_str}: Error: {e}"
                            )
                            parsed_coreqs = {"error": "parsing failed"}

                        filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
                        filtered_coreqs = filter_parsed_requisites(parsed_coreqs)

                    else:
                        print(
                            f"DB Task: WARNING - Course {course_code_str} not found in DB."
                        )
                        filtered_prereqs = None
                        filtered_coreqs = None

                    # Compute reverse dependency lookup
                    prereq_for_list = prereq_for_map.get(course_code_str_no_space, [])
                    coreq_for_list = coreq_for_map.get(course_code_str_no_space, [])

                    # Populate the dictionary including the new fields
                    enhanced_courses_dict[course_code_str_no_space] = {
                        "prerequisites": filtered_prereqs or {},
                        "corequisites": filtered_coreqs or {},
                        "prerequisite_for": prereq_for_list,  # Add new list
                        "corequisite_for": coreq_for_list,  # Add new list
                    }
            # Serialize the dictionary
            program_courses_json = json.dumps(enhanced_courses_dict)

            enhanced_tech_courses_dict = {}
            if tech_courses_list:
                for tech_course_code_str in tech_courses_list:
                    tech_course_code_str_no_space = tech_course_code_str.replace(
                        " ", ""
                    )
                    course_db_entry = (
                        db_session.query(Course)
                        .filter(Course.course_code == tech_course_code_str_no_space)
                        .order_by(desc(Course.year), desc(Course.term))
                        .first()
                    )

                    parsed_prereqs = {}
                    parsed_coreqs = {}
                    if course_db_entry:
                        prereq_str = course_db_entry.prerequisites
                        coreq_str = course_db_entry.corequisites
                        try:
                            lexer.lineno = 1
                            parsed_prereqs = parse_prerequisites(prereq_str or "") or {}
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Prereq parse failed for {tech_course_code_str}: Error: {e}"
                            )
                            parsed_prereqs = {"error": "parsing failed"}
                        try:
                            lexer.lineno = 1
                            parsed_coreqs = parse_corequisites(coreq_str or "") or {}
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Coreq parse failed for {tech_course_code_str}: Error: {e}"
                            )
                            parsed_coreqs = {"error": "parsing failed"}

                        filtered_prereqs = filter_parsed_requisites(parsed_prereqs)
                        filtered_coreqs = filter_parsed_requisites(parsed_coreqs)

                    else:
                        print(
                            f"DB Task: WARNING - Course {tech_course_code_str} not found in DB."
                        )
                        filtered_prereqs = None
                        filtered_coreqs = None

                    # Reverse dependency lookup
                    prereq_for_list = prereq_for_map.get(
                        tech_course_code_str_no_space, []
                    )
                    coreq_for_list = coreq_for_map.get(
                        tech_course_code_str_no_space, []
                    )

                    # Populate the dictionary including the new fields
                    enhanced_tech_courses_dict[tech_course_code_str_no_space] = {
                        "prerequisites": filtered_prereqs or {},
                        "corequisites": filtered_coreqs or {},
                        "prerequisite_for": prereq_for_list,  # Add new list
                        "corequisite_for": coreq_for_list,  # Add new list
                    }
            program_technical_courses_json = json.dumps(enhanced_tech_courses_dict)

            # Calculate longest path
            program_courses_and_tech_union = list(
                set(courses_list).union(tech_courses_list)
            )
            # course_code_highest_ancestor is unused for now
            number_highest_ancestor, course_code_highest_ancestor = (
                get_highest_ancestor(db_session, program_courses_and_tech_union)
            )

            program = Program(
                code=program_code,
                name=program_name,
                degree_type=program_degree_type,
                credits=program_credits,
                courses=program_courses_json,  # JSON string of DICTIONARY of objects
                english=program_english,
                spanish=program_spanish,
                humanities=program_humanities,
                social=program_social,
                sociohumanistics=program_sociohumanistics,
                technical=program_technical,
                technical_courses=program_technical_courses_json,  # JSON string of DICTIONARY of objects
                free=program_free,
                kinesiology=program_kinesiology,
                longest_path=number_highest_ancestor,
            )

            # Add to session.
            db_session.add(program)
            count += 1
            print(f"DB Task: Added program: {program_code} - {program_name}")

        # Commit the transaction.
        db_session.commit()
        print(
            f"\nDB Task: Successfully replaced {num_rows_deleted} records with {count} new programs in the database."
        )

    except Exception as e:
        print(f"DB Task: An error occurred: {e}")
        db_session.rollback()  # Roll back changes if an error occurs.
    finally:
        db_session.close()  # Always close the session.


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting...")
        sys.exit(0)
