from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.exam_mock_test_service import generate_exam_mock_test, evaluate_exam_mock_test
from app.models.new_schemas import (
    ExamMockTestRequest, ExamMockTestResponse,
    ExamTestSubmission, ExamTestResult,
)

router = APIRouter()


@router.post("/exam-mock-test/generate", response_model=ExamMockTestResponse)
def generate_test(request: ExamMockTestRequest):
    """
    Generate a mock test for any CAT, IPMAT or CLAT subject/topic.

    Example body:
    {
        "student_id": 1,
        "exam_target": "CAT",
        "subject": "Quantitative Aptitude (QA)",
        "topic": "Probability",
        "difficulty": "Intermediate",
        "num_questions": 10
    }
    """
    try:
        return generate_exam_mock_test(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exam-mock-test/evaluate", response_model=ExamTestResult)
def evaluate_test(
    submission: ExamTestSubmission,
    db: Session = Depends(get_db),
):
    """
    Evaluate a submitted mock test.
    - Scores and grades the attempt
    - Saves to DB (mock_test_results + student_progress)
    - Returns next recommended topic based on adaptive logic
    """
    try:
        return evaluate_exam_mock_test(submission, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
