"""
coordinator.py — write API for persons, medical facts, and emergency contacts.

NOTE: No authentication. These endpoints are intentionally local-only for the
prototype. Auth + tiered access is a later slice.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.qr import build_qr_svg

from app.db import get_db
from app.models.person import MedicalFact, EmergencyContact, Person
from app.schemas.coordinator import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
    FactCreate,
    FactRead,
    FactUpdate,
    InsuranceCreate,
    InsuranceRead,
    InsuranceUpdate,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from app.services import person_service

router = APIRouter(prefix="/coordinator", tags=["coordinator"])
templates = Jinja2Templates(directory="app/templates")


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


# ── HTML Coordinator Pages ──────────────────────────────────────────────────────

@router.get("/family")
def family_list_html(request: Request, db: Session = Depends(get_db)):
    """Renders the family roster (HTML coordinator surface, not public crisis page)."""
    persons = db.execute(
        select(Person).order_by(Person.full_name)
    ).scalars().all()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"persons": persons}
    )


# ── QR code (coordinator setup surface; encodes the public crisis URL) ────────

@router.get("/persons/{person_id}/qr.svg")
def person_qr_svg(person_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    """Raw SVG QR encoding this person's crisis URL — embedded by the card page."""
    person = _get_person_or_404(db, person_id)
    svg = build_qr_svg(person_service.crisis_url(person.crisis_slug))
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/persons/{person_id}/qr")
def person_qr_card(
    person_id: uuid.UUID, request: Request, db: Session = Depends(get_db)
):
    """Print-friendly QR card: the 'MEDICAL EMERGENCY — SCAN ME' physical layer."""
    person = _get_person_or_404(db, person_id)
    url = person_service.crisis_url(person.crisis_slug)
    return templates.TemplateResponse(
        request=request,
        name="qr_card.html",
        context={
            "person": person,
            "crisis_url": url,
            # Inlined (not an <img src>) so the card prints as one self-contained page.
            "qr_svg": build_qr_svg(url),
        },
    )


# ── Person endpoints ──────────────────────────────────────────────────────────

@router.post("/persons", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(data: PersonCreate, db: Session = Depends(get_db)) -> Person:
    return person_service.create_person(db, data)


@router.get("/persons", response_model=list[PersonRead])
def list_persons(db: Session = Depends(get_db)) -> list[Person]:
    persons = db.execute(
        select(Person).order_by(Person.full_name)
    ).scalars().all()
    return persons


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


@router.post("/persons/{person_id}/facts/{fact_id}/confirm", response_model=FactRead)
def confirm_fact(
    person_id: uuid.UUID, fact_id: uuid.UUID, db: Session = Depends(get_db)
) -> MedicalFact:
    """Re-affirm a fact is still accurate (bumps last_confirmed_at to now)."""
    _get_person_or_404(db, person_id)
    fact = _get_fact_or_404(db, fact_id, person_id)
    return person_service.confirm_fact(db, fact)


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


# ── Insurance endpoints (one-to-one; PUT upsert + PATCH, see D7) ───────────────

@router.get("/persons/{person_id}/insurance", response_model=InsuranceRead)
def get_insurance(person_id: uuid.UUID, db: Session = Depends(get_db)):
    person = _get_person_or_404(db, person_id)
    insurance = person_service.get_insurance(db, person)
    if insurance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No insurance on file"
        )
    return insurance


@router.put("/persons/{person_id}/insurance", response_model=InsuranceRead)
def put_insurance(
    person_id: uuid.UUID, data: InsuranceCreate, db: Session = Depends(get_db)
):
    """Create-or-replace the single insurance row for this person."""
    person = _get_person_or_404(db, person_id)
    return person_service.set_insurance(db, person, data)


@router.patch("/persons/{person_id}/insurance", response_model=InsuranceRead)
def patch_insurance(
    person_id: uuid.UUID, data: InsuranceUpdate, db: Session = Depends(get_db)
):
    person = _get_person_or_404(db, person_id)
    insurance = person_service.get_insurance(db, person)
    if insurance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No insurance on file"
        )
    return person_service.update_insurance(db, insurance, data)
