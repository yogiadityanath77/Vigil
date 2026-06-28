"""
crisis.py — the one public route for slice 1.

GET /c/{slug}  →  renders the crisis page for the person with that slug.

Security notes:
  - The slug is the only "auth" at this layer. It must be unguessable (generated
    with secrets.token_urlsafe) — that guarantee lives in seed.py / coordinator
    creation, not here.
  - We return a plain 404 on miss — no detail that distinguishes "slug not found"
    from "bad slug format." Don't give an attacker information about slug space.
  - selectinload eagerly fetches relationships in a single extra query each,
    avoiding the N+1 that lazy-loading would cause per fact/contact row.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.person import Person
from app.services.transform import build_crisis_script

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/c/{slug}")
def crisis_page(slug: str, request: Request, db: Session = Depends(get_db)):
    stmt = (
        select(Person)
        .where(Person.crisis_slug == slug)
        .options(
            selectinload(Person.medical_facts),
            selectinload(Person.emergency_contacts),
        )
    )
    person = db.execute(stmt).scalar_one_or_none()

    if person is None:
        raise HTTPException(status_code=404)

    script = build_crisis_script(person)
    return templates.TemplateResponse(
    request=request, name="crisis.html", context={"script": script}
)
