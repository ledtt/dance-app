# services/booking/crud.py

import datetime
import structlog
from collections.abc import Sequence
from uuid import UUID
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import Column
from typing import Optional
import asyncio

from .models import Booking
from .schemas import BookingCreate
from .external_schedule import get_class_template_by_id, get_user_by_id, get_class_ids_by_filter
from shared.exceptions import BookingError, ResourceNotFoundError, CapacityExceededError
from shared.constants import ERROR_MESSAGES

logger = structlog.get_logger()


async def create_booking(
    db: AsyncSession,
    user_id: UUID,
    booking_in: BookingCreate,
    admin_override: bool = False
) -> Booking:
    """Create a new booking with improved transaction handling"""
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        
        # Get class template information
        template = await get_class_template_by_id(str(booking_in.class_id))
        if not template:
            raise ResourceNotFoundError(ERROR_MESSAGES["class_not_found"])
        
        # Validate weekday
        # Python weekday(): 0=Monday, 1=Tuesday, ..., 6=Sunday
        # Database weekday: 1=Monday, 2=Tuesday, ..., 7=Sunday
        python_weekday = booking_in.date.weekday()  # 0-6
        db_weekday = template.get("weekday", 1)  # 1-7
        expected_python_weekday = db_weekday - 1  # Convert 1-7 to 0-6
        
        if python_weekday != expected_python_weekday:
            raise BookingError(ERROR_MESSAGES["wrong_weekday"])
        
        # Determine actual user ID (admin can book for others)
        actual_user_id = booking_in.user_id if booking_in.user_id and admin_override else user_id
        
        # Combined check for capacity and existing booking in one query
        check_query = (
            select(
                func.count(Booking.id).label("current_bookings"),
                func.count(Booking.id).filter(Booking.user_id == actual_user_id).label("user_has_booking")
            )
            .where(
                and_(
                    Booking.class_id == booking_in.class_id,
                    Booking.date == booking_in.date
                )
            )
        )
        
        check_result = await db.execute(check_query)
        counts = check_result.one()
        
        # Check capacity
        if counts.current_bookings >= template["capacity"]:
            raise CapacityExceededError(ERROR_MESSAGES["capacity_exceeded"])
        
        # Check if user already has a booking (unless admin override)
        if not admin_override and counts.user_has_booking > 0:
            raise BookingError(ERROR_MESSAGES["already_booked"])
        
        # Create and add booking
        # Get start_time from template
        start_time_str = template.get("start_time", "18:00")
        try:
            # Parse time string to datetime.time
            hour, minute = map(int, start_time_str.split(':'))
            time_obj = datetime.time(hour, minute)
            # Create datetime object by combining date and time
            start_time = datetime.datetime.combine(booking_in.date, time_obj)
        except (ValueError, TypeError):
            # Fallback to default time
            time_obj = datetime.time(18, 0)
            start_time = datetime.datetime.combine(booking_in.date, time_obj)
        
        booking = Booking(
            class_id=booking_in.class_id,
            user_id=actual_user_id,
            date=booking_in.date,
            start_time=start_time
        )
        
        db.add(booking)
        await db.flush()  # Get the ID without committing
        await db.refresh(booking)
        
        logger.info("Booking created successfully", 
                   booking_id=str(booking.id), 
                   user_id=str(actual_user_id),
                   class_id=str(booking_in.class_id),
                   date=booking_in.date.isoformat())
        
        return booking


async def get_bookings_for_user(db: AsyncSession, user_id: str) -> list:
    """Get all bookings for a specific user with enriched data"""
    result = await db.execute(
        select(Booking).where(Booking.user_id == user_id)
    )
    bookings = result.scalars().all()
    return await _enrich_bookings(bookings)


