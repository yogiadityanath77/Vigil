"""
crisis.py — public crisis routes.

GET /c/{slug} →  crisis page for the person with that slug

Security notes:
  - The slug is the only "auth" at this layer. It must be unguessable (generated
    with secrets.token_urlsafe) — that guarantee lives in coordinator creation.
  - We return a plain 404 on miss — no detail that distinguishes "slug not found"
    from "bad slug format." Don't give an attacker information about slug space.
  - selectinload eagerly fetches relationships in a single extra query each,
    avoiding the N+1 that lazy-loading would cause per fact/contact row.

The family roster is served from /coordinator/persons (the coordinator setup
surface), not from a public / route. See DECISIONS.md (D6) for the rationale.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.person import Person
from app.schemas.crisis import NotifiedContact, NotifyRequest, NotifyResponse
from app.services import person_service
from app.services.notify import build_notification_messages, maps_link
from app.services.transform import build_crisis_script, build_family_view

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_person_by_slug(db: Session, slug: str) -> Person:
    """Load a person by crisis slug with relationships, or 404 (no info leak)."""
    stmt = (
        select(Person)
        .where(Person.crisis_slug == slug)
        .options(
            selectinload(Person.medical_facts),
            selectinload(Person.emergency_contacts),
            selectinload(Person.insurance),
        )
    )
    person = db.execute(stmt).scalar_one_or_none()
    if person is None:
        raise HTTPException(status_code=404)
    return person


@router.get("/c/{slug}")
def crisis_page(slug: str, request: Request, db: Session = Depends(get_db)):
    person = _get_person_by_slug(db, slug)
    script = build_crisis_script(person, now=datetime.now(timezone.utc))
    return templates.TemplateResponse(
        request=request,
        name="crisis.html",
        context={"script": script, "slug": slug},
    )


@router.get("/c/{slug}/family")
def family_page(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    The richer 'for family' tier. Reached by anyone holding the slug — the tiering
    is in *presentation*, not enforcement (prototype-spec: 'shown, not secured').
    Real access-gating (per-tier tokens) is a later slice.
    """
    person = _get_person_by_slug(db, slug)
    view = build_family_view(person, now=datetime.now(timezone.utc))
    return templates.TemplateResponse(
        request=request,
        name="family.html",
        context={"view": view, "slug": slug},
    )


@router.post("/c/{slug}/notify", response_model=NotifyResponse)
def notify_family(
    slug: str, data: NotifyRequest, db: Session = Depends(get_db)
) -> NotifyResponse:
    """
    Responder-triggered family alert. Simulated send: record the audit event and
    return the messages that *would* be dispatched to each contact. No real SMS.

    Lives on the public crisis surface (not coordinator) because the responder
    in the room triggers it. The slug is the only gate, same as the page itself.
    """
    person = _get_person_by_slug(db, slug)

    event = person_service.record_notification(db, person, data.lat, data.lng)

    map_link = maps_link(data.lat, data.lng)
    # The "Details:" secure link points at the richer family-tier view (Slice 9),
    # keeping the sensitive detail out of the message body itself.
    secure_link = person_service.family_url(slug)

    messages = build_notification_messages(
        person_name=person.full_name,
        contacts=person.emergency_contacts,
        secure_link=secure_link,
        map_link=map_link,
    )

    return NotifyResponse(
        person_name=person.full_name,
        triggered_at=event.triggered_at,
        location_shared=map_link is not None,
        map_link=map_link,
        secure_link=secure_link,
        contacts=[
            NotifiedContact(
                name=m.contact_name,
                phone=m.contact_phone,
                relation=m.contact_relation,
                message=m.body,
            )
            for m in messages
        ],
    )
