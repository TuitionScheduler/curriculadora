import sys
import logging
import math
from sqlalchemy import create_engine, select, update, desc
from sqlalchemy.orm import sessionmaker, Session
from data.database.database import Course
from data.parser.parser_utils import (
    parse_prerequisites,
    lexer,
    calculate_all_course_paths,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///data/database/courses.db"
engine = create_engine(DATABASE_URL, echo=False)  # Use synchronous engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_calculations_and_update():
    db: Session = SessionLocal()
    all_parsed_reqs = {}
    course_credits_map = {}  # To store credits

    try:
        # Load prerequisite strings AND credits for all unique courses (latest version)
        logger.info("Loading latest prerequisites and credits for unique courses...")
        unique_codes_stmt = select(Course.course_code).distinct()
        unique_codes = db.execute(unique_codes_stmt).scalars().all()

        all_course_prereq_strings = {}
        processed_codes = 0
        total_codes = len(unique_codes)
        logger.info(f"Found {total_codes} unique course codes. Fetching latest data...")
        for code in unique_codes:
            latest_course = (
                db.query(Course)
                .filter(Course.course_code == code)
                .order_by(desc(Course.year), desc(Course.term))
                .first()
            )
            if latest_course:
                all_course_prereq_strings[code] = latest_course.prerequisites
                # Store credits, ensuring it's an int (handle None)
                course_credits_map[code] = int(latest_course.credits or 0)
            processed_codes += 1
            if processed_codes % 100 == 0 or processed_codes == total_codes:
                logger.info(f"Fetched data for {processed_codes}/{total_codes} codes.")

        # Parse all prerequisites (same as before)
        logger.info("Parsing all prerequisites...")
        processed_codes = 0
        total_codes_to_parse = len(all_course_prereq_strings)
        for code, prereq_str in all_course_prereq_strings.items():
            try:
                lexer.lineno = 1
                parsed = parse_prerequisites(prereq_str or "") or {}
                all_parsed_reqs[code] = parsed
            except Exception as e:
                logger.error(
                    f"Failed to parse prereqs for {code}: '{prereq_str}'. Error: {e}"
                )
                all_parsed_reqs[code] = {}  # Store empty if parse fails
            processed_codes += 1
            if processed_codes % 100 == 0 or processed_codes == total_codes_to_parse:
                logger.info(
                    f"Parsed prereqs for {processed_codes}/{total_codes_to_parse} unique codes."
                )

        # Calculate longest path for all courses (same as before)
        course_path_lengths = calculate_all_course_paths(all_parsed_reqs)

        # Calculate Difficulty and Update Database
        logger.info("Calculating difficulty and updating 'courses' table...")
        updated_count = 0
        error_count = 0
        # Use the keys from where we have parsed reqs as the source of codes to update
        codes_to_update = set(all_parsed_reqs.keys())
        total_to_update = len(codes_to_update)

        # Define column names to update
        path_column_name = "highest_ancestor"
        difficulty_column_name = "difficulty"

        for course_code in codes_to_update:
            # Get path length
            path_length = course_path_lengths.get(
                course_code, 0
            )  # Default to 0 if code missing
            path_length_to_store = path_length  # Store the actual value (-1 for cycles)

            # Use 0 for difficulty calculation if path is 0 or cyclic
            path_length_for_calc = path_length if path_length > 0 else 0

            # Get other components for difficulty formula
            try:
                # Extract level from course code
                if len(course_code) >= 5 and course_code[4:].isdigit():
                    level = int(course_code[4:]) // 1000
                else:
                    logger.warning(
                        f"Could not determine level for {course_code}. Using 0."
                    )
                    level = 0  # Default level if format is unexpected

                # Get credits from map
                credits = course_credits_map.get(
                    course_code, 0
                )  # Default to 0 if not found

                # Calculate log term, handling path_length <= 0
                log_term = (
                    math.log2(path_length_for_calc) if path_length_for_calc > 0 else 0
                )

                # Calculate difficulty score using integer division
                difficulty_score = (level + credits + log_term) // 3

                # Prepare update values for BOTH columns
                update_values = {
                    path_column_name: path_length_to_store,
                    difficulty_column_name: int(
                        round(difficulty_score)
                    ),  # Ensure integer
                }

                # Execute update for the specific course code
                stmt = (
                    update(Course)
                    .where(Course.course_code == course_code)
                    .values(**update_values)
                )
                result = db.execute(stmt)
                # Increment count based on rows affected (should be 1 if code exists)
                updated_count += result.rowcount

            except Exception as e:
                logger.error(f"Failed calculation or update for {course_code}: {e}")
                error_count += 1

            # Log progress periodically
            processed_count = updated_count + error_count
            if processed_count % 100 == 0 or processed_count == total_to_update:
                logger.info(
                    f"Processed updates for {processed_count}/{total_to_update} courses."
                )

        logger.info("Committing updates...")
        db.commit()
        logger.info(
            f"Successfully updated path/difficulty for {updated_count} course entries."
        )
        if error_count > 0:
            logger.warning(
                f"Failed to update path/difficulty for {error_count} course entries."
            )

    except Exception as e:
        logger.exception(f"An critical error occurred: {e}")
        db.rollback()
    finally:
        logger.info("Closing database session.")
        db.close()


if __name__ == "__main__":
    try:
        run_calculations_and_update()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting...")
        sys.exit(0)
