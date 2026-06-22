import re

from sqlalchemy import select
from app.database import get_db_session
from app.models import User


def _normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    if _is_fake_number(digits):
        return None
    return f"+91{digits}"


def _is_fake_number(digits: str) -> bool:
    if len(set(digits)) == 1:
        return True
    ascending = "01234567890123456789"
    descending = "98765432109876543210"
    if digits in ascending or digits in descending:
        return True
    if digits[0] in "012345":
        return True
    return False


async def handle_identify_user(phone_number: str) -> dict:
    normalized = _normalize_phone(phone_number)
    if normalized is None:
        return {
            "error": "invalid_phone",
            "is_new": False,
            "message": (
                "I didn't quite catch a valid phone number. "
                "Could you please tell me your 10-digit mobile number?"
            ),
        }
    phone_number = normalized

    async with get_db_session() as db:
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        user = result.scalar_one_or_none()

        if user:
            return {
                "user_id": user.id,
                "phone_number": user.phone_number,
                "name": user.name or "Patient",
                "is_new": False,
                "message": f"Welcome back! I've found your record. How can I help you today?",
            }
        else:
            user = User(phone_number=phone_number, name=None)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return {
                "user_id": user.id,
                "phone_number": user.phone_number,
                "name": "Patient",
                "is_new": True,
                "message": "I've registered your number. What would you like to do — book an appointment, or something else?",
            }