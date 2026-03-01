"""
Exam Mock Test Service (CAT / IPMAT / CLAT)
- generate_exam_mock_test: Groq-powered MCQs for any subject+topic+difficulty
- evaluate_exam_mock_test: Score, save to DB, update progress
"""

import re
import json
from typing import Any

# allow code to load when groq isn't installed (e.g. during linting/tests)
try:
    from groq import Groq  # type: ignore
except ImportError:  # type: ignore
    Groq = None

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import MockTestResult
from app.syllabus import get_section_for_topic, get_difficulty_from_score, get_syllabus
from app.models.new_schemas import (
    AssessmentQuestion, ExamMockTestRequest, ExamMockTestResponse,
    ExamTestSubmission, ExamTestResult
)
from app.services.assessment_service import _upsert_progress


def _client() -> Any:
    if Groq is None:
        raise ImportError("groq library is required for exam mock test generation")
    return Groq(api_key=settings.groq_api_key, timeout=90.0)


# ─── Topic type detection ─────────────────────────────────────────────────────

RC_TOPICS = {
    "reading comprehension", "main idea", "author's tone", "author tone",
    "inference questions", "inference", "specific detail", "vocabulary in context",
    "critical reasoning", "para summary", "vocabulary in context",
}

PARA_JUMBLE_TOPICS = {
    "para jumbles", "para jumble", "odd sentence out", "para completion",
    "sentence rearrangement",
}

def _is_rc_topic(topic: str) -> bool:
    return topic.lower().strip() in RC_TOPICS or "comprehension" in topic.lower()

def _is_para_jumble_topic(topic: str) -> bool:
    return topic.lower().strip() in PARA_JUMBLE_TOPICS or "jumble" in topic.lower()


# ─── RC passage-based generator ──────────────────────────────────────────────

def _generate_rc_questions(
    exam: str, subject: str, topic: str, difficulty: str, n: int
) -> list:
    """
    Generates a passage (150-200 words for intermediate/advanced,
    100-130 for beginner) followed by questions based on it.
    Each question embeds the full passage using [PASSAGE]...[/PASSAGE] tags.
    """
    word_count = {
        "Beginner": "100–130 words",
        "Intermediate": "150–180 words",
        "Advanced": "180–220 words",
    }.get(difficulty, "150–180 words")

    difficulty_q_guide = {
        "Beginner": "direct factual questions — answers are clearly stated in the passage",
        "Intermediate": "a mix of direct detail, inference, and tone questions",
        "Advanced": "mostly inference, critical reasoning, author's intent, and vocabulary-in-context questions",
    }.get(difficulty, "a mix of question types")

    prompt = (
        f'You are an expert {exam} Reading Comprehension question setter.\n\n'
        f'STEP 1 — Write ONE passage of {word_count} on any substantive topic '
        f'(economics, science, history, environment, technology, philosophy). '
        f'The passage must be cohesive, well-written, and appropriate for {exam} level.\n\n'
        f'STEP 2 — Write exactly {n} multiple-choice questions based ONLY on this passage. '
        f'At {difficulty} level, use {difficulty_q_guide}.\n\n'
        f'CRITICAL FORMAT RULE:\n'
        f'Every question\'s "question" field MUST start with the full passage inside '
        f'[PASSAGE] and [/PASSAGE] tags, then two newlines, then the actual question text. '
        f'Like this exactly:\n'
        f'"[PASSAGE] <full passage here> [/PASSAGE]\\n\\n<question text here>"\n\n'
        f'Return ONLY this JSON, nothing else:\n'
        f'{{"questions":['
        f'{{"id":"q1","section":"{subject}","topic":"Reading Comprehension",'
        f'"question":"[PASSAGE] full passage text [/PASSAGE]\\n\\nWhat is the main idea?",'
        f'"options":{{"A":"...","B":"...","C":"...","D":"..."}},'
        f'"correct_answer":"A","explanation":"..."}}'
        f']}}'
    )

    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        return json.loads(raw).get("questions", [])
    except Exception as e:
        print(f"[RC ExamMock ERROR] {e}")
        return []


