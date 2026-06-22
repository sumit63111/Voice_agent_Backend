from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Appointment, AppointmentStatus
from app.schemas import AppointmentOut, AppointmentCreate, AppointmentModify
from typing import List

router = APIRouter()


@router.get("/{user_id}", response_model=List[AppointmentOut])
async def list_appointments(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Appointment)
        .where(Appointment.user_id == user_id, Appointment.status != AppointmentStatus.cancelled)
        .order_by(Appointment.date, Appointment.time)
    )
    return result.scalars().all()


@router.post("/", response_model=AppointmentOut)
async def create_appointment(data: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    conflict = await db.execute(
        select(Appointment).where(
            Appointment.date == data.date,
            Appointment.time == data.time,
            Appointment.status == AppointmentStatus.active,
        )
    )
    if conflict.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slot already booked")

    appt = Appointment(**data.model_dump())
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", response_model=AppointmentOut)
async def cancel_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = AppointmentStatus.cancelled
    await db.commit()
    await db.refresh(appt)
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def modify_appointment(appointment_id: str, data: AppointmentModify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if data.new_date:
        appt.date = data.new_date
    if data.new_time:
        appt.time = data.new_time
    if data.reason:
        appt.reason = data.reason
    appt.status = AppointmentStatus.modified

    await db.commit()
    await db.refresh(appt)
    return appt
