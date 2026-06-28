"""
test_crisis.py — integration tests for the public crisis routes (Slice 4).

Tests individual crisis pages. Family list is tested in test_coordinator.py
(it lives at /coordinator/persons, the coordinator setup surface).
Requires DATABASE_URL to be set (same .env as the app).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.main import app
from app.schemas.coordinator import ContactCreate, FactCreate, PersonCreate
from app.models.person import FactType
from app.services.person_service import add_contact, add_fact, create_person

client = TestClient(app)


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def two_persons(db: Session):
    p1 = create_person(db, PersonCreate(full_name="Test Alice"))
    add_fact(db, p1, FactCreate(type=FactType.allergy, value="Penicillin"))
    add_contact(db, p1, ContactCreate(name="Bob", phone="111", relation="spouse", notify_order=1))

    p2 = create_person(db, PersonCreate(full_name="Test Bob"))
    add_fact(db, p2, FactCreate(type=FactType.condition, value="Asthma"))
    add_contact(db, p2, ContactCreate(name="Alice", phone="222", relation="spouse", notify_order=1))

    yield p1, p2

    db.delete(p1)
    db.delete(p2)
    db.commit()


def test_crisis_page_renders_for_first_person(two_persons):
    p1, _ = two_persons
    resp = client.get(f"/c/{p1.crisis_slug}")
    assert resp.status_code == 200
    assert p1.full_name in resp.text
    assert "Penicillin" in resp.text


def test_crisis_page_renders_for_second_person(two_persons):
    _, p2 = two_persons
    resp = client.get(f"/c/{p2.crisis_slug}")
    assert resp.status_code == 200
    assert p2.full_name in resp.text
    assert "Asthma" in resp.text


def test_crisis_page_404_on_unknown_slug():
    resp = client.get("/c/doesnotexist000000")
    assert resp.status_code == 404
