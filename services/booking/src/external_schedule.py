# services/booking/external_schedule.py

import os
import httpx

BASE_URL = os.getenv("SCHEDULE_SERVICE_URL", "http://schedule-service:8000") # можно взять из env
print("SCHEDULE_SERVICE_URL =", BASE_URL)

async def get_class_template_by_id(class_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/schedule/{class_id}")
            if resp.status_code == 200:
                return resp.json()
            return None
    except httpx.RequestError:
        return None
