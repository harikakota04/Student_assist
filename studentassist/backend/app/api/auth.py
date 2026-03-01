from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.student_service import register_student, login_student
from app.models.new_schemas import StudentRegister, StudentLogin, AuthResponse

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
def register(data: StudentRegister, db: Session = Depends(get_db)):
    """Register a new student. Returns profile + prompts for assessment."""
    try:
        return register_student(data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(data: StudentLogin, db: Session = Depends(get_db)):
    """Login. Returns student profile. If assessment not taken, message prompts it."""
    try:
        return login_student(data, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
