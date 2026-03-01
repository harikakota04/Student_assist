from fastapi import APIRouter, HTTPException
from app.syllabus import get_syllabus
from app.models.new_schemas import SyllabusResponse

router = APIRouter()


@router.get("/syllabus/{exam_target}", response_model=SyllabusResponse)
def get_exam_syllabus(exam_target: str):
    """
    Returns the full section → topics syllabus for CAT, IPMAT or CLAT.
    Use this to populate subject/topic dropdowns in your frontend.
    """
    exam = exam_target.upper()
    if exam not in ("CAT", "IPMAT", "CLAT"):
        raise HTTPException(status_code=400, detail="exam_target must be CAT, IPMAT or CLAT")
    return SyllabusResponse(exam_target=exam, sections=get_syllabus(exam))