# ─── Para-jumble generator ────────────────────────────────────────────────────

def _generate_para_jumble_questions(
    exam: str, subject: str, topic: str, difficulty: str, n: int
) -> list:
    prompt = (
        f'You are an expert {exam} verbal ability question setter.\n\n'
        f'Generate exactly {n} para-jumble or odd-sentence-out questions '
        f'at {difficulty} level for {exam}.\n\n'
        f'Rules:\n'
        f'- PARA JUMBLE: Show 4 sentences labelled P, Q, R, S (each on its own line). '
        f'Options are orderings like "PRQS", "QPSR", "SQRP", "PQSR".\n'
        f'- ODD SENTENCE OUT: Show 4 sentences and ask which one does not fit the group. '
        f'Options are A, B, C, D pointing to one of the 4 sentences.\n'
        f'- ALWAYS include the actual sentences in the question field, one per line.\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"questions":['
        f'{{"id":"q1","section":"{subject}","topic":"Para Jumbles",'
        f'"question":"Arrange these sentences into a coherent paragraph:\\nP: ...\\nQ: ...\\nR: ...\\nS: ...",'
        f'"options":{{"A":"PRQS","B":"QPSR","C":"SQRP","D":"PQSR"}},'
        f'"correct_answer":"A","explanation":"..."}}'
        f']}}'
    )
    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        return json.loads(raw).get("questions", [])
    except Exception as e:
        print(f"[ParaJumble ExamMock ERROR] {e}")
        return []


# ─── Standard generator ───────────────────────────────────────────────────────

def _generate_standard_questions(
    exam: str, subject: str, topic: str, difficulty: str, n: int
) -> list:
    prompt = (
        f'You are an expert {exam} coach creating a practice test.\n'
        f'Exam: {exam} | Subject: {subject} | Topic: {topic} | Difficulty: {difficulty}\n\n'
        f'Generate exactly {n} multiple-choice questions on "{topic}" '
        f'at {difficulty} level, matching {exam} style.\n\n'
        f'Difficulty guidelines:\n'
        f'- Beginner: Direct formula/concept application, no tricks\n'
        f'- Intermediate: 2-step problems, mild reasoning\n'
        f'- Advanced: Multi-step, time-pressured, tricky options\n\n'
        f'IMPORTANT: Every question must be self-contained — include all numbers, '
        f'data, sentences, or context needed. Never reference external material.\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"questions":[{{"id":"q1","section":"{subject}","topic":"{topic}",'
        f'"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},'
        f'"correct_answer":"A","explanation":"..."}}]}}'
    )
    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.35,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        return json.loads(raw).get("questions", [])
    except Exception as e:
        print(f"[ExamMockTest ERROR] {e}")
        return []


# ─── Main generate function ───────────────────────────────────────────────────

def generate_exam_mock_test(request: ExamMockTestRequest) -> ExamMockTestResponse:
    exam      = request.exam_target.value
    subject   = request.subject
    topic     = request.topic
    difficulty = request.difficulty
    n         = request.num_questions

    # Route to correct generator
    if _is_rc_topic(topic):
        raw_questions = _generate_rc_questions(exam, subject, topic, difficulty, n)
    elif _is_para_jumble_topic(topic):
        raw_questions = _generate_para_jumble_questions(exam, subject, topic, difficulty, n)
    else:
        raw_questions = _generate_standard_questions(exam, subject, topic, difficulty, n)

    questions = []
    for i, q in enumerate(raw_questions, 1):
        questions.append(AssessmentQuestion(
            id=q.get("id", f"q{i}"),
            section=q.get("section", subject),
            topic=q.get("topic", topic),
            question=q.get("question", ""),
            options=q.get("options", {}),
            correct_answer=q.get("correct_answer", "A"),
            explanation=q.get("explanation", ""),
        ))

    return ExamMockTestResponse(
        exam_target=exam,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        total_questions=len(questions),
        questions=questions,
    )


