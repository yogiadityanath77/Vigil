"""
Pydantic schemas for the coordinator write API (Slice 3).

Separate from any future public/crisis-side read schemas.
No auth fields here — this API is local-only for now.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.models.person import FactType


# ── Fact ────────────────────────────────────────────────────────────────────

class FactCreate(BaseModel):
    type: FactType
    value: str

    @field_validator("value")
    @classmethod
    def value_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("value must not be blank")
        return v.strip()


class FactUpdate(BaseModel):
    type: FactType | None = None
    value: str | None = None

    @field_validator("value")
    @classmethod
    def value_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("value must not be blank")
        return v.strip() if v is not None else v

    @model_validator(mode="after")
    def at_least_one_field(self) -> FactUpdate:
        if self.type is None and self.value is None:
            raise ValueError("at least one of type or value must be provided")
        return self


class FactRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: FactType
    value: str
    created_at: datetime


# ── Contact ─────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str
    phone: str
    relation: str | None = None
    notify_order: int = 1

    @field_validator("name", "phone")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("notify_order")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("notify_order must be >= 1")
        return v


class ContactUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    relation: str | None = None
    notify_order: int | None = None

    @field_validator("name", "phone")
    @classmethod
    def not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("must not be blank")
        return v.strip() if v is not None else v

    @field_validator("notify_order")
    @classmethod
    def positive(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("notify_order must be >= 1")
        return v

    @model_validator(mode="after")
    def at_least_one_field(self) -> ContactUpdate:
        if all(f is None for f in (self.name, self.phone, self.relation, self.notify_order)):
            raise ValueError("at least one field must be provided")
        return self


class ContactRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    phone: str
    relation: str | None
    notify_order: int
    created_at: datetime


# ── Person ───────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name must not be blank")
        return v.strip()


class PersonUpdate(BaseModel):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name must not be blank")
        return v.strip()


class PersonRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    crisis_slug: str
    created_at: datetime
    medical_facts: list[FactRead]
    emergency_contacts: list[ContactRead]
