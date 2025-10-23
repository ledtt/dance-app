# services/booking/models.py

import uuid
import datetime

from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0-style base class.
    All models inherit from DeclarativeBase,
    which is understood by Pylance and allows field annotation.
    """


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
    )

    start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='active',
        index=True,
    )



    def __repr__(self) -> str:
        return f'<Booking id={self.id} user_id={self.user_id} class_id={self.class_id}>'
