# services/booking/crud.py

import datetime
from collections.abc import Sequence
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


from .models import Booking
from .schemas import BookingCreate
from .external_schedule import get_class_template_by_id


async def create_booking(
    db: AsyncSession,
    user_id: UUID,
    booking_in: BookingCreate
) -> Booking:
    template = await get_class_template_by_id(str(booking_in.class_id))
    if not template:
        raise ValueError("Class template not found")

    if booking_in.date.isoweekday() != template["weekday"]:
        raise ValueError("Неверный день недели для занятия")

    start_time = datetime.datetime.combine(
        booking_in.date,
        datetime.time.fromisoformat(template["time"])
    )

    count_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.class_id == booking_in.class_id,
            Booking.date == booking_in.date
        )
    )
    count = count_result.scalar_one()
    if count >= template["capacity"]:
        raise ValueError("Запись невозможна — все места заняты")

    existing_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.user_id == user_id,
            Booking.class_id == booking_in.class_id,
            Booking.date == booking_in.date
        )
    )
    existing = existing_result.scalar_one()
    if existing:
        raise ValueError("Вы уже записаны на это занятие")

    booking = Booking(
        user_id=user_id,
        class_id=booking_in.class_id,
        date=booking_in.date,
        start_time=start_time
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_bookings_for_user(db: AsyncSession, user_id: str) -> Sequence[Booking]:
    result = await db.execute(
        select(Booking).where(Booking.user_id == user_id)
    )
    return result.scalars().all()


async def get_all_bookings_with_summary(db: AsyncSession) -> Sequence[Booking]:
    result = await db.execute(select(Booking))
    return result.scalars().all()
