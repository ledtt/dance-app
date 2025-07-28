# tests/test_booking.py

import uuid
import datetime
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.db import init_db
from src import crud
from src.auth import get_current_user_id


@pytest.mark.asyncio
async def test_booking_flow(monkeypatch):
    await init_db()

    class_id = uuid.uuid4()
    user_token = "Bearer testtoken"
    user_id = str(uuid.uuid4())

    # capacity = 1, weekday = today
    async def fake_get_class_template_by_id(class_id_str: str):
        return SimpleNamespace(
            id=class_id_str,
            name="Ballet",
            teacher="Анна",
            weekday=datetime.date.today().isoweekday(),
            time="18:00",
            capacity=1
        )

    # Мокаем внешний вызов расписания
    monkeypatch.setattr(crud, "get_class_template_by_id", fake_get_class_template_by_id)

    # Переопределяем зависимость аутентификации
    app.dependency_overrides[get_current_user_id] = lambda token: user_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        date_str = datetime.date.today().isoformat()

        # ✅ 1. Успешная запись
        response = await client.post(
            "/book",
            headers={"Authorization": user_token},
            json={"class_id": str(class_id), "date": date_str},
        )
        assert response.status_code == 201, response.text
        booking = response.json()
        assert booking["class_id"] == str(class_id)
        assert booking["user_id"] == user_id

        # ❌ 2. Повторная запись тем же пользователем
        response = await client.post(
            "/book",
            headers={"Authorization": user_token},
            json={"class_id": str(class_id), "date": date_str},
        )
        assert response.status_code == 400
        assert "уже записаны" in response.text.lower()

        # ❌ 3. Переполнение capacity — другой пользователь
        another_user_id = str(uuid.uuid4())
        app.dependency_overrides[get_current_user_id] = lambda token: another_user_id
        response = await client.post(
            "/book",
            headers={"Authorization": "Bearer second"},
            json={"class_id": str(class_id), "date": date_str},
        )
        assert response.status_code == 400
        assert "места заняты" in response.text.lower()

        # ✅ 4. Мои записи (у нового пользователя пусто)
        response = await client.get(
            "/my-bookings",
            headers={"Authorization": "Bearer second"},
        )
        assert response.status_code == 200
        assert response.json() == []

        # ✅ 5. Админ-сводка содержит нашу запись
        response = await client.get("/admin/summary")
        assert response.status_code == 200
        assert "<table" in response.text
        assert str(class_id) in response.text
