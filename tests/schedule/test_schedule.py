# tests/test_schedule.py

import pytest
from httpx import AsyncClient, ASGITransport
from services.schedule.src.main import app
from services.schedule.src.db import init_db


@pytest.mark.asyncio
async def test_create_and_get_schedule():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Добавление занятия
        response = await client.post("/schedule", json={
            "name": "Contemporary",
            "teacher": "Ирина",
            "weekday": 3,
            "time": "17:30",
            "capacity": 20
        })
        assert response.status_code == 201, response.text
        class_data = response.json()
        assert class_data["name"] == "Contemporary"
        assert class_data["weekday"] == 3

        # 2. Получение всех занятий
        response = await client.get("/schedule")
        assert response.status_code == 200
        data = response.json()
        assert any(c["name"] == "Contemporary" for c in data)

        # 3. Фильтрация по преподавателю
        response = await client.get("/schedule?teacher=ирина")
        assert response.status_code == 200
        filtered = response.json()
        assert all("Ирина" in c["teacher"] for c in filtered)
