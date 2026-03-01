"""
Prep Tracker Service
- Monthly assessment gating (30-day cooldown)
- Weekly study log CRUD
- Prep schedule: generate template + save + update
"""

import json
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import Student, AssessmentResult, WeeklyLog, PrepSchedule
from app.syllabus import CAT_SYLLABUS, IPMAT_SYLLABUS, CLAT_SYLLABUS


# ══════════════════════════════════════════════════════════════════════════════
# MONTHLY ASSESSMENT GATING
# ══════════════════════════════════════════════════════════════════════════════

def get_assessment_status(student_id: int, db: Session) -> dict:
    """
    Returns:
      can_take     : bool   — True if no attempt or last attempt > 30 days ago
      days_remaining: int  — 0 if can_take, else days left
      last_attempt : str   — ISO date string or None
      attempt_number: int  — which attempt this would be (1-indexed)
      history      : list  — all past attempts [{attempt_number, percentage, grade, taken_at}]
    """
    attempts = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.student_id == student_id)
        .order_by(AssessmentResult.taken_at.desc())
        .all()
    )

    if not attempts:
        return {
            "can_take": True,
            "days_remaining": 0,
            "last_attempt": None,
            "attempt_number": 1,
            "history": [],
        }

    latest = attempts[0]
    last_dt = latest.taken_at
    now = datetime.utcnow()
    delta = now - last_dt
    days_since = delta.days
    cooldown = 30

    can_take = days_since >= cooldown
    days_remaining = max(0, cooldown - days_since)

    history = [
        {
            "attempt_number": a.attempt_number,
            "percentage": a.percentage,
            "difficulty_level": a.difficulty_level,
            "grade": _grade(a.percentage),
            "taken_at": a.taken_at.strftime("%d %b %Y"),
            "section_scores": a.section_scores or {},
        }
        for a in reversed(attempts)
    ]

    return {
        "can_take": can_take,
        "days_remaining": days_remaining,
        "last_attempt": last_dt.strftime("%d %b %Y"),
        "attempt_number": len(attempts) + 1,
        "history": history,
    }


def _grade(pct: float) -> str:
    if pct >= 80: return "A"
    if pct >= 60: return "B"
    if pct >= 40: return "C"
    return "D"


# ══════════════════════════════════════════════════════════════════════════════
# WEEKLY STUDY LOG
# ══════════════════════════════════════════════════════════════════════════════

def _monday(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())

def _week_label(monday: date) -> str:
    return f"Week of {monday.day} {monday.strftime('%b %Y')}"


def get_week_start(for_date: Optional[date] = None) -> str:
    d = for_date or date.today()
    return _monday(d).strftime("%Y-%m-%d")


def get_weekly_log(student_id: int, week_start: str, db: Session) -> Optional[WeeklyLog]:
    return db.query(WeeklyLog).filter(
        WeeklyLog.student_id == student_id,
        WeeklyLog.week_start == week_start,
    ).first()


def get_all_weekly_logs(student_id: int, db: Session) -> List[WeeklyLog]:
    return (
        db.query(WeeklyLog)
        .filter(WeeklyLog.student_id == student_id)
        .order_by(WeeklyLog.week_start.desc())
        .all()
    )


def save_weekly_log(
    student_id: int,
    exam_target: str,
    week_start: str,
    topics_covered: List[Dict],
    summary_notes: str,
    db: Session,
) -> WeeklyLog:
    # Calculate total hours
    total_hours = sum(float(t.get("hours", 0)) for t in topics_covered)

    # Parse monday
    monday = datetime.strptime(week_start, "%Y-%m-%d").date()
    label = _week_label(monday)

    existing = get_weekly_log(student_id, week_start, db)
    if existing:
        existing.topics_covered = topics_covered
        existing.total_hours    = total_hours
        existing.summary_notes  = summary_notes
        existing.week_label     = label
        existing.updated_at     = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        log = WeeklyLog(
            student_id     = student_id,
            exam_target    = exam_target,
            week_start     = week_start,
            week_label     = label,
            topics_covered = topics_covered,
            total_hours    = total_hours,
            summary_notes  = summary_notes,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log


def get_tracker_summary(student_id: int, db: Session) -> dict:
    """Aggregate stats across all weekly logs."""
    logs = get_all_weekly_logs(student_id, db)
    if not logs:
        return {
            "total_weeks_logged": 0,
            "total_hours": 0.0,
            "total_topics_covered": 0,
            "avg_hours_per_week": 0.0,
            "topic_frequency": {},
            "confidence_by_topic": {},
            "logs": [],
        }

    all_topics = []
    for log in logs:
        all_topics.extend(log.topics_covered or [])

    topic_freq: Dict[str, int] = {}
    conf_map: Dict[str, List[float]] = {}
    for t in all_topics:
        name = t.get("topic", "Unknown")
        topic_freq[name] = topic_freq.get(name, 0) + 1
        conf = float(t.get("confidence", 3))
        conf_map.setdefault(name, []).append(conf)

    avg_conf = {t: round(sum(v)/len(v), 1) for t, v in conf_map.items()}
    total_hours = sum(log.total_hours or 0 for log in logs)

    return {
        "total_weeks_logged": len(logs),
        "total_hours": round(total_hours, 1),
        "total_topics_covered": len(all_topics),
        "avg_hours_per_week": round(total_hours / len(logs), 1) if logs else 0,
        "topic_frequency": dict(sorted(topic_freq.items(), key=lambda x: -x[1])[:10]),
        "confidence_by_topic": avg_conf,
        "logs": [
            {
                "week_start": log.week_start,
                "week_label": log.week_label,
                "total_hours": log.total_hours,
                "topics_count": len(log.topics_covered or []),
                "summary_notes": log.summary_notes,
                "topics": log.topics_covered or [],
            }
            for log in logs
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# PREP SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════

# Templates: ordered list of (subject_short, topic) per week
CAT_TEMPLATE_6M = [
    # Month 1 — Arithmetic foundation
    {"focus": "Arithmetic", "topics": [("QA","Percentages"),("QA","Profit and Loss")]},
    {"focus": "Arithmetic", "topics": [("QA","Ratio and Proportion"),("QA","Averages and Mixtures")]},
    {"focus": "Arithmetic", "topics": [("QA","Time, Speed and Distance"),("QA","Time and Work")]},
    {"focus": "Arithmetic + Number System", "topics": [("QA","Simple and Compound Interest"),("QA","Number System")]},
    # Month 2 — Algebra + VARC intro
    {"focus": "Algebra", "topics": [("QA","Linear Equations"),("QA","Quadratic Equations")]},
    {"focus": "Algebra", "topics": [("QA","Progressions (AP, GP)"),("QA","Inequalities")]},
    {"focus": "VARC", "topics": [("VARC","Reading Comprehension"),("VARC","Para Jumbles")]},
    {"focus": "VARC", "topics": [("VARC","Para Summary"),("VARC","Sentence Correction")]},
    # Month 3 — Geometry + DILR intro
    {"focus": "Geometry", "topics": [("QA","Lines and Angles"),("QA","Triangles")]},
    {"focus": "Geometry + Mensuration", "topics": [("QA","Circles"),("QA","Mensuration: Area and Volume")]},
    {"focus": "DILR", "topics": [("DILR","Bar Charts"),("DILR","Tables and Caselets")]},
    {"focus": "DILR", "topics": [("DILR","Arrangements (Linear & Circular)"),("DILR","Puzzles")]},
    # Month 4 — Modern Math + VARC deep
    {"focus": "Modern Math", "topics": [("QA","Permutation and Combination"),("QA","Probability")]},
    {"focus": "Modern Math", "topics": [("QA","Set Theory"),("QA","Functions and Graphs")]},
    {"focus": "VARC", "topics": [("VARC","Critical Reasoning"),("VARC","Vocabulary in Context")]},
    {"focus": "DILR", "topics": [("DILR","Venn Diagrams"),("DILR","Syllogisms")]},
    # Month 5 — Mixed practice + revision
    {"focus": "QA Revision", "topics": [("QA","HCF and LCM"),("QA","Coordinate Geometry")]},
    {"focus": "QA + DILR", "topics": [("QA","Trigonometry"),("DILR","Blood Relations")]},
    {"focus": "VARC + DILR", "topics": [("VARC","Odd Sentence Out"),("DILR","Binary Logic")]},
    {"focus": "Full Revision", "topics": [("QA","Arithmetic revision"),("VARC","RC revision")]},
    # Month 6 — Mock tests + weak area polish
    {"focus": "Mock + Analysis", "topics": [("ALL","Full mock test"),("ALL","Error analysis")]},
    {"focus": "Weak Areas", "topics": [("ALL","Weak topic 1"),("ALL","Weak topic 2")]},
    {"focus": "Mock + Analysis", "topics": [("ALL","Full mock test"),("ALL","Section test")]},
    {"focus": "Final Revision", "topics": [("ALL","Formula revision"),("ALL","Speed drills")]},
]

CAT_TEMPLATE_3M = CAT_TEMPLATE_6M[12:]   # last 12 weeks of 6M plan
CAT_TEMPLATE_9M = (
    [{"focus": "Foundation", "topics": [("QA","Basic Arithmetic"),("QA","HCF and LCM")]}]*4 +
    CAT_TEMPLATE_6M
)

IPMAT_TEMPLATE_6M = [
    {"focus": "QA Arithmetic", "topics": [("QA","Percentages"),("QA","Profit and Loss")]},
    {"focus": "QA Arithmetic", "topics": [("QA","Ratio and Proportion"),("QA","Time, Speed and Distance")]},
    {"focus": "QA Algebra",    "topics": [("QA","Linear Equations"),("QA","Quadratic Equations")]},
    {"focus": "QA Algebra",    "topics": [("QA","Progressions (AP, GP)"),("QA","Logarithms")]},
    {"focus": "VA Grammar",    "topics": [("VA","Grammar and Error Correction"),("VA","Sentence Completion")]},
    {"focus": "VA Vocabulary", "topics": [("VA","Synonyms and Antonyms"),("VA","Idioms and Phrases")]},
    {"focus": "LR Basics",     "topics": [("LR","Coding and Decoding"),("LR","Series Completion")]},
    {"focus": "LR Puzzles",    "topics": [("LR","Blood Relations"),("LR","Directions and Distances")]},
    {"focus": "QA Geometry",   "topics": [("QA","Geometry: Lines, Angles, Triangles"),("QA","Mensuration: Area and Volume")]},
    {"focus": "QA Modern",     "topics": [("QA","Permutation and Combination"),("QA","Probability")]},
    {"focus": "VA RC",         "topics": [("VA","Reading Comprehension"),("VA","Para Jumbles")]},
    {"focus": "LR Advanced",   "topics": [("LR","Puzzles and Arrangements"),("LR","Syllogisms")]},
    {"focus": "QA Revision",   "topics": [("QA","Set Theory and Venn Diagrams"),("QA","Matrices and Determinants (Basic)")]},
    {"focus": "VA + LR Mix",   "topics": [("VA","Critical Reasoning"),("LR","Statement and Assumptions")]},
    {"focus": "Mock Tests",    "topics": [("ALL","Full mock test"),("ALL","Error analysis")]},
    {"focus": "Weak Areas",    "topics": [("ALL","Weak topic 1"),("ALL","Weak topic 2")]},
    {"focus": "Mock + Drill",  "topics": [("ALL","Timed section test"),("ALL","Speed practice")]},
    {"focus": "Final Prep",    "topics": [("ALL","Formula cards"),("ALL","Last revision")]},
]

TEMPLATES = {
    "CAT":   {"3": CAT_TEMPLATE_3M, "6": CAT_TEMPLATE_6M, "9": CAT_TEMPLATE_9M},
    "IPMAT": {"3": IPMAT_TEMPLATE_6M[:12], "6": IPMAT_TEMPLATE_6M, "9": IPMAT_TEMPLATE_6M*2},
    "CLAT":  {},  # CLAT uses dynamic syllabus-based generation above
}


def _build_weeks(
    exam: str,
    plan_months: int,
    start_date: date,
) -> List[Dict]:
    """Generate week-by-week entries based on exam.

    CAT and IPMAT use hardcoded templates; CLAT builds a simple cycling
    plan from the syllabus since its structure differs significantly.
    """
    n_weeks = plan_months * 4

    # custom CLAT handling: flatten syllabus topics into a rotating list
    if exam == "CLAT":
        from app.syllabus import CLAT_SYLLABUS
        flat = []
        for subj, tlist in CLAT_SYLLABUS.items():
            for t in tlist:
                flat.append((subj, t))
        weeks = []
        for i in range(n_weeks):
            w_start = start_date + timedelta(weeks=i)
            subj, top = flat[i % len(flat)]
            weeks.append({
                "week_number": i + 1,
                "week_start":  w_start.strftime("%Y-%m-%d"),
                "week_label":  f"Week {i+1}  ({w_start.day} {w_start.strftime('%b')})",
                "focus":       subj,
                "topics":      [{"subject": subj, "topic": top}],
                "notes":       "",
                "completed":   False,
            })
        return weeks

    # fallback to templated plan for CAT/IPMAT
    template_key = str(min(plan_months, 9))
    template = TEMPLATES.get(exam, TEMPLATES["CAT"]).get(template_key, CAT_TEMPLATE_6M)

    weeks = []
    for i in range(n_weeks):
        w_start = start_date + timedelta(weeks=i)
        tmpl = template[i % len(template)]
        weeks.append({
            "week_number": i + 1,
            "week_start":  w_start.strftime("%Y-%m-%d"),
            "week_label":  f"Week {i+1}  ({w_start.day} {w_start.strftime('%b')})",
            "focus":       tmpl["focus"],
            "topics":      [{"subject": s, "topic": t} for s, t in tmpl["topics"]],
            "notes":       "",
            "completed":   False,
        })
    return weeks


def get_schedule(student_id: int, db: Session) -> Optional[PrepSchedule]:
    return db.query(PrepSchedule).filter(
        PrepSchedule.student_id == student_id
    ).first()


def create_schedule(
    student_id: int,
    exam_target: str,
    plan_months: int,
    start_date_str: str,
    exam_date_str: str,
    db: Session,
) -> PrepSchedule:
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    weeks = _build_weeks(exam_target, plan_months, start)

    # Delete existing
    old = get_schedule(student_id, db)
    if old:
        db.delete(old)
        db.commit()

    sched = PrepSchedule(
        student_id  = student_id,
        exam_target = exam_target,
        plan_months = plan_months,
        start_date  = start_date_str,
        exam_date   = exam_date_str,
        weeks       = weeks,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


def update_week(
    student_id: int,
    week_number: int,
    focus: str,
    topics: List[Dict],
    notes: str,
    completed: bool,
    db: Session,
) -> PrepSchedule:
    sched = get_schedule(student_id, db)
    if not sched:
        raise ValueError("No schedule found. Create one first.")

    weeks = list(sched.weeks)
    for w in weeks:
        if w["week_number"] == week_number:
            w["focus"]     = focus
            w["topics"]    = topics
            w["notes"]     = notes
            w["completed"] = completed
            break

    sched.weeks      = weeks
    sched.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sched)
    return sched