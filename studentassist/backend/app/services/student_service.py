"""
Student Auth Service
- register: create new student, hash password
- login: verify credentials, return student profile
- get_student: fetch by ID
"""

import hashlib
import secrets
from sqlalchemy.orm import Session
from app.database import Student
from app.models.new_schemas import StudentRegister, StudentLogin, StudentProfile, AuthResponse


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash with a salt. Use bcrypt in production."""
    salt = "studentassist_salt_2025"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def register_student(data: StudentRegister, db: Session) -> AuthResponse:
    existing = db.query(Student).filter(Student.email == data.email).first()
    if existing:
        raise ValueError("Email already registered.")

    student = Student(
        name=data.name,
        email=data.email,
        password_hash=_hash_password(data.password),
        exam_target=data.exam_target.value,
        has_taken_assessment=False,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return AuthResponse(
        student=StudentProfile.from_orm(student),
        message=f"Welcome {student.name}! Please take your placement assessment to get started.",
    )


def login_student(data: StudentLogin, db: Session) -> AuthResponse:
    student = db.query(Student).filter(Student.email == data.email).first()
    if not student:
        raise ValueError("Invalid email or password.")
    if student.password_hash != _hash_password(data.password):
        raise ValueError("Invalid email or password.")

    msg = "Welcome back!"
    if not student.has_taken_assessment:
        msg = "Welcome! You haven't taken your placement assessment yet. Please complete it to unlock your personalized dashboard."

    return AuthResponse(
        student=StudentProfile.from_orm(student),
        message=msg,
    )


def get_student_by_id(student_id: int, db: Session) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student {student_id} not found.")
    return student


def update_exam_target(student_id: int, exam_target: str, db: Session) -> Student:
    student = get_student_by_id(student_id, db)
    student.exam_target = exam_target.upper()
    db.commit()
    db.refresh(student)
    return student