async def get_all_bookings_with_summary(
    db: AsyncSession, 
    limit: int = 100,
    offset: int = 0,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id_filter: Optional[str] = None,
    teacher: Optional[str] = None,
    class_name: Optional[str] = None,
    class_id: Optional[str] = None
) -> list:
    """Get all bookings with enriched user and class information"""
    logger.info("Getting all bookings with summary", 
                limit=limit, offset=offset,
                date_from=date_from, date_to=date_to,
                user_id_filter=user_id_filter, teacher=teacher,
                class_name=class_name, class_id=class_id)
    
    # Логируем все входящие фильтры для отладки
    logger.info("Input filters received", 
               teacher=teacher, class_name=class_name, 
               has_teacher_filter=teacher is not None,
               has_class_name_filter=class_name is not None)
    
    # Оптимизация: Если есть фильтры по teacher или class_name, сначала получаем ID классов
    filtered_class_ids = None
    if teacher or class_name:
        logger.info("Applying teacher/class_name filters", teacher=teacher, class_name=class_name)
        try:
            logger.info("Calling schedule service for class IDs...")
            filtered_class_ids = await get_class_ids_by_filter(teacher=teacher, name=class_name)
            logger.info("Response from schedule service", 
                       filtered_class_ids=filtered_class_ids, 
                       response_type=type(filtered_class_ids).__name__)
            
            if filtered_class_ids is None:
                logger.error("Failed to get class IDs from schedule service - received None")
                return []
            
            if not filtered_class_ids:
                logger.info("No classes found matching teacher/class_name filters", 
                           teacher=teacher, class_name=class_name)
                return []
            
            logger.info(f"Found {len(filtered_class_ids)} classes matching filters", 
                       teacher=teacher, class_name=class_name, class_ids=filtered_class_ids[:5])  # Log first 5 IDs
        except (ValueError, TypeError, ConnectionError) as e:
            logger.error("Exception while getting class IDs from schedule service", 
                        error=str(e), teacher=teacher, class_name=class_name)
            return []
    
    # Начинаем строить запрос
    query = select(Booking).order_by(Booking.created_at.desc())
    
    # Динамически добавляем фильтры
    conditions = []
    
    if date_from:
        from_date = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
        conditions.append(Booking.date >= from_date)
    
    if date_to:
        to_date = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
        conditions.append(Booking.date <= to_date)
    
    if class_id:
        conditions.append(Booking.class_id == UUID(class_id))
    
    # Добавляем фильтр по ID классов, если они были получены из schedule-service
    if filtered_class_ids:
        # Преобразуем строковые ID в UUID
        class_uuid_list = [UUID(class_id_str) for class_id_str in filtered_class_ids]
        conditions.append(Booking.class_id.in_(class_uuid_list))
        logger.info(f"Added class_id filter with {len(class_uuid_list)} class IDs", 
                   first_few_ids=[str(uuid) for uuid in class_uuid_list[:3]])
    
    # Добавляем фильтр по user_id на уровне базы данных
    if user_id_filter:
        conditions.append(Booking.user_id == UUID(user_id_filter))
    
    if conditions:
        query = query.where(and_(*conditions))
        logger.info(f"Applied {len(conditions)} database filters", 
                   conditions=[str(cond) for cond in conditions])
    
    # Применяем пагинацию
    query = query.offset(offset).limit(limit)
    
    # Логируем финальный SQL запрос для отладки
    logger.info("Executing database query", 
               query=str(query.compile(compile_kwargs={"literal_binds": True})))
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    if not bookings:
        logger.info("No bookings found after database filtering")
        return []
    
    logger.info(f"Found {len(bookings)} bookings after database filtering, enriching with user and class data")
    
    # Собираем уникальные ID пользователей и классов
    user_ids = list(set(str(booking.user_id) for booking in bookings))
    class_ids = list(set(str(booking.class_id) for booking in bookings))
    
    logger.info(f"Unique user IDs: {len(user_ids)}, unique class IDs: {len(class_ids)}")
    
    # Создаем задачи для параллельного получения данных
    class_tasks = [get_class_template_by_id(class_id) for class_id in class_ids]
    user_tasks = [get_user_by_id(user_id) for user_id in user_ids]
    
    # Execute all tasks concurrently
    logger.info("Starting concurrent requests", class_count=len(class_tasks), user_count=len(user_tasks))
    all_tasks = class_tasks + user_tasks
    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    
    # Split results back into class and user results
    class_results = results[:len(class_tasks)]
    user_results = results[len(class_tasks):]
    
    # Debug logging
    logger.info("Class results received", count=len(class_results))
    logger.info("User results received", count=len(user_results))
    
    # Log first few results for debugging
    for i, result in enumerate(class_results[:3]):
        if isinstance(result, Exception):
            logger.error(f"Class result {i} is exception", error=str(result))
        else:
            logger.info(f"Class result {i}", class_id=class_ids[i] if i < len(class_ids) else "unknown", result=result)
    
    for i, result in enumerate(user_results[:3]):
        if isinstance(result, Exception):
            logger.error(f"User result {i} is exception", error=str(result))
        else:
            logger.info(f"User result {i}", user_id=user_ids[i] if i < len(user_ids) else "unknown", result=result)
    
    # Create lookup dictionaries
    class_lookup = {}
    for i, class_id in enumerate(class_ids):
        if i < len(class_results):
            result = class_results[i]
            if isinstance(result, Exception):
                logger.warning(f"Failed to get class {class_id}", error=str(result))
                class_lookup[class_id] = None
            else:
                class_lookup[class_id] = result
    
    user_lookup = {}
    for i, user_id in enumerate(user_ids):
        if i < len(user_results):
            result = user_results[i]
            if isinstance(result, Exception):
                logger.warning(f"Failed to get user {user_id}", error=str(result))
                user_lookup[user_id] = None
            else:
                user_lookup[user_id] = result
    
    # Enrich bookings with user and class information
    enriched_bookings = []
    for booking in bookings:
        booking_dict = {
            'id': str(booking.id),
            'class_id': str(booking.class_id),
            'user_id': str(booking.user_id),
            'date': booking.date.isoformat(),
            'start_time': booking.start_time.isoformat(),
            'created_at': booking.created_at.isoformat(),
            'status': getattr(booking, 'status', 'active')  # Add status field with default
        }
        
        # Add class information
        class_info = class_lookup.get(str(booking.class_id))
        if class_info:
            booking_dict['class_info'] = {
                'id': str(booking.class_id),
                'name': class_info.get('name', 'Unknown Class'),
                'teacher': class_info.get('teacher', 'Unknown Teacher'),
                'weekday': class_info.get('weekday', 1),
                'start_time': class_info.get('start_time', '00:00'),
                'capacity': class_info.get('capacity', 0),
                'active': class_info.get('active', False),
                'created_at': datetime.datetime.now().isoformat()
            }
        else:
            booking_dict['class_info'] = _get_default_class(str(booking.class_id))
        
        # Add user information
        user_info = user_lookup.get(str(booking.user_id))
        if user_info:
            booking_dict['user'] = {
                'id': str(booking.user_id),
                'name': user_info.get('name', 'Unknown User'),
                'email': user_info.get('email', 'unknown@example.com'),
                'role': user_info.get('role', 'user'),
                'is_active': user_info.get('is_active', True),  # Add missing required field
                'created_at': user_info.get('created_at', datetime.datetime.now().isoformat())
            }
        else:
            booking_dict['user'] = _get_default_user(str(booking.user_id))
        
        enriched_bookings.append(booking_dict)
    
    logger.info(f"Returning {len(enriched_bookings)} enriched bookings after all filtering")
    return enriched_bookings


