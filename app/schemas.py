from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    id: str
    phone_number: str
    name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentOut(BaseModel):
    id: str
    user_id: str
    date: str
    time: str
    reason: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    user_id: str
    date: str
    time: str
    reason: Optional[str] = None


class AppointmentModify(BaseModel):
    new_date: Optional[str] = None
    new_time: Optional[str] = None
    reason: Optional[str] = None


class TokenRequest(BaseModel):
    room_name: Optional[str] = None
    participant_identity: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    room_name: str
    url: str


class CallSummaryOut(BaseModel):
    id: str
    room_name: str
    summary: Optional[str]
    transcript: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True
