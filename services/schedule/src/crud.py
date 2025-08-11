from uuid import UUID
from collections.abc import Sequence
from typing import Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from .models import ClassTemplate
from .schemas import ClassCreate
from shared.exceptions import ResourceNotFoundError, ValidationError
from shared.constants import ERROR_MESSAGES, MAX_CLASS_CAPACITY, MIN_CLASS_CAPACITY





async def get_schedule(db: AsyncSession, limit: int = 100, offset: int = 0) -> Sequence[ClassTemplate]:
    """Get all classes with pagination"""
    result = await db.execute(
        select(ClassTemplate)
        .limit(limit)
        .offset(offset)
        .order_by(ClassTemplate.weekday, ClassTemplate.start_time)
    )
    return result.scalars().all()


async def get_classes_by_filter(
    db: AsyncSession, 
    day: Optional[int] = None, 
    teacher: Optional[str] = None, 
    name: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> Sequence[ClassTemplate]:
    """Get classes with filtering"""
    import structlog
    logger = structlog.get_logger()
    
    logger.info("Filtering classes", day=day, teacher=teacher, name=name, active=active)
    
    conditions = []
    
    if day is not None:
        conditions.append(ClassTemplate.weekday == day)
    if teacher:
        conditions.append(ClassTemplate.teacher.ilike(f"%{teacher}%"))
    if name:
        conditions.append(ClassTemplate.name.ilike(f"%{name}%"))
    if active is not None:
        conditions.append(ClassTemplate.active == active)
    
    logger.info("Built conditions", conditions_count=len(conditions))
    
    query = select(ClassTemplate)
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(
        query
        .limit(limit)
        .offset(offset)
        .order_by(ClassTemplate.weekday, ClassTemplate.start_time)
    )
    
    classes = result.scalars().all()
    logger.info("Query executed", result_count=len(classes))
    
    return classes


async def get_class_by_id(db: AsyncSession, class_id: UUID) -> Optional[ClassTemplate]:
    """Get a specific class by ID"""
    result = await db.execute(select(ClassTemplate).where(ClassTemplate.id == class_id))
    return result.scalar_one_or_none()


async def check_teacher_schedule_conflict(
    db: AsyncSession,
    teacher: str,
    weekday: int,
    start_time: datetime.time,
    exclude_class_id: Optional[UUID] = None
) -> bool:
    """Check if teacher has schedule conflict"""
    # Debug: Log the type and value of start_time
    import structlog
    logger = structlog.get_logger()
    logger.info("Checking teacher schedule conflict", 
                teacher=teacher, 
                weekday=weekday, 
                start_time=start_time, 
                start_time_type=type(start_time).__name__)
    
    conditions = [
        ClassTemplate.teacher == teacher,
        ClassTemplate.weekday == weekday,
        ClassTemplate.start_time == start_time,
        ClassTemplate.active == True
    ]
    
    if exclude_class_id:
        conditions.append(ClassTemplate.id != exclude_class_id)
    
    result = await db.execute(
        select(func.count())
        .select_from(ClassTemplate)
        .where(and_(*conditions))
    )
    
    count = result.scalar_one()
    return count > 0


async def create_class(db: AsyncSession, class_data: ClassCreate) -> ClassTemplate:
    """Create a new class"""
    # Debug: Log the incoming data
    import structlog
    logger = structlog.get_logger()
    logger.info("Creating class", 
                name=class_data.name,
                teacher=class_data.teacher,
                weekday=class_data.weekday,
                start_time=class_data.start_time,
                start_time_type=type(class_data.start_time).__name__,
                capacity=class_data.capacity)
    
    # Validate capacity
    if class_data.capacity < MIN_CLASS_CAPACITY or class_data.capacity > MAX_CLASS_CAPACITY:
        raise ValidationError(f"Capacity must be between {MIN_CLASS_CAPACITY} and {MAX_CLASS_CAPACITY}")
    
    # Validate weekday
    if class_data.weekday < 1 or class_data.weekday > 7:
        raise ValidationError("Weekday must be between 1 and 7")
    
    # Check for teacher schedule conflict
    has_conflict = await check_teacher_schedule_conflict(
        db, class_data.teacher, class_data.weekday, class_data.start_time
    )
    
    if has_conflict:
        raise ValidationError(
            f"Teacher {class_data.teacher} already has a class on "
            f"weekday {class_data.weekday} at {class_data.start_time}"
        )
    
    new_class = ClassTemplate(
        name=class_data.name,
        teacher=class_data.teacher,
        weekday=class_data.weekday,
        start_time=class_data.start_time,
        capacity=class_data.capacity,
        comment=class_data.comment,
        active=True
    )
    
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class


async def update_class(db: AsyncSession, class_id: UUID, class_data: ClassCreate) -> ClassTemplate:
    """Update an existing class"""
    existing_class = await get_class_by_id(db, class_id)
    if not existing_class:
        raise ResourceNotFoundError(ERROR_MESSAGES["class_not_found"])
    
    # Validate capacity
    if class_data.capacity < MIN_CLASS_CAPACITY or class_data.capacity > MAX_CLASS_CAPACITY:
        raise ValidationError(f"Capacity must be between {MIN_CLASS_CAPACITY} and {MAX_CLASS_CAPACITY}")
    
    # Validate weekday
    if class_data.weekday < 1 or class_data.weekday > 7:
        raise ValidationError("Weekday must be between 1 and 7")
    
    # Check for teacher schedule conflict (excluding current class)
    has_conflict = await check_teacher_schedule_conflict(
        db, class_data.teacher, class_data.weekday, class_data.start_time, exclude_class_id=class_id
    )
    
    if has_conflict:
        raise ValidationError(
            f"Teacher {class_data.teacher} already has a class on "
            f"weekday {class_data.weekday} at {class_data.start_time}"
        )
    
    existing_class.name = class_data.name
    existing_class.teacher = class_data.teacher
    existing_class.weekday = class_data.weekday
    existing_class.start_time = class_data.start_time
    existing_class.capacity = class_data.capacity
    existing_class.comment = class_data.comment
    
    await db.commit()
    await db.refresh(existing_class)
    return existing_class


async def delete_class(db: AsyncSession, class_id: UUID) -> None:
    """Delete a class"""
    existing_class = await get_class_by_id(db, class_id)
    if not existing_class:
        raise ResourceNotFoundError(ERROR_MESSAGES["class_not_found"])
    
    await db.delete(existing_class)
    await db.commit()


async def get_classes_by_teacher(db: AsyncSession, teacher_name: str, limit: int = 100, offset: int = 0) -> Sequence[ClassTemplate]:
    """Get all classes taught by a specific teacher"""
    result = await db.execute(
        select(ClassTemplate)
        .where(ClassTemplate.teacher.ilike(f"%{teacher_name}%"))
        .limit(limit)
        .offset(offset)
        .order_by(ClassTemplate.weekday, ClassTemplate.start_time)
    )
    return result.scalars().all()


async def get_classes_by_weekday(db: AsyncSession, weekday: int, limit: int = 100, offset: int = 0) -> Sequence[ClassTemplate]:
    """Get all classes for a specific weekday"""
    result = await db.execute(
        select(ClassTemplate)
        .where(ClassTemplate.weekday == weekday)
        .limit(limit)
        .offset(offset)
        .order_by(ClassTemplate.start_time)
    )
    return result.scalars().all()


async def get_class_statistics(db: AsyncSession) -> dict:
    """Get class statistics for admin dashboard"""
    # Total classes
    total_result = await db.execute(select(func.count(ClassTemplate.id)))
    total_classes = total_result.scalar_one()
    
    # Active classes
    active_result = await db.execute(select(func.count(ClassTemplate.id)).where(ClassTemplate.active == True))
    active_classes = active_result.scalar_one()
    
    # Total unique teachers
    teachers_result = await db.execute(select(func.count(func.distinct(ClassTemplate.teacher))))
    total_teachers = teachers_result.scalar_one()
    
    # Classes by weekday
    weekday_result = await db.execute(
        select(ClassTemplate.weekday, func.count(ClassTemplate.id).label('count'))
        .group_by(ClassTemplate.weekday)
        .order_by(ClassTemplate.weekday)
    )
    classes_by_weekday = weekday_result.all()
    
    # Most popular teachers
    teacher_result = await db.execute(
        select(ClassTemplate.teacher, func.count(ClassTemplate.id).label('count'))
        .group_by(ClassTemplate.teacher)
        .order_by(func.count(ClassTemplate.id).desc())
        .limit(5)
    )
    popular_teachers = teacher_result.all()
    
    # Average capacity
    capacity_result = await db.execute(select(func.avg(ClassTemplate.capacity)))
    avg_capacity = capacity_result.scalar_one()
    
    return {
        "total_classes": total_classes,
        "active_classes": active_classes,
        "total_teachers": total_teachers,
        "inactive_classes": total_classes - active_classes,
        "classes_by_weekday": [{"weekday": w.weekday, "count": w.count} for w in classes_by_weekday],
        "popular_teachers": [{"teacher": t.teacher, "count": t.count} for t in popular_teachers],
        "average_capacity": round(avg_capacity, 2) if avg_capacity else 0
    }
