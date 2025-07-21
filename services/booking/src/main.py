# services/booking/main.py

from uuid import UUID
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db, init_db
from .schemas import BookingCreate, BookingOut
from .auth import get_current_user_id
from .crud import (
    create_booking,
    get_bookings_for_user,
    get_all_bookings_with_summary,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Booking Service",
    description="Сервис записи на занятия",
    version="1.0.0",
    lifespan=lifespan,
)

@app.post("/book", response_model=BookingOut, status_code=201)
async def book_class(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        booking = await create_booking(db, UUID(user_id), booking_in)
        return booking
    except ValueError as e:
        logger.warning("Ошибка записи: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@app.get("/my-bookings", response_model=list[BookingOut])
async def my_bookings(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await get_bookings_for_user(db, user_id)


@app.get("/admin/summary", response_class=HTMLResponse)
async def admin_summary(db: AsyncSession = Depends(get_db)):
    rows = await get_all_bookings_with_summary(db)

    html = "<h2>Записи на занятия</h2><table border='1'><tr><th>Дата</th><th>Время</th><th>Класс</th><th>Пользователь</th></tr>"
    for row in rows:
        html += f"<tr><td>{row.date}</td><td>{row.start_time.strftime('%H:%M')}</td><td>{row.class_id}</td><td>{row.user_id}</td></tr>"
    html += "</table>"

    return html
