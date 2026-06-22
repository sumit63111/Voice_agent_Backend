from datetime import datetime, timedelta, date as date_type
from sqlalchemy import select
from app.database import get_db_session
from app.models import Appointment, AppointmentStatus

SLOT_TIMES = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]


async def handle_fetch_slots(date_str: str) -> dict:
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"slots": [], "message": f"Invalid date format. Please use YYYY-MM-DD."}

    today = date_type.today()
    if target_date < today:
        return {"slots": [], "message": "That date has already passed. Please choose a future date."}
    if target_date.weekday() == 6:
        return {"slots": [], "message": "The clinic is closed on Sundays. Please choose another day."}

    async with get_db_session() as db:
        result = await db.execute(
            select(Appointment.time).where(
                Appointment.date == date_str,
                Appointment.status == AppointmentStatus.active,
            )
        )
        booked_times = {row[0] for row in result.fetchall()}

    available = [t for t in SLOT_TIMES if t not in booked_times]

    if not available:
        return {
            "slots": [],
            "message": f"No slots available on {target_date.strftime('%B %d, %Y')}. Please try another date.",
        }

    slots_str = ", ".join(
        datetime.strptime(t, "%H:%M").strftime("%I:%M %p") for t in available
    )
    return {
        "slots": available,
        "message": f"Available slots on {target_date.strftime('%A, %B %d')}: {slots_str}. Which time works for you?",
    }
