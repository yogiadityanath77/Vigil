"""
test_transform.py

Tests for app/services/transform.py.

These are UNIT tests — no database, no HTTP, no FastAPI app.
The transform is a pure function; we construct plain ORM model instances
and verify the output directly.

Note on SQLAlchemy model instantiation in tests:
  Accessing a relationship on an ORM object that isn't bound to a session
  would normally raise DetachedInstanceError (lazy-load attempted, no session).
  We avoid this by explicitly assigning the relationship attributes as Python
  lists before calling the transform. The transform then iterates those lists
  without touching the session.
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.person import EmergencyContact, FactType, Insurance, MedicalFact, Person
from app.services.transform import CrisisScript, GuardRail, build_crisis_script


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_person(
    full_name: str = "Test Person",
    facts: list[MedicalFact] | None = None,
    contacts: list[EmergencyContact] | None = None,
    insurance: Insurance | None = None,
) -> Person:
    """Construct a detached Person instance for testing — no session needed."""
    person = Person(
        id=uuid.uuid4(),
        full_name=full_name,
        crisis_slug="test-slug",
        created_at=_now(),
    )
    # Explicitly set relationship attributes to bypass lazy-loading.
    person.medical_facts = facts or []
    person.emergency_contacts = contacts or []
    person.insurance = insurance
    return person


def _insurance(
    provider: str = "Star Health",
    policy_number: str = "SH-123",
    hospital_preference: str | None = None,
    cashless: bool = True,
) -> Insurance:
    return Insurance(
        id=uuid.uuid4(),
        provider=provider,
        policy_number=policy_number,
        hospital_preference=hospital_preference,
        cashless=cashless,
        created_at=_now(),
    )


def _fact(type: FactType, value: str) -> MedicalFact:
    return MedicalFact(
        id=uuid.uuid4(),
        type=type,
        value=value,
        created_at=_now(),
    )


def _contact(name: str, phone: str, relation: str | None = None, notify_order: int = 1) -> EmergencyContact:
    return EmergencyContact(
        id=uuid.uuid4(),
        name=name,
        phone=phone,
        relation=relation,
        notify_order=notify_order,
        created_at=_now(),
    )


# ── Tests ───────────────────────────────────────────────────────────────────

class TestBuildCrisisScript:

    def test_returns_crisis_script(self):
        person = _make_person()
        result = build_crisis_script(person)
        assert isinstance(result, CrisisScript)

    def test_person_name_passed_through(self):
        person = _make_person(full_name="Priya Sharma")
        script = build_crisis_script(person)
        assert script.person_name == "Priya Sharma"

    def test_primary_contact_fields(self):
        person = _make_person(
            contacts=[_contact("Rahul Sharma", "+91 98765 43210", relation="husband")]
        )
        script = build_crisis_script(person)
        assert script.call_name == "Rahul Sharma"
        assert script.call_phone == "+91 98765 43210"
        assert script.call_relation == "husband"

    def test_no_contact_gives_safe_fallback(self):
        person = _make_person(contacts=[])
        script = build_crisis_script(person)
        assert script.call_name == "No contact listed"
        assert script.call_phone == ""

    def test_contact_ordering_by_notify_order(self):
        """Lower notify_order wins as the primary contact."""
        person = _make_person(
            contacts=[
                _contact("Secondary", "+91 11111 11111", notify_order=2),
                _contact("Primary", "+91 99999 99999", notify_order=1),
            ]
        )
        script = build_crisis_script(person)
        assert script.call_name == "Primary"

    def test_allergy_line_rendered(self):
        person = _make_person(facts=[_fact(FactType.allergy, "Penicillin")])
        script = build_crisis_script(person)
        assert any("Penicillin" in line for line in script.doctor_lines)

    def test_medication_line_rendered(self):
        person = _make_person(facts=[_fact(FactType.medication, "Metformin 500mg")])
        script = build_crisis_script(person)
        assert any("Metformin 500mg" in line for line in script.doctor_lines)

    def test_condition_line_rendered(self):
        person = _make_person(facts=[_fact(FactType.condition, "Type 2 diabetes")])
        script = build_crisis_script(person)
        assert any("Type 2 diabetes" in line for line in script.doctor_lines)

    def test_doctor_line_ordering_allergies_first(self):
        """Allergies must precede medications, which must precede conditions."""
        person = _make_person(facts=[
            _fact(FactType.condition, "Hypertension"),
            _fact(FactType.medication, "Metformin 500mg"),
            _fact(FactType.allergy, "Penicillin"),
        ])
        script = build_crisis_script(person)
        allergy_idx = next(i for i, l in enumerate(script.doctor_lines) if "Penicillin" in l)
        med_idx = next(i for i, l in enumerate(script.doctor_lines) if "Metformin" in l)
        condition_idx = next(i for i, l in enumerate(script.doctor_lines) if "Hypertension" in l)
        assert allergy_idx < med_idx < condition_idx

    def test_no_facts_gives_empty_doctor_lines(self):
        person = _make_person(facts=[])
        script = build_crisis_script(person)
        assert script.doctor_lines == []
        assert not script.has_medical_info

    def test_has_medical_info_true_when_facts_present(self):
        person = _make_person(facts=[_fact(FactType.allergy, "Aspirin")])
        script = build_crisis_script(person)
        assert script.has_medical_info


class TestGuardRail:
    """The money/insurance guard-rail composition (Slice 5)."""

    def test_no_insurance_gives_no_guard_rail(self):
        person = _make_person(insurance=None)
        script = build_crisis_script(person)
        assert script.guard_rail is None
        assert not script.has_guard_rail

    def test_cashless_headline_says_dont_pay_upfront(self):
        person = _make_person(insurance=_insurance(cashless=True))
        script = build_crisis_script(person)
        assert script.has_guard_rail
        assert isinstance(script.guard_rail, GuardRail)
        assert "don't pay upfront" in script.guard_rail.headline.lower()

    def test_cashless_detail_shows_provider_and_policy(self):
        person = _make_person(
            insurance=_insurance(provider="Star Health", policy_number="SH-999")
        )
        script = build_crisis_script(person)
        assert "Star Health" in script.guard_rail.detail
        assert "SH-999" in script.guard_rail.detail

    def test_non_cashless_headline_says_keep_bills(self):
        person = _make_person(
            insurance=_insurance(provider="HDFC Ergo", cashless=False)
        )
        script = build_crisis_script(person)
        assert "HDFC Ergo" in script.guard_rail.headline
        assert "reimbursement" in script.guard_rail.headline.lower()
        assert "don't pay upfront" not in script.guard_rail.headline.lower()

    def test_hospital_preference_rendered_when_present(self):
        person = _make_person(
            insurance=_insurance(hospital_preference="Apollo, Jubilee Hills")
        )
        script = build_crisis_script(person)
        assert script.guard_rail.hospital_line is not None
        assert "Apollo, Jubilee Hills" in script.guard_rail.hospital_line

    def test_no_hospital_preference_gives_none_hospital_line(self):
        person = _make_person(insurance=_insurance(hospital_preference=None))
        script = build_crisis_script(person)
        assert script.guard_rail.hospital_line is None
