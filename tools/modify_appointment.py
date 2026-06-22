from datetime import datetime
from sqlalchemy import select
from app.database import get_db_session
from app.models import Appointment, AppointmentStatus


async def handle_modify_appointment(appointment_id: str, new_date: str | None, new_time: str | None) -> dict:
    if not new_date and not new_time:
        return {"status": "error", "message": "Please tell me the new date or time you'd like."}

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
            return {"status": "error", "message": "That appointment has been cancelled and cannot be modified."}

        target_date = new_date or appt.date
        target_time = new_time or appt.time

        if new_time:
            for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
                try:
                    target_time = datetime.strptime(new_time.strip(), fmt).strftime("%H:%M")
                    break
                except ValueError:
                    continue

        conflict = await db.execute(
            select(Appointment).where(
                Appointment.date == target_date,
                Appointment.time == target_time,
                Appointment.status == AppointmentStatus.active,
                Appointment.id != appt.id,
            )
        )
        if conflict.scalar_one_or_none():
            return {
                "status": "conflict",
                "message": f"That slot is already taken. Would you like to choose a different time?",
            }

        appt.date = target_date
        appt.time = target_time
        appt.status = AppointmentStatus.modified
        await db.commit()

        try:
            display_date = datetime.strptime(target_date, "%Y-%m-%d").strftime("%A, %B %d, %Y")
            display_time = datetime.strptime(target_time, "%H:%M").strftime("%I:%M %p")
        except ValueError:
            display_date = target_date
            display_time = target_time

        return {
            "status": "done",
            "appointment_id": appt.id,
            "message": f"Your appointment has been updated to {display_date} at {display_time}. Is there anything else I can help with?",
        }
