"""
Run this instead of uvicorn directly:
  python run.py

Sets h11_max_incomplete_event_size and timeout_keep_alive high enough
for long Groq calls (30-45 seconds).
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=120,   # keep connection alive for 2 min
        workers=1,
    )