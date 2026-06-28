#!/usr/bin/env python3
"""
seed.py — populates the DB with two fake family members.

Idempotent: skips a person if they already exist by name.
Run from backend/:
    python seed.py

Uses FAKE data only. Never put real medical or insurance data in a
learning prototype that has no real access controls.
"""
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models.person import FactType, MedicalFact, Person
from app.schemas.coordinator import (
    ContactCreate,
    FactCreate,
    InsuranceCreate,
    PersonCreate,
)
from app.services.person_service import (
    add_contact,
    add_fact,
    create_person,
    set_insurance,
)


def _backdate_fact(db, person: Person, value: str, days: int) -> None:
    """Set a fact's last_confirmed_at into the past, to demo the freshness signal."""
    fact = db.execute(
        select(MedicalFact).where(
            MedicalFact.person_id == person.id, MedicalFact.value == value
        )
    ).scalar_one()
    fact.last_confirmed_at = datetime.now(timezone.utc) - timedelta(days=days)
    db.commit()


def _get_or_create(db, full_name: str) -> tuple[Person, bool]:
    # Note: this assumes unique names within the seed data. If two family members
    # share a name, scalar_one_or_none() will raise MultipleResultsFound.
    # For now, acceptable for fixed fake data; a real setup would use stable IDs.
    existing = db.execute(
        select(Person).where(Person.full_name == full_name)
    ).scalar_one_or_none()
    if existing:
        return existing, False
    return create_person(db, PersonCreate(full_name=full_name)), True


def seed() -> None:
    db = SessionLocal()
    try:
        person, created = _get_or_create(db, "Priya Sharma")
        if not created:
            print(f"[SKIP] {person.full_name} already exists")
        else:
            for fact in [
                FactCreate(type=FactType.allergy, value="Penicillin"),
                FactCreate(type=FactType.allergy, value="Sulfa drugs"),
                FactCreate(type=FactType.medication, value="Metformin 500mg, twice daily"),
                FactCreate(type=FactType.medication, value="Lisinopril 10mg, once daily"),
                FactCreate(type=FactType.condition, value="Type 2 diabetes"),
                FactCreate(type=FactType.condition, value="Hypertension"),
            ]:
                add_fact(db, person, fact)
            # Backdate a couple of facts so the demo shows the freshness signal as
            # a fresh/stale MIX — one recently confirmed, one clearly outdated.
            _backdate_fact(db, person, "Sulfa drugs", days=21)        # "3 weeks ago"
            _backdate_fact(db, person, "Hypertension", days=240)      # "8 months ago" → stale

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
            set_insurance(
                db,
                person,
                InsuranceCreate(
                    provider="Star Health",
                    policy_number="SH-IND-4471902",
                    hospital_preference="Apollo Hospital, Jubilee Hills",
                    cashless=True,
                ),
            )
            print(f"[OK] Seeded: {person.full_name}")
            print(f"  Crisis URL -> http://localhost:8000/c/{person.crisis_slug}")

        person2, created2 = _get_or_create(db, "Arjun Sharma")
        if not created2:
            print(f"[SKIP] {person2.full_name} already exists")
        else:
            for fact in [
                FactCreate(type=FactType.allergy, value="Aspirin"),
                FactCreate(type=FactType.medication, value="Atorvastatin 20mg, once daily"),
                FactCreate(type=FactType.condition, value="Mild asthma"),
            ]:
                add_fact(db, person2, fact)

            add_contact(
                db,
                person2,
                ContactCreate(
                    name="Priya Sharma",
                    phone="+91 87654 32109",
                    relation="wife",
                    notify_order=1,
                ),
            )
            set_insurance(
                db,
                person2,
                InsuranceCreate(
                    provider="HDFC Ergo",
                    policy_number="HE-IND-8830245",
                    hospital_preference=None,
                    cashless=False,
                ),
            )
            print(f"[OK] Seeded: {person2.full_name}")
            print(f"  Crisis URL -> http://localhost:8000/c/{person2.crisis_slug}\n")

    except Exception as e:
        db.rollback()
        print(f"[FAILED] Seed failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
