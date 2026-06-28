"""
test_coordinator.py — integration tests for the coordinator write API.

These tests hit the real FastAPI app via TestClient with a real DB session
(no mocking). They use pytest fixtures to set up and tear down data.

Requires DATABASE_URL to be set (same .env as the app).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.main import app
from app.models.person import FactType
from app.schemas.coordinator import ContactCreate, FactCreate, PersonCreate
from app.services.person_service import add_contact, add_fact, create_person

client = TestClient(app)


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def person(db: Session):
    p = create_person(db, PersonCreate(full_name="Test User"))
    yield p
    # clean up — cascades remove facts + contacts
    db.delete(p)
    db.commit()


# ── Person ────────────────────────────────────────────────────────────────────

class TestPersonEndpoints:

    def test_create_person_returns_201(self):
        resp = client.post("/coordinator/persons", json={"full_name": "Jane Doe"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["full_name"] == "Jane Doe"
        assert "crisis_slug" in body
        assert "id" in body
        # clean up
        with SessionLocal() as db:
            from app.services.person_service import get_person
            import uuid
            p = get_person(db, uuid.UUID(body["id"]))
            if p:
                db.delete(p)
                db.commit()

    def test_create_person_blank_name_returns_422(self):
        resp = client.post("/coordinator/persons", json={"full_name": "   "})
        assert resp.status_code == 422

    def test_get_person(self, person):
        resp = client.get(f"/coordinator/persons/{person.id}")
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Test User"

    def test_get_unknown_person_returns_404(self):
        import uuid
        resp = client.get(f"/coordinator/persons/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_update_person_name(self, person):
        resp = client.patch(
            f"/coordinator/persons/{person.id}", json={"full_name": "Updated Name"}
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_crisis_slug_not_in_create_input(self):
        """Slug must be server-generated; input schema has no slug field."""
        from app.schemas.coordinator import PersonCreate
        import pydantic
        # If the field existed, model_fields would include it; it must not.
        assert "crisis_slug" not in PersonCreate.model_fields


# ── Medical facts ─────────────────────────────────────────────────────────────

class TestFactEndpoints:

    def test_add_fact(self, person):
        resp = client.post(
            f"/coordinator/persons/{person.id}/facts",
            json={"type": "allergy", "value": "Aspirin"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["type"] == "allergy"
        assert body["value"] == "Aspirin"

    def test_add_fact_blank_value_returns_422(self, person):
        resp = client.post(
            f"/coordinator/persons/{person.id}/facts",
            json={"type": "allergy", "value": "  "},
        )
        assert resp.status_code == 422

    def test_update_fact(self, person, db):
        fact = add_fact(db, person, FactCreate(type=FactType.allergy, value="Aspirin"))
        resp = client.patch(
            f"/coordinator/persons/{person.id}/facts/{fact.id}",
            json={"value": "Ibuprofen"},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == "Ibuprofen"

    def test_update_fact_empty_body_returns_422(self, person, db):
        fact = add_fact(db, person, FactCreate(type=FactType.allergy, value="X"))
        resp = client.patch(
            f"/coordinator/persons/{person.id}/facts/{fact.id}", json={}
        )
        assert resp.status_code == 422

    def test_delete_fact(self, person, db):
        fact = add_fact(db, person, FactCreate(type=FactType.condition, value="Asthma"))
        resp = client.delete(f"/coordinator/persons/{person.id}/facts/{fact.id}")
        assert resp.status_code == 204
        # confirm gone
        resp2 = client.patch(
            f"/coordinator/persons/{person.id}/facts/{fact.id}", json={"value": "x"}
        )
        assert resp2.status_code == 404

    def test_fact_belongs_to_person(self, person, db):
        """A fact from another person must not be reachable via this person's URL."""
        import uuid
        other = create_person(db, PersonCreate(full_name="Other"))
        fact = add_fact(db, other, FactCreate(type=FactType.allergy, value="X"))
        resp = client.patch(
            f"/coordinator/persons/{person.id}/facts/{fact.id}", json={"value": "Y"}
        )
        assert resp.status_code == 404
        db.delete(other)
        db.commit()


# ── Emergency contacts ────────────────────────────────────────────────────────

class TestContactEndpoints:

    def test_add_contact(self, person):
        resp = client.post(
            f"/coordinator/persons/{person.id}/contacts",
            json={"name": "Alice", "phone": "+91 99999 00000", "notify_order": 1},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Alice"
        assert body["notify_order"] == 1

    def test_update_contact(self, person, db):
        contact = add_contact(
            db, person, ContactCreate(name="Bob", phone="+91 11111 22222")
        )
        resp = client.patch(
            f"/coordinator/persons/{person.id}/contacts/{contact.id}",
            json={"phone": "+91 33333 44444"},
        )
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+91 33333 44444"

    def test_delete_contact(self, person, db):
        contact = add_contact(
            db, person, ContactCreate(name="Carol", phone="+91 55555 66666")
        )
        resp = client.delete(
            f"/coordinator/persons/{person.id}/contacts/{contact.id}"
        )
        assert resp.status_code == 204

    def test_contact_isolation(self, person, db):
        """Contact from another person must not be editable via this person's URL."""
        other = create_person(db, PersonCreate(full_name="Other"))
        contact = add_contact(db, other, ContactCreate(name="X", phone="+91 00000 00000"))
        resp = client.patch(
            f"/coordinator/persons/{person.id}/contacts/{contact.id}",
            json={"name": "Hacked"},
        )
        assert resp.status_code == 404
        db.delete(other)
        db.commit()
