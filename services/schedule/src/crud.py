from uuid import UUID
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import ClassTemplate
from .schemas import ClassCreate


async def create_class(db: AsyncSession, class_data: ClassCreate) -> ClassTemplate:
    new_class = ClassTemplate(**class_data.model_dump())
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class

async def get_schedule(db: AsyncSession) -> Sequence[ClassTemplate]:
    result = await db.execute(
        select(ClassTemplate).where(ClassTemplate.active.is_(True))
    )
    return result.scalars().all()

async def get_classes_by_filter(
    db: AsyncSession,
    day: int | None,
    teacher: str | None,
    name: str | None,
) -> Sequence[ClassTemplate]:
    query = select(ClassTemplate).where(ClassTemplate.active.is_(True))
    if day is not None:
        query = query.where(ClassTemplate.weekday == day)
    if teacher:
        query = query.where(ClassTemplate.teacher.ilike(f"%{teacher}%"))
    if name:
        query = query.where(ClassTemplate.name.ilike(f"%{name}%"))
    result = await db.execute(query)
    return result.scalars().all()

async def get_class_by_id(db: AsyncSession, class_id: UUID) -> ClassTemplate | None:
    result = await db.execute(select(ClassTemplate).where(ClassTemplate.id == class_id))
    return result.scalar_one_or_none()
