from datetime import datetime, date
from sqlalchemy import select
from app.database import get_db_session
from app.models import Appointment, AppointmentStatus


async def handle_retrieve_appointments(user_id: str) -> dict:
    if not user_id:
        return {"appointments": [], "message": "I need to identify you first. Please share your phone number."}

    today = date.today().strftime("%Y-%m-%d")

    async with get_db_session() as db:
        result = await db.execute(
            select(Appointment).where(
                Appointment.user_id == user_id,
                Appointment.date >= today,
                Appointment.status == AppointmentStatus.active,
            ).order_by(Appointment.date, Appointment.time)
        )
        appointments = result.scalars().all()

    if not appointments:
        return {
            "appointments": [],
            "message": "You have no upcoming appointments. Would you like to book one?",
        }

    lines = []
    appt_list = []
    for appt in appointments:
        try:
            display_date = datetime.strptime(appt.date, "%Y-%m-%d").strftime("%A, %B %d")
            display_time = datetime.strptime(appt.time, "%H:%M").strftime("%I:%M %p")
        except ValueError:
            display_date = appt.date
            display_time = appt.time
        lines.append(f"{display_date} at {display_time} — {appt.reason or 'General consultation'} (ID: {appt.id[:8]})")
        appt_list.append({"id": appt.id, "date": appt.date, "time": appt.time, "reason": appt.reason})

    summary = "; ".join(lines)
    return {
        "appointments": appt_list,
        "message": f"You have {len(appointments)} upcoming appointment(s): {summary}. What would you like to do?",
    }
