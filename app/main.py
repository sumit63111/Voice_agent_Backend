from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.config import settings
from app.api import livekit_routes, appointments, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Voice AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(livekit_routes.router, prefix="/api/livekit", tags=["livekit"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Voice AI"}
