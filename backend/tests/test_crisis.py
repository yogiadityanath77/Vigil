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
from app.schemas.coordinator import (
    ContactCreate,
    FactCreate,
    InsuranceCreate,
    PersonCreate,
)
from app.models.person import FactType
from app.services.person_service import (
    add_contact,
    add_fact,
    create_person,
    set_insurance,
)

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
    set_insurance(
        db,
        p1,
        InsuranceCreate(provider="Star Health", policy_number="SH-CRISIS-1", cashless=True),
    )

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


def test_crisis_page_renders_guard_rail_for_insured_person(two_persons):
    p1, _ = two_persons
    resp = client.get(f"/c/{p1.crisis_slug}")
    assert resp.status_code == 200
    # The signature money guard-rail line + the policy to show at the desk.
    # (The apostrophe in "don't" is HTML-escaped, so match on "pay upfront".)
    assert "pay upfront" in resp.text.lower()
    assert "SH-CRISIS-1" in resp.text


def test_crisis_page_guard_rail_falls_back_when_no_insurance(two_persons):
    """The Step 3 header always renders (no numbering gap); only its body falls
    back to a 'no insurance' note when there's no insurance row."""
    _, p2 = two_persons  # p2 has no insurance row
    resp = client.get(f"/c/{p2.crisis_slug}")
    assert resp.status_code == 200
    assert "Before you pay" in resp.text          # step still present
    assert "No insurance details on file" in resp.text  # fallback body
    assert "Step 4" in resp.text                  # numbering stays contiguous


def test_crisis_page_404_on_unknown_slug():
    resp = client.get("/c/doesnotexist000000")
    assert resp.status_code == 404


def test_crisis_page_has_family_hint(two_persons):
    p1, _ = two_persons
    resp = client.get(f"/c/{p1.crisis_slug}")
    assert resp.status_code == 200
    assert f"/c/{p1.crisis_slug}/family" in resp.text


# ── Family-tier view (Slice 9) ────────────────────────────────────────────────

def test_family_page_renders(two_persons):
    p1, _ = two_persons  # Test Alice: contact "Bob", allergy "Penicillin", insurance
    resp = client.get(f"/c/{p1.crisis_slug}/family")
    assert resp.status_code == 200
    assert "For Family" in resp.text
    assert "Bob" in resp.text          # full contact roster
    assert "Penicillin" in resp.text   # medical history
    assert "last confirmed" in resp.text  # exact date label
    assert "Back to emergency script" in resp.text


def test_family_page_404_on_unknown_slug():
    resp = client.get("/c/doesnotexist000000/family")
    assert resp.status_code == 404


def test_notify_secure_link_points_to_family(two_persons):
    p1, _ = two_persons
    resp = client.post(f"/c/{p1.crisis_slug}/notify", json={})
    assert resp.status_code == 200
    assert resp.json()["secure_link"].endswith(f"/c/{p1.crisis_slug}/family")


def test_crisis_page_shows_freshness_label(two_persons):
    p1, _ = two_persons  # facts just created → "confirmed today"
    resp = client.get(f"/c/{p1.crisis_slug}")
    assert resp.status_code == 200
    assert "confirmed today" in resp.text


def test_crisis_page_flags_stale_fact(db):
    from datetime import datetime, timedelta, timezone

    p = create_person(db, PersonCreate(full_name="Test Stale"))
    fact = add_fact(db, p, FactCreate(type=FactType.condition, value="Old condition"))
    fact.last_confirmed_at = datetime.now(timezone.utc) - timedelta(days=240)
    db.commit()
    try:
        resp = client.get(f"/c/{p.crisis_slug}")
        assert resp.status_code == 200
        assert "may be outdated" in resp.text
        assert "8 months ago" in resp.text
    finally:
        db.delete(p)
        db.commit()


def test_crisis_page_has_notify_button(two_persons):
    p1, _ = two_persons
    resp = client.get(f"/c/{p1.crisis_slug}")
    assert resp.status_code == 200
    assert "Notify family" in resp.text


# ── Notify family (simulated send) ────────────────────────────────────────────

def test_notify_with_location_returns_messages(two_persons):
    p1, _ = two_persons  # has contact "Bob"
    resp = client.post(f"/c/{p1.crisis_slug}/notify", json={"lat": 17.4, "lng": 78.5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["person_name"] == "Test Alice"
    assert body["location_shared"] is True
    assert body["map_link"] == "https://www.google.com/maps?q=17.4,78.5"
    assert f"/c/{p1.crisis_slug}" in body["secure_link"]
    assert len(body["contacts"]) == 1
    msg = body["contacts"][0]
    assert msg["name"] == "Bob"
    assert "Test Alice" in msg["message"]
    assert "78.5" in msg["message"]


def test_notify_without_location_still_succeeds(two_persons):
    p1, _ = two_persons
    resp = client.post(f"/c/{p1.crisis_slug}/notify", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["location_shared"] is False
    assert body["map_link"] is None
    assert "not shared" in body["contacts"][0]["message"]


def test_notify_records_event(two_persons, db):
    from app.models.person import NotificationEvent
    from sqlalchemy import select

    p1, _ = two_persons
    before = db.execute(
        select(NotificationEvent).where(NotificationEvent.person_id == p1.id)
    ).scalars().all()
    client.post(f"/c/{p1.crisis_slug}/notify", json={"lat": 1.0, "lng": 2.0})
    db.expire_all()
    after = db.execute(
        select(NotificationEvent).where(NotificationEvent.person_id == p1.id)
    ).scalars().all()
    assert len(after) == len(before) + 1


def test_notify_invalid_coords_returns_422(two_persons):
    p1, _ = two_persons
    resp = client.post(f"/c/{p1.crisis_slug}/notify", json={"lat": 999, "lng": 0})
    assert resp.status_code == 422


def test_notify_404_on_unknown_slug():
    resp = client.post("/c/doesnotexist000000/notify", json={})
    assert resp.status_code == 404
