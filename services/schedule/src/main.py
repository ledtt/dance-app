# services/schedule/main.py
from uuid import UUID
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db, init_db
from .schemas import ClassCreate, ClassOut
from .crud import get_schedule, get_classes_by_filter, create_class, get_class_by_id


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Schedule Service",
    description="Сервис управления расписанием",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/schedule", response_model=list[ClassOut])
async def list_schedule(
    day: int | None = Query(default=None, ge=1, le=7),
    teacher: str | None = None,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if day is not None or teacher or name:
        return await get_classes_by_filter(db, day=day, teacher=teacher, name=name)
    return await get_schedule(db)

@app.get("/schedule/{class_id}", response_model=ClassOut)
async def get_class(class_id: UUID, db: AsyncSession = Depends(get_db)):
    class_template = await get_class_by_id(db, class_id)
    if class_template is None:
        raise HTTPException(status_code=404, detail="Class template not found")
    return class_template

@app.post("/schedule", response_model=ClassOut, status_code=201)
async def add_class(class_data: ClassCreate, db: AsyncSession = Depends(get_db)):
    return await create_class(db, class_data)