# ─── Evaluate ─────────────────────────────────────────────────────────────────

def evaluate_exam_mock_test(
    submission: ExamTestSubmission,
    db: Session,
) -> ExamTestResult:
    exam = submission.exam_target
    user_answers = submission.user_answers
    questions = submission.questions

    correct_count = 0
    detailed = []
    topic_scores: dict = {}

    for q in questions:
        user_ans = user_answers.get(q.id, "").upper()
        is_correct = user_ans == q.correct_answer.upper()
        if is_correct:
            correct_count += 1

        # Per-topic tracking
        t = q.topic
        if t not in topic_scores:
            topic_scores[t] = {"correct": 0, "total": 0}
        topic_scores[t]["total"] += 1
        if is_correct:
            topic_scores[t]["correct"] += 1

        detailed.append({
            "question_id": q.id,
            "question": q.question,
            "user_answer": user_ans,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    total = len(questions)
    score = round(correct_count / total * 100, 1) if total > 0 else 0.0
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"

    # Save mock test result
    mock_result = MockTestResult(
        student_id=submission.student_id,
        exam_target=exam,
        subject=submission.subject,
        topic=submission.topic,
        difficulty=submission.difficulty,
        total_questions=total,
        correct_answers=correct_count,
        score=score,
        grade=grade,
        topic_breakdown={
            t: round(v["correct"] / v["total"] * 100, 1) if v["total"] else 0
            for t, v in topic_scores.items()
        },
    )
    db.add(mock_result)

    # Update StudentProgress — defer commit so both writes land in one transaction
    _upsert_progress(
        db=db,
        student_id=submission.student_id,
        exam_target=exam,
        subject=submission.subject,
        topic=submission.topic,
        new_score=score,
        commit=False,
    )

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[evaluate_exam_mock_test DB ERROR] {e}")
        raise

    # Next recommended topic
    next_topic = _recommend_next_topic(
        db=db,
        student_id=submission.student_id,
        exam=exam,
        current_topic=submission.topic,
        score=score,
    )

    adaptive_msg = _adaptive_message(score, submission.topic, next_topic, submission.difficulty)

    return ExamTestResult(
        student_id=submission.student_id,
        exam_target=exam,
        subject=submission.subject,
        topic=submission.topic,
        total_questions=total,
        correct_answers=correct_count,
        score=score,
        grade=grade,
        detailed_results=detailed,
        next_recommended_topic=next_topic,
        adaptive_message=adaptive_msg,
    )


def _recommend_next_topic(
    db: Session, student_id: int, exam: str,
    current_topic: str, score: float
) -> str:
    """Pick the next best topic to study based on progress."""
    from app.database import StudentProgress
    from app.syllabus import get_all_topics

    # All tested topics and their scores
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == student_id,
        StudentProgress.exam_target == exam,
    ).all()
    tested = {p.topic: p.avg_score for p in progress}
    all_topics = get_all_topics(exam)

    if score < 50:
        # Stay on current topic — not ready to move on
        return current_topic

    # Find untested topics first
    untested = [t for t in all_topics if t not in tested and t != current_topic]
    if untested:
        return untested[0]

    # Else return lowest-scoring tested topic
    weakest = sorted(tested.items(), key=lambda x: x[1])
    for t, s in weakest:
        if t != current_topic:
            return t
    return current_topic


def _adaptive_message(score: float, topic: str, next_topic: str, difficulty: str) -> str:
    if score >= 80:
        if next_topic != topic:
            return f"Excellent! You've mastered {topic} at {difficulty} level. Move on to {next_topic} next."
        else:
            return f"Outstanding! Try {topic} at Advanced difficulty to push further."
    elif score >= 60:
        return f"Good work on {topic}! Practice a few more questions to solidify your understanding before moving to {next_topic}."
    elif score >= 40:
        return f"Keep going! Review the explanations for {topic}, then try again. Next up: {next_topic}."
    else:
        return f"Don't worry — {topic} takes practice. Review the basics and retry. Consider starting with easier sub-topics first."