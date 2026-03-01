"""
QA Knowledge Base Routes
GET    /qa/search?q=...&subject=...     — fuzzy search
POST   /qa/ask                          — ask a question (check DB → AI fallback → auto-save)
POST   /qa/save                         — manually save a Q&A pair
POST   /qa/import                       — bulk import list of Q&A
GET    /qa/list                         — paginated list (admin)
PUT    /qa/{id}                         — edit entry
DELETE /qa/{id}                         — delete entry
POST   /qa/{id}/helpful                 — mark as helpful
GET    /qa/stats                        — summary stats
"""

import json
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.qa_service import (
    search_qa, search_qa_multi, save_qa, bulk_import_qa,
    list_qa, delete_qa, update_qa, mark_helpful, get_stats,
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AskPayload(BaseModel):
    question:   str
    student_id: Optional[int] = None
    subject:    Optional[str] = None
    topic:      Optional[str] = None
    # If AI already produced an answer, pass it here to save
    ai_answer:  Optional[str] = None

class SavePayload(BaseModel):
    question:   str
    answer:     str
    subject:    str = "General"
    topic:      str = "General"
    source:     str = "manual"
    student_id: Optional[int] = None

class UpdatePayload(BaseModel):
    question: Optional[str] = None
    answer:   Optional[str] = None
    subject:  Optional[str] = None
    topic:    Optional[str] = None

class BulkItem(BaseModel):
    question: str
    answer:   str
    subject:  str = "General"
    topic:    str = "General"

class BulkPayload(BaseModel):
    entries: List[BulkItem]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/qa/search")
def qa_search(
    q:       str,
    subject: Optional[str] = None,
    top_k:   int = 3,
    db: Session = Depends(get_db),
):
    """Fuzzy search — returns top matches above threshold."""
    results = search_qa_multi(q, db, top_k=top_k)
    return {"query": q, "results": results, "count": len(results)}


@router.post("/qa/ask")
def qa_ask(payload: AskPayload, db: Session = Depends(get_db)):
    """
    Main entry point for the Ask AI tab.
    1. Search DB — if match found, return it (from_cache=True)
    2. If ai_answer is provided (from client after calling Groq), save it and return
    3. If no match and no ai_answer, return from_cache=False so client calls AI
    """
    match = search_qa(payload.question, db, subject=payload.subject)

    if match:
        return {
            "from_cache":  True,
            "answer":      match["answer"],
            "question":    match["question"],
            "subject":     match["subject"],
            "topic":       match["topic"],
            "match_score": match["score"],
            "entry_id":    match["id"],
        }

    # No cache hit — if client sent an AI answer, save it
    if payload.ai_answer and payload.ai_answer.strip():
        entry = save_qa(
            question  = payload.question,
            answer    = payload.ai_answer,
            db        = db,
            subject   = payload.subject or "General",
            topic     = payload.topic   or "General",
            source    = "ai",
            asked_by  = payload.student_id,
        )
        return {
            "from_cache": False,
            "saved":      True,
            "entry_id":   entry.id,
            "answer":     payload.ai_answer,
        }

    return {"from_cache": False, "saved": False}


@router.post("/qa/save")
def qa_save(payload: SavePayload, db: Session = Depends(get_db)):
    entry = save_qa(
        question  = payload.question,
        answer    = payload.answer,
        db        = db,
        subject   = payload.subject,
        topic     = payload.topic,
        source    = payload.source,
        asked_by  = payload.student_id,
    )
    return {"saved": True, "id": entry.id}


@router.post("/qa/import")
def qa_import(payload: BulkPayload, db: Session = Depends(get_db)):
    result = bulk_import_qa(
        [i.dict() for i in payload.entries], db, source="import"
    )
    return result


@router.post("/qa/import-csv")
async def qa_import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV with columns: question, answer, subject (opt), topic (opt)
    """
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    entries = []
    for row in reader:
        q = row.get("question", row.get("Question", "")).strip()
        a = row.get("answer",   row.get("Answer",   "")).strip()
        s = row.get("subject",  row.get("Subject",  "General")).strip()
        t = row.get("topic",    row.get("Topic",    "General")).strip()
        if q and a:
            entries.append({"question": q, "answer": a, "subject": s, "topic": t})

    result = bulk_import_qa(entries, db, source="import")
    return result


@router.post("/qa/import-json")
async def qa_import_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a JSON file: [{question, answer, subject?, topic?}] or
    {data: [{...}]} or {"qa": [{...}]}
    """
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Handle various wrappers
    if isinstance(data, dict):
        data = data.get("data", data.get("qa", data.get("questions", [])))
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON must be a list of Q&A objects")

    entries = []
    for item in data:
        q = item.get("question", item.get("q", "")).strip()
        a = item.get("answer",   item.get("a", "")).strip()
        s = item.get("subject",  "General")
        t = item.get("topic",    "General")
        if q and a:
            entries.append({"question": q, "answer": a, "subject": s, "topic": t})

    result = bulk_import_qa(entries, db, source="import")
    return result


@router.get("/qa/list")
def qa_list(
    subject: Optional[str] = None,
    search:  Optional[str] = None,
    skip:    int = 0,
    limit:   int = 50,
    db: Session = Depends(get_db),
):
    return list_qa(db, subject=subject, search=search, skip=skip, limit=limit)


@router.get("/qa/stats")
def qa_stats(db: Session = Depends(get_db)):
    return get_stats(db)


@router.put("/qa/{entry_id}")
def qa_update(entry_id: int, payload: UpdatePayload, db: Session = Depends(get_db)):
    result = update_qa(entry_id, payload.question, payload.answer, payload.subject, payload.topic, db)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return result


@router.delete("/qa/{entry_id}")
def qa_delete(entry_id: int, db: Session = Depends(get_db)):
    ok = delete_qa(entry_id, db)
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"deleted": True, "id": entry_id}


@router.post("/qa/{entry_id}/helpful")
def qa_helpful(entry_id: int, db: Session = Depends(get_db)):
    ok = mark_helpful(entry_id, db)
    if not ok:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"marked": True}
