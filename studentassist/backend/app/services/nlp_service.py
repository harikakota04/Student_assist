"""
NLP Service - Sentence Transformers + Groq LLaMA3
Analyzes any student query to extract intent, topic, difficulty, keywords, explanation.
No singleton - fresh instance per request to avoid stale state.
"""

import re
import json
from typing import Tuple, Dict
from sentence_transformers import SentenceTransformer
from groq import Groq

from app.models.schemas import QueryAnalysis, IntentType, DifficultyLevel
from app.core.config import settings

INTENT_PATTERNS = {
    IntentType.EXPLANATION: [
        r"\bexplain\b", r"\bwhat is\b", r"\bwhat are\b", r"\bhow does\b",
        r"\bdefine\b", r"\bi don.t understand\b", r"\btell me about\b",
        r"\bdescribe\b",
    ],
    IntentType.EXAMPLE: [
        r"\bexample\b", r"\bshow me\b", r"\bdemonstrate\b",
        r"\buse case\b", r"\billustrate\b", r"\bgive me\b",
    ],
    IntentType.DOUBT_CLARIFICATION: [
        r"\bwhy\b", r"\bconfused\b", r"\bdifference between\b",
        r"\bvs\b", r"\bversus\b", r"\bwhen to use\b", r"\bclarify\b", r"\bdoubt\b",
    ],
    IntentType.REVISION: [
        r"\brevise\b", r"\bsummary\b", r"\bsummarize\b", r"\brecap\b",
        r"\bkey points\b", r"\bremind me\b", r"\brefresh\b", r"\bmain points\b",
    ],
}

DIFFICULTY_INDICATORS = {
    DifficultyLevel.BEGINNER: [
        r"\bbasic\b", r"\bbeginner\b", r"\bintroduction\b", r"\bsimple\b",
        r"\bnew to\b", r"\bjust started\b",
    ],
    DifficultyLevel.ADVANCED: [
        r"\badvanced\b", r"\bin depth\b", r"\bdeep dive\b", r"\bcomplex\b",
        r"\bunder the hood\b", r"\barchitecture\b",
    ],
}


class NLPService:
    def __init__(self):
        self.embedder = SentenceTransformer(settings.model_name)
        self.groq = Groq(api_key=settings.groq_api_key)

    def _classify_intent(self, query: str) -> Tuple[IntentType, float]:
        q = query.lower()
        scores: Dict[IntentType, int] = {i: 0 for i in IntentType}
        for intent, patterns in INTENT_PATTERNS.items():
            for p in patterns:
                if re.search(p, q):
                    scores[intent] += 1
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        if scores[best] == 0:
            return IntentType.EXPLANATION, 0.5
        return best, scores[best] / total

    def _classify_difficulty(self, query: str) -> Tuple[DifficultyLevel, float]:
        q = query.lower()
        for level, patterns in DIFFICULTY_INDICATORS.items():
            for p in patterns:
                if re.search(p, q):
                    return level, 0.8
        wc = len(query.split())
        if wc <= 6:
            return DifficultyLevel.BEGINNER, 0.6
        elif wc <= 15:
            return DifficultyLevel.INTERMEDIATE, 0.6
        return DifficultyLevel.ADVANCED, 0.6

    def _groq_analyze(self, query: str, intent: str, difficulty: str) -> dict:
        prompt = (
            f'A student asked: "{query}"\n'
            f'Initial classification - Intent: {intent}, Difficulty: {difficulty}\n\n'
            f'Return ONLY a JSON object, nothing else:\n'
            f'{{"intent":"<Explanation|Example|Doubt Clarification|Revision>",'
            f'"topic":"<the specific subject being asked about>",'
            f'"difficulty_level":"<Beginner|Intermediate|Advanced>",'
            f'"keywords":["word1","word2","word3","word4"],'
            f'"explanation":"<one sentence: what does this student need?>"}}'
        )
        resp = self.groq.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        return json.loads(raw)

    def analyze_query(self, query: str) -> QueryAnalysis:
        intent, ic = self._classify_intent(query)
        difficulty, dc = self._classify_difficulty(query)

        try:
            refined = self._groq_analyze(query, intent.value, difficulty.value)
            intent_map = {i.value.lower(): i for i in IntentType}
            diff_map   = {d.value.lower(): d for d in DifficultyLevel}
            f_intent = intent_map.get(refined.get("intent", "").lower(), intent)
            f_diff   = diff_map.get(refined.get("difficulty_level", "").lower(), difficulty)
            f_topic  = refined.get("topic", query[:60])
            keywords = refined.get("keywords", [])
            expl     = refined.get("explanation", "")
            print(f"[NLP] topic={f_topic} intent={f_intent} diff={f_diff}")
        except Exception as e:
            print(f"[NLP Groq ERROR] {e}")
            f_intent = intent
            f_diff   = difficulty
            f_topic  = query[:60]
            keywords = [w for w in query.split() if len(w) > 3][:5]
            expl     = f"The student needs help with: {query[:80]}"

        return QueryAnalysis(
            intent=f_intent,
            topic=f_topic,
            difficulty_level=f_diff,
            confidence=round((ic + dc) / 2, 2),
            explanation=expl,
            keywords=keywords,
        )