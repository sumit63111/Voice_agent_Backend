# Voice AI — Backend

Python FastAPI backend + LiveKit Agent for a healthcare front-desk AI voice assistant.

## Stack
- **Agent**: LiveKit Agents (Python)
- **STT**: Deepgram `nova-3-general` (`multi` — English by default, Hindi on request)
- **LLM**: Groq `gpt-oss-safegauard-120b`
- **TTS**: ElevenLabs (`eleven_turbo_v2_5`, Priyanka voice)
- **Avatar**: Tavus (optional)
- **Safeguard**: Groq content classifier
- **API**: FastAPI + Uvicorn
- **DB**: SQLite (via SQLAlchemy async)

## Setup

```bash
cd backend
cp .env.example .env
# Fill in your API keys in .env

pip install -r requirements.txt
```

## Run (Development)

**Terminal 1 — FastAPI server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — LiveKit Agent worker:**
```bash
python -m agent.agent start
```

## Run (Docker)

```bash
docker-compose up --build
```

## Directory Structure

```
backend/
├── app/               # FastAPI application
│   ├── api/           # Route handlers
│   ├── models.py      # SQLAlchemy models
│   ├── schemas.py     # Pydantic schemas
│   ├── database.py    # DB setup
│   └── main.py        # App entry point
├── agent/             # LiveKit agent
│   ├── agent.py       # Main agent entry point
│   ├── prompt.py      # System prompt
│   └── safeguard.py   # Content safety filter
├── tools/             # Agent tool handlers (one file per tool)
│   ├── identify_user.py
│   ├── fetch_slots.py
│   ├── book_appointment.py
│   ├── retrieve_appointments.py
│   ├── cancel_appointment.py
│   ├── modify_appointment.py
│   └── end_conversation.py
└── data/              # SQLite database files
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/livekit/token` | Get LiveKit room token |
| GET | `/api/appointments/{user_id}` | List user appointments |
| POST | `/api/appointments/` | Create appointment |
| DELETE | `/api/appointments/{id}` | Cancel appointment |
| PATCH | `/api/appointments/{id}` | Modify appointment |
| GET | `/api/summary/{room_name}` | Get call summary |
| GET | `/health` | Health check |
