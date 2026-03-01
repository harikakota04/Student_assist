# 🤖 AI Teaching Assistant

An intelligent, adaptive teaching assistant powered by **Groq LLaMA**, **Sentence Transformers**, and the **YouTube Data API**. It supports CAT, IPMAT, and CLAT aspirants by analyzing student queries, detecting intent and difficulty level, generating personalized explanations, and building a custom learning path with real video resources.

---

## 🗂️ Project Structure

```
project-root/
├── main.py                        # FastAPI entry point
├── app.py                         # Streamlit frontend
├── .env                           # Environment variables (not committed)
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── health.py              # Health check endpoint
│   │   ├── query.py               # /analyze-query and /full-analysis endpoints
│   │   └── learning_path.py      # /learning-path endpoint
│   ├── core/
│   │   └── config.py             # Pydantic settings / .env loader
│   ├── models/
│   │   └── schemas.py            # All Pydantic data models
│   └── services/
│       ├── nlp_service.py        # Intent + difficulty detection via MiniLM + Groq
│       └── learning_path_service.py  # Explanation + path generation + YouTube
```

---

## ⚙️ Prerequisites

- Python 3.10+
- Node.js (not required unless generating docs)
- A [Groq API key](https://console.groq.com/)
- A [YouTube Data API v3 key](https://console.developers.google.com/) *(optional)*

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/harikakota04/student-assist
cd student-assist
```

### 2. Create and Activate a Virtual Environment

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Your `requirements.txt` should include:

```
fastapi
uvicorn
pydantic-settings
groq
sentence-transformers
httpx
streamlit
requests
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here   # optional
LLM_MODEL=llama-3.3-70b-versatile
MODEL_NAME=all-MiniLM-L6-v2
```

> ⚠️ Never commit your `.env` file. Add it to `.gitignore`.

---

## ▶️ Running the Application

You need **two terminals open at the same time**.

### Terminal 1 — Start the FastAPI Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Confirm it's running by visiting: [http://localhost:8000/docs](http://localhost:8000/docs)

You should see the Swagger UI with all available endpoints.

### Terminal 2 — Start the Streamlit Frontend

```bash
streamlit run app.py
```

The app will open automatically in your browser at [http://localhost:8501](http://localhost:8501).

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze-query` | Analyze a student query (NLP only) |
| POST | `/api/full-analysis` | Full pipeline: NLP + learning path + YouTube |
| POST | `/api/learning-path` | Generate learning path from structured request |

### Example Request — `/api/full-analysis`

```bash
curl -X POST http://localhost:8000/api/full-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am confused about backpropagation",
    "student_id": "student_001",
    "previous_topics": ["Neural Networks", "Gradient Descent"]
  }'
```

---

## 🧠 Intent Types Detected

| Intent | Example Query |
|--------|--------------|
| 💡 Explanation | "What is backpropagation?" |
| 🔍 Example | "Give me an example of a transformer" |
| ❓ Doubt Clarification | "I'm confused about L1 vs L2 regularization" |
| 📖 Revision | "Revise key points of gradient descent" |

---

## 🐛 Troubleshooting

**"Cannot connect to backend"**
Make sure FastAPI is running on port 8000 before clicking the button in Streamlit.

**"model_decommissioned" error**
Update `LLM_MODEL` in your `.env` file to `llama-3.3-70b-versatile` and restart the backend.

**No YouTube videos showing**
Add a valid `YOUTUBE_API_KEY` to your `.env`. Without it, fallback search links are shown instead.

**Slow first load**
The `all-MiniLM-L6-v2` model is downloaded on first use (~90MB). Subsequent starts are fast.

---

## 📄 License

This project was built as part of the ThinkPlus AI/ML Engineer Assignment.
