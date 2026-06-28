#!/usr/bin/env python3
"""
seed.py — one-shot dev script to populate the DB with a single fake person.

Run from backend/:
    python seed.py

Uses FAKE data only. Never put real medical or insurance data in a
learning prototype that has no real access controls.
"""
import sys

from app.db import SessionLocal
from app.models.person import FactType
from app.schemas.coordinator import (
    ContactCreate,
    FactCreate,
    PersonCreate,
)
from app.services.person_service import add_contact, add_fact, create_person


def seed() -> None:
    db = SessionLocal()
    try:
        person = create_person(db, PersonCreate(full_name="Priya Sharma"))

        for fact in [
            FactCreate(type=FactType.allergy, value="Penicillin"),
            FactCreate(type=FactType.allergy, value="Sulfa drugs"),
            FactCreate(type=FactType.medication, value="Metformin 500mg, twice daily"),
            FactCreate(type=FactType.medication, value="Lisinopril 10mg, once daily"),
            FactCreate(type=FactType.condition, value="Type 2 diabetes"),
            FactCreate(type=FactType.condition, value="Hypertension"),
        ]:
            add_fact(db, person, fact)

        add_contact(
            db,
            person,
            ContactCreate(
                name="Rahul Sharma",
                phone="+91 98765 43210",
                relation="husband",
                notify_order=1,
            ),
        )

        print(f"\n[OK] Seeded: {person.full_name}")
        print(f"  Crisis URL -> http://localhost:8000/c/{person.crisis_slug}\n")

    except Exception as e:
        db.rollback()
        print(f"[FAILED] Seed failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
