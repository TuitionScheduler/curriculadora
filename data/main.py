import logging
import datetime
from data.logic.availability import fetch_next_term_year
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Set, Tuple, AsyncGenerator


from data.logic.recommendation_scheduler import (
    generate_sequence,  # New main generation function
    load_program_data,
    load_course_data_lookups,
    SchedulerResult,
    SchedulerSkeletonResult,
)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

app = FastAPI()


# Pydantic models
class CreditLoad(BaseModel):
    min: int = Field(..., ge=3, description="Minimum credits per term")
    max: int = Field(..., le=21, description="Maximum credits per term")

    @validator("max")
    def max_must_be_gte_min(cls, max_val, values):
        min_val = values.get("min")
        if min_val is not None and max_val < min_val:
            raise ValueError("Max credits must be greater than or equal to min credits")
        return max_val


class ScheduleRequest(BaseModel):
    program_code: str = Field(..., description="Program code (e.g., '0508')")
    start_year: int = Field(
        ...,
        description="Academic year to start planning FROM (e.g., 2025 for Fall 2025/Spring 2026)",
    )
    start_term: Literal[
        "Fall", "Spring", "FirstSummer", "SecondSummer", "ExtendedSummer"
    ] = Field(..., description="Term to start planning FROM")
    target_grad_year: int = Field(..., description="Target academic year of graduation")
    target_grad_term: Literal["Fall", "Spring"] = Field(
        ..., description="Target term of graduation (usually Fall or Spring)"
    )
    taken_courses: List[str] = Field(
        [], description="List of course codes already passed"
    )
    credit_load_preference: CreditLoad
    summer_preference: Literal["None", "All", "Specific"] = Field(
        ..., description="Preference for taking summer courses"
    )
    specific_summers: Optional[List[int]] = Field(
        None,
        description="List of years to take summer classes if preference is 'Specific'",
    )
    difficulty_curve: Literal["Flat", "Decreasing", "Increasing"] = Field(
        "Flat", description="Desired difficulty curve across terms"
    )
    specific_elective_credits_initial: Dict[str, int] = Field(  # New field
        default_factory=dict,
        description="Credits completed by category (e.g., {'humanities': 6, 'technical': 3})",
    )

    @validator("specific_summers", pre=True, always=True)
    def check_specific_summers(cls, v, values):
        if values.get("summer_preference") == "Specific" and not v:
            raise ValueError(
                'specific_summers must be provided if summer_preference is "Specific"'
            )
        if values.get("summer_preference") != "Specific" and v:
            raise ValueError(
                'specific_summers should only be provided if summer_preference is "Specific"'
            )
        return v


class TermSchedule(BaseModel):  # For API response, mirrors structure of scheduler
    term_name: str
    courses: List[str]
    credits: int
    difficulty_sum: float


class RecommendedSchedule(BaseModel):
    rank: int
    score: float
    schedule_details: List[TermSchedule]
    is_complete: bool


class ScheduleResponse(BaseModel):
    recommendations: List[RecommendedSchedule]
    warnings: List[str] = []


# Async database setup
# Ensure this path points to your actual database file
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./data/database/courses.db"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL, echo=False  # Set echo=True for SQL debugging
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Helper to map request terms to scheduler's internal terms
def map_request_term_to_scheduler_term(req_term: str) -> str:
    term_lower = req_term.lower()
    # The scheduler's get_next_term uses: ["spring", "firstsummer", "secondsummer", "fall"]
    mapping = {
        "fall": "fall",
        "spring": "spring",
        "firstsummer": "firstsummer",
        "secondsummer": "secondsummer",
        "extendedsummer": "secondsummer",  # Map ExtendedSummer to SecondSummer for now
    }
    if term_lower not in mapping:
        # This case should ideally be caught by FastAPI's Literal validation if not in Enum
        raise ValueError(f"Unsupported start term for scheduler: {req_term}")
    return mapping[term_lower]


