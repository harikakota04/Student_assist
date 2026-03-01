# Backend Connection Issues - Quick Fix Guide

## Problem
Frontend is trying to connect to `http://localhost:8000/api/v1` but backend is not responding.

---

## ✅ Quick Start (3 steps)

### Step 1: Open a terminal in the backend folder
```bash
cd d:\studentassist\backend
```

### Step 2: Run the diagnostics (checks dependencies & starts server)
```bash
python startup_check.py
```

Or on Windows, double-click: `run_backend.bat`

### Step 3: Watch for the startup message
You should see:
```
✅ ALL CHECKS PASSED — Backend is ready to start!
🚀 Starting FastAPI server...
   Listening on: http://0.0.0.0:8000
```

Once you see this, the backend is **READY**. Don't close this window.

---

## 🔧 If it fails...

### "ModuleNotFoundError: No module named 'groq'"
```bash
pip install groq
```

### "Missing env vars: GROQ_API_KEY, LLM_MODEL"
Edit the `.env` file (or create it at `d:\studentassist\.env`):
```
GROQ_API_KEY=your-groq-api-key-here
YOUTUBE_API_KEY=optional
LLM_MODEL=llama-3.3-70b-versatile
MODEL_NAME=all-MiniLM-L6-v2
```

Get a free Groq API key from: https://console.groq.com/

### "Address already in use: ('0.0.0.0', 8000)"
Another process is using port 8000. Either:
- Close the other process, or
- Kill the port: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`, or
- Change the port in `run.py` line 13 to 8001, 8002, etc.

### Other errors during startup
The diagnostic output will tell you exactly what's wrong. Most issues are:
1. Missing Python packages → `pip install <package>`
2. Missing env vars → add to `.env`
3. Corrupted database → delete `student_assist.db` and restart

---

## 🎯 Parallel Terminal Setup

Once backend is running, **in a NEW terminal**:

```bash
cd d:\studentassist\frontend
streamlit run app.py
```

The frontend should now connect successfully to the backend!

---

## 📋 Checklist

- [ ] Backend terminal: `python startup_check.py` running without errors
- [ ] Backend terminal shows: "Listening on: http://0.0.0.0:8000"
- [ ] Frontend terminal: `streamlit run app.py` running
- [ ] Browser: http://localhost:8501 loads StudentAssist
- [ ] Login page appears (not connection error)

---

## 🆘 Still Not Working?

1. Copy the full error message from the backend terminal
2. Check that **GROQ_API_KEY** is set (required for any AI generation)
3. Make sure port 8000 is not blocked by firewall
4. Try a fresh `.env` file with all required vars

