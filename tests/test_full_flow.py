import pytest
import httpx
import asyncio
from datetime import date, timedelta
from uuid import uuid4

AUTH_URL = "http://localhost:8001"
SCHEDULE_URL = "http://localhost:8002"
BOOKING_URL = "http://localhost:8003"

email = f"user_{uuid4().hex[:6]}@example.com"

@pytest.mark.asyncio
async def test_full_flow():
    async with httpx.AsyncClient() as client:
        # 1. Регистрация пользователя
        r = await client.post(f"{AUTH_URL}/register", json={
            "email": email,
            "name": "Test User",
            "password": "Pass1234"
        })
        assert r.status_code == 201
        user_id = r.json()["id"]

        # 2. Получение токена
        r = await client.post(f"{AUTH_URL}/login", data={
            "username": email,
            "password": "Pass1234"
        })
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Создание шаблона занятия в schedule
        today = date.today()
        weekday = today.isoweekday()
        r = await client.post(f"{SCHEDULE_URL}/schedule", json={
            "name": "Hip-Hop",
            "teacher": "Анна",
            "weekday": weekday,
            "time": "18:00:00",
            "capacity": 3
        })
        assert r.status_code == 201
        class_id = r.json()["id"]

        # 4. Проверка расписания
        r = await client.get(f"{SCHEDULE_URL}/schedule")
        assert r.status_code == 200
        schedule = r.json()
        assert any(c["id"] == class_id for c in schedule)

        # 5. Запись на занятие
        r = await client.post(f"{BOOKING_URL}/book", json={
            "class_id": class_id,
            "date": today.isoformat()
        }, headers=headers)
        print("Booking response:", r.status_code, r.text)
        assert r.status_code == 201
        booking = r.json()

        # 6. Проверка своих записей
        r = await client.get(f"{BOOKING_URL}/my-bookings", headers=headers)
        assert r.status_code == 200
        my_bookings = r.json()
        assert any(b["id"] == booking["id"] for b in my_bookings)
