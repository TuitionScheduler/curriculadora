import logging
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Set
from data.database.database import get_db, Program, Course
from data.logic.scheduler import (
    generate_schedule_heuristic,
    load_program_data,
    load_course_data_lookups,
    SchedulerResult,
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

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


class TermSchedule(BaseModel):
    term_name: str  # e.g., "Fall 2025"
    courses: List[str]
    credits: int
    difficulty_sum: float  # Sum of difficulty scores for courses in the term


class RecommendedSchedule(BaseModel):
    rank: int
    score: float  # Score indicating how well it fits the curve (lower might be better)
    schedule_details: List[TermSchedule]
    is_complete: bool  # Indicates if all requirements were met by target date


class ScheduleResponse(BaseModel):
    recommendations: List[RecommendedSchedule]
    warnings: List[str] = []  # To report issues like invalid schedules


# Async atabase setup

# Define the database URL - USE YOUR CORRECT PATH
# Ensure you use the async driver prefix 'sqlite+aiosqlite:///'
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///data/database/courses.db"

# Create the async engine (used by FastAPI app)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL, echo=False
)  # Set echo=True for debugging SQL

# Create the async session factory (used by get_db)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Recommended for FastAPI
)


# FastAPI dependency function
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency function that yields an async SQLAlchemy session.
    Handles session opening and closing automatically per request.
    """
    async with AsyncSessionLocal() as session:
        # You could potentially begin a transaction here if needed globally
        # async with session.begin():
        try:
            yield session
        except Exception:
            # Rollback in case of exceptions during the request handling
            await session.rollback()
            raise
        # Session is automatically closed by 'async with'


# API endpoint


@app.post("/recommend-schedule", response_model=ScheduleResponse)
async def recommend_schedule_endpoint(
    request: ScheduleRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generates recommended course schedule sequences based on student input.
    """
    warnings = []
    try:
        # Load Static/Pre-computed Data (Do this efficiently)
        program_reqs = await load_program_data(request.program_code, db)
        if not program_reqs:
            raise HTTPException(
                status_code=404, detail=f"Program '{request.program_code}' not found"
            )

        # Load Course data: code -> {credits, difficulty, highest_ancestor, parsed_prereqs, parsed_coreqs, last_terms...}
        # This might load ALL courses initially, or be optimized later.
        course_lookups = await load_course_data_lookups(db)
        if not course_lookups:
            raise HTTPException(status_code=500, detail="Failed to load course data")

        # --- Input Validation ---
        # Ensure target grad date is after start date
        # (Add more specific date/term comparison logic if needed)
        if request.target_grad_year < request.start_year:
            raise HTTPException(
                status_code=400,
                detail="Target graduation year cannot be before start year.",
            )

        # Generate Schedule(s) using the heuristic function
        # This function will contain the core logic (loops, checks, selection)
        schedule_results: List[SchedulerResult] = await generate_schedule_heuristic(
            program_reqs=program_reqs,
            course_lookups=course_lookups,
            start_year=request.start_year,
            start_term=request.start_term,
            end_year=request.target_grad_year,
            end_term=request.target_grad_term,
            taken_courses_set=set(request.taken_courses),
            credit_limits=request.credit_load_preference.model_dump(),
            summer_pref=request.summer_preference,
            specific_summers=request.specific_summers,
            difficulty_curve=request.difficulty_curve,
            db_session=db,
            num_schedules_to_generate=3,  # Example: Try to generate top 3 variations
        )

        if not schedule_results:
            warnings.append(
                "Could not generate any valid schedules with the given constraints."
            )
            return ScheduleResponse(recommendations=[], warnings=warnings)

        # Format Output
        recommendations = []
        for i, result in enumerate(schedule_results):
            formatted_details = []
            for term_key, term_data in result.schedule.items():
                formatted_details.append(
                    TermSchedule(
                        term_name=term_key,
                        courses=term_data.courses,
                        credits=term_data.credits,
                        difficulty_sum=term_data.difficulty_sum,
                    )
                )
            recommendations.append(
                RecommendedSchedule(
                    rank=i + 1,
                    score=result.score,
                    schedule_details=formatted_details,
                    is_complete=result.is_complete,
                )
            )
            if not result.is_complete:
                warnings.append(
                    f"Schedule #{i+1} might be incomplete or exceed target graduation date."
                )

        return ScheduleResponse(recommendations=recommendations, warnings=warnings)

    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTP exceptions from validation/loading
    except Exception as e:
        logging.exception(
            f"Error generating schedule for program {request.program_code}"
        )  # Use proper logging
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: Failed to generate schedule.",
        )


# If using APIRouter, include it in your main app:
# app.include_router(router, prefix="/schedule", tags=["Scheduling"])
