# tests/test_auth.py

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.db import init_db

@pytest.mark.asyncio
async def test_register_login_me_flow():
    await init_db()  # инициализация схемы БД
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Регистрация нового пользователя
        resp = await client.post("/register", json={
            "email": "user@example.com",
            "name": "Test User",
            "password": "Qwerty123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "user@example.com"
        assert data["name"] == "Test User"
        assert "id" in data

        # Повторная регистрация
        resp = await client.post("/register", json={
            "email": "user@example.com",
            "name": "Duplicate",
            "password": "Qwerty123"
        })
        assert resp.status_code == 409

        # Успешный логин
        resp = await client.post("/login", data={
            "username": "user@example.com",
            "password": "Qwerty123"
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # /me с токеном
        resp = await client.get("/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@example.com"

        # Неверный пароль
        resp = await client.post("/login", data={
            "username": "user@example.com",
            "password": "wrong"
        })
        assert resp.status_code == 401

        # /me без токена
        resp = await client.get("/me")
        assert resp.status_code == 401

        # Невалидный email
        resp = await client.post("/register", json={
            "email": "bademail",
            "name": "Test",
            "password": "Qwerty123"
        })
        assert resp.status_code == 422

        # Пароль без цифр
        resp = await client.post("/register", json={
            "email": "no_digits@example.com",
            "name": "NoDigits",
            "password": "PasswordOnly"
        })
        assert resp.status_code == 422

        # Невалидный токен
        resp = await client.get("/me", headers={"Authorization": "Bearer bad.token"})
        assert resp.status_code == 401

        # Без имени
        resp = await client.post("/register", json={
            "email": "no_name@example.com",
            "password": "Pass1234"
        })
        assert resp.status_code == 422
