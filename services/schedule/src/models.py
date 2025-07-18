import uuid
import datetime  # импорт целиком

from sqlalchemy import String, Time, Integer, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0-style базовый класс.
    Все модели наследуют DeclarativeBase,
    которое понимается Pylance и позволяет аннотировать поля.
    """


class ClassTemplate(Base):
    __tablename__ = "class_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    teacher: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    weekday: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    time: Mapped[datetime.time] = mapped_column(  # <-- вот тут
        Time,
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ClassTemplate id={self.id} name='{self.name}' teacher='{self.teacher}'>"
