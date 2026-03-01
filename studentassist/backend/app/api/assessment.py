from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.assessment_service import generate_assessment, evaluate_assessment
from app.models.new_schemas import AssessmentTest, AssessmentSubmission, AssessmentResultResponse

router = APIRouter()


@router.get("/assessment/{exam_target}", response_model=AssessmentTest)
def get_assessment(exam_target: str):
    """
    Generate a placement assessment.
    exam_target: CAT, IPMAT or CLAT
    Returns 15 basic questions (5 per section) covering that exam's syllabus.
    """
    try:
        exam = exam_target.upper()
        if exam not in ("CAT", "IPMAT", "CLAT"):
            raise HTTPException(status_code=400, detail="exam_target must be CAT, IPMAT or CLAT")
        return generate_assessment(exam)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assessment/submit", response_model=AssessmentResultResponse)
def submit_assessment(
    submission: AssessmentSubmission,
    db: Session = Depends(get_db),
):
    """
    Submit placement assessment answers.
    - Scores each section and topic
    - Identifies weak topics (< 50%) and strong topics (>= 70%)
    - Saves results to SQLite
    - Marks student as assessed
    """
    try:
        return evaluate_assessment(submission, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
