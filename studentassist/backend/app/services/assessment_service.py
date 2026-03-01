"""
Assessment Service
- generate_assessment: builds a basic placement test for CAT, IPMAT, or CLAT
- evaluate_assessment: scores it, detects weak/strong topics, saves to DB
"""

import re
import json
from typing import Any, List, Dict, Tuple

# groq is optional for offline/static analysis; if missing we handle gracefully
try:
    from groq import Groq  # type: ignore
except ImportError:  # type: ignore
    Groq = None  # placeholder for type checking

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import Student, AssessmentResult, StudentProgress
from app.syllabus import (
    CAT_SYLLABUS, IPMAT_SYLLABUS, ASSESSMENT_CONFIG,
    get_syllabus, get_section_for_topic, get_difficulty_from_score
)
from app.models.new_schemas import (
    AssessmentQuestion, AssessmentTest, AssessmentSubmission,
    AssessmentResultResponse
)


def _client() -> Any:
    if Groq is None:
        raise ImportError("groq library is required for AI generation")
    return Groq(api_key=settings.groq_api_key, timeout=90.0)


# ─── Topics that require a passage ────────────────────────────────────────────

RC_TOPICS = {
    "Reading Comprehension",
    "Critical Reasoning",
    "Para Summary",
    "Vocabulary in Context",
}

PARA_JUMBLE_TOPICS = {
    "Para Jumbles",
    "Odd Sentence Out",
    "Para Completion",
}


# ─── RC / Passage-based generator ────────────────────────────────────────────

