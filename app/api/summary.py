from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.database import get_db_session
from app.models import CallSession
from app.schemas import CallSummaryOut

router = APIRouter()


@router.get("/{room_name}", response_model=CallSummaryOut)
async def get_summary(room_name: str):
    async with get_db_session() as db:
        result = await db.execute(
            select(CallSession).where(CallSession.room_name == room_name)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
