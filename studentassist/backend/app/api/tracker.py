"""
Routes for:
- GET  /assessment-status/{student_id}   — monthly cooldown check
- GET  /weekly-log/{student_id}/{week}   — fetch one week's log
- GET  /weekly-logs/{student_id}         — all logs + summary
- POST /weekly-log                       — save/update a week log
- GET  /schedule/{student_id}            — get prep schedule
- POST /schedule                         — create schedule from template
- PUT  /schedule/week                    — update one week
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.database import get_db
from app.services.prep_tracker_service import (
    get_assessment_status, get_weekly_log, get_all_weekly_logs,
    save_weekly_log, get_tracker_summary,
    get_schedule, create_schedule, update_week,
)

router = APIRouter()


# ── Assessment status ─────────────────────────────────────────────────────────

@router.get("/assessment-status/{student_id}")
def assessment_status(student_id: int, db: Session = Depends(get_db)):
    return get_assessment_status(student_id, db)


# ── Weekly log ────────────────────────────────────────────────────────────────

class WeeklyLogPayload(BaseModel):
    student_id:     int
    exam_target:    str
    week_start:     str          # "YYYY-MM-DD"
    topics_covered: List[Dict]   # [{topic,subject,hours,confidence,notes}]
    summary_notes:  str = ""

@router.get("/weekly-logs/{student_id}")
def all_weekly_logs(student_id: int, db: Session = Depends(get_db)):
    return get_tracker_summary(student_id, db)

@router.get("/weekly-log/{student_id}/{week_start}")
def one_weekly_log(student_id: int, week_start: str, db: Session = Depends(get_db)):
    log = get_weekly_log(student_id, week_start, db)
    if not log:
        return {"exists": False, "topics_covered": [], "summary_notes": "", "total_hours": 0}
    return {
        "exists":         True,
        "week_start":     log.week_start,
        "week_label":     log.week_label,
        "topics_covered": log.topics_covered,
        "summary_notes":  log.summary_notes,
        "total_hours":    log.total_hours,
    }

@router.post("/weekly-log")
def save_log(payload: WeeklyLogPayload, db: Session = Depends(get_db)):
    log = save_weekly_log(
        student_id     = payload.student_id,
        exam_target    = payload.exam_target,
        week_start     = payload.week_start,
        topics_covered = payload.topics_covered,
        summary_notes  = payload.summary_notes,
        db             = db,
    )
    return {"saved": True, "week_start": log.week_start, "total_hours": log.total_hours}


# ── Prep schedule ─────────────────────────────────────────────────────────────

class ScheduleCreate(BaseModel):
    student_id:   int
    exam_target:  str
    plan_months:  int    # 3 / 6 / 9
    start_date:   str    # "YYYY-MM-DD"
    exam_date:    str = ""

class WeekUpdate(BaseModel):
    student_id:  int
    week_number: int
    focus:       str
    topics:      List[Dict]
    notes:       str = ""
    completed:   bool = False

@router.get("/schedule/{student_id}")
def fetch_schedule(student_id: int, db: Session = Depends(get_db)):
    sched = get_schedule(student_id, db)
    if not sched:
        return {"exists": False}
    return {
        "exists":      True,
        "exam_target": sched.exam_target,
        "plan_months": sched.plan_months,
        "start_date":  sched.start_date,
        "exam_date":   sched.exam_date,
        "weeks":       sched.weeks,
    }

@router.post("/schedule")
def create_sched(payload: ScheduleCreate, db: Session = Depends(get_db)):
    sched = create_schedule(
        student_id    = payload.student_id,
        exam_target   = payload.exam_target,
        plan_months   = payload.plan_months,
        start_date_str= payload.start_date,
        exam_date_str = payload.exam_date,
        db            = db,
    )
    return {"created": True, "weeks": sched.weeks, "plan_months": sched.plan_months}

@router.put("/schedule/week")
def update_sched_week(payload: WeekUpdate, db: Session = Depends(get_db)):
    try:
        sched = update_week(
            student_id  = payload.student_id,
            week_number = payload.week_number,
            focus       = payload.focus,
            topics      = payload.topics,
            notes       = payload.notes,
            completed   = payload.completed,
            db          = db,
        )
        return {"updated": True, "week_number": payload.week_number}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
