from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.flashcard_service import get_flashcard_topics, generate_flashcards

router = APIRouter()


class FlashcardRequest(BaseModel):
    topic: str
    subject: str
    num_cards: int = 6


@router.get("/flashcards/topics")
def flashcard_topics():
    """
    Returns the full subject → category → topic tree.
    Used by the frontend to build the sidebar selector.
    """
    return {"topics": get_flashcard_topics()}


@router.post("/flashcards/generate")
def flashcard_generate(request: FlashcardRequest):
    """
    Generates AI flashcards for a given topic.
    RC topics automatically get passage-based cards.
    """
    try:
        cards = generate_flashcards(
            topic=request.topic,
            subject=request.subject,
            num_cards=request.num_cards,
        )
        if not cards:
            raise HTTPException(status_code=500, detail="Card generation failed — no cards returned.")
        return {"topic": request.topic, "subject": request.subject, "cards": cards}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))