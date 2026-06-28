"""
ORM models: Person, MedicalFact, EmergencyContact.

SQLAlchemy 2.0 style throughout:
  - Mapped[T] for typed column declarations
  - mapped_column() instead of legacy Column()
  - relationship() with back_populates for explicit bidirectionality

Slice 1 only — date_of_birth, blood_group, last_confirmed_at, and all
access/audit/insurance/notification tables are intentionally absent.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class FactType(str, enum.Enum):
    allergy = "allergy"
    medication = "medication"
    condition = "condition"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Person(Base):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    # crisis_slug: unguessable public identifier used in the crisis URL.
    # Generated with secrets.token_urlsafe — NOT random.randint, NOT sequential.
    # This value is permanent once a QR code is printed (slice 6).
    crisis_slug: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    medical_facts: Mapped[list[MedicalFact]] = relationship(
        "MedicalFact", back_populates="person", cascade="all, delete-orphan"
    )
    emergency_contacts: Mapped[list[EmergencyContact]] = relationship(
        "EmergencyContact", back_populates="person", cascade="all, delete-orphan"
    )


class MedicalFact(Base):
    __tablename__ = "medical_fact"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[FactType] = mapped_column(SAEnum(FactType), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    person: Mapped[Person] = relationship("Person", back_populates="medical_facts")


class EmergencyContact(Base):
    __tablename__ = "emergency_contact"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    # Named `relation` (not `relationship`) to avoid shadowing SQLAlchemy's
    # `relationship()` function, which is also imported into this module.
    relation: Mapped[str | None] = mapped_column(Text, nullable=True)
    notify_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    person: Mapped[Person] = relationship(
        "Person", back_populates="emergency_contacts"
    )
