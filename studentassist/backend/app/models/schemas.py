from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    EXPLANATION        = "Explanation"
    EXAMPLE            = "Example"
    DOUBT_CLARIFICATION = "Doubt Clarification"
    REVISION           = "Revision"


class DifficultyLevel(str, Enum):
    BEGINNER     = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED     = "Advanced"


# ── Query / NLP ───────────────────────────────────────────────────────────────

class StudentQuery(BaseModel):
    query: str
    student_id: Optional[str] = None
    previous_topics: Optional[List[str]] = []


class QueryAnalysis(BaseModel):
    intent: IntentType
    topic: str
    difficulty_level: DifficultyLevel
    confidence: float
    explanation: str
    keywords: List[str] = []


# ── Learning Path ─────────────────────────────────────────────────────────────

class LearningPathRequest(BaseModel):
    topic: str
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    intent: IntentType = IntentType.EXPLANATION
    student_id: Optional[str] = None
    previous_topics: Optional[List[str]] = []


class LearningResource(BaseModel):
    title: str
    type: str
    url: str
    difficulty: DifficultyLevel
    estimated_time: str
    description: str = ""


class LearningPath(BaseModel):
    topic: str
    topic_explanation: str = ""
    recommended_path: List[str] = []
    resources: List[LearningResource] = []
    prerequisites: List[str] = []
    next_topics: List[str] = []
    estimated_completion: str = ""
    personalized_tip: str = ""


class FullAnalysisResponse(BaseModel):
    query_analysis: QueryAnalysis
    learning_path: LearningPath


# ── News ──────────────────────────────────────────────────────────────────────

class ArticleSummary(BaseModel):
    title: str
    summary: str
    url: str = ""
    source: str = ""
    published_at: str = ""
    category: str = ""


class NewsResponse(BaseModel):
    articles: List[ArticleSummary]
    total: int


# ── Word Assistant ────────────────────────────────────────────────────────────

class WordDoubtRequest(BaseModel):
    word: str
    sentence_context: Optional[str] = None


class WordDoubtResponse(BaseModel):
    word: str
    word_type: str
    meaning: str
    simple_explanation: str
    example_sentences: List[str] = []
    synonyms: List[str] = []
    antonyms: List[str] = []
    origin: str = ""


# ── Mock Test ─────────────────────────────────────────────────────────────────

class QuestionOption(BaseModel):
    option_id: str    # "A", "B", "C", "D"
    text: str


class Question(BaseModel):
    question_id: str                  # frontend uses q["question_id"]
    question: str
    options: List[QuestionOption]     # frontend expects list of {option_id, text}
    correct_answer: str               # "A", "B", "C", or "D"
    explanation: str
    difficulty_tag: str = "Medium"   # "Easy" | "Medium" | "Hard"
    skill_tested: str = "comprehension"


class MockTestRequest(BaseModel):
    article_content: str
    article_title: str
    difficulty: str = "Intermediate"
    num_questions: int = 10


class MockTestResponse(BaseModel):
    title: str
    difficulty: str
    questions: List[Question]
    total_questions: int
    estimated_time: str = "10-15 min"
    skills_covered: List[str] = []


class TestSubmission(BaseModel):
    questions: List[Question]
    user_answers: Dict[str, str]   # {question_id: selected_option e.g. "A"}


class TestResult(BaseModel):
    total_questions: int
    correct_answers: int
    score: float
    grade: str
    detailed_results: List[Dict[str, Any]]