from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import get_dashboard
from app.models.new_schemas import StudentDashboard

router = APIRouter()


@router.get("/dashboard/{student_id}", response_model=StudentDashboard)
def student_dashboard(student_id: int, db: Session = Depends(get_db)):
    """
    Full personalized dashboard for a student. Returns:
    - Assessment results (weak/strong topics, section scores)
    - Recent mock test history (last 10)
    - Per-topic progress (attempts, avg, best, last score)
    - Adaptive learning path (personalized from actual performance)
    - Overall stats
    """
    try:
        return get_dashboard(student_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
