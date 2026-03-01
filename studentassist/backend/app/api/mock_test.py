import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import MockTestRequest, MockTestResponse, TestSubmission
from app.services.mock_test_service import generate_mock_test, evaluate_test

router = APIRouter()


@router.post("/mock-test/generate", response_model=MockTestResponse)
async def create_mock_test(request: MockTestRequest):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: generate_mock_test(
                article_content=request.article_content,
                article_title=request.article_title,
                difficulty=request.difficulty,
                num_questions=request.num_questions,
            )
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mock-test/evaluate")
async def evaluate_mock_test(submission: TestSubmission):
    """
    Returns a plain dict with: score, total, percentage, grade,
    skill_breakdown, diff_breakdown, weak_areas, feedback,
    improvement_tips, detailed_results.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: evaluate_test(submission)
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))