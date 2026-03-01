"""
Syllabus definitions for CAT, IPMAT, and CLAT.
Used by assessment and mock test services to scope questions correctly.
"""

from typing import Dict, List

# ─── CAT Syllabus ─────────────────────────────────────────────────────────────

CAT_SYLLABUS: Dict[str, List[str]] = {
    "Verbal Ability and Reading Comprehension (VARC)": [
        "Reading Comprehension",
        "Para Jumbles",
        "Para Summary",
        "Sentence Correction",
        "Odd Sentence Out",
        "Fill in the Blanks",
        "Critical Reasoning",
        "Vocabulary in Context",
    ],
    "Data Interpretation and Logical Reasoning (DILR)": [
        "Bar Charts",
        "Line Graphs",
        "Pie Charts",
        "Tables and Caselets",
        "Arrangements (Linear & Circular)",
        "Puzzles",
        "Blood Relations",
        "Directions and Distances",
        "Syllogisms",
        "Binary Logic",
        "Venn Diagrams",
    ],
    "Quantitative Aptitude (QA)": [
        "Number System",
        "HCF and LCM",
        "Percentages",
        "Profit and Loss",
        "Simple and Compound Interest",
        "Ratio and Proportion",
        "Time, Speed and Distance",
        "Time and Work",
        "Averages and Mixtures",
        "Algebra and Equations",
        "Quadratic Equations",
        "Progressions (AP, GP)",
        "Geometry and Mensuration",
        "Coordinate Geometry",
        "Trigonometry",
        "Permutation and Combination",
        "Probability",
        "Set Theory",
        "Functions and Graphs",
        "Inequalities",
    ],
}

# ─── IPMAT Syllabus ───────────────────────────────────────────────────────────

IPMAT_SYLLABUS: Dict[str, List[str]] = {
    "Quantitative Ability (QA)": [
        "Number System",
        "HCF and LCM",
        "Percentages",
        "Profit and Loss",
        "Simple and Compound Interest",
        "Ratio, Proportion and Variation",
        "Time, Speed and Distance",
        "Time and Work",
        "Averages and Weighted Averages",
        "Mixtures and Alligations",
        "Algebra: Linear and Quadratic Equations",
        "Progressions (AP, GP, HP)",
        "Geometry: Lines, Angles, Triangles",
        "Mensuration: Area and Volume",
        "Permutation and Combination",
        "Probability",
        "Set Theory and Venn Diagrams",
        "Logarithms and Surds",
        "Matrices and Determinants (Basic)",
        "Functions",
    ],
    "Verbal Ability (VA)": [
        "Reading Comprehension",
        "Grammar and Error Correction",
        "Sentence Completion",
        "Vocabulary: Synonyms and Antonyms",
        "Idioms and Phrases",
        "Para Jumbles",
        "Para Completion",
        "Fill in the Blanks",
        "Analogies",
        "Critical Reasoning",
    ],
    "Logical Reasoning (LR)": [
        "Coding and Decoding",
        "Series Completion",
        "Analogies",
        "Blood Relations",
        "Directions and Distances",
        "Puzzles and Arrangements",
        "Syllogisms",
        "Statement and Assumptions",
        "Statement and Conclusions",
        "Cause and Effect",
        "Data Sufficiency",
    ],
}

# ─── CLAT Syllabus ────────────────────────────────────────────────────────────

CLAT_SYLLABUS: Dict[str, List[str]] = {
    "English Language": [
        "Reading Comprehension",
        "Grammar and Error Correction",
        "Sentence Completion",
        "Fill in the Blanks",
        "Vocabulary: Synonyms and Antonyms",
        "Synonyms",
        "Antonyms",
        "Odd Sentence Out",
        "Para Jumbles",
        "Analogies",
        "Phrase Meaning",
        "Connected Passage",
    ],
    "Current Affairs and General Knowledge": [
        "Indian Constitution and Polity",
        "International Relations",
        "Indian History",
        "World History",
        "Geography (Physical and Political)",
        "Economics and Finance",
        "Science and Technology",
        "Social Issues and Ethics",
        "Sports",
        "Awards and Recognition",
        "Environment and Sustainability",
        "Current Political Events",
    ],
    "Logical Reasoning": [
        "Coding and Decoding",
        "Series Completion",
        "Analogies",
        "Blood Relations",
        "Directions and Distances",
        "Syllogisms",
        "Statement and Assumptions",
        "Statement and Conclusions",
        "Strong and Weak Arguments",
        "Cause and Effect",
        "Data Sufficiency",
        "Circular Arrangements",
        "Linear Arrangements",
    ],
    "Legal Reasoning": [
        "Constitutional Law",
        "Criminal Law",
        "Tort Law",
        "Contract Law",
        "Property Law",
        "Family Law",
        "Administrative Law",
        "International Law",
        "Statutory Interpretation",
        "Case-based Scenarios",
        "Legal Principles and Applications",
        "Right to Information",
    ],
    "Quantitative Techniques": [
        "Number System",
        "Percentages",
        "Profit and Loss",
        "Simple and Compound Interest",
        "Ratio and Proportion",
        "Time, Speed and Distance",
        "Time and Work",
        "Averages",
        "Mixtures and Alligations",
        "Algebra: Linear Equations",
        "Geometry: Basic Concepts",
        "Mensuration",
        "Basic Statistics",
        "Data Interpretation",
    ],
}

# ─── Assessment Config ────────────────────────────────────────────────────────

ASSESSMENT_CONFIG = {
    "CAT": {
        "sections": list(CAT_SYLLABUS.keys()),
        "questions_per_section": 5,   # 15 total — keeps it quick
        "time_limit_minutes": 30,
        "description": "CAT Placement Assessment — covers VARC, DILR, and QA basics",
    },
    "IPMAT": {
        "sections": list(IPMAT_SYLLABUS.keys()),
        "questions_per_section": 5,   # 15 total
        "time_limit_minutes": 30,
        "description": "IPMAT Placement Assessment — covers QA, VA, and LR basics",
    },
    "CLAT": {
        "sections": list(CLAT_SYLLABUS.keys()),
        "questions_per_section": 3,   # 15 total
        "time_limit_minutes": 30,
        "description": "CLAT Placement Assessment — covers English, GK, LR, Legal Reasoning, and QT",
    },
}

# ─── Mock Test Config ─────────────────────────────────────────────────────────

MOCK_TEST_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]

def get_syllabus(exam: str) -> Dict[str, List[str]]:
    exam_upper = exam.upper().strip()
    if exam_upper == "CAT":
        return CAT_SYLLABUS
    elif exam_upper == "IPMAT":
        return IPMAT_SYLLABUS
    elif exam_upper == "CLAT":
        return CLAT_SYLLABUS
    else:
        return CAT_SYLLABUS  # Default to CAT

def get_all_topics(exam: str) -> List[str]:
    syllabus = get_syllabus(exam)
    return [topic for topics in syllabus.values() for topic in topics]

def get_section_for_topic(exam: str, topic: str) -> str:
    for section, topics in get_syllabus(exam).items():
        if topic in topics:
            return section
    return "General"

def get_difficulty_from_score(score: float) -> str:
    if score < 40:
        return "Beginner"
    elif score < 70:
        return "Intermediate"
    return "Advanced"

def get_exam_list() -> List[str]:
    """Return list of available exams."""
    return ["CAT", "IPMAT", "CLAT"]
