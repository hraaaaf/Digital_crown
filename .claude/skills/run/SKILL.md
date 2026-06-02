# Run Skill — DigitalCrown

## Project

**DigitalCrown** — SaaS de gestion de cabinet dentaire  
Stack : FastAPI backend (port 8005) + React/Vite frontend (port 5173)  
OS : Windows, venv à la racine du projet (`venv/`)

---

## How to launch

### Check if already running (always do this first)

```bash
# Backend health
curl -s http://127.0.0.1:8005/health

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

Si les deux répondent → les serveurs tournent déjà. Ne pas relancer.

---

### Start Backend (if not running)

```bash
cd "C:/Users/lenovo/Documents/Cabinet/DigitalCrown"
venv/Scripts/python.exe -m uvicorn backend.main:app \
  --host 127.0.0.1 --port 8005 --reload --reload-delay 2 \
  > /tmp/dc_backend.log 2>&1 &
echo "Backend PID: $!"
sleep 6
curl -s http://127.0.0.1:8005/health
```

### Start Frontend (if not running)

```bash
cd "C:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend"
npm run dev > /tmp/dc_frontend.log 2>&1 &
echo "Frontend PID: $!"
sleep 4
curl -s -o /dev/null -w "Frontend HTTP: %{http_code}\n" http://localhost:5173
```

---

## Verify startup — checklist

```bash
# 1. Backend health
curl -s http://127.0.0.1:8005/health | python -c "import sys,json; d=json.load(sys.stdin); print('DB:', d['db'], '| Status:', d['status'])"

# 2. Auth endpoint responds
curl -s -o /dev/null -w "Auth: %{http_code}\n" http://127.0.0.1:8005/api/auth/login

# 3. Frontend loads
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:5173

# 4. Tail backend logs (5s)
timeout 5 tail -f /tmp/dc_backend.log 2>/dev/null || cat /tmp/dc_backend.log | tail -20
```

Expected healthy output:
```
DB: ok | Status: ok
Auth: 422       ← 422 = endpoint exists (no body sent), not an error
Frontend: 200
INFO: Application startup complete.
INFO: Moteur Panoramique ELITE activé
```

---

## Key URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:8005/api |
| Health check | http://127.0.0.1:8005/health |
| API docs | http://127.0.0.1:8005/docs |

---

## Known issues & fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: passlib` | Python système au lieu du venv | Utiliser `venv/Scripts/python.exe` |
| Port 8005 already in use | Backend déjà lancé | Ne pas relancer |
| Port 5173 already in use | Frontend déjà lancé | Ne pas relancer |
| WS ghost-insights × 20 | Fuite WebSocket (fixé dans GhostBrainWidget) | Recharger le frontend |
| GET /treasury-hub 401 flood | JWT expiré + polling (fixé dans api.ts) | Se reconnecter |

---

## Credentials de test

Email : `benmoussa.achraf@gmail.com`  
Password : défini dans `backend/.env` → `SUPERADMIN_INITIAL_PASSWORD`

---

## Stop servers

```bash
# Kill backend
pkill -f "uvicorn backend.main"

# Kill frontend
pkill -f "vite"
```

Windows : utiliser les fenêtres CMD ouvertes par `Start_DigitalCrown.bat` et les fermer.
