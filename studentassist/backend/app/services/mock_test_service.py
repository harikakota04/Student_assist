"""
Mock Test Service
- generate_mock_test: Uses Groq to create MCQs from article content
- evaluate_test: Scores a submitted test against correct answers
- generate_mock_test_from_short_content: Expands short content then generates test
"""

import re
import json
from groq import Groq
from app.models.schemas import (
    MockTestResponse, MockTestRequest, TestSubmission, TestResult,
    Question, QuestionOption
)
from app.core.config import settings


def _client() -> Groq:
    return Groq(api_key=settings.groq_api_key, timeout=60.0)


SKILLS = ["comprehension", "vocabulary", "inference", "main idea", "critical thinking"]
DIFF_TAGS = ["Easy", "Medium", "Hard"]


def generate_mock_test(
    article_content: str,
    article_title: str,
    difficulty: str = "Mixed",
    num_questions: int = 10,
) -> MockTestResponse:
    """Generate MCQs from article content using Groq."""

    prompt = (
        f'You are a teacher creating a multiple-choice quiz.\n'
        f'Article Title: "{article_title}"\n'
        f'Article Content:\n{article_content[:3000]}\n\n'
        f'Create exactly {num_questions} multiple-choice questions.\n'
        f'Mix difficulty: roughly 30% Easy, 45% Medium, 25% Hard.\n'
        f'Vary the skill_tested across: comprehension, vocabulary, inference, main idea, critical thinking.\n\n'
        f'Return ONLY a JSON object in this exact format, nothing before or after:\n'
        f'{{\n'
        f'  "questions": [\n'
        f'    {{\n'
        f'      "question_id": "q1",\n'
        f'      "question": "...",\n'
        f'      "options": [\n'
        f'        {{"option_id": "A", "text": "..."}},\n'
        f'        {{"option_id": "B", "text": "..."}},\n'
        f'        {{"option_id": "C", "text": "..."}},\n'
        f'        {{"option_id": "D", "text": "..."}}\n'
        f'      ],\n'
        f'      "correct_answer": "A",\n'
        f'      "explanation": "...",\n'
        f'      "difficulty_tag": "Easy",\n'
        f'      "skill_tested": "comprehension"\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
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
        skills_seen = set()

        for i, q in enumerate(data.get("questions", [])):
            # Handle options — accept either list or dict from Groq
            raw_opts = q.get("options", [])
            if isinstance(raw_opts, dict):
                # Convert {"A": "text"} → [{"option_id": "A", "text": "text"}]
                opts = [QuestionOption(option_id=k, text=v) for k, v in raw_opts.items()]
            else:
                opts = [QuestionOption(option_id=o["option_id"], text=o["text"]) for o in raw_opts]

            skill = q.get("skill_tested", SKILLS[i % len(SKILLS)])
            dtag  = q.get("difficulty_tag", DIFF_TAGS[i % len(DIFF_TAGS)])
            skills_seen.add(skill)

            questions.append(Question(
                question_id=q.get("question_id", f"q{i+1}"),
                question=q.get("question", ""),
                options=opts,
                correct_answer=q.get("correct_answer", "A"),
                explanation=q.get("explanation", ""),
                difficulty_tag=dtag,
                skill_tested=skill,
            ))

        return MockTestResponse(
            title=article_title,
            difficulty=difficulty,
            questions=questions,
            total_questions=len(questions),
            estimated_time=f"{len(questions) * 1}-{len(questions) * 2} min",
            skills_covered=list(skills_seen),
        )

    except Exception as e:
        print(f"[MockTest ERROR] {e}")
        return MockTestResponse(
            title=article_title,
            difficulty=difficulty,
            questions=[],
            total_questions=0,
            estimated_time="—",
            skills_covered=[],
        )


def evaluate_test(submission: TestSubmission) -> TestResult:
    """Score a submitted test by comparing answers to correct answers."""

    questions    = submission.questions
    user_answers = submission.user_answers  # {question_id: "A" / "B" / ...}

    correct_count = 0
    total         = len(questions)
    results       = []

    skill_scores: dict = {}
    diff_scores:  dict = {}

    for q in questions:
        user_ans   = user_answers.get(q.question_id, "")
        is_correct = user_ans.upper() == q.correct_answer.upper()
        if is_correct:
            correct_count += 1

        # Track per-skill accuracy
        sk = q.skill_tested
        if sk not in skill_scores:
            skill_scores[sk] = {"correct": 0, "total": 0}
        skill_scores[sk]["total"] += 1
        if is_correct:
            skill_scores[sk]["correct"] += 1

        # Track per-difficulty accuracy
        dt = q.difficulty_tag
        if dt not in diff_scores:
            diff_scores[dt] = {"correct": 0, "total": 0}
        diff_scores[dt]["total"] += 1
        if is_correct:
            diff_scores[dt]["correct"] += 1

        results.append({
            "question_id":    q.question_id,
            "question":       q.question,
            "user_answer":    user_ans,
            "correct_answer": q.correct_answer,
            "is_correct":     is_correct,
            "explanation":    q.explanation,
        })

    score = round((correct_count / total) * 100, 2) if total > 0 else 0.0
    pct   = int(score)

    if pct >= 90:
        grade = "A+"
    elif pct >= 80:
        grade = "A"
    elif pct >= 70:
        grade = "B"
    elif pct >= 60:
        grade = "C"
    elif pct >= 40:
        grade = "D"
    else:
        grade = "F"

    # Skill breakdown as percentages
    skill_breakdown = {
        sk: round((v["correct"] / v["total"]) * 100)
        for sk, v in skill_scores.items() if v["total"] > 0
    }

    # Difficulty breakdown as percentages
    diff_breakdown = {
        dt: round((v["correct"] / v["total"]) * 100)
        for dt, v in diff_scores.items() if v["total"] > 0
    }

    # Weak areas = skills below 50%
    weak_areas = [sk for sk, p in skill_breakdown.items() if p < 50]

    # Simple feedback
    if pct >= 80:
        feedback = "Excellent work! You have a strong understanding of this article."
    elif pct >= 60:
        feedback = "Good effort! Review the topics you missed and you'll improve quickly."
    else:
        feedback = "Keep practicing! Re-read the article and focus on your weak areas."

    improvement_tips = []
    for wa in weak_areas:
        improvement_tips.append(f"Focus on improving your {wa} skill — try re-reading the relevant sections.")

    return TestResult(
        total_questions=total,
        correct_answers=correct_count,
        score=correct_count,
        grade=grade,
        detailed_results=results,
        # Extra fields the frontend uses — stored in detailed_results isn't enough,
        # so we attach them directly. Pydantic will ignore extras unless we allow them,
        # so we pass as part of a dict approach below.
    )


# ── Monkey-patch TestResult to carry extra fields the frontend reads ──────────
# The frontend reads: percentage, score, total, skill_breakdown, diff_breakdown,
# weak_areas, feedback, improvement_tips — so override evaluate_test return.

def evaluate_test(submission: TestSubmission) -> dict:  # noqa: F811
    """Score a submitted test — returns a plain dict matching frontend expectations."""

    questions    = submission.questions
    user_answers = submission.user_answers

    correct_count = 0
    total         = len(questions)
    results       = []
    skill_scores: dict = {}
    diff_scores:  dict = {}

    for q in questions:
        user_ans   = user_answers.get(q.question_id, "")
        is_correct = user_ans.upper() == q.correct_answer.upper()
        if is_correct:
            correct_count += 1

        sk = q.skill_tested
        skill_scores.setdefault(sk, {"correct": 0, "total": 0})
        skill_scores[sk]["total"] += 1
        if is_correct:
            skill_scores[sk]["correct"] += 1

        dt = q.difficulty_tag
        diff_scores.setdefault(dt, {"correct": 0, "total": 0})
        diff_scores[dt]["total"] += 1
        if is_correct:
            diff_scores[dt]["correct"] += 1

        results.append({
            "question_id":    q.question_id,
            "question":       q.question,
            "user_answer":    user_ans,
            "correct_answer": q.correct_answer,
            "is_correct":     is_correct,
            "explanation":    q.explanation,
        })

    pct = round((correct_count / total) * 100) if total > 0 else 0

    if pct >= 90:   grade = "A+"
    elif pct >= 80: grade = "A"
    elif pct >= 70: grade = "B"
    elif pct >= 60: grade = "C"
    elif pct >= 40: grade = "D"
    else:           grade = "F"

    skill_breakdown = {
        sk: round((v["correct"] / v["total"]) * 100)
        for sk, v in skill_scores.items() if v["total"] > 0
    }
    diff_breakdown = {
        dt: round((v["correct"] / v["total"]) * 100)
        for dt, v in diff_scores.items() if v["total"] > 0
    }
    weak_areas = [sk for sk, p in skill_breakdown.items() if p < 50]

    if pct >= 80:
        feedback = "Excellent work! You have a strong understanding of this article."
    elif pct >= 60:
        feedback = "Good effort! Review the topics you missed and you'll improve quickly."
    else:
        feedback = "Keep practicing! Re-read the article and focus on your weak areas."

    improvement_tips = [
        f"Focus on improving your {wa} skill — try re-reading the relevant sections."
        for wa in weak_areas
    ]

    return {
        "score":            correct_count,
        "total":            total,
        "percentage":       pct,
        "grade":            grade,
        "skill_breakdown":  skill_breakdown,
        "diff_breakdown":   diff_breakdown,
        "weak_areas":       weak_areas,
        "feedback":         feedback,
        "improvement_tips": improvement_tips,
        "detailed_results": results,
    }


def generate_mock_test_from_short_content(
    title: str,
    summary: str,
    num_questions: int = 10,
):
    """Expands short content with Groq and generates a test in one step."""
    from app.services.news_service import _expand_with_groq  # late import avoids circular
    full_content = _expand_with_groq(title, summary)
    test = generate_mock_test(full_content, title, num_questions=num_questions)
    return full_content, test