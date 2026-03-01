from fastapi import APIRouter, HTTPException
from app.models.schemas import StudentQuery, QueryAnalysis, FullAnalysisResponse, LearningPathRequest
from app.services.nlp_service import NLPService
from app.services.learning_path_service import LearningPathService

router = APIRouter()


@router.post("/analyze-query", response_model=QueryAnalysis)
async def analyze_query(student_query: StudentQuery):
    try:
        service = NLPService()
        return service.analyze_query(student_query.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-analysis", response_model=FullAnalysisResponse)
async def full_analysis(student_query: StudentQuery):
    try:
        # Step 1: analyze query
        nlp = NLPService()
        query_analysis = nlp.analyze_query(student_query.query)
        print(f"[Query] topic={query_analysis.topic} intent={query_analysis.intent} diff={query_analysis.difficulty_level}")

        # Step 2: build learning path request from real analysis
        lp_request = LearningPathRequest(
            topic=query_analysis.topic,
            difficulty_level=query_analysis.difficulty_level,
            intent=query_analysis.intent,
            student_id=student_query.student_id,
            previous_topics=student_query.previous_topics or [],
        )

        # Step 3: generate learning path
        lp_service = LearningPathService()
        learning_path = lp_service.generate_learning_path(lp_request)
        print(f"[Path] explanation={learning_path.topic_explanation[:60] if learning_path.topic_explanation else 'EMPTY'}")

        return FullAnalysisResponse(
            query_analysis=query_analysis,
            learning_path=learning_path,
        )
    except Exception as e:
        import traceback
        print(f"[ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))