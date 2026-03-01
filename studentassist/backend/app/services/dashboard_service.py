"""
Dashboard Service
Aggregates student data from SQLite into a rich dashboard:
- Assessment results (weak/strong topics)
- Mock test history
- Per-topic progress
- Adaptive learning path recommendation
"""

import json
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.database import Student, AssessmentResult, MockTestResult, StudentProgress
from app.models.new_schemas import (
    StudentDashboard, StudentProfile, MockTestSummary, TopicProgress
)
from app.syllabus import get_syllabus, get_difficulty_from_score


def _safe_json(value, default):
    """
    SQLite stores JSON columns as text. This safely deserializes them
    back into Python lists/dicts. Returns `default` if value is None,
    already the correct type, or fails to parse.
    """
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def get_dashboard(student_id: int, db: Session) -> StudentDashboard:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student {student_id} not found.")

    # Assessment — most recent attempt
    assessment = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.student_id == student_id)
        .order_by(AssessmentResult.taken_at.desc())
        .first()
    )

    # Mock tests — last 10
    mock_tests = (
        db.query(MockTestResult)
        .filter(MockTestResult.student_id == student_id)
        .order_by(MockTestResult.taken_at.desc())
        .limit(10)
        .all()
    )

    # Topic progress
    progress_rows = (
        db.query(StudentProgress)
        .filter(StudentProgress.student_id == student_id)
        .order_by(StudentProgress.avg_score.asc())
        .all()
    )

    # Aggregates
    total_tests = (
        db.query(MockTestResult)
        .filter(MockTestResult.student_id == student_id)
        .count()
    )

    all_scores = [
        m.score for m in
        db.query(MockTestResult)
        .filter(MockTestResult.student_id == student_id)
        .all()
    ]
    overall_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    # Safely deserialize JSON fields — SQLite stores them as raw text strings
    weak_topics    = _safe_json(getattr(assessment, "weak_topics",    None), [])
    strong_topics  = _safe_json(getattr(assessment, "strong_topics",  None), [])
    section_scores = _safe_json(getattr(assessment, "section_scores", None), {})

    # Build adaptive learning path based on progress
    adaptive_path = _build_adaptive_path(
        exam=student.exam_target,
        assessment=assessment,
        progress_rows=progress_rows,
        overall_avg=overall_avg,
        weak_topics=weak_topics,
        section_scores=section_scores,
    )

    return StudentDashboard(
        student=StudentProfile.from_orm(student),
        exam_target=student.exam_target,
        assessment_taken=student.has_taken_assessment,
        overall_score=assessment.percentage if assessment else None,
        difficulty_level=assessment.difficulty_level if assessment else None,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        section_scores=section_scores,
        recent_mock_tests=[
            MockTestSummary(
                subject=m.subject,
                topic=m.topic,
                score=m.score,
                grade=m.grade,
                taken_at=m.taken_at,
            )
            for m in mock_tests
        ],
        topic_progress=[
            TopicProgress(
                topic=p.topic,
                subject=p.subject,
                attempts=p.attempts,
                avg_score=p.avg_score,
                best_score=p.best_score,
                last_score=p.last_score,
                last_attempt=p.last_attempt,
            )
            for p in progress_rows
        ],
        adaptive_learning_path=adaptive_path,
        total_tests_taken=total_tests,
        overall_avg_score=overall_avg,
    )


def _build_adaptive_path(
    exam: str,
    assessment: Optional[AssessmentResult],
    progress_rows: List[StudentProgress],
    overall_avg: float,
    weak_topics: List[str],
    section_scores: Dict[str, float],
) -> Dict[str, Any]:
    """
    Build a personalized learning path from the student's actual performance data.
    Priority order: weak assessment topics > low mock test scores > untested topics.
    """

    syllabus = get_syllabus(exam)
    all_topics = [t for topics in syllabus.values() for t in topics]

    # Topics with progress data
    tested_topics = {p.topic: p.avg_score for p in progress_rows}

    # Weak: low score in tests
    struggling = sorted(
        [(t, s) for t, s in tested_topics.items() if s < 50],
        key=lambda x: x[1]
    )
    # Moderate: 50-70
    needs_work = sorted(
        [(t, s) for t, s in tested_topics.items() if 50 <= s < 70],
        key=lambda x: x[1]
    )
    # Untested
    untested = [t for t in all_topics if t not in tested_topics]

    # Determine overall difficulty
    if assessment:
        difficulty = assessment.difficulty_level or get_difficulty_from_score(overall_avg)
    else:
        difficulty = get_difficulty_from_score(overall_avg)

    # Build priority queue — assessment weak_topics first, then progress-based
    priority_topics = []
    for t in weak_topics:
        if t not in priority_topics:
            priority_topics.append(t)
    for t, _ in struggling[:3]:
        if t not in priority_topics:
            priority_topics.append(t)
    for t, _ in needs_work[:2]:
        if t not in priority_topics:
            priority_topics.append(t)
    for t in untested[:3]:
        if t not in priority_topics:
            priority_topics.append(t)

    if not priority_topics:
        priority_topics = all_topics[:5]

    # weak_sections — section_scores is already a clean dict here (pre-deserialized)
    weak_sections = [
        sec for sec, score in section_scores.items()
        if score < 50
    ]

    return {
        "difficulty_level": difficulty,
        "focus_topics": priority_topics[:6],
        "weak_sections": weak_sections,
        "suggested_steps": _build_steps(priority_topics[:4], difficulty, exam),
        "daily_goal": _daily_goal(difficulty),
        "motivational_tip": _tip(len(struggling), len(untested)),
    }


def _build_steps(topics: List[str], difficulty: str, exam: str) -> List[str]:
    if not topics:
        return ["Complete your placement assessment to get personalized steps."]
    steps = []
    for i, topic in enumerate(topics, 1):
        if difficulty == "Beginner":
            steps.append(f"Step {i}: Study {topic} basics — definitions, formulas, and 1 solved example")
        elif difficulty == "Intermediate":
            steps.append(f"Step {i}: Practice 10 {exam}-level {topic} questions and review mistakes")
        else:
            steps.append(f"Step {i}: Solve advanced {topic} problems and time yourself (CAT/IPMAT/CLAT speed)")
    steps.append(f"Step {len(topics) + 1}: Take a mock test to measure improvement")
    return steps


def _daily_goal(difficulty: str) -> str:
    goals = {
        "Beginner":     "Study 1 new topic + solve 10 basic questions daily (45 min)",
        "Intermediate": "Solve 20 practice questions across 2 topics daily (1 hour)",
        "Advanced":     "Attempt 1 full section mock + review all errors daily (1.5 hours)",
    }
    return goals.get(difficulty, "Study consistently every day")


def _tip(weak_count: int, untested_count: int) -> str:
    if weak_count > 5:
        return "Focus on fundamentals before attempting timed practice — accuracy first, speed later."
    elif untested_count > 10:
        return "You have many untested topics — try a mock test in each section to identify gaps faster."
    else:
        return "You're making progress! Keep practicing weak topics daily and watch your scores improve."