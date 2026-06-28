"""
person_service.py — thin service layer for Person CRUD.

Centralises crisis_slug generation here so it is never client-supplied
and never constructed inline elsewhere (seed.py, tests, etc. call this).
"""
from __future__ import annotations

import secrets
import uuid

from sqlalchemy.orm import Session

from app.config import settings

from app.models.person import (
    EmergencyContact,
    FactType,
    Insurance,
    MedicalFact,
    NotificationEvent,
    Person,
)
from app.schemas.coordinator import (
    ContactCreate,
    ContactUpdate,
    FactCreate,
    FactUpdate,
    InsuranceCreate,
    InsuranceUpdate,
    PersonCreate,
    PersonUpdate,
)


def generate_crisis_slug() -> str:
    return secrets.token_urlsafe(8)


def crisis_url(slug: str) -> str:
    """
    Build the full public crisis URL for a slug. Centralized here (next to slug
    generation) so the `{base_url}/c/{slug}` shape is never hand-assembled — the
    QR encodes exactly this, and the route is /c/{slug} in routers/crisis.py.
    """
    return f"{settings.base_url.rstrip('/')}/c/{slug}"


# ── Person ───────────────────────────────────────────────────────────────────

def create_person(db: Session, data: PersonCreate) -> Person:
    person = Person(full_name=data.full_name, crisis_slug=generate_crisis_slug())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def get_person(db: Session, person_id: uuid.UUID) -> Person | None:
    return db.get(Person, person_id)


def update_person(db: Session, person: Person, data: PersonUpdate) -> Person:
    person.full_name = data.full_name
    db.commit()
    db.refresh(person)
    return person


# ── Medical facts ─────────────────────────────────────────────────────────────

def add_fact(db: Session, person: Person, data: FactCreate) -> MedicalFact:
    fact = MedicalFact(person_id=person.id, type=data.type, value=data.value)
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact


def get_fact(db: Session, fact_id: uuid.UUID, person_id: uuid.UUID) -> MedicalFact | None:
    fact = db.get(MedicalFact, fact_id)
    if fact is None or fact.person_id != person_id:
        return None
    return fact


def update_fact(db: Session, fact: MedicalFact, data: FactUpdate) -> MedicalFact:
    if data.type is not None:
        fact.type = data.type
    if data.value is not None:
        fact.value = data.value
    db.commit()
    db.refresh(fact)
    return fact


def delete_fact(db: Session, fact: MedicalFact) -> None:
    db.delete(fact)
    db.commit()


# ── Emergency contacts ────────────────────────────────────────────────────────

def add_contact(db: Session, person: Person, data: ContactCreate) -> EmergencyContact:
    contact = EmergencyContact(
        person_id=person.id,
        name=data.name,
        phone=data.phone,
        relation=data.relation,
        notify_order=data.notify_order,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contact(
    db: Session, contact_id: uuid.UUID, person_id: uuid.UUID
) -> EmergencyContact | None:
    contact = db.get(EmergencyContact, contact_id)
    if contact is None or contact.person_id != person_id:
        return None
    return contact


def update_contact(db: Session, contact: EmergencyContact, data: ContactUpdate) -> EmergencyContact:
    if data.name is not None:
        contact.name = data.name
    if data.phone is not None:
        contact.phone = data.phone
    if data.relation is not None:
        contact.relation = data.relation
    if data.notify_order is not None:
        contact.notify_order = data.notify_order
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact: EmergencyContact) -> None:
    db.delete(contact)
    db.commit()


# ── Insurance (one-to-one) ────────────────────────────────────────────────────

def get_insurance(db: Session, person: Person) -> Insurance | None:
    return person.insurance


def set_insurance(db: Session, person: Person, data: InsuranceCreate) -> Insurance:
    """
    Upsert the single insurance row (backs PUT). If one exists, replace every
    field; otherwise create it. Identity-preserving on update so a future
    `last_confirmed_at` (slice 8) survives — consistent with the spirit of D5.
    """
    insurance = person.insurance
    if insurance is None:
        insurance = Insurance(person_id=person.id)
        db.add(insurance)
    insurance.provider = data.provider
    insurance.policy_number = data.policy_number
    insurance.hospital_preference = data.hospital_preference
    insurance.cashless = data.cashless
    db.commit()
    db.refresh(insurance)
    return insurance


def update_insurance(db: Session, insurance: Insurance, data: InsuranceUpdate) -> Insurance:
    if data.provider is not None:
        insurance.provider = data.provider
    if data.policy_number is not None:
        insurance.policy_number = data.policy_number
    if data.hospital_preference is not None:
        insurance.hospital_preference = data.hospital_preference
    if data.cashless is not None:
        insurance.cashless = data.cashless
    db.commit()
    db.refresh(insurance)
    return insurance


# ── Notification events (simulated "Notify family") ───────────────────────────

def record_notification(
    db: Session,
    person: Person,
    lat: float | None,
    lng: float | None,
) -> NotificationEvent:
    """Persist the audit row for one notify tap. status is always 'sent' (simulated)."""
    event = NotificationEvent(
        person_id=person.id, location_lat=lat, location_lng=lng, status="sent"
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
