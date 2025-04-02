import json
import sys
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from data.database.database import Base, Program, Course
from data.input_files.programs_metadata import PROGRAMS_METADATA
from data.parser.requisite_parser import parse_prerequisites, parse_corequisites, lexer


def main():
    engine = create_engine("sqlite:///data/database/courses.db", echo=False)

    # Create the table if it does not exist.
    Base.metadata.create_all(engine)

    # Create a session factory.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    try:
        num_rows_deleted = db_session.query(Program).delete()
        print(
            f"DB Task: Deleted {num_rows_deleted} existing records from the 'programs' table."
        )
        print("DB Task: Starting database insertion.")
        count = 0
        for program_code in PROGRAMS_METADATA:
            program_info = PROGRAMS_METADATA.get(program_code)
            if not program_info:
                print(
                    f"DB Task: Skipping entry, program info not found for key: {program_code}"
                )
                continue
            if len(program_info) != 13:
                print(f"DB Task: Skipping entry, missing fields for: {program_code}")
                continue

            (
                program_name,
                program_degree_type,
                program_credits,
                program_courses,
                program_english,
                program_spanish,
                program_humanities,
                program_social,
                program_sociohumanistics,
                program_technical,
                program_technical_courses,
                program_free,
                program_kinesiology,
            ) = (
                program_info.get("name"),
                program_info.get("degree_type"),
                program_info.get("credits"),
                program_info.get("courses"),
                program_info.get("english"),
                program_info.get("spanish"),
                program_info.get("humanities"),
                program_info.get("social"),
                program_info.get("sociohumanistics"),
                program_info.get("technical"),
                program_info.get("technical_courses"),
                program_info.get("free"),
                program_info.get("kinesiology"),
            )

            # --- Process Courses List ---
            enhanced_courses = []
            if program_courses:  # Check if the list is not empty/None.
                for course_code_str in program_courses:
                    # Query the LATEST entry for the course code in the Course table.
                    # Assumes scrape_to_sql keeps the Course table updated.
                    course_db_entry = (
                        db_session.query(Course)
                        .filter(Course.course_code == course_code_str)
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
                            parsed_prereqs = parse_prerequisites(prereq_str or "")
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Failed to parse prereqs for {course_code_str}: '{prereq_str}'. Error: {e}"
                            )
                        try:
                            lexer.lineno = 1
                            parsed_coreqs = parse_corequisites(coreq_str or "")
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Failed to parse coreqs for {course_code_str}: '{coreq_str}'. Error: {e}"
                            )
                    else:
                        print(
                            f"DB Task: WARNING - Course code {course_code_str} not found in 'courses' table for prereq/coreq lookup."
                        )

                    enhanced_courses.append(
                        {
                            "code": course_code_str,
                            "prerequisites": parsed_prereqs
                            or {},  # Ensure it is a dict.
                            "corequisites": parsed_coreqs or {},  # Ensure it is a dict.
                        }
                    )
            program_courses_json = json.dumps(enhanced_courses)
            # --- End Process Courses List ---

            # --- Process Technical Courses List ---
            enhanced_tech_courses = []
            if program_technical_courses:  # Check if the list is not empty/None.
                for tech_course_code_str in program_technical_courses:
                    # Query the LATEST entry for the course code.
                    course_db_entry = (
                        db_session.query(Course)
                        .filter(Course.course_code == tech_course_code_str)
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
                            parsed_prereqs = parse_prerequisites(prereq_str or "")
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Failed to parse prereqs for {tech_course_code_str}: '{prereq_str}'. Error: {e}"
                            )
                        try:
                            lexer.lineno = 1
                            parsed_coreqs = parse_corequisites(coreq_str or "")
                        except Exception as e:
                            print(
                                f"DB Task: WARNING - Failed to parse coreqs for {tech_course_code_str}: '{coreq_str}'. Error: {e}"
                            )
                    else:
                        print(
                            f"DB Task: WARNING - Course code {tech_course_code_str} not found in 'courses' table for prereq/coreq lookup."
                        )

                    enhanced_tech_courses.append(
                        {
                            "code": tech_course_code_str,
                            "prerequisites": parsed_prereqs
                            or {},  # Ensure it is a dict.
                            "corequisites": parsed_coreqs or {},  # Ensure it is a dict.
                        }
                    )
            program_technical_courses_json = json.dumps(enhanced_tech_courses)
            # --- End Process Technical Courses List ---

            # Create Program object.
            program = Program(
                code=program_code,
                name=program_name,
                degree_type=program_degree_type,
                credits=program_credits,
                courses=program_courses_json,
                english=program_english,
                spanish=program_spanish,
                humanities=program_humanities,
                social=program_social,
                sociohumanistics=program_sociohumanistics,
                technical=program_technical,
                technical_courses=program_technical_courses_json,
                free=program_free,
                kinesiology=program_kinesiology,
                longest_path=0,
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