async def cancel_booking(db: AsyncSession, booking_id: UUID, user_id: UUID) -> None:
    """Cancel a booking for a specific user by changing status to cancelled"""
    result = await db.execute(
        select(Booking).where(
            and_(
                Booking.id == booking_id,
                Booking.user_id == user_id
            )
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise ResourceNotFoundError(ERROR_MESSAGES["booking_not_found"])
    
    # Update status to cancelled instead of deleting
    booking.status = 'cancelled'
    await db.commit()


async def get_booking_by_id(db: AsyncSession, booking_id: UUID, user_id: UUID) -> Optional[dict]:
    """Get a specific booking by ID for a user with enriched data"""
    result = await db.execute(
        select(Booking).where(
            and_(
                Booking.id == booking_id,
                Booking.user_id == user_id
            )
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return None
    
    enriched_bookings = await _enrich_bookings([booking])
    return enriched_bookings[0] if enriched_bookings else None


async def get_bookings_by_class(db: AsyncSession, class_id: UUID, limit: int = 100, offset: int = 0) -> list:
    """Get all bookings for a specific class with enriched data"""
    result = await db.execute(
        select(Booking)
        .where(Booking.class_id == class_id)
        .limit(limit)
        .offset(offset)
    )
    bookings = result.scalars().all()
    return await _enrich_bookings(bookings)


async def get_booking_statistics(db: AsyncSession) -> dict:
    """Get booking statistics for admin dashboard"""
    # Total bookings
    total_result = await db.execute(select(func.count(Booking.id)))
    total_bookings = total_result.scalar_one()
    
    # Today's bookings
    today = datetime.date.today()
    today_result = await db.execute(
        select(func.count(Booking.id)).where(Booking.date == today)
    )
    today_bookings = today_result.scalar_one()
    
    # This week's bookings
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_result = await db.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= week_start, Booking.date <= week_end)
        )
    )
    week_bookings = week_result.scalar_one()
    
    # Active users (unique users who have made bookings)
    active_users_result = await db.execute(
        select(func.count(func.distinct(Booking.user_id)))
    )
    active_users = active_users_result.scalar_one()
    
    # Most popular classes
    popular_classes_result = await db.execute(
        select(Booking.class_id, func.count(Booking.id).label('count'))
        .group_by(Booking.class_id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    )
    popular_classes = popular_classes_result.all()
    
    return {
        "total_bookings": total_bookings,
        "today_bookings": today_bookings,
        "week_bookings": week_bookings,
        "active_users": active_users,
        "popular_classes": [{"class_id": str(c.class_id), "count": c.count} for c in popular_classes]
    }


async def _enrich_bookings(bookings: list[Booking]) -> list[dict]:
    """Helper function to enrich bookings with user and class information"""
    if not bookings:
        return []

    logger.info(f"Enriching {len(bookings)} bookings with user and class data")
    
    # Собираем уникальные ID пользователей и классов
    class_ids = list(set(str(booking.class_id) for booking in bookings))
    user_ids = list(set(str(booking.user_id) for booking in bookings))
    
    logger.info(f"Unique user IDs: {len(user_ids)}, unique class IDs: {len(class_ids)}")
    
    # Создаем задачи для параллельного получения данных
    class_tasks = [get_class_template_by_id(class_id) for class_id in class_ids]
    user_tasks = [get_user_by_id(user_id) for user_id in user_ids]
    
    # Execute all tasks concurrently
    logger.info("Starting concurrent requests", class_count=len(class_tasks), user_count=len(user_tasks))
    all_tasks = class_tasks + user_tasks
    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    
    # Split results back into class and user results
    class_results = results[:len(class_tasks)]
    user_results = results[len(class_tasks):]
    
    # Debug logging
    logger.info("Class results received", count=len(class_results))
    logger.info("User results received", count=len(user_results))
    
    # Log first few results for debugging
    for i, result in enumerate(class_results[:3]):
        if isinstance(result, Exception):
            logger.error(f"Class result {i} is exception", error=str(result))
        else:
            logger.info(f"Class result {i}", class_id=class_ids[i] if i < len(class_ids) else "unknown", result=result)
    
    for i, result in enumerate(user_results[:3]):
        if isinstance(result, Exception):
            logger.error(f"User result {i} is exception", error=str(result))
        else:
            logger.info(f"User result {i}", user_id=user_ids[i] if i < len(user_ids) else "unknown", result=result)
    
    # Create lookup dictionaries
    class_lookup = {}
    for i, class_id in enumerate(class_ids):
        if i < len(class_results):
            result = class_results[i]
            if isinstance(result, Exception):
                logger.warning(f"Failed to get class {class_id}", error=str(result))
                class_lookup[class_id] = None
            else:
                class_lookup[class_id] = result
    
    user_lookup = {}
    for i, user_id in enumerate(user_ids):
        if i < len(user_results):
            result = user_results[i]
            if isinstance(result, Exception):
                logger.warning(f"Failed to get user {user_id}", error=str(result))
                user_lookup[user_id] = None
            else:
                user_lookup[user_id] = result
    
    # Enrich bookings with user and class information
    enriched_bookings = []
    for booking in bookings:
        booking_dict = {
            'id': str(booking.id),
            'class_id': str(booking.class_id),
            'user_id': str(booking.user_id),
            'date': booking.date.isoformat(),
            'start_time': booking.start_time.isoformat(),
            'created_at': booking.created_at.isoformat(),
            'status': getattr(booking, 'status', 'active')  # Add status field with default
        }
        
        # Add class information
        class_info = class_lookup.get(str(booking.class_id))
        if class_info:
            booking_dict['class_info'] = {
                'id': str(booking.class_id),
                'name': class_info.get('name', 'Unknown Class'),
                'teacher': class_info.get('teacher', 'Unknown Teacher'),
                'weekday': class_info.get('weekday', 1),
                'start_time': class_info.get('start_time', '00:00'),
                'capacity': class_info.get('capacity', 0),
                'active': class_info.get('active', False),
                'created_at': datetime.datetime.now().isoformat()
            }
        else:
            booking_dict['class_info'] = _get_default_class(str(booking.class_id))
        
        # Add user information
        user_info = user_lookup.get(str(booking.user_id))
        if user_info:
            booking_dict['user'] = {
                'id': str(booking.user_id),
                'name': user_info.get('name', 'Unknown User'),
                'email': user_info.get('email', 'unknown@example.com'),
                'role': user_info.get('role', 'user'),
                'is_active': user_info.get('is_active', True),  # Add missing required field
                'created_at': user_info.get('created_at', datetime.datetime.now().isoformat())
            }
        else:
            booking_dict['user'] = _get_default_user(str(booking.user_id))
        
        enriched_bookings.append(booking_dict)
    
    logger.info(f"Successfully enriched {len(enriched_bookings)} bookings")
    return enriched_bookings


def _get_default_class(class_id: str) -> dict:
    """Helper function to create default class info when class not found"""
    return {
        'id': class_id,
        'name': 'Archived/Deleted Class',
        'teacher': 'Unknown Teacher',
        'weekday': 1,
        'start_time': '00:00',
        'capacity': 0,
        'active': False,
        'created_at': datetime.datetime.now().isoformat()
    }


def _get_default_user(user_id: str) -> dict:
    """Helper function to create default user info when user not found"""
    return {
        'id': user_id,
        'name': 'Unknown User',
        'email': 'unknown@example.com',
        'role': 'user',
        'is_active': True,  # Add missing required field
        'created_at': datetime.datetime.now().isoformat()
    }


async def update_booking_statuses(db: AsyncSession) -> None:
    """Update booking statuses based on current time and class schedule"""
    now = datetime.datetime.now()
    
    # Get all active bookings
    result = await db.execute(
        select(Booking).where(Booking.status == 'active')
    )
    active_bookings = result.scalars().all()
    
    updated_count = 0
    for booking in active_bookings:
        # Create datetime for class start time
        class_datetime = datetime.datetime.combine(booking.date, datetime.time.min)
        if booking.start_time:
            # If start_time is a datetime, extract time part
            if isinstance(booking.start_time, datetime.datetime):
                class_datetime = datetime.datetime.combine(booking.date, booking.start_time.time())
            else:
                # If start_time is a time string, parse it
                try:
                    time_parts = str(booking.start_time).split(':')
                    class_datetime = datetime.datetime.combine(
                        booking.date, 
                        datetime.time(int(time_parts[0]), int(time_parts[1]))
                    )
                except (ValueError, IndexError):
                    # If parsing fails, use default time
                    pass
        
        # If class is in the past and not cancelled, mark as completed
        if class_datetime < now and booking.status != 'cancelled':
            booking.status = 'completed'
            updated_count += 1
    
    if updated_count > 0:
        await db.commit()
        logger.info(f"Updated {updated_count} booking statuses to completed")
