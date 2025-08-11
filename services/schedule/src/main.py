# services/schedule/main.py
from uuid import UUID
import structlog
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timezone

import os
from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db, init_db
from .schemas import ClassCreate, ClassOut
from shared.schemas import PaginatedResponse
from .crud import (
    get_schedule, 
    get_classes_by_filter, 
    create_class, 
    get_class_by_id,
    update_class,
    delete_class,
    get_classes_by_teacher,
    get_classes_by_weekday,
    get_class_statistics
)
from .auth import get_current_admin_user, verify_service_token, UserInToken
from shared.exceptions import ResourceNotFoundError, ValidationError
from shared.constants import ERROR_MESSAGES, SUCCESS_MESSAGES, WeekDay

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_paginated_response(items: List, total: int, page: int, size: int) -> PaginatedResponse:
    """Create a paginated response with calculated pages"""
    pages = (total + size - 1) // size if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Schedule Service",
    description="Schedule management service with advanced features",
    version="1.0.0",
    lifespan=lifespan,
)

# Add trusted host middleware
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "localhost")
allowed_hosts = [host.strip() for host in allowed_hosts_str.split(',')]

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=allowed_hosts
)

@app.get("/health")
async def health_check():
    """Health check endpoint for AWS monitoring"""
    return {
        "status": "healthy",
        "service": "schedule",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@app.get("/schedule", response_model=PaginatedResponse[ClassOut])
async def list_schedule(
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    teacher: Optional[str] = Query(None, description="Filter by teacher name"),
    weekday: Optional[int] = Query(None, ge=1, le=7, description="Filter by weekday (1=Monday, 7=Sunday)"),
    day: Optional[int] = Query(None, ge=1, le=7, description="Filter by weekday (1=Monday, 7=Sunday) - deprecated, use weekday"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status - deprecated, use active"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(100, ge=1, le=1000, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get schedule with advanced filtering and pagination"""
    try:
        # Handle deprecated parameters
        if day is not None:
            weekday = day
        if is_active is not None:
            active = is_active
        
        # Calculate offset from page and size
        offset = (page - 1) * size
        
        # Build filter parameters
        filters = {}
        if weekday is not None:
            filters['day'] = weekday
        if teacher is not None:
            filters['teacher'] = teacher
        if name is not None:
            filters['name'] = name
        if active is not None:
            filters['active'] = active
        
        # Apply date range filtering if provided
        if start_date or end_date:
            # This would require additional implementation in crud.py
            # For now, we'll use the existing filtering
            pass
        
        if filters:
            classes = await get_classes_by_filter(db, **filters, limit=size, offset=offset)
            # For now, we'll use the length as total count
            # In a real implementation, you'd want to get the total count separately
            total_count = len(classes)
            logger.info("Filtered schedule retrieved", filters=filters, count=len(classes))
        else:
            classes = await get_schedule(db, limit=size, offset=offset)
            # For now, we'll use the length as total count
            # In a real implementation, you'd want to get the total count separately
            total_count = len(classes)
            logger.info("Full schedule retrieved", count=len(classes))
        
        return create_paginated_response(classes, total_count, page, size)
    except Exception as e:
        logger.error("Error retrieving schedule", error=str(e))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.get("/schedule/ids", response_model=List[str])
async def get_class_ids(
    teacher: Optional[str] = Query(None, description="Filter by teacher name"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    service_payload: dict = Depends(verify_service_token),
):
    """Get class IDs with filtering for internal service communication"""
    try:
        logger.info("Received request for class IDs", 
                   teacher=teacher, name=name, active=active,
                   service=service_payload.get("service"))
        
        # Build filter parameters
        filters = {}
        if teacher is not None:
            filters['teacher'] = teacher
        if name is not None:
            filters['name'] = name
        if active is not None:
            filters['active'] = active
        
        logger.info("Built filters for class search", filters=filters)
        
        # Get classes with filters
        classes = await get_classes_by_filter(db, **filters, limit=1000, offset=0)
        
        logger.info("Classes found in database", count=len(classes))
        
        # Extract IDs
        class_ids = [str(class_template.id) for class_template in classes]
        
        logger.info("Class IDs retrieved for filtering", 
                   filters=filters, count=len(class_ids), 
                   service=service_payload.get("service"),
                   first_few_ids=class_ids[:5] if class_ids else [])
        
        return class_ids
    except Exception as e:
        logger.error("Error retrieving class IDs", error=str(e))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.post("/schedule", response_model=ClassOut, status_code=201)
async def add_class(
    class_data: ClassCreate, 
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user)
):
    """Create a new class (admin only)"""
    try:
        new_class = await create_class(db, class_data)
        logger.info("Class created successfully", class_id=str(new_class.id), name=new_class.name, admin_id=admin.id)
        return new_class
    except ValidationError as e:
        logger.warning("Class creation failed - validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error creating class", error=str(e))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.get("/schedule/statistics")
async def get_schedule_statistics(db: AsyncSession = Depends(get_db)):
    """Get schedule statistics for admin dashboard"""
    try:
        stats = await get_class_statistics(db)
        logger.info("Schedule statistics retrieved")
        return stats
    except Exception as e:
        logger.error("Error retrieving schedule statistics", error=str(e))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.get("/schedule/{class_id}", response_model=ClassOut)
async def get_class(
    class_id: UUID, 
    db: AsyncSession = Depends(get_db),
    service_payload: dict = Depends(verify_service_token)
):
    """Get a specific class by ID"""
    try:
        logger.info("Received request for class", class_id=str(class_id), service=service_payload.get("service"))
        class_template = await get_class_by_id(db, class_id)
        if class_template is None:
            logger.warning("Class template not found", class_id=str(class_id))
            raise HTTPException(status_code=404, detail=ERROR_MESSAGES["class_not_found"])
        logger.info("Class template retrieved", class_id=str(class_id))
        return class_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving class template", error=str(e), class_id=str(class_id))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.put("/schedule/{class_id}", response_model=ClassOut)
async def update_class_endpoint(
    class_id: UUID, 
    class_data: ClassCreate, 
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user)
):
    """Update an existing class (admin only)"""
    try:
        updated_class = await update_class(db, class_id, class_data)
        logger.info("Class updated successfully", class_id=str(class_id), admin_id=admin.id)
        return updated_class
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=ERROR_MESSAGES["class_not_found"])
    except ValidationError as e:
        logger.warning("Class update failed - validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error updating class", error=str(e), class_id=str(class_id))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.delete("/schedule/{class_id}")
async def delete_class_endpoint(
    class_id: UUID, 
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user)
):
    """Delete a class (admin only)"""
    try:
        await delete_class(db, class_id)
        logger.info("Class deleted successfully", class_id=str(class_id), admin_id=admin.id)
        return {"message": SUCCESS_MESSAGES["class_deleted"]}
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=ERROR_MESSAGES["class_not_found"])
    except Exception as e:
        logger.error("Error deleting class", error=str(e), class_id=str(class_id))
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.get("/schedule/teacher/{teacher_name}", response_model=List[ClassOut], deprecated=True)
async def get_classes_by_teacher_endpoint(
    teacher_name: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get all classes taught by a specific teacher (DEPRECATED - use GET /schedule?teacher=name)"""
    try:
        classes = await get_classes_by_teacher(db, teacher_name, limit, offset)
        logger.info("Classes retrieved by teacher", teacher=teacher_name, count=len(classes))
        return classes
    except Exception as e:
        logger.error("Error retrieving classes by teacher", error=str(e), teacher=teacher_name)
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e

@app.get("/schedule/weekday/{weekday}", response_model=List[ClassOut], deprecated=True)
async def get_classes_by_weekday_endpoint(
    weekday: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get all classes for a specific weekday (DEPRECATED - use GET /schedule?weekday=day)"""
    try:
        if weekday < 1 or weekday > 7:
            raise HTTPException(status_code=400, detail="Weekday must be between 1 and 7")
        
        classes = await get_classes_by_weekday(db, weekday, limit, offset)
        weekday_name = WeekDay(weekday).name
        logger.info("Classes retrieved by weekday", weekday=weekday_name, count=len(classes))
        return classes
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving classes by weekday", error=str(e), weekday=weekday)
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_error"]) from e
