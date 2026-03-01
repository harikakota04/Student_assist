"""
Learning Path Service
- Groq Call 1: intent-aware topic explanation (Explanation / Example / Doubt Clarification / Revision)
- Groq Call 2: structured JSON learning path
- YouTube Data API v3: real video resources
"""

import re
import json
import httpx
from typing import List
from groq import Groq

from app.models.schemas import (
    LearningPath, LearningPathRequest, LearningResource, DifficultyLevel
)
from app.core.config import settings

DIFFICULTY_MAP = {
    "beginner":     DifficultyLevel.BEGINNER,
    "intermediate": DifficultyLevel.INTERMEDIATE,
    "advanced":     DifficultyLevel.ADVANCED,
}


class LearningPathService:

    def _client(self) -> Groq:
        return Groq(api_key=settings.groq_api_key)

    # ── Call 1: intent-aware explanation ──────────────────────────────────────

    def _explanation(self, topic: str, difficulty: str, intent: str) -> str:
        intent_prompts = {
            "Explanation": (
                f'In exactly 3 sentences, explain "{topic}" to a {difficulty} level student.\n'
                f'Sentence 1: What is {topic}?\n'
                f'Sentence 2: Why does it matter or how is it used?\n'
                f'Sentence 3: Give one concrete real-world example or interesting fact.'
            ),
            "Example": (
                f'Give a clear, concrete example of "{topic}" for a {difficulty} level student.\n'
                f'Sentence 1: Briefly state what {topic} is in one line.\n'
                f'Sentence 2: Walk through a specific, real-world example step by step.\n'
                f'Sentence 3: Explain what the example demonstrates about {topic}.'
            ),
            "Doubt Clarification": (
                f'A {difficulty} level student is confused about "{topic}". Clear their doubt.\n'
                f'Sentence 1: Identify the most common misconception or confusion about {topic}.\n'
                f'Sentence 2: Clarify the correct understanding in simple terms.\n'
                f'Sentence 3: Give a simple analogy or contrast to make it stick.'
            ),
            "Revision": (
                f'Summarize "{topic}" for a {difficulty} level student who is revising.\n'
                f'Sentence 1: The core definition or concept in one crisp sentence.\n'
                f'Sentence 2: The 2-3 most important points to remember.\n'
                f'Sentence 3: One likely exam or interview question and its short answer.'
            ),
        }
        chosen = intent_prompts.get(intent, intent_prompts["Explanation"])
        prompt = (
            f'You are a teacher.\n{chosen}\n'
            f'Write ONLY the 3 sentences. No bullet points, no headers, no JSON, no intro text.'
        )
        resp = self._client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.5,
        )
        return resp.choices[0].message.content.strip()

    # ── Call 2: learning path JSON ────────────────────────────────────────────

    def _path(self, topic: str, intent: str, difficulty: str, previous: list) -> dict:
        prior = f"Already studied: {', '.join(previous)}." if previous else ""
        prompt = (
            f'Create a personalized study plan for the topic: "{topic}"\n'
            f'Student intent: {intent}\n'
            f'Student level: {difficulty}\n'
            f'{prior}\n\n'
            f'IMPORTANT: All steps, prerequisites, and next_topics must be SPECIFIC to "{topic}".\n'
            f'Do NOT give generic steps. Tailor everything to this exact topic and intent.\n\n'
            f'Return ONLY the following JSON, nothing before or after it:\n'
            f'{{"recommended_path":['
            f'"Step 1: <specific action for {topic}>","Step 2: <specific action>","Step 3: <specific action>",'
            f'"Step 4: <specific action>","Step 5: <specific action>"],'
            f'"prerequisites":["<actual prereq for {topic}>","<another prereq>","<another prereq>"],'
            f'"next_topics":["<logical next topic after {topic}>","<another next topic>","<another>"],'
            f'"estimated_completion":"<realistic time>",'
            f'"personalized_tip":"<specific actionable advice for {intent} intent on {topic} at {difficulty} level>"}}'
        )
        resp = self._client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        return json.loads(raw)

    # ── YouTube ───────────────────────────────────────────────────────────────

    def _youtube(self, topic: str, difficulty: str) -> List[LearningResource]:
        if not settings.youtube_api_key:
            return []
        suffix = {
            "Beginner":     "explained for beginners",
            "Intermediate": "tutorial",
            "Advanced":     "advanced in depth",
        }.get(difficulty, "explained")
        try:
            r = httpx.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": f"{topic} {suffix}",
                    "type": "video",
                    "maxResults": 3,
                    "order": "relevance",
                    "videoDuration": "medium",
                    "key": settings.youtube_api_key,
                },
                timeout=10,
            )
            r.raise_for_status()
            out = []
            for item in r.json().get("items", []):
                vid  = item["id"]["videoId"]
                snip = item["snippet"]
                desc = snip.get("description", "")[:120] + "..."
                out.append(LearningResource(
                    title=snip.get("title", ""),
                    type="video",
                    url=f"https://www.youtube.com/watch?v={vid}",
                    difficulty=DIFFICULTY_MAP.get(difficulty.lower(), DifficultyLevel.INTERMEDIATE),
                    estimated_time="10-20 min",
                    description=f"{desc} — {snip.get('channelTitle', '')}",
                ))
            return out
        except Exception as e:
            print(f"[YouTube ERROR] {e}")
            return []

    # ── Main ──────────────────────────────────────────────────────────────────

    def generate_learning_path(self, request: LearningPathRequest) -> LearningPath:
        topic      = request.topic
        difficulty = request.difficulty_level.value
        intent     = request.intent.value
        previous   = request.previous_topics or []

        # Intent-aware explanation
        try:
            explanation = self._explanation(topic, difficulty, intent)
            print(f"[Explanation] intent={intent} | {explanation[:80]}")
        except Exception as e:
            print(f"[Explanation ERROR] {e}")
            explanation = ""

        # Learning path
        try:
            path = self._path(topic, intent, difficulty, previous)
            print(f"[Path] steps={len(path.get('recommended_path', []))}")
            steps       = path.get("recommended_path", [])
            prereqs     = path.get("prerequisites", [])[:4]
            next_topics = path.get("next_topics", [])[:3]
            est_time    = path.get("estimated_completion", "2-4 hours")
            tip         = path.get("personalized_tip", "")
        except Exception as e:
            print(f"[Path ERROR] {e}")
            steps       = []
            prereqs     = []
            next_topics = []
            est_time    = "2-4 hours"
            tip         = ""

        # YouTube
        resources = self._youtube(topic, difficulty)

        return LearningPath(
            topic=topic,
            topic_explanation=explanation,
            recommended_path=steps,
            resources=resources,
            prerequisites=prereqs,
            next_topics=next_topics,
            estimated_completion=est_time,
            personalized_tip=tip,
        )