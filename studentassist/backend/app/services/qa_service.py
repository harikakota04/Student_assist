"""
QA Knowledge Base Service
─────────────────────────
search_qa      : fuzzy-search the database for a matching question
save_qa        : save a new Q&A pair (called after every AI answer)
bulk_import_qa : import from list of {question, answer, subject, topic}
list_qa        : paginated list for admin UI
delete_qa      : remove an entry
update_qa      : edit question or answer
mark_helpful   : increment helpful_count
"""

import re
import difflib
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import QAEntry


# ══════════════════════════════════════════════════════════════════════════════
# FUZZY SEARCH
# ══════════════════════════════════════════════════════════════════════════════

MATCH_THRESHOLD = 0.55   # 0–1; lower = more lenient


def _normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio between two normalised strings."""
    return difflib.SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


def _keyword_overlap(query: str, question: str) -> float:
    """Fraction of query words found in the stored question."""
    q_words = set(_normalise(query).split())
    d_words = set(_normalise(question).split())
    if not q_words:
        return 0.0
    # Remove very common stop words
    stops = {"what","is","the","a","an","how","why","when","where","which",
             "does","do","can","are","to","of","for","in","on","at","and","or"}
    q_words -= stops
    if not q_words:
        return 0.0
    hits = q_words & d_words
    return len(hits) / len(q_words)


def search_qa(
    query: str,
    db: Session,
    subject: Optional[str] = None,
    top_k: int = 1,
) -> Optional[Dict]:
    """
    Search the database for a question matching `query`.
    Returns the best match dict if score >= MATCH_THRESHOLD, else None.

    Scoring = 0.6 × sequence_similarity + 0.4 × keyword_overlap
    """
    if not query.strip():
        return None

    # Pull candidates — optionally filter by subject first
    q = db.query(QAEntry)
    if subject:
        q = q.filter(QAEntry.subject == subject)
    entries = q.all()

    if not entries:
        return None

    best_score = 0.0
    best_entry = None

    for entry in entries:
        seq  = _similarity(query, entry.question)
        kw   = _keyword_overlap(query, entry.question)
        score = 0.6 * seq + 0.4 * kw

        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score >= MATCH_THRESHOLD and best_entry:
        return {
            "id":          best_entry.id,
            "question":    best_entry.question,
            "answer":      best_entry.answer,
            "subject":     best_entry.subject,
            "topic":       best_entry.topic,
            "source":      best_entry.source,
            "score":       round(best_score, 3),
            "from_cache":  True,
        }
    return None


def search_qa_multi(
    query: str,
    db: Session,
    top_k: int = 3,
) -> List[Dict]:
    """Return top-k matches above threshold (for UI browsing)."""
    entries = db.query(QAEntry).all()
    scored  = []

    for entry in entries:
        seq   = _similarity(query, entry.question)
        kw    = _keyword_overlap(query, entry.question)
        score = 0.6 * seq + 0.4 * kw
        if score >= MATCH_THRESHOLD:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [
        {
            "id":       e.id,
            "question": e.question,
            "answer":   e.answer,
            "subject":  e.subject,
            "topic":    e.topic,
            "source":   e.source,
            "score":    round(s, 3),
        }
        for s, e in scored[:top_k]
    ]


# ══════════════════════════════════════════════════════════════════════════════
# SAVE / AUTO-SAVE
# ══════════════════════════════════════════════════════════════════════════════

def save_qa(
    question:  str,
    answer:    str,
    db:        Session,
    subject:   str = "General",
    topic:     str = "General",
    source:    str = "ai",         # "ai" | "manual" | "import"
    asked_by:  Optional[int] = None,
) -> QAEntry:
    """
    Save a Q&A pair. Checks for near-duplicate first —
    if a very similar question already exists (score ≥ 0.85),
    updates its answer instead of inserting a duplicate.
    """
    # Near-duplicate check (tighter threshold)
    entries = db.query(QAEntry).all()
    for entry in entries:
        if _similarity(question, entry.question) >= 0.85:
            # Update existing answer if AI produced a better/newer one
            if source == "ai":
                entry.answer     = answer
                entry.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(entry)
            return entry

    new_entry = QAEntry(
        question  = question.strip(),
        answer    = answer.strip(),
        subject   = subject,
        topic     = topic,
        source    = source,
        asked_by  = asked_by,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def bulk_import_qa(
    entries:  List[Dict],
    db:       Session,
    source:   str = "import",
) -> Dict:
    """
    Import a list of {question, answer, subject?, topic?} dicts.
    Skips near-duplicates. Returns import summary.
    """
    added   = 0
    skipped = 0

    for item in entries:
        q = item.get("question", "").strip()
        a = item.get("answer",   "").strip()
        if not q or not a:
            skipped += 1
            continue

        # Check for near-duplicate
        existing = db.query(QAEntry).all()
        is_dup = any(_similarity(q, e.question) >= 0.85 for e in existing)
        if is_dup:
            skipped += 1
            continue

        db.add(QAEntry(
            question = q,
            answer   = a,
            subject  = item.get("subject", "General"),
            topic    = item.get("topic",   "General"),
            source   = source,
        ))
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped, "total": len(entries)}


# ══════════════════════════════════════════════════════════════════════════════
# CRUD FOR ADMIN
# ══════════════════════════════════════════════════════════════════════════════

def list_qa(
    db:      Session,
    subject: Optional[str] = None,
    search:  Optional[str] = None,
    skip:    int = 0,
    limit:   int = 50,
) -> Dict:
    q = db.query(QAEntry)
    if subject and subject != "All":
        q = q.filter(QAEntry.subject == subject)
    if search:
        q = q.filter(or_(
            QAEntry.question.contains(search),
            QAEntry.answer.contains(search),
        ))
    total = q.count()
    items = q.order_by(QAEntry.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id":            e.id,
                "question":      e.question,
                "answer":        e.answer,
                "subject":       e.subject,
                "topic":         e.topic,
                "source":        e.source,
                "helpful_count": e.helpful_count,
                "created_at":    e.created_at.strftime("%d %b %Y"),
            }
            for e in items
        ],
    }


def delete_qa(entry_id: int, db: Session) -> bool:
    entry = db.query(QAEntry).filter(QAEntry.id == entry_id).first()
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def update_qa(
    entry_id: int,
    question: Optional[str],
    answer:   Optional[str],
    subject:  Optional[str],
    topic:    Optional[str],
    db:       Session,
) -> Optional[Dict]:
    entry = db.query(QAEntry).filter(QAEntry.id == entry_id).first()
    if not entry:
        return None
    if question: entry.question = question.strip()
    if answer:   entry.answer   = answer.strip()
    if subject:  entry.subject  = subject
    if topic:    entry.topic    = topic
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "question": entry.question, "answer": entry.answer}


def mark_helpful(entry_id: int, db: Session) -> bool:
    entry = db.query(QAEntry).filter(QAEntry.id == entry_id).first()
    if not entry:
        return False
    entry.helpful_count += 1
    db.commit()
    return True


def get_stats(db: Session) -> Dict:
    total   = db.query(func.count(QAEntry.id)).scalar()
    ai      = db.query(func.count(QAEntry.id)).filter(QAEntry.source == "ai").scalar()
    manual  = db.query(func.count(QAEntry.id)).filter(QAEntry.source == "manual").scalar()
    imp     = db.query(func.count(QAEntry.id)).filter(QAEntry.source == "import").scalar()
    subjects= db.query(QAEntry.subject, func.count(QAEntry.id)).group_by(QAEntry.subject).all()
    return {
        "total":    total,
        "ai":       ai,
        "manual":   manual,
        "imported": imp,
        "by_subject": {s: c for s, c in subjects},
    }
