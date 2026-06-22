import json
from datetime import datetime
from groq import AsyncGroq
from sqlalchemy import select
from app.config import settings
from app.database import get_db_session
from app.models import CallSession, Appointment, AppointmentStatus


async def handle_end_conversation(room, session_data: dict) -> dict:
    user_id = session_data.get("user_id")
    room_name = room.name if room else "unknown"

    appointments_list = []
    if user_id:
        async with get_db_session() as db:
            result = await db.execute(
                select(Appointment).where(
                    Appointment.user_id == user_id,
                    Appointment.status == AppointmentStatus.active,
                ).order_by(Appointment.date)
            )
            for appt in result.scalars().all():
                appointments_list.append({
                    "id": appt.id,
                    "date": appt.date,
                    "time": appt.time,
                    "reason": appt.reason,
                    "status": appt.status.value,
                })

    summary = ""
    try:
        client = AsyncGroq(api_key=settings.groq_api_key)
        context = f"Patient phone: {session_data.get('phone_number', 'unknown')}\n"
        if appointments_list:
            context += f"Appointments: {json.dumps(appointments_list, indent=2)}\n"

        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical call summarizer. Write a brief, professional summary of this healthcare appointment call in 2-3 sentences.",
                },
                {"role": "user", "content": context},
            ],
            max_tokens=200,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as e:
        summary = f"Call completed. Patient: {session_data.get('phone_number', 'unknown')}. Appointments: {len(appointments_list)}."

    async with get_db_session() as db:
        existing = await db.execute(
            select(CallSession).where(CallSession.room_name == room_name)
        )
        session_record = existing.scalar_one_or_none()
        if session_record:
            session_record.ended_at = datetime.utcnow()
            session_record.summary = summary
            session_record.user_id = user_id
        else:
            session_record = CallSession(
                room_name=room_name,
                user_id=user_id,
                ended_at=datetime.utcnow(),
                summary=summary,
            )
            db.add(session_record)
        await db.commit()

    return {
        "summary": summary,
        "appointments": appointments_list,
        "message": "Thank you for calling. Have a great day and take care! Goodbye.",
    }