# API endpoint
@app.post("/recommend-schedule", response_model=ScheduleResponse)
async def recommend_schedule_endpoint(
    request: ScheduleRequest, db: AsyncSession = Depends(get_db)
):

    # logging.basicConfig(
    #     level=logging.DEBUG,  # Set the logging level
    #     format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
    #     handlers=[
    #         logging.FileHandler(
    #             f"run-{datetime.datetime.now()}.log"
    #         ),  # Log to a file named 'app.log'
    #         # logging.StreamHandler(),  # Optional: Log to the console as well
    #     ],
    # )
    api_warnings = []  # Use a different name to avoid conflict with result warnings
    try:
        program_reqs = await load_program_data(request.program_code, db)
        if not program_reqs:
            raise HTTPException(
                status_code=404, detail=f"Program '{request.program_code}' not found"
            )

        course_lookups = await load_course_data_lookups(db)
        if not course_lookups:
            raise HTTPException(
                status_code=500,
                detail="Failed to load course data or course data is empty.",
            )

        # --- Input Validation ---
        if request.target_grad_year < request.start_year or (
            request.target_grad_year == request.start_year
            and request.target_grad_term.lower() == "spring"
            and request.start_term.lower() in ["fall", "extendedsummer", "secondsummer"]
        ):  # More precise check
            raise HTTPException(
                status_code=400,
                detail="Target graduation date cannot be before or invalidly same as start date.",
            )

        try:
            scheduler_start_term = map_request_term_to_scheduler_term(
                request.start_term
            )
        except ValueError as e:  # Should not happen if Literal validation is correct
            raise HTTPException(status_code=400, detail=str(e))

        max_terms_for_scheduler = (
            request.target_grad_year - request.start_year + 1
        ) * 4
        if max_terms_for_scheduler <= 0:  # Should be caught by detailed check above
            max_terms_for_scheduler = 4  # Fallback, ensure at least 1 year

        # Acknowledge preferences not yet fully supported by the new backend
        if request.summer_preference != "All":
            api_warnings.append(
                f"Note: 'summer_preference' for '{request.summer_preference}' is noted. "
                "The current scheduler version primarily includes summer courses based on availability. "
                "Advanced summer term management is under development."
            )
        if request.specific_summers and request.summer_preference == "Specific":
            api_warnings.append(
                f"Note: 'specific_summers' preference is noted. "
                "The current scheduler version does not yet support targeting specific summer years. "
                "Advanced summer term management is under development."
            )
        if request.difficulty_curve != "Flat":
            api_warnings.append(
                f"Note: 'difficulty_curve' preference for '{request.difficulty_curve}' is noted. "
                "The current scheduler uses a default term difficulty target. "
                "Dynamic difficulty curve shaping is under development."
            )

        # TODO: implement course prediction based on start year and term as request start year and term refer to
        # when a student enrolled rather than the first term/year they are planning for using our scheduler.
        upcoming_start_term, upcoming_start_year = fetch_next_term_year()
        if request.start_year > upcoming_start_year:
            # Handle case where the student hasn't enrolled yet
            upcoming_start_term = "fall"
            upcoming_start_year = request.start_year

        # Call the new generate_sequence function
        result_tuple: Tuple[
            Optional[SchedulerResult], Optional[SchedulerSkeletonResult]
        ] = await generate_sequence(
            program_reqs=program_reqs,
            course_lookups=course_lookups,
            start_term_name=upcoming_start_term,
            start_year=upcoming_start_year,
            initial_taken_courses_set=set(request.taken_courses),
            specific_elective_credits_initial=request.specific_elective_credits_initial,
            credit_limits=request.credit_load_preference.model_dump(),
            db_session=db,
            max_terms=max_terms_for_scheduler,
        )

        resolved_schedule_result: Optional[SchedulerResult] = result_tuple[0]
        skeleton_result_for_log: Optional[SchedulerSkeletonResult] = result_tuple[
            1
        ]  # For logging/debug

        if (
            skeleton_result_for_log and skeleton_result_for_log.warnings
        ):  # Capture warnings from skeleton
            api_warnings.extend(
                w for w in skeleton_result_for_log.warnings if w not in api_warnings
            )

        if not resolved_schedule_result:
            api_warnings.append(
                "Could not generate any valid schedules with the given constraints using the current scheduler."
            )
            return ScheduleResponse(
                recommendations=[], warnings=list(set(api_warnings))
            )  # Ensure unique warnings

        if resolved_schedule_result.warnings:  # Capture warnings from resolved result
            api_warnings.extend(
                w for w in resolved_schedule_result.warnings if w not in api_warnings
            )

        recommendations = []
        formatted_schedule_details = []

        term_order_map = {"spring": 0, "firstsummer": 1, "secondsummer": 2, "fall": 3}
        sorted_term_keys = []
        if resolved_schedule_result.schedule:  # Check if schedule dict is not empty
            try:
                sorted_term_keys = sorted(
                    resolved_schedule_result.schedule.keys(),
                    key=lambda tk: (
                        int(tk.split()[1]),
                        term_order_map.get(tk.split()[0].lower(), -1),
                    ),
                )
            except Exception as e:
                logging.warning(
                    f"Could not sort term keys for display: {e}. Using unsorted."
                )
                sorted_term_keys = list(resolved_schedule_result.schedule.keys())

            for term_key in sorted_term_keys:
                term_data = resolved_schedule_result.schedule[
                    term_key
                ]  # This is scheduler
                formatted_schedule_details.append(
                    TermSchedule(  # Convert to API's TermSchedule model
                        term_name=term_key,
                        courses=term_data.courses,
                        credits=term_data.credits,
                        difficulty_sum=term_data.difficulty_sum,
                    )
                )

        schedule_meets_target_date = True
        if not resolved_schedule_result.is_complete:
            api_warnings.append(
                "Warning: Generated schedule might be incomplete or not meet all program requirements."
            )
            schedule_meets_target_date = (
                False  # If reqs not met, it implicitly doesn't meet target completion.
            )

        if formatted_schedule_details:
            last_term_in_schedule_str = formatted_schedule_details[-1].term_name
            last_term_parts = last_term_in_schedule_str.split()
            last_term_name_sched = last_term_parts[0].lower()
            last_term_year_sched = int(last_term_parts[1])
            target_grad_term_lower = request.target_grad_term.lower()

            if last_term_year_sched > request.target_grad_year:
                api_warnings.append(
                    f"Warning: Generated schedule extends beyond target graduation year ({request.target_grad_year}). Last term: {last_term_in_schedule_str}"
                )
                schedule_meets_target_date = False
            elif last_term_year_sched == request.target_grad_year:
                if term_order_map.get(last_term_name_sched, -1) > term_order_map.get(
                    target_grad_term_lower, 4
                ):
                    api_warnings.append(
                        f"Warning: Generated schedule extends beyond target graduation term ({request.target_grad_term} {request.target_grad_year}). Last term: {last_term_in_schedule_str}"
                    )
                    schedule_meets_target_date = False
        elif (
            not resolved_schedule_result.is_complete
        ):  # No terms generated, and program not complete
            api_warnings.append(
                "Warning: No schedule terms were generated, and program requirements are not met."
            )
            schedule_meets_target_date = False

        recommendations.append(
            RecommendedSchedule(
                rank=1,
                score=resolved_schedule_result.score,
                schedule_details=formatted_schedule_details,
                is_complete=resolved_schedule_result.is_complete
                and schedule_meets_target_date,
            )
        )

        return ScheduleResponse(
            recommendations=recommendations, warnings=list(set(api_warnings))
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.exception(
            f"Unexpected error generating schedule for program {request.program_code}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: Failed to generate schedule. Error: {str(e)}",
        )
