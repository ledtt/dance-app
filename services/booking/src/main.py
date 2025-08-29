# services/booking/main.py

from uuid import UUID
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Query, APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional

from .db import get_db, init_db
from .schemas import BookingCreate, BookingOut, BookingFilterParams
from shared.schemas import PaginatedResponse
from .auth import get_current_user, get_current_admin_user, UserInToken
from .crud import (
    create_booking,
    get_bookings_for_user,
    get_all_bookings_with_summary,
    cancel_booking,
    get_booking_by_id,
    get_bookings_by_class,
    get_booking_statistics,
    update_booking_statuses,
)
from .external_schedule import get_class_template_by_id
from shared.exceptions import BookingError, ResourceNotFoundError, CapacityExceededError
from shared.constants import ERROR_MESSAGES, SUCCESS_MESSAGES

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
    title="Booking Service",
    description="Class booking service with advanced features",
    version="1.0.0",
    lifespan=lifespan,
)

# Create router with prefix for all booking endpoints
booking_router = APIRouter(
    prefix="/api/booking",
    tags=["booking"]
)

# Health check endpoint (no prefix needed)
@app.get("/health")
async def health_check():
    """Health check endpoint for AWS monitoring"""
    return {
        "status": "healthy",
        "service": "booking",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# Booking endpoints with router prefix
@booking_router.post("/book", response_model=BookingOut, status_code=201)
async def book_class(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user),
):
    """Book a class for the current user"""
    try:
        booking = await create_booking(db, UUID(current_user.id), booking_in)
        logger.info("Booking created successfully", booking_id=str(booking.id), user_id=current_user.id)
        return booking
    except (ValueError, BookingError) as e:
        logger.warning("Booking failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected booking error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.get("/my-bookings", response_model=List[BookingOut])
async def my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user),
):
    """Get all bookings for the current user"""
    try:
        # Update booking statuses based on current time
        await update_booking_statuses(db)
        
        bookings = await get_bookings_for_user(db, current_user.id)
        logger.info("Retrieved user bookings", user_id=current_user.id, count=len(bookings))
        return bookings
    except Exception as e:
        logger.error("Error retrieving user bookings", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.delete("/bookings/{booking_id}")
async def cancel_my_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user),
):
    """Cancel a booking for the current user"""
    try:
        await cancel_booking(db, booking_id, UUID(current_user.id))
        
        # Update booking statuses after cancellation
        await update_booking_statuses(db)
        
        logger.info("Booking cancelled successfully", booking_id=str(booking_id), user_id=current_user.id)
        return {"message": SUCCESS_MESSAGES["booking_cancelled"]}
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES["booking_not_found"])
    except Exception as e:
        logger.error("Error cancelling booking", error=str(e), booking_id=str(booking_id), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user),
):
    """Get a specific booking by ID"""
    try:
        booking = await get_booking_by_id(db, booking_id, UUID(current_user.id))
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES["booking_not_found"])
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving booking", error=str(e), booking_id=str(booking_id), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


