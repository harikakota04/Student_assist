"""
Pydantic Schemas — add these to your existing app/models/schemas.py
or import from here in new routes.
"""

from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class ExamTarget(str, Enum):
    CAT  = "CAT"
    IPMAT = "IPMAT"
    CLAT = "CLAT"


# ─── Auth / Student ───────────────────────────────────────────────────────────

class StudentRegister(BaseModel):
    name: str
    email: str
    password: str
    exam_target: ExamTarget = ExamTarget.CAT


class StudentLogin(BaseModel):
    email: str
    password: str


class StudentProfile(BaseModel):
    id: int
    name: str
    email: str
    exam_target: str
    has_taken_assessment: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    student: StudentProfile
    message: str


# ─── Assessment ───────────────────────────────────────────────────────────────

class AssessmentQuestion(BaseModel):
    id: str
    section: str
    topic: str
    question: str
    options: Dict[str, str]   # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: str
    explanation: str


class AssessmentTest(BaseModel):
    exam_target: str
    description: str
    time_limit_minutes: int
    total_questions: int
    sections: List[str]
    questions: List[AssessmentQuestion]


class AssessmentSubmission(BaseModel):
    student_id: int
    exam_target: str
    answers: Dict[str, str]   # {question_id: selected_option}
    questions: List[AssessmentQuestion]


class SectionScore(BaseModel):
    section: str
    score: float
    correct: int
    total: int


class AssessmentResultResponse(BaseModel):
    student_id: int
    exam_target: str
    total_score: float
    percentage: float
    grade: str
    difficulty_level: str
    section_scores: Dict[str, float]
    weak_topics: List[str]
    strong_topics: List[str]
    message: str


# ─── Dashboard ────────────────────────────────────────────────────────────────

class TopicProgress(BaseModel):
    topic: str
    subject: str
    attempts: int
    avg_score: float
    best_score: float
    last_score: float
    last_attempt: Optional[datetime]


class MockTestSummary(BaseModel):
    subject: str
    topic: str
    score: float
    grade: str
    taken_at: datetime


class StudentDashboard(BaseModel):
    student: StudentProfile
    exam_target: str
    assessment_taken: bool
    overall_score: Optional[float]
    difficulty_level: Optional[str]
    weak_topics: List[str]
    strong_topics: List[str]
    section_scores: Dict[str, float]
    recent_mock_tests: List[MockTestSummary]
    topic_progress: List[TopicProgress]
    adaptive_learning_path: Optional[Dict[str, Any]]
    total_tests_taken: int
    overall_avg_score: float


# ─── Mock Test (Extended) ─────────────────────────────────────────────────────

class ExamMockTestRequest(BaseModel):
    student_id: int
    exam_target: ExamTarget
    subject: str
    topic: str
    difficulty: str = "Intermediate"
    num_questions: int = 10


class ExamMockTestResponse(BaseModel):
    exam_target: str
    subject: str
    topic: str
    difficulty: str
    total_questions: int
    questions: List[AssessmentQuestion]


class ExamTestSubmission(BaseModel):
    student_id: int
    exam_target: str
    subject: str
    topic: str
    difficulty: str
    questions: List[AssessmentQuestion]
    user_answers: Dict[str, str]


class ExamTestResult(BaseModel):
    student_id: int
    exam_target: str
    subject: str
    topic: str
    total_questions: int
    correct_answers: int
    score: float
    grade: str
    detailed_results: List[Dict]
    next_recommended_topic: Optional[str]
    adaptive_message: str


# ─── Syllabus Browser ─────────────────────────────────────────────────────────

class SyllabusResponse(BaseModel):
    exam_target: str
    sections: Dict[str, List[str]]
