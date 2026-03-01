# StudentAssist — Feature Integration Guide
## CAT, IPMAT & CLAT Adaptive Learning Platform

---

## 1. New Files — Where Each Goes

| File | Place in your project |
|------|-----------------------|
| `database.py` | `app/database.py` |
| `syllabus.py` | `app/syllabus.py` |
| `new_schemas.py` | `app/models/new_schemas.py` |
| `student_service.py` | `app/services/student_service.py` |
| `assessment_service.py` | `app/services/assessment_service.py` |
| `dashboard_service.py` | `app/services/dashboard_service.py` |
| `exam_mock_test_service.py` | `app/services/exam_mock_test_service.py` |
| `route_auth.py` | `app/api/auth.py` |
| `route_assessment.py` | `app/api/assessment.py` |
| `route_dashboard.py` | `app/api/dashboard.py` |
| `route_exam_mock_test.py` | `app/api/exam_mock_test.py` |
| `route_syllabus.py` | `app/api/syllabus_route.py` |
| `main.py` | Replace your `app/main.py` |

---

## 2. SQLite Database — 4 Tables

```
students               — name, email, password, exam_target, has_taken_assessment
assessment_results     — section_scores, weak_topics, strong_topics, difficulty_level
mock_test_results      — every mock test taken, per-topic breakdown
student_progress       — rolling avg/best/last score per topic (updated after every test)
```

Tables are **created automatically** on startup via `init_db()`. No migrations needed.

---

## 3. Student Flow

### Step 1 — Register
```
POST /api/v1/register
{
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "password": "mypassword",
  "exam_target": "CAT"          ← "CAT" or "IPMAT"
}
```
Response includes: student profile + message prompting assessment.

### Step 2 — Login
```
POST /api/v1/login
{ "email": "priya@example.com", "password": "mypassword" }
```
If `has_taken_assessment = false` → message tells them to take assessment first.

### Step 3 — Take Placement Assessment (once)
```
GET /api/v1/assessment/CAT
```
Returns 15 basic questions (5 per section: VARC, DILR, QA).
For IPMAT: 5 per section across QA, VA, LR.

```
POST /api/v1/assessment/submit
{
  "student_id": 1,
  "exam_target": "CAT",
  "answers": { "q1": "B", "q2": "A", ... },
  "questions": [ ...the questions array from GET response... ]
}
```
Returns: section scores, weak/strong topics, difficulty level, personalized message.
Saves everything to SQLite automatically.

### Step 4 — View Dashboard
```
GET /api/v1/dashboard/1
```
Returns full dashboard:
- `section_scores` — e.g. `{"VARC": 60.0, "DILR": 40.0, "QA": 80.0}`
- `weak_topics` — topics scored < 50%
- `strong_topics` — topics scored >= 70%
- `topic_progress` — per-topic: attempts, avg_score, best_score
- `recent_mock_tests` — last 10 tests
- `adaptive_learning_path` — personalized steps based on actual performance
- `overall_avg_score` — rolling average across all mock tests

### Step 5 — Mock Tests (subject/topic/difficulty)
```
GET /api/v1/syllabus/CAT       ← Get all sections + topics to show dropdowns
```

```
POST /api/v1/exam-mock-test/generate
{
  "student_id": 1,
  "exam_target": "CAT",
  "subject": "Quantitative Aptitude (QA)",
  "topic": "Probability",
  "difficulty": "Intermediate",
  "num_questions": 10
}
```

```
POST /api/v1/exam-mock-test/evaluate
{
  "student_id": 1,
  "exam_target": "CAT",
  "subject": "Quantitative Aptitude (QA)",
  "topic": "Probability",
  "difficulty": "Intermediate",
  "questions": [ ...questions from generate response... ],
  "user_answers": { "q1": "C", "q2": "B", ... }
}
```
Returns: score, grade, detailed results, **next recommended topic**, adaptive message.
Updates `mock_test_results` and `student_progress` in SQLite.

---

## 4. Adaptive Learning Logic

The dashboard's `adaptive_learning_path` is rebuilt every time from real data:

1. **Topics with avg_score < 50%** → prioritized first (fix weakest)
2. **Topics with avg_score 50–70%** → second priority (needs more work)
3. **Untested topics** → third priority (explore gaps)
4. Difficulty adapts: score < 40% → Beginner, 40–70% → Intermediate, > 70% → Advanced

After each mock test, `_recommend_next_topic` is called:
- Score < 50% → stay on same topic
- Score >= 50% → move to first untested topic or lowest-scoring tested topic

---

## 5. CAT vs IPMAT Differences

| | CAT | IPMAT |
|---|---|---|
| Sections | VARC, DILR, QA | QA, VA, LR |
| QA topics | ~20 topics | ~20 topics (slightly different scope) |
| VARC/VA | Reading Comprehension focus | Grammar + Vocab focus |
| LR | Part of DILR | Separate section |
| Question style | Groq prompted with "CAT standard" | Groq prompted with "IPMAT standard" |

Choosing `exam_target` at registration filters ALL content — assessment, mock tests, syllabus, and adaptive path are all scoped to that exam.

---

## 6. Install Dependencies

```bash
pip install sqlalchemy --break-system-packages
# Already have: groq, fastapi, pydantic, httpx
```

No Alembic needed — SQLite tables auto-create on startup.

---

## 7. Updating Existing `mock_test_service.py`

Your existing `mock_test_service.py` needs these exports (which the article mock test route uses):
- `generate_mock_test(article_content, article_title, difficulty, num_questions)`
- `evaluate_test(submission)`
- `generate_mock_test_from_short_content(title, summary)`

The `mock_test_service.py` file provided in the previous fix handles this. The new
`exam_mock_test_service.py` is a **separate service** for CAT/IPMAT/CLAT subject tests.
