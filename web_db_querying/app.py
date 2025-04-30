# import sqlite3
# from sqlalchemy import create_engine, Column, Integer, String, MetaData, Index, UniqueConstraint
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship

import os
import sys
import sqlite3
from sqlalchemy import (
    Boolean,
    ForeignKey,
    create_engine,
    Column,
    Integer,
    String,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

class Program(Base):
    __tablename__ = "programs"
    code = Column(String(5), primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    degree_type = Column(String(1), nullable=False)
    credits = Column(Integer)
    courses = Column(String)
    english = Column(Integer)
    spanish = Column(Integer)
    humanities = Column(Integer)
    social = Column(Integer)
    sociohumanistics = Column(Integer)
    technical = Column(Integer)
    technical_courses = Column(String)
    free = Column(Integer)
    kinesiology = Column(Integer)
    longest_path = Column(Integer)


class Course(Base):
    __tablename__ = "courses"
    cid = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(10), nullable=False)
    course_name = Column(String)
    year = Column(Integer, nullable=False)
    term = Column(String, nullable=False)
    last_Fall = Column(Integer)
    last_Spring = Column(Integer)
    credits = Column(Integer)
    department = Column(String)
    prerequisites = Column(String)
    corequisites = Column(String)
    difficulty = Column(Integer)

    # Define a one-to-many relationship between Course and Section
    sections = relationship(
        "Section", back_populates="course", cascade="all, delete, delete-orphan"
    )

    __table_args__ = (
        Index("idx_term", term),
        Index("idx_year", year),
        UniqueConstraint("course_code", "term", "year", name="uq_course_term_year"),
    )


class Section(Base):
    __tablename__ = "sections"
    sid = Column(Integer, primary_key=True, autoincrement=True)
    section_code = Column(String(5), nullable=False)
    meetings_text = Column(String)  # comma separated
    modality = Column(String)
    capacity = Column(Integer, default=0)
    taken = Column(Integer, default=0)
    reserved = Column(Boolean)
    professors = Column(String)  # comma separated
    misc = Column(String)  # comma separated

    # Define a many-to-one relationship between Section and Course
    cid = Column(Integer, ForeignKey("courses.cid"), nullable=False)
    course = relationship("Course", back_populates="sections")

    # Define a one-to-many relationship between Section and Meeting
    meetings = relationship(
        "Meeting", back_populates="section", cascade="all, delete, delete-orphan"
    )

    # Define a one-to-many relationship between Section and GradeDistribution
    grade_distributions = relationship("GradeDistribution", back_populates="section")

    __table_args__ = (UniqueConstraint("sid", "cid", name="unique_sections"),)


class Meeting(Base):
    __tablename__ = "meetings"
    mid = Column(Integer, primary_key=True, autoincrement=True)
    building = Column(String)
    room = Column(String)
    days = Column(String)
    start_time = Column(String)
    end_time = Column(String)

    # Define a many-to-one relationship between Meeting and Section
    sid = Column(Integer, ForeignKey("sections.sid"), nullable=False)
    section = relationship("Section", back_populates="meetings")


class GradeDistribution(Base):
    __tablename__ = "grade_distributions"
    tid = Column(
        Integer, primary_key=True, autoincrement=True
    )  # tid->table id to not overlap with Incomplete D
    sid = Column(Integer, ForeignKey("sections.sid"), nullable=False)
    A = Column(Integer, default=0, nullable=False)
    B = Column(Integer, default=0, nullable=False)
    C = Column(Integer, default=0, nullable=False)
    D = Column(Integer, default=0, nullable=False)
    F = Column(Integer, default=0, nullable=False)
    I = Column(Integer, default=0, nullable=False)
    IA = Column(Integer, default=0, nullable=False)
    IB = Column(Integer, default=0, nullable=False)
    IC = Column(Integer, default=0, nullable=False)
    ID = Column(Integer, default=0, nullable=False)
    IF = Column(Integer, default=0, nullable=False)
    NS = Column(Integer, default=0, nullable=False)
    P = Column(Integer, default=0, nullable=False)
    S = Column(Integer, default=0, nullable=False)
    W = Column(Integer, default=0, nullable=False)

    section = relationship("Section", back_populates="grade_distributions")


# Setup SQLAlchemy PostgreSQL connection
postgres_url = os.environ["DATABASE_URL"]
#https://curriculadora-db-app-c1d0a13ccbf0.herokuapp.com/
if postgres_url.startswith("postgres://"):
    postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(postgres_url)
Base.metadata.create_all(engine)

# Check if SQLite file exists
sqlite_url = "data/database/courses.db"
if not os.path.exists(sqlite_url):
    print(f"Error: SQLite file not found at {sqlite_url}")
    sys.exit(1)

# SQLite connection
sqlite_url = "data/database/courses.db"
sqlite_conn = sqlite3.connect(sqlite_url)
cursor = sqlite_conn.cursor()

# Setup SQLAlchemy session for PostgreSQL
Session = sessionmaker(bind=engine)
session = Session()

# TRUNCATE existing data to ensure clean replacement
session.execute(text("TRUNCATE grade_distributions, meetings, sections, courses, programs RESTART IDENTITY CASCADE"))
session.commit()


try:
    # Excecute query for programs table
    cursor.execute("SELECT " \
    "code, name, degree_type, credits, courses, english, spanish, humanities, " \
    "social, sociohumanistics, technical, technical_courses, free, kinesiology, longest_path " \
    " FROM programs")
    program_rows = cursor.fetchall()

    program_list = []

    for row in program_rows:
        program = Program(

            code=row[0],
            name=row[1],
            degree_type=row[2],
            credits=row[3],
            courses=row[4],
            english=row[5],
            spanish=row[6],
            humanities=row[7],
            social=row[8],
            sociohumanistics=row[9],
            technical=row[10],
            technical_courses=row[11],
            free=row[12],
            kinesiology=row[13],
            longest_path=row[14])
        
        program_list.append(program)

    # Insert data into PostgreSQL
    session.add_all(program_list)




    # Excecute query for courses table
    cursor.execute("SELECT " \
    "cid, course_code, course_name, year, term, credits, department, prerequisites, corequisites, " \
    "difficulty " \
    " FROM courses")
    course_rows = cursor.fetchall()

    course_list = []

    for row in course_rows:
        course = Course(

            course_code=row[1],
            course_name=row[2],
            year=row[3],
            term=row[4],
            credits=row[5],
            department=row[6],
            prerequisites=row[7],
            corequisites=row[8],
            difficulty=row[9])
        
        course_list.append(course)

    session.add_all(course_list)





    # Excecute query for sections table
    cursor.execute("SELECT " \
    "sid, section_code, meetings_text, modality, capacity, taken, reserved, professors, misc, " \
    "cid " \
    " FROM sections")
    section_rows = cursor.fetchall()

    section_list = []

    for row in section_rows:
        section = Section(

            section_code=row[1],
            meetings_text=row[2],
            modality=row[3],
            capacity=row[4],
            taken=row[5],
            reserved=row[6],
            professors=row[7],
            misc=row[8], 
            cid=row[9])
        
        section_list.append(section)

    session.add_all(section_list)





    # Execute query for meetings table
    cursor.execute("SELECT " \
    "mid, building, room, days, start_time, end_time, sid " \
    " FROM meetings")
    meeting_rows = cursor.fetchall()

    meeting_list = []

    for row in meeting_rows:
        meeting = Meeting(

            building=row[1],
            room=row[2],
            days=row[3],
            start_time=row[4],
            end_time=row[5],
            sid=row[6])
        
        meeting_list.append(meeting)

    session.add_all(meeting_list)





    # Excecute query for grade_distributions table
    cursor.execute("SELECT " \
    "tid, sid, A, B, C, D, F, " \
    "I, IA, IB, IC, ID, IF, NS, P, S, W " \
    " FROM grade_distributions")
    grade_distribution_rows = cursor.fetchall()

    grade_distribution_list = []

    for row in grade_distribution_rows:
        grade_distribution = GradeDistribution(

            sid=row[1],
            A=row[2],
            B=row[3],
            C=row[4],
            D=row[5],
            F=row[6],
            I=row[7],
            IA=row[8],
            IB=row[9],
            IC=row[10],
            ID=row[11],
            IF=row[12],
            NS=row[13],
            P=row[14],
            S=row[15],
            W=row[16])
        
        grade_distribution_list.append(grade_distribution)

    session.add_all(grade_distribution_list)

    # Commit inserted data to PostgreSQL
    session.commit()
    print("Migration completed successfully.")

except Exception as e:
    session.rollback()
    print(f"Error during migration: {e}")
    sys.exit(1)

finally:
    # Clean up
    session.close()
    sqlite_conn.close()