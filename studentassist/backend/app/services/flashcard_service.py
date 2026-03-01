# pyright: reportMissingImports=false
"""
Flashcard Service
- get_flashcard_topics: returns the full CAT/IPMAT/CLAT topic tree for the UI
- generate_flashcards: uses Groq to create front/back concept cards for any topic
"""

import re
import json
from typing import Any

# groq import may not be resolvable in some static checks or test environments
try:
    from groq import Groq
except ImportError:  # type: ignore
    Groq = None

from app.core.config import settings

# ─── Topic Tree (drives the sidebar in the Flashcards tab) ───────────────────

FLASHCARD_TOPICS = {
    "Quantitative Ability": {
        "Arithmetic": [
            "Percentages", "Profit and Loss", "Simple and Compound Interest",
            "Ratio and Proportion", "Averages and Mixtures", "Time, Speed and Distance",
            "Time and Work",
        ],
        "Algebra": [
            "Linear Equations", "Quadratic Equations", "Inequalities",
            "Progressions (AP, GP)", "Functions and Graphs", "Logarithms",
        ],
        "Geometry & Mensuration": [
            "Lines and Angles", "Triangles", "Circles",
            "Quadrilaterals", "Mensuration: Area and Volume", "Coordinate Geometry",
        ],
        "Number System": [
            "Number System", "HCF and LCM", "Divisibility Rules",
            "Remainders", "Surds and Indices",
        ],
        "Modern Math": [
            "Permutation and Combination", "Probability",
            "Set Theory", "Trigonometry",
        ],
    },
    "Logical Reasoning": {
        "Deductive Reasoning": [
            "Syllogisms", "Statement and Assumptions",
            "Statement and Conclusions", "Cause and Effect",
        ],
        "Puzzles & Arrangements": [
            "Linear Arrangements", "Circular Arrangements",
            "Puzzles", "Blood Relations", "Directions and Distances",
        ],
        "Data Sufficiency & Coding": [
            "Data Sufficiency", "Coding and Decoding",
            "Series Completion", "Analogies",
        ],
        "Critical Reasoning": [
            "Strengthen / Weaken Arguments", "Assumption-based Questions",
            "Paradox Resolution", "Binary Logic",
        ],
    },
    "Verbal Ability": {
        "Reading Comprehension": [
            "Main Idea", "Author's Tone", "Inference Questions",
            "Specific Detail", "Vocabulary in Context",
        ],
        "Grammar": [
            "Sentence Correction", "Fill in the Blanks",
            "Subject-Verb Agreement", "Tenses", "Prepositions",
        ],
        "Vocabulary": [
            "Synonyms and Antonyms", "Idioms and Phrases",
            "Word Usage in Context", "One Word Substitution",
        ],
        "Verbal Logic": [
            "Para Jumbles", "Para Summary", "Odd Sentence Out",
            "Para Completion", "Critical Reasoning (Verbal)",
        ],
    },
    "Data Interpretation": {
        "Charts & Graphs": [
            "Bar Charts", "Line Graphs", "Pie Charts", "Stacked Bar Charts",
        ],
        "Tables & Caselets": [
            "Simple Tables", "Complex Tables", "Caselets",
        ],
        "Mixed DI": [
            "Venn Diagrams", "Network / Route Diagrams", "Games and Tournaments",
        ],
    },
    "General Knowledge (IPMAT)": {
        "Economy & Finance": [
            "Indian Economy Basics", "Banking and Finance", "Stock Markets",
        ],
        "Current Affairs": [
            "National Current Affairs", "International Events", "Awards and Honours",
        ],
        "Static GK": [
            "Indian Constitution", "Geography", "Sports",
        ],
    },
    "English Language (CLAT)": {
        "Reading Comprehension": [
            "Main Idea", "Author's Tone", "Inference and Implications",
            "Specific Detail Questions", "Vocabulary in Context",
        ],
        "Vocabulary & Grammar": [
            "Synonyms and Antonyms", "Fill in the Blanks",
            "Grammar and Error Correction", "Sentence Completion",
            "Idioms and Phrases", "Prepositions", "Tenses",
        ],
        "Para Jumbles": [
            "Sentence Arrangement", "Paragraph Organization",
            "Logical Flow", "Connectives",
        ],
    },
    "Current Affairs & GK (CLAT)": {
        "Indian Polity & Constitution": [
            "Constitutional Articles", "Fundamental Rights",
            "Directive Principles", "Election Commission", "Parliament",
        ],
        "History & Culture": [
            "Indian History", "World History", "Cultural Heritage",
            "Independence Movement", "Ancient India",
        ],
        "Geography": [
            "Physical Geography", "Political Geography",
            "Indian Geography", "Climate and Weather",
        ],
        "Current Events": [
            "National News", "International Affairs",
            "Awards and Honours", "Sports and Games",
        ],
        "Economics & Finance": [
            "Indian Economy", "Banking Fundamentals",
            "Monetary Policy", "GST and Taxation",
        ],
    },
    "Logical Reasoning (CLAT)": {
        "Deductive Reasoning": [
            "Syllogisms", "Statement and Assumptions",
            "Statement and Conclusions", "Logical Sequences",
        ],
        "Analytical Reasoning": [
            "Puzzles", "Arrangements", "Blood Relations",
            "Directions", "Coding and Decoding",
        ],
        "Argument Analysis": [
            "Strong and Weak Arguments", "Strengthen Arguments",
            "Weaken Arguments", "Course of Action",
        ],
    },
    "Legal Reasoning (CLAT)": {
        "Constitutional Law": [
            "Articles and Amendments", "Rights and Duties",
            "Federal Structure", "Judicial Review",
        ],
        "Criminal Law": [
            "IPC Sections", "General Principles",
            "Specific Offences", "Punishment and Liability",
        ],
        "Civil Law": [
            "Contract Law", "Tort Law", "Property Law",
            "Family Law", "Commercial Transactions",
        ],
        "Statutory Interpretation": [
            "Reading Statutes", "Interpretation Rules",
            "Case-based Scenarios", "Legal Principles",
        ],
    },
    "Quantitative Techniques (CLAT)": {
        "Arithmetic": [
            "Percentages", "Profit and Loss", "Simple and Compound Interest",
            "Ratio and Proportion", "Averages", "Mixtures",
        ],
        "Algebra": [
            "Linear Equations", "Quadratic Equations",
            "Progressions", "Set Theory",
        ],
        "Geometry & Mensuration": [
            "Basic Geometry", "Triangles and Circles",
            "Area and Volume", "Coordinate Geometry",
        ],
        "Data Analysis": [
            "Basic Statistics", "Data Interpretation",
            "Probability", "Permutation and Combination",
        ],
    },
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _client() -> Any:
    if Groq is None:
        raise ImportError("groq library is required for flashcard generation")
    return Groq(api_key=settings.groq_api_key, timeout=60.0)


# ─── RC-specific card generator ──────────────────────────────────────────────

def _generate_rc_cards(topic: str, subject: str, num_cards: int) -> list:
    """
    For Reading Comprehension sub-topics, generate cards that include a
    mini-passage on the front so the student practises with real text.
    """
    prompt = (
        f'You are a CAT/IPMAT/CLAT verbal ability tutor creating flashcards for "{topic}" '
        f'under "{subject}".\n\n'
        f'Generate exactly {num_cards} flashcards.\n'
        f'Each card must:\n'
        f'- FRONT: A short 80-100 word passage followed by ONE question about it.\n'
        f'  Format the front as: [PASSAGE] <passage text> [/PASSAGE]\\n\\n<question>\n'
        f'- BACK: The correct answer with a 1-sentence explanation.\n'
        f'- EXAMPLE: A second shorter passage example or a sentence demonstrating the concept.\n'
        f'- TIP: One exam strategy tip for this question type in CAT/IPMAT/CLAT.\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"cards": ['
        f'{{"front": "[PASSAGE] ...passage... [/PASSAGE]\\n\\n...question...", '
        f'"back": "...answer + explanation...", '
        f'"example": "...short example...", '
        f'"tip": "...exam tip..."}}'
        f']}}'
    )
    return _call_groq(prompt, num_cards)


# ─── Standard card generator ─────────────────────────────────────────────────

def _generate_standard_cards(topic: str, subject: str, num_cards: int) -> list:
    prompt = (
        f'You are a CAT/IPMAT/CLAT tutor creating concise flashcards for the topic "{topic}" '
        f'under the subject "{subject}".\n\n'
        f'Generate exactly {num_cards} flashcards covering key concepts, formulas, and tricks.\n\n'
        f'Each card:\n'
        f'- FRONT: A clear concept question or "What is X?" or "Formula for X?" '
        f'or a short problem to solve.\n'
        f'- BACK: The answer — a crisp definition, formula, or solution with working.\n'
        f'- EXAMPLE: A concrete numerical or real-world example demonstrating the concept.\n'
        f'- TIP: One exam shortcut or memory trick for CAT/IPMAT/CLAT.\n\n'
        f'Return ONLY this JSON:\n'
        f'{{"cards": ['
        f'{{"front": "...", "back": "...", "example": "...", "tip": "..."}}'
        f']}}'
    )
    return _call_groq(prompt, num_cards)


def _call_groq(prompt: str, num_cards: int) -> list:
    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        data = json.loads(raw)
        return data.get("cards", [])
    except Exception as e:
        print(f"[Flashcard Groq ERROR] {e}")
        return []


# ─── Public API ──────────────────────────────────────────────────────────────

RC_SUBTOPICS = {
    "Main Idea", "Author's Tone", "Inference Questions",
    "Specific Detail", "Vocabulary in Context",
    "Reading Comprehension",
}

def get_flashcard_topics() -> dict:
    return FLASHCARD_TOPICS


def generate_flashcards(topic: str, subject: str, num_cards: int = 6) -> list:
    """Route to the right generator based on topic type."""
    if topic in RC_SUBTOPICS or "comprehension" in topic.lower():
        cards = _generate_rc_cards(topic, subject, num_cards)
    else:
        cards = _generate_standard_cards(topic, subject, num_cards)

    # Sanitise — ensure all fields present
    clean = []
    for c in cards:
        clean.append({
            "front":   c.get("front", ""),
            "back":    c.get("back", ""),
            "example": c.get("example", ""),
            "tip":     c.get("tip", ""),
        })
    return clean