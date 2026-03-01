"""
SQLite Database — StudentAssist
Tables:
  students, assessment_results, mock_test_results, student_progress,
  weekly_logs, prep_schedule
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, Boolean, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./studentassist.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String(100), nullable=False)
    email                = Column(String(150), unique=True, index=True, nullable=False)
    password_hash        = Column(String(256), nullable=False)
    exam_target          = Column(String(10), nullable=False, default="CAT")
    has_taken_assessment = Column(Boolean, default=False)
    created_at           = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("AssessmentResult", back_populates="student", order_by="AssessmentResult.taken_at")
    mock_tests  = relationship("MockTestResult",   back_populates="student")
    progress    = relationship("StudentProgress",  back_populates="student")
    weekly_logs = relationship("WeeklyLog",        back_populates="student")
    schedules   = relationship("PrepSchedule",     back_populates="student")


class AssessmentResult(Base):
    """Monthly assessment — one row per attempt (retakeable every 30 days)."""
    __tablename__ = "assessment_results"
    id               = Column(Integer, primary_key=True, index=True)
    student_id       = Column(Integer, ForeignKey("students.id"), index=True)
    exam_target      = Column(String(10))
    attempt_number   = Column(Integer, default=1)
    total_score      = Column(Float)
    percentage       = Column(Float)
    section_scores   = Column(JSON)
    weak_topics      = Column(JSON)
    strong_topics    = Column(JSON)
    difficulty_level = Column(String(20))
    taken_at         = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="assessments")


class MockTestResult(Base):
    __tablename__ = "mock_test_results"
    id              = Column(Integer, primary_key=True, index=True)
    student_id      = Column(Integer, ForeignKey("students.id"))
    exam_target     = Column(String(10))
    subject         = Column(String(60))
    topic           = Column(String(100))
    difficulty      = Column(String(20))
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    score           = Column(Float)
    grade           = Column(String(2))
    topic_breakdown = Column(JSON)
    taken_at        = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="mock_tests")


class StudentProgress(Base):
    __tablename__ = "student_progress"
    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"))
    exam_target  = Column(String(10))
    subject      = Column(String(60))
    topic        = Column(String(100))
    attempts     = Column(Integer, default=0)
    avg_score    = Column(Float,   default=0.0)
    best_score   = Column(Float,   default=0.0)
    last_score   = Column(Float,   default=0.0)
    last_attempt = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="progress")


class WeeklyLog(Base):
    """One row per week. topics_covered = [{topic,subject,hours,confidence,notes}]"""
    __tablename__ = "weekly_logs"
    id             = Column(Integer, primary_key=True, index=True)
    student_id     = Column(Integer, ForeignKey("students.id"), index=True)
    exam_target    = Column(String(10))
    week_start     = Column(String(12))
    week_label     = Column(String(40))
    topics_covered = Column(JSON, default=list)
    total_hours    = Column(Float, default=0.0)
    summary_notes  = Column(Text, default="")
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="weekly_logs")


class PrepSchedule(Base):
    """One schedule per student. weeks = [{week_number,week_label,topics,notes,completed}]"""
    __tablename__ = "prep_schedule"
    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"), index=True, unique=True)
    exam_target  = Column(String(10))
    plan_months  = Column(Integer, default=6)
    start_date   = Column(String(12))
    exam_date    = Column(String(12), default="")
    weeks        = Column(JSON, default=list)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student", back_populates="schedules")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)


class QAEntry(Base):
    """
    Community Q&A database.
    Every question ever asked + its answer lives here.
    New AI answers are auto-saved. Admins can import bulk data.
    """
    __tablename__ = "qa_entries"

    id           = Column(Integer, primary_key=True, index=True)
    question     = Column(Text, nullable=False)
    answer       = Column(Text, nullable=False)
    subject      = Column(String(80),  default="General")   # QA / VARC / LR / General
    topic        = Column(String(100), default="General")
    source       = Column(String(30),  default="ai")        # "ai" | "manual" | "import"
    asked_by     = Column(Integer, ForeignKey("students.id"), nullable=True)
    helpful_count= Column(Integer, default=0)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow)