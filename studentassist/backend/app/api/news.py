import asyncio
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.models.schemas import NewsResponse
from app.services.news_service import fetch_articles, expand_article_with_groq
from app.services.mock_test_service import generate_mock_test_from_short_content

router = APIRouter()

@router.get("/news", response_model=NewsResponse)
async def get_news(category: str = "editorial", max_articles: int = 8):
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fetch_articles(category, max_articles))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/article/expand-and-test")
async def expand_and_test(title: str, summary: str):
    try:
        loop = asyncio.get_event_loop()
        content, test = await loop.run_in_executor(
            None, lambda: generate_mock_test_from_short_content(title, summary)
        )
        return {"content": content, "test": test.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))