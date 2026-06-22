from datetime import datetime
from sqlalchemy import select
from app.database import get_db_session
from app.models import Appointment, AppointmentStatus, User


async def handle_book_appointment(user_id: str, date_str: str, time_str: str, reason: str) -> dict:
    if not user_id:
        return {"status": "error", "message": "I need to identify you first. Could you please share your phone number?"}

    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
        try:
            time_str = datetime.strptime(time_str.strip(), fmt).strftime("%H:%M")
            break
        except ValueError:
            continue

    async with get_db_session() as db:
        conflict = await db.execute(
            select(Appointment).where(
                Appointment.date == date_str,
                Appointment.time == time_str,
                Appointment.status == AppointmentStatus.active,
            )
        )
        if conflict.scalar_one_or_none():
            return {
                "status": "conflict",
                "message": f"Sorry, {time_str} on {date_str} is already taken. Would you like to choose a different time?",
            }

        user_conflict = await db.execute(
            select(Appointment).where(
                Appointment.user_id == user_id,
                Appointment.date == date_str,
                Appointment.status == AppointmentStatus.active,
            )
        )
        if user_conflict.scalar_one_or_none():
            return {
                "status": "conflict",
                "message": f"You already have an appointment on {date_str}. Would you like to modify it instead?",
            }

        appt = Appointment(
            user_id=user_id,
            date=date_str,
            time=time_str,
            reason=reason,
            status=AppointmentStatus.active,
        )
        db.add(appt)
        await db.commit()
        await db.refresh(appt)

        try:
            display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %d, %Y")
            display_time = datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p")
        except ValueError:
            display_date = date_str
            display_time = time_str

        return {
            "status": "done",
            "appointment_id": appt.id,
            "date": date_str,
            "time": time_str,
            "reason": reason,
            "message": (
                f"Your appointment is confirmed! "
                f"Date: {display_date}, Time: {display_time}, Reason: {reason}. "
                f"Is there anything else I can help you with?"
            ),
        }