# Admin endpoints
@booking_router.post("/admin/bookings", response_model=BookingOut, status_code=201)
async def admin_create_booking(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user),
):
    """Create a booking on behalf of a user (admin only)"""
    try:
        booking = await create_booking(db, UUID(admin.id), booking_in, admin_override=True)
        logger.info("Admin created booking", admin_id=admin.id, booking_id=str(booking.id))
        return booking
    except (ValueError, BookingError) as e:
        logger.warning("Admin booking failed", error=str(e), admin_id=admin.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected admin booking error", error=str(e), admin_id=admin.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.get("/admin/bookings", response_model=PaginatedResponse[BookingOut])
async def admin_get_all_bookings(
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    user_id_filter: Optional[str] = Query(None, alias="user_id", description="Filter by user ID"),
    teacher: Optional[str] = Query(None, description="Filter by teacher name"),
    class_name: Optional[str] = Query(None, description="Filter by class name"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(100, ge=1, le=1000, description="Number of items per page"),
):
    """Get all bookings with optional filtering and pagination (admin only)"""
    try:
        # Update booking statuses based on current time
        await update_booking_statuses(db)
        
        # Calculate offset from page and size
        offset = (page - 1) * size
        
        # Create filter params object
        filters = BookingFilterParams(
            date_from=date_from,
            date_to=date_to,
            user_id=user_id_filter,
            teacher=teacher,
            class_name=class_name,
            class_id=class_id,
            limit=size,
            offset=offset
        )
        
        logger.info("Admin request for bookings", 
                   admin_id=admin.id,
                   filters=filters.model_dump(),
                   teacher_filter=filters.teacher,
                   class_name_filter=filters.class_name)
        
        # Вызываем единую функцию с поддержкой всех фильтров
        logger.info("Calling get_all_bookings_with_summary with filters", 
                   teacher=filters.teacher, class_name=filters.class_name)
        
        bookings = await get_all_bookings_with_summary(
            db=db,
            limit=filters.limit,
            offset=filters.offset,
            date_from=str(filters.date_from) if filters.date_from else None,
            date_to=str(filters.date_to) if filters.date_to else None,
            user_id_filter=str(filters.user_id) if filters.user_id else None,
            teacher=filters.teacher,
            class_name=filters.class_name,
            class_id=str(filters.class_id) if filters.class_id else None
        )
        
        # For now, we'll use the length as total count
        # In a real implementation, you'd want to get the total count separately
        total_count = len(bookings)
        
        logger.info("Admin retrieved bookings", 
                   admin_id=admin.id, 
                   count=len(bookings),
                   had_teacher_filter=bool(filters.teacher),
                   had_class_name_filter=bool(filters.class_name))
        
        return create_paginated_response(bookings, total_count, page, size)
    except (ValueError, TypeError, ConnectionError) as e:
        logger.error("Error retrieving bookings for admin", 
                    error=str(e), 
                    error_type=type(e).__name__,
                    admin_id=admin.id,
                    filters=filters.model_dump() if 'filters' in locals() else {})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.get("/admin/statistics")
async def admin_statistics(
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user),
):
    """Get booking statistics in JSON format (admin only)"""
    try:
        stats = await get_booking_statistics(db)
        
        # Get most popular class name
        most_popular_class = None
        if stats["popular_classes"]:
            most_popular_class_id = stats["popular_classes"][0]["class_id"]
            try:
                class_info = await get_class_template_by_id(most_popular_class_id)
                if class_info:
                    most_popular_class = {
                        "id": most_popular_class_id,
                        "name": class_info.get("name", "Unknown Class")
                    }
            except (ValueError, TypeError, ConnectionError):
                most_popular_class = {
                    "id": most_popular_class_id,
                    "name": "Unknown Class"
                }
        
        response = {
            "bookings_today": stats["today_bookings"],
            "active_users": stats["active_users"],
            "revenue_month": 0.0,  # Placeholder - would need payment integration
            "total_bookings": stats["total_bookings"],
            "bookings_this_week": stats.get("week_bookings", 0),
            "most_popular_class": most_popular_class
        }
        
        logger.info("Admin statistics generated", admin_id=admin.id)
        return response
    except Exception as e:
        logger.error("Error generating admin statistics", error=str(e), admin_id=admin.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e


@booking_router.get("/admin/summary", response_class=HTMLResponse)
async def admin_summary(
    db: AsyncSession = Depends(get_db),
    admin: UserInToken = Depends(get_current_admin_user),
):
    """Get HTML summary of all bookings (admin only) - DEPRECATED, use /admin/statistics"""
    try:
        rows = await get_all_bookings_with_summary(db)
        
        html = (
            "<h2>Class Bookings Summary</h2>"
            "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr style='background-color: #f2f2f2;'>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>Date</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>Time</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>Class ID</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>User ID</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>Created</th>"
            "</tr></thead><tbody>")
        
        for row in rows:
            html += (
                f"<tr>"
                f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['date']}</td>"
                f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['start_time']}</td>"
                f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['class_id']}</td>"
                f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['user_id']}</td>"
                f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['created_at']}</td>"
                f"</tr>"
            )
        
        html += "</tbody></table>"
        
        logger.info("Admin summary generated", admin_id=admin.id)
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error("Error generating admin summary", error=str(e), admin_id=admin.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ERROR_MESSAGES["internal_error"]) from e

# Include the booking router
app.include_router(booking_router)
