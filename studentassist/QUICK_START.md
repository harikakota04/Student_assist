# 🚀 StudentAssist Startup Guide

## The Problem You Had
```
HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded...
```
→ Backend wasn't running. **Now fixed!**

---

## ✅ How to Start Everything (Pick 1)

### **Option 1: Easiest (Windows) - One Click**
1. Go to root folder: `d:\studentassist\`
2. **Double-click:** `run_all.bat`
3. Two windows will open (backend + frontend)
4. Browser opens at `http://localhost:8501`

---

### **Option 2: Easiest (All OS) - Smart Startup**
```bash
# Terminal 1: Backend
cd backend
python startup_check.py
```
This will:
- ✅ Check all dependencies 
- ✅ Verify environment variables
- ✅ Validate imports
- ✅ Start the server
- ✅ Show "Listening on: http://0.0.0.0:8000"

```bash
# Terminal 2: Frontend (after backend shows "Listening on...")
cd frontend
streamlit run app.py
```

---

### **Option 3: Classic **
```bash
# Terminal 1
cd backend
python run.py

# Terminal 2
cd frontend
streamlit run app.py
```

---

## 📋 What to Expect

### Backend Terminal (should show):
```
✅ ALL CHECKS PASSED — Backend is ready to start!
🚀 Starting FastAPI server...
   Listening on: http://0.0.0.0:8000
   Docs will be at: http://localhost:8000/docs
   Press Ctrl+C to stop.

[DB] Tables ready.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend Terminal (should show):
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Browser (should open):
- `http://localhost:8501` shows StudentAssist login page
- No red error messages about backend

---

## 🔧 If Something's Wrong

| Problem | Fix |
|---------|-----|
| Backend won't start | Check `TROUBLESHOOTING.md` |
| "ModuleNotFoundError: groq" | `pip install groq` |
| Port 8000 already in use | `netstat -ano \| findstr :8000` then kill PID |
| Frontend shows red error | Run `python startup_check.py` in backend folder |
| Database errors | Delete `backend/student_assist.db` and restart |

See `TROUBLESHOOTING.md` for full guide.

---

## ✅ Quick Checklist

- [ ] Backend terminal shows "Listening on: http://0.0.0.0:8000"
- [ ] Frontend terminal shows "Local URL: http://localhost:8501"
- [ ] Browser loads login page (not error)
- [ ] No red warnings/errors on login screen
- [ ] Can type in login form

**If all ✅, you're ready to use StudentAssist!**

---

## 📞 Useful URLs

| What | URL |
|------|-----|
| Frontend App | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Backend Health | http://localhost:8000/api/v1/health |

---

## 🛑 To Stop Everything

- Backend: Press `Ctrl+C` in backend terminal
- Frontend: Press `Ctrl+C` in frontend terminal  
- Or just close both terminal windows

