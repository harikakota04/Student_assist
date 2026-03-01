from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import query, learning_path, news, word_assistant, mock_test
from app.api.auth           import router as auth_router
from app.api.assessment     import router as assessment_router
from app.api.dashboard      import router as dashboard_router
from app.api.exam_mock_test import router as exam_mock_test_router
from app.api.syllabus_route import router as syllabus_router
from app.api.flashcards     import router as flashcards_router
from app.api.tracker        import router as tracker_router
from app.api.qa             import router as qa_router
from app.database import init_db

app = FastAPI(title="StudentAssist API", version="2.2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Health check endpoint (no auth needed)
@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "message": "StudentAssist Backend is running"}

@app.on_event("startup")
def startup():
    init_db()
    print("[DB] Tables ready.")

app.include_router(query.router,          prefix="/api/v1", tags=["NLP"])
app.include_router(learning_path.router,  prefix="/api/v1", tags=["Learning Path"])
app.include_router(news.router,           prefix="/api/v1", tags=["News"])
app.include_router(word_assistant.router, prefix="/api/v1", tags=["Word"])
app.include_router(mock_test.router,      prefix="/api/v1", tags=["Article Test"])
app.include_router(auth_router,           prefix="/api/v1", tags=["Auth"])
app.include_router(assessment_router,     prefix="/api/v1", tags=["Assessment"])
app.include_router(dashboard_router,      prefix="/api/v1", tags=["Dashboard"])
app.include_router(exam_mock_test_router, prefix="/api/v1", tags=["Mock Tests"])
app.include_router(syllabus_router,       prefix="/api/v1", tags=["Syllabus"])
app.include_router(flashcards_router,     prefix="/api/v1", tags=["Flashcards"])
app.include_router(tracker_router,        prefix="/api/v1", tags=["Tracker"])
app.include_router(qa_router,             prefix="/api/v1", tags=["Q&A Knowledge Base"])

@app.get("/")
def root():
    return {"message": "StudentAssist API v2.2"}