def _generate_rc_questions(
    exam: str,
    section: str,
    num_questions: int = 3,
) -> List[AssessmentQuestion]:
    """
    Generate a short passage followed by questions based on it.
    The passage is embedded into every question's text so the student
    always has context when answering.
    """
    prompt = (
        f'You are creating a Reading Comprehension question set for a {exam} placement test.\n\n'
        f'Step 1 — Write a short passage (120–160 words) on any general topic '
        f'(science, society, history, environment, technology). '
        f'The passage must be self-contained and suitable for a beginner-level student.\n\n'
        f'Step 2 — Write exactly {num_questions} multiple-choice questions BASED ONLY on that passage.\n'
        f'Question types to include (pick from): '
        f'main idea, author\'s tone, specific detail, inference, vocabulary in context.\n\n'
        f'CRITICAL RULE: Each question\'s "question" field must START with the full passage '
        f'enclosed in [PASSAGE] tags, then a blank line, then the actual question. Like this:\n'
        f'[PASSAGE] <full passage text here> [/PASSAGE]\\n\\n<question text here>\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"questions": ['
        f'{{"id": "q1", "section": "{section}", "topic": "Reading Comprehension", '
        f'"question": "[PASSAGE] ...passage... [/PASSAGE]\\n\\nWhat is the main idea of the passage?", '
        f'"options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, '
        f'"correct_answer": "A", "explanation": "..."}}'
        f']}}'
    )

    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        data = json.loads(raw)
        questions = []
        for i, q in enumerate(data.get("questions", []), 1):
            questions.append(AssessmentQuestion(
                id=q.get("id", f"rc{i}"),
                section=q.get("section", section),
                topic=q.get("topic", "Reading Comprehension"),
                question=q.get("question", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
            ))
        return questions

    except Exception as e:
        print(f"[RC Gen ERROR] section={section} | {e}")
        return []


# ─── Para Jumble / Odd Sentence generator ─────────────────────────────────────

def _generate_para_jumble_questions(
    exam: str,
    section: str,
    num_questions: int = 2,
) -> List[AssessmentQuestion]:
    """
    Generate para-jumble and odd-sentence-out questions with
    actual sentences to arrange — not vague abstract questions.
    """
    prompt = (
        f'You are creating verbal ability questions for a {exam} placement test.\n\n'
        f'Generate exactly {num_questions} questions. Alternate between:\n'
        f'1. PARA JUMBLE: Give 4 sentences labelled P, Q, R, S in jumbled order. '
        f'The student must find the correct sequence to form a coherent paragraph. '
        f'Options are different orderings like "PRQS", "QPSR", etc.\n'
        f'2. ODD SENTENCE OUT: Give 4 sentences A, B, C, D. Three form a logical group; '
        f'one does not fit. Student picks the odd one.\n\n'
        f'IMPORTANT: Include the actual sentences in the "question" field. '
        f'Do NOT write abstract questions like "arrange the sentences" without showing them.\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"questions": ['
        f'{{"id": "q1", "section": "{section}", "topic": "Para Jumbles", '
        f'"question": "Arrange sentences P, Q, R, S into a coherent paragraph:\\nP: ...\\nQ: ...\\nR: ...\\nS: ...", '
        f'"options": {{"A": "PSRQ", "B": "QPSR", "C": "PRQS", "D": "SQRP"}}, '
        f'"correct_answer": "A", "explanation": "..."}}'
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
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        data = json.loads(raw)
        questions = []
        for i, q in enumerate(data.get("questions", []), 1):
            questions.append(AssessmentQuestion(
                id=q.get("id", f"pj{i}"),
                section=q.get("section", section),
                topic=q.get("topic", "Para Jumbles"),
                question=q.get("question", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
            ))
        return questions

    except Exception as e:
        print(f"[Para Jumble Gen ERROR] | {e}")
        return []


# ─── Standard MCQ generator (non-RC topics) ──────────────────────────────────

def _generate_standard_questions(
    exam: str,
    section: str,
    topics: List[str],
    num_questions: int,
) -> List[AssessmentQuestion]:
    """Generate standard MCQs for Quant, LR, DI, Grammar, Vocab etc."""

    topic_list = ", ".join(topics[:8])
    prompt = (
        f'You are creating a placement/diagnostic test for students preparing for {exam}.\n'
        f'Section: "{section}"\n'
        f'Topics to cover (pick the most basic and fundamental ones): {topic_list}\n\n'
        f'Generate exactly {num_questions} BEGINNER-LEVEL multiple choice questions.\n'
        f'Rules:\n'
        f'- Questions must be self-contained — include all numbers, data, or context needed to solve them\n'
        f'- Each question must belong to a specific topic from the list\n'
        f'- Vary topics so different topics are tested\n'
        f'- For Quantitative/LR questions: include actual numbers and solve-able problems\n'
        f'- For Grammar questions: include an actual sentence to correct or fill\n'
        f'- For Vocabulary questions: include an actual sentence with the word in context\n'
        f'- For {exam} standard and beginner difficulty\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"questions": ['
        f'{{"id": "q1", "section": "{section}", "topic": "<topic name>", '
        f'"question": "<complete self-contained question with all necessary data>", '
        f'"options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, '
        f'"correct_answer": "A", "explanation": "<brief explanation>"}}'
        f']}}'
    )

    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        data = json.loads(raw)
        questions = []
        for i, q in enumerate(data.get("questions", []), 1):
            questions.append(AssessmentQuestion(
                id=q.get("id", f"q{i}"),
                section=q.get("section", section),
                topic=q.get("topic", "General"),
                question=q.get("question", ""),
                options=q.get("options", {}),
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
            ))
        return questions

    except Exception as e:
        print(f"[Assessment Gen ERROR] section={section} | {e}")
        return []


# ─── Smart section dispatcher ─────────────────────────────────────────────────

def _generate_section_questions(
    exam: str,
    section: str,
    topics: List[str],
    num_questions: int = 5,
) -> List[AssessmentQuestion]:
    """
    Routes to the right generator based on section/topics:
    - VARC sections with RC → passage-based questions
    - Para Jumble topics → sentence-arrangement questions
    - Everything else → standard MCQ
    """
    section_lower = section.lower()
    is_verbal_section = any(k in section_lower for k in ("verbal", "varc", "reading", "english"))

    if is_verbal_section:
        # Split budget: RC gets ~60%, Para Jumbles ~20%, standard ~20%
        rc_count  = max(2, round(num_questions * 0.6))
        pj_count  = max(1, round(num_questions * 0.2))
        std_count = num_questions - rc_count - pj_count

        std_topics = [
            t for t in topics
            if t not in RC_TOPICS and t not in PARA_JUMBLE_TOPICS
        ]

        questions: List[AssessmentQuestion] = []

        rc_qs = _generate_rc_questions(exam, section, num_questions=rc_count)
        questions.extend(rc_qs)

        pj_qs = _generate_para_jumble_questions(exam, section, num_questions=pj_count)
        questions.extend(pj_qs)

        if std_count > 0 and std_topics:
            std_qs = _generate_standard_questions(exam, section, std_topics, std_count)
            questions.extend(std_qs)

        return questions[:num_questions]

    else:
        return _generate_standard_questions(exam, section, topics, num_questions)


def generate_assessment(exam_target: str) -> AssessmentTest:
    """Build the full placement assessment for CAT or IPMAT."""
    exam = exam_target.upper()
    config = ASSESSMENT_CONFIG.get(exam, ASSESSMENT_CONFIG["CAT"])
    syllabus = get_syllabus(exam)

    all_questions: List[AssessmentQuestion] = []
    qnum = 1

    for section, topics in syllabus.items():
        section_qs = _generate_section_questions(
            exam=exam,
            section=section,
            topics=topics,
            num_questions=config["questions_per_section"],
        )
        # Re-index IDs sequentially
        for q in section_qs:
            q.id = f"q{qnum}"
            qnum += 1
        all_questions.extend(section_qs)

    return AssessmentTest(
        exam_target=exam,
        description=config["description"],
        time_limit_minutes=config["time_limit_minutes"],
        total_questions=len(all_questions),
        sections=config["sections"],
        questions=all_questions,
    )


# ─── Evaluation ───────────────────────────────────────────────────────────────

def _score_sections(
    questions: List[AssessmentQuestion],
    answers: Dict[str, str],
) -> Tuple[Dict[str, Dict], Dict[str, float]]:
    """
    Returns:
      topic_results: {topic: {correct: int, total: int}}
      section_scores: {section: percentage}
    """
    topic_results: Dict[str, Dict] = {}
    section_data: Dict[str, Dict] = {}

    for q in questions:
        topic = q.topic
        section = q.section
        user_ans = answers.get(q.id, "").upper()
        correct = user_ans == q.correct_answer.upper()

        if topic not in topic_results:
            topic_results[topic] = {"correct": 0, "total": 0}
        topic_results[topic]["total"] += 1
        if correct:
            topic_results[topic]["correct"] += 1

        if section not in section_data:
            section_data[section] = {"correct": 0, "total": 0}
        section_data[section]["total"] += 1
        if correct:
            section_data[section]["correct"] += 1

    section_scores = {
        sec: round(d["correct"] / d["total"] * 100, 1) if d["total"] > 0 else 0.0
        for sec, d in section_data.items()
    }
    return topic_results, section_scores


def evaluate_assessment(
    submission: AssessmentSubmission,
    db: Session,
) -> AssessmentResultResponse:
    exam = submission.exam_target.upper()
    topic_results, section_scores = _score_sections(
        submission.questions, submission.answers
    )

    # Overall score
    total_correct = sum(v["correct"] for v in topic_results.values())
    total_qs = sum(v["total"] for v in topic_results.values())
    percentage = round(total_correct / total_qs * 100, 1) if total_qs > 0 else 0.0
    difficulty = get_difficulty_from_score(percentage)

    weak_topics = [
        t for t, v in topic_results.items()
        if v["total"] > 0 and (v["correct"] / v["total"]) < 0.5
    ]
    strong_topics = [
        t for t, v in topic_results.items()
        if v["total"] > 0 and (v["correct"] / v["total"]) >= 0.7
    ]

    if percentage >= 80:
        grade = "A"
    elif percentage >= 60:
        grade = "B"
    elif percentage >= 40:
        grade = "C"
    else:
        grade = "D"

    # Save to DB — all writes in one transaction
    student = db.query(Student).filter(Student.id == submission.student_id).first()
    if student:
        prior_count = db.query(AssessmentResult).filter(
            AssessmentResult.student_id == submission.student_id
        ).count()

        result = AssessmentResult(
            student_id       = submission.student_id,
            exam_target      = exam,
            attempt_number   = prior_count + 1,
            total_score      = float(total_correct),
            percentage       = percentage,
            section_scores   = section_scores,   # stored as JSON by SQLAlchemy
            weak_topics      = weak_topics,       # stored as JSON by SQLAlchemy
            strong_topics    = strong_topics,     # stored as JSON by SQLAlchemy
            difficulty_level = difficulty,
        )
        db.add(result)
        student.has_taken_assessment = True

        # Seed StudentProgress for each topic — batched before single commit
        for topic, v in topic_results.items():
            topic_score = round(v["correct"] / v["total"] * 100, 1) if v["total"] > 0 else 0.0
            section = get_section_for_topic(exam, topic)
            _upsert_progress(
                db=db,
                student_id=submission.student_id,
                exam_target=exam,
                subject=section,
                topic=topic,
                new_score=topic_score,
                commit=False,   # defer commit — we do one at the end
            )

        # Single commit for the entire transaction
        try:
            db.commit()
            db.refresh(result)
        except Exception as e:
            db.rollback()
            print(f"[evaluate_assessment DB ERROR] {e}")
            raise

    return AssessmentResultResponse(
        student_id=submission.student_id,
        exam_target=exam,
        total_score=float(total_correct),
        percentage=percentage,
        grade=grade,
        difficulty_level=difficulty,
        section_scores=section_scores,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        message=_feedback_message(percentage, weak_topics, strong_topics),
    )


def _feedback_message(pct: float, weak: List[str], strong: List[str]) -> str:
    if pct >= 70:
        return (
            f"Great start! You scored {pct}%. "
            f"Your strengths are {', '.join(strong[:3]) if strong else 'spread across topics'}. "
            f"Focus on polishing: {', '.join(weak[:3]) if weak else 'keep practicing all areas'}."
        )
    elif pct >= 40:
        return (
            f"Good effort! You scored {pct}%. "
            f"Work on these weak areas first: {', '.join(weak[:4]) if weak else 'all sections evenly'}. "
            f"Your learning path has been personalized for you."
        )
    else:
        return (
            f"You scored {pct}%. Don't worry — everyone starts somewhere! "
            f"We've identified {len(weak)} areas to focus on and built you a beginner-friendly path."
        )


# ─── Progress Upsert (shared by mock test service too) ───────────────────────

def _upsert_progress(
    db: Session,
    student_id: int,
    exam_target: str,
    subject: str,
    topic: str,
    new_score: float,
    commit: bool = True,   # allow callers to batch commits
):
    from datetime import datetime

    prog = db.query(StudentProgress).filter(
        StudentProgress.student_id == student_id,
        StudentProgress.topic == topic,
        StudentProgress.exam_target == exam_target,
    ).first()

    if prog:
        total_score = prog.avg_score * prog.attempts + new_score
        prog.attempts += 1
        prog.avg_score = round(total_score / prog.attempts, 1)
        prog.best_score = max(prog.best_score, new_score)
        prog.last_score = new_score
        prog.last_attempt = datetime.utcnow()
    else:
        prog = StudentProgress(
            student_id=student_id,
            exam_target=exam_target,
            subject=subject,
            topic=topic,
            attempts=1,
            avg_score=new_score,
            best_score=new_score,
            last_score=new_score,
            last_attempt=datetime.utcnow(),
        )
        db.add(prog)

    if commit:
        db.commit()