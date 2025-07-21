import asyncio

import pytest
import httpx

AUTH_URL = "http://localhost:8001"
BOOKING_URL = "http://localhost:8003"

@pytest.mark.asyncio
async def test_booking_with_auth():
    # Подождём, пока сервисы стартуют (в реальности лучше healthcheck)
    await asyncio.sleep(3)

    async with httpx.AsyncClient() as client:
        # 1. Регистрация
        r = await client.post(f"{AUTH_URL}/register", json={
            "email": "testuser@example.com",
            "name": "Test",
            "password": "pass1234A"
        })
        assert r.status_code == 201
        user_id = r.json()["id"]

        # 2. Авторизация
        r = await client.post(f"{AUTH_URL}/login", data={
            "username": "testuser@example.com",
            "password": "pass1234A"
        })
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Попробуем запросить записи (в ответе будет [])
        r = await client.get(f"{BOOKING_URL}/my-bookings", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
