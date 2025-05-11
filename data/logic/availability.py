import logging
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from data.database.database import Course

logger = logging.getLogger(__name__)


async def predict_availability(
    course_code: str, term_type: str, db_session: AsyncSession
) -> bool:
    """
    Predicts if a course is likely available in a given term and year
    based on the last known year it was offered in that term type.
    (Asynchronous version)
    Args:
        course_code: The course code (e.g., "MATE3031").
        term_type: The term ("Fall", "Spring", "FirstSummer",
                   "SecondSummer", "ExtendedSummer"). Case-insensitive.
        year: The academic year for which the prediction is needed
              (e.g., 2025 for Fall 2025, 2026 for Spring 2026).
        db_session: SQLAlchemy AsyncSession object for database query.
    Returns:
        True if the course is predicted to be available, False otherwise.
    """
    course_code_formatted = course_code.replace(" ", "")  # Ensure consistent format
    term_type_lower = term_type.lower()

    # Get current year
    current_date = date.today()
    year = current_date.year

    # Query the course record - we only need one record per course code
    # as it should contain the latest 'last offered' info for all term types.
    stmt = select(Course).where(Course.course_code == course_code_formatted)
    try:
        result = await db_session.execute(stmt)
        course_record = result.scalars().first()
    except Exception as e:
        logger.error(
            f"Database query failed for {course_code_formatted} during availability check: {e}"
        )
        return False  # Assume unavailable on DB error

    if not course_record:
        # Log less verbosely if this happens often during scheduling?
        logger.warning(
            f"Course {course_code_formatted} not found in DB for availability check."
        )
        return False  # Course not in DB, assume unavailable

    # Get last offered years, default to 0 if column is None/Null
    last_fall = course_record.last_Fall or 0
    last_spring = course_record.last_Spring or 0
    last_first_summer = course_record.last_FirstSummer or 0
    last_second_summer = course_record.last_SecondSummer or 0
    last_extended_summer = course_record.last_ExtendedSummer or 0

    # Simple prediction logic
    if term_type_lower == "fall":
        # Predict available if offered in the Fall of the *previous* academic year.
        # E.g., For Fall 2025 (year=2025), was it offered Fall 2024 (last_fall >= 2024)?
        # The 'year' argument corresponds to the start of the academic year for Fall.
        return last_fall >= (year - 1)

    elif term_type_lower == "spring":
        # Predict available if offered in the Spring of the *previous* academic year.
        # E.g., For Spring 2026 (year=2026), was it offered Spring 2025 (last_spring >= 2025)?
        # Spring term belongs to the academic year that started the previous Fall.
        return last_spring >= (
            year - 1
        )  # Check against the year the academic year *started*

    elif term_type_lower in ["firstsummer", "secondsummer", "extendedsummer"]:
        # Predict available if offered in *any* summer session of the *previous* summer.
        # E.g., For Summer 2026 (year=2026), was it offered Summer 2025 (max(last_summers) >= 2025)?
        last_any_summer = max(
            last_first_summer, last_second_summer, last_extended_summer
        )
        return last_any_summer >= (
            year - 1
        )  # Check against the year the academic year *started*

    else:
        logger.error(
            f"Unknown term_type '{term_type}' for availability check for {course_code_formatted}."
        )
        return False  # Unknown term type is treated as unavailable


def fetch_next_term_year() -> tuple[str, int]:
    """
    Fetches the next term based on the current date.
    Returns:
        str: The next term in the format "Fall YYYY", "Spring YYYY", etc.
    """
    current_date = date.today()
    year = current_date.year
    month = current_date.month

    if month <= 7:
        return "fall", year
    else:
        return "spring", year + 1
