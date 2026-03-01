from fastapi import APIRouter, HTTPException
from app.models.schemas import LearningPathRequest, LearningPath
from app.services.learning_path_service import LearningPathService

router = APIRouter()


@router.post("/learning-path", response_model=LearningPath)
async def get_learning_path(request: LearningPathRequest):
    try:
        service = LearningPathService()
        return service.generate_learning_path(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))