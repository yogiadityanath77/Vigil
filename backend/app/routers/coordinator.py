"""
coordinator.py — write API for persons, medical facts, and emergency contacts.

NOTE: No authentication. These endpoints are intentionally local-only for the
prototype. Auth + tiered access is a later slice.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.person import MedicalFact, EmergencyContact, Person
from app.schemas.coordinator import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
    FactCreate,
    FactRead,
    FactUpdate,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from app.services import person_service

router = APIRouter(prefix="/coordinator", tags=["coordinator"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_person_or_404(db: Session, person_id: uuid.UUID) -> Person:
    person = person_service.get_person(db, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return person


def _get_fact_or_404(db: Session, fact_id: uuid.UUID, person_id: uuid.UUID) -> MedicalFact:
    fact = person_service.get_fact(db, fact_id, person_id)
    if fact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found")
    return fact


def _get_contact_or_404(
    db: Session, contact_id: uuid.UUID, person_id: uuid.UUID
) -> EmergencyContact:
    contact = person_service.get_contact(db, contact_id, person_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


# ── Person endpoints ──────────────────────────────────────────────────────────

@router.post("/persons", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(data: PersonCreate, db: Session = Depends(get_db)) -> Person:
    return person_service.create_person(db, data)


@router.get("/persons/{person_id}", response_model=PersonRead)
def get_person(person_id: uuid.UUID, db: Session = Depends(get_db)) -> Person:
    return _get_person_or_404(db, person_id)


@router.patch("/persons/{person_id}", response_model=PersonRead)
def update_person(
    person_id: uuid.UUID, data: PersonUpdate, db: Session = Depends(get_db)
) -> Person:
    person = _get_person_or_404(db, person_id)
    return person_service.update_person(db, person, data)


# ── Medical fact endpoints ────────────────────────────────────────────────────

@router.post(
    "/persons/{person_id}/facts",
    response_model=FactRead,
    status_code=status.HTTP_201_CREATED,
)
def add_fact(
    person_id: uuid.UUID, data: FactCreate, db: Session = Depends(get_db)
) -> MedicalFact:
    person = _get_person_or_404(db, person_id)
    return person_service.add_fact(db, person, data)


@router.patch("/persons/{person_id}/facts/{fact_id}", response_model=FactRead)
def update_fact(
    person_id: uuid.UUID,
    fact_id: uuid.UUID,
    data: FactUpdate,
    db: Session = Depends(get_db),
) -> MedicalFact:
    _get_person_or_404(db, person_id)
    fact = _get_fact_or_404(db, fact_id, person_id)
    return person_service.update_fact(db, fact, data)


@router.delete(
    "/persons/{person_id}/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_fact(
    person_id: uuid.UUID, fact_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    _get_person_or_404(db, person_id)
    fact = _get_fact_or_404(db, fact_id, person_id)
    person_service.delete_fact(db, fact)


# ── Emergency contact endpoints ───────────────────────────────────────────────

@router.post(
    "/persons/{person_id}/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def add_contact(
    person_id: uuid.UUID, data: ContactCreate, db: Session = Depends(get_db)
) -> EmergencyContact:
    person = _get_person_or_404(db, person_id)
    return person_service.add_contact(db, person, data)


@router.patch("/persons/{person_id}/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    person_id: uuid.UUID,
    contact_id: uuid.UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
) -> EmergencyContact:
    _get_person_or_404(db, person_id)
    contact = _get_contact_or_404(db, contact_id, person_id)
    return person_service.update_contact(db, contact, data)


@router.delete(
    "/persons/{person_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_contact(
    person_id: uuid.UUID, contact_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    _get_person_or_404(db, person_id)
    contact = _get_contact_or_404(db, contact_id, person_id)
    person_service.delete_contact(db, contact)
