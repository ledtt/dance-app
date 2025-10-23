# tests/unit/booking/test_booking_crud.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

# Mock all database and external dependencies before importing
with patch('services.booking.src.db.get_db'), \
     patch('services.booking.src.db.engine'), \
     patch('sqlalchemy.ext.asyncio.create_async_engine'), \
     patch('sqlalchemy.ext.asyncio.async_sessionmaker'), \
     patch('services.booking.src.external_schedule.get_class_template_by_id'), \
     patch('services.booking.src.external_schedule.get_user_by_id'), \
     patch('httpx.AsyncClient'):
    
    from services.booking.src.crud import (
        create_booking,
        get_bookings_for_user,
        get_all_bookings_with_summary,
        _enrich_bookings,
        cancel_booking,
        get_booking_by_id
    )
    from services.booking.src.schemas import BookingCreate
    from services.booking.src.models import Booking
    from shared.exceptions import BookingError, ResourceNotFoundError, CapacityExceededError

# --- Fixtures ---

@pytest.fixture
def mock_db() -> AsyncMock:
    """Provides a reusable mock for the AsyncSession."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def sample_user_id() -> str:
    """Provides a sample user ID."""
    return str(uuid4())

@pytest.fixture
def sample_class_id() -> str:
    """Provides a sample class ID."""
    return str(uuid4())

@pytest.fixture
def sample_booking_create(sample_class_id: str) -> BookingCreate:
    """Provides a sample valid BookingCreate schema object."""
    return BookingCreate(
        class_id=sample_class_id,
        date=date.today()
    )

@pytest.fixture
def mock_class_template() -> dict:
    """Provides a mock response from the schedule service."""
    return {
        "id": str(uuid4()),
        "name": "Salsa Class",
        "teacher": "John Doe",
        "weekday": date.today().isoweekday(), # Ensures weekday check passes
        "start_time": "19:00",
        "capacity": 10
    }

# --- Unit Tests for crud.py ---

@pytest.mark.asyncio
@patch('services.booking.src.crud.get_class_template_by_id')
async def test_create_booking_success(mock_get_template: AsyncMock, mock_db: AsyncMock, sample_user_id: str, sample_booking_create: BookingCreate, mock_class_template: dict):
    """Test successful booking creation."""
    # Arrange
    mock_get_template.return_value = mock_class_template
    
    # Mock database count checks to return object with attributes
    mock_counts = MagicMock()
    mock_counts.current_bookings = 0
    mock_counts.user_has_booking = 0
    mock_result = MagicMock()
    mock_result.one.return_value = mock_counts
    mock_db.execute.return_value = mock_result

    # Act
    new_booking = await create_booking(mock_db, uuid4(), sample_booking_create)

    # Assert
    assert new_booking.class_id == sample_booking_create.class_id
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()

@pytest.mark.asyncio
@patch('services.booking.src.crud.get_class_template_by_id')
async def test_create_booking_capacity_exceeded(mock_get_template: AsyncMock, mock_db: AsyncMock, sample_user_id: str, sample_booking_create: BookingCreate, mock_class_template: dict):
    """Test that booking fails when class capacity is exceeded."""
    # Arrange
    mock_get_template.return_value = mock_class_template
    
    # Mock database count to show class is full
    mock_counts = MagicMock()
    mock_counts.current_bookings = 10
    mock_counts.user_has_booking = 0
    mock_result = MagicMock()
    mock_result.one.return_value = mock_counts
    mock_db.execute.return_value = mock_result

    # Act & Assert
    with pytest.raises(CapacityExceededError):
        await create_booking(mock_db, uuid4(), sample_booking_create)
    
    mock_db.add.assert_not_called()

@pytest.mark.asyncio
@patch('services.booking.src.crud.get_class_template_by_id')
async def test_create_booking_already_booked(mock_get_template: AsyncMock, mock_db: AsyncMock, sample_user_id: str, sample_booking_create: BookingCreate, mock_class_template: dict):
    """Test that booking fails if the user is already booked for the class."""
    # Arrange
    mock_get_template.return_value = mock_class_template
    
    # Mock database count to show user already has a booking
    mock_counts = MagicMock()
    mock_counts.current_bookings = 5
    mock_counts.user_has_booking = 1
    mock_result = MagicMock()
    mock_result.one.return_value = mock_counts
    mock_db.execute.return_value = mock_result

    # Act & Assert
    with pytest.raises(BookingError) as exc_info:
        await create_booking(mock_db, uuid4(), sample_booking_create)
    
    assert "already booked" in str(exc_info.value)
    mock_db.add.assert_not_called()

@pytest.mark.asyncio
@patch('services.booking.src.crud.get_class_template_by_id')
async def test_create_booking_class_not_found(mock_get_template: AsyncMock, mock_db: AsyncMock, sample_user_id: str, sample_booking_create: BookingCreate):
    """Test that booking fails if the class template is not found."""
    # Arrange
    mock_get_template.return_value = None

    # Act & Assert
    with pytest.raises(ResourceNotFoundError):
        await create_booking(mock_db, uuid4(), sample_booking_create)

@pytest.mark.asyncio
async def test_enrich_bookings(mock_db: AsyncMock):
    """Test the internal _enrich_bookings helper function."""
    # Arrange
    user_id_1 = str(uuid4())
    class_id_1 = str(uuid4())
    
    bookings = [
        Booking(id=uuid4(), user_id=user_id_1, class_id=class_id_1, date=date.today(), start_time=datetime.now(), created_at=datetime.now())
    ]
    
    mock_user_data = {"id": user_id_1, "name": "Test User"}
    mock_class_data = {"id": class_id_1, "name": "Test Class"}
    
    with patch('services.booking.src.crud.get_user_by_id', return_value=mock_user_data) as mock_get_user, \
         patch('services.booking.src.crud.get_class_template_by_id', return_value=mock_class_data) as mock_get_class:
        
        # Act
        enriched_result = await _enrich_bookings(bookings)
        
        # Assert
        assert len(enriched_result) == 1
        assert enriched_result[0]['user']['name'] == "Test User"
        assert enriched_result[0]['class_info']['name'] == "Test Class"
        mock_get_user.assert_awaited_once_with(user_id_1)
        mock_get_class.assert_awaited_once_with(class_id_1)

@pytest.mark.asyncio
async def test_cancel_booking_success(mock_db: AsyncMock):
    """Test successful cancellation of a booking."""
    booking_id = uuid4()
    user_id = uuid4()
    
    # Arrange: Mock the database to return a booking to be cancelled
    mock_booking = Booking(id=booking_id, user_id=user_id, status='active')
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_booking
    mock_db.execute.return_value = mock_result
    
    # Act
    await cancel_booking(mock_db, booking_id, user_id)
    
    # Assert
    assert mock_booking.status == 'cancelled'
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_cancel_booking_not_found(mock_db: AsyncMock):
    """Test that cancelling a non-existent booking raises ResourceNotFoundError."""
    booking_id = uuid4()
    user_id = uuid4()
    
    # Arrange: Mock the database to return None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act & Assert
    with pytest.raises(ResourceNotFoundError):
        await cancel_booking(mock_db, booking_id, user_id)
    
    mock_db.delete.assert_not_called()