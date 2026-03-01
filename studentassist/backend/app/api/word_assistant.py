import asyncio
from fastapi import APIRouter, HTTPException
from app.models.schemas import WordDoubtRequest, WordDoubtResponse
from app.services.word_assistant_service import explain_word

router = APIRouter()

@router.post("/word-assist", response_model=WordDoubtResponse)
async def word_assist(request: WordDoubtRequest):
    try:
        loop = asyncio.get_event_loop()
        # Handle optional context
        ctx = request.sentence_context if request.sentence_context else ""
        result = await loop.run_in_executor(None, lambda: explain_word(request.word, ctx))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant Error: {str(e)}")