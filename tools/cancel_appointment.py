from datetime import datetime
from sqlalchemy import select
from app.database import get_db_session
from app.models import Appointment, AppointmentStatus


async def handle_cancel_appointment(appointment_id: str) -> dict:
    async with get_db_session() as db:
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appt = result.scalar_one_or_none()

        if not appt:
            result = await db.execute(select(Appointment))
            all_appts = result.scalars().all()
            appt = next((a for a in all_appts if a.id.startswith(appointment_id)), None)

        if not appt:
            return {"status": "error", "message": "I couldn't find that appointment. Could you confirm the appointment ID?"}

        if appt.status == AppointmentStatus.cancelled:
            return {"status": "error", "message": "That appointment has already been cancelled."}

        appt.status = AppointmentStatus.cancelled
        await db.commit()

        try:
            display_date = datetime.strptime(appt.date, "%Y-%m-%d").strftime("%B %d, %Y")
            display_time = datetime.strptime(appt.time, "%H:%M").strftime("%I:%M %p")
        except ValueError:
            display_date = appt.date
            display_time = appt.time

        return {
            "status": "done",
            "appointment_id": appt.id,
            "message": f"Your appointment on {display_date} at {display_time} has been cancelled. Is there anything else I can help with?",
        }
