"""
transform.py — the fact-to-sentence transform.

CONTRACT (never break this):
  - Pure function. No DB access. No HTTP. No side effects.
  - Input: a Person ORM object with .medical_facts and .emergency_contacts loaded.
  - Output: a CrisisScript dataclass — plain data, ready for any renderer.

This isolation means:
  - The test never needs a DB session.
  - When the crisis page moves from Jinja2 → Next.js SSR, this file is untouched.
  - When the script grows (guard-rails, tiers, more fact types), changes stay here.
"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.person import Person

from app.models.person import FactType


@dataclass
class GuardRail:
    """
    The money/insurance guard-rail — pre-composed instructions for a responder
    so they don't pay upfront or miss a cashless benefit. Plain data, no model.

    `headline` is the single loud instruction; `detail` carries the policy to
    show at the desk; `hospital_line` is an optional "where to go" hint.
    """

    headline: str
    detail: str
    hospital_line: str | None


@dataclass
class CrisisScript:
    """The composed crisis script — one value object, ready to render."""

    person_name: str

    # Contact to call first
    call_name: str
    call_phone: str
    call_relation: str | None  # "husband", "son", etc.

    # Pre-composed "tell the doctor" sentences, in display order:
    # allergies first (highest urgency), then medications, then conditions.
    doctor_lines: list[str] = field(default_factory=list)

    # The money guard-rail (insurance). None when no insurance is on file.
    guard_rail: GuardRail | None = None

    @property
    def has_medical_info(self) -> bool:
        return bool(self.doctor_lines)

    @property
    def has_guard_rail(self) -> bool:
        return self.guard_rail is not None


def build_crisis_script(person: "Person") -> CrisisScript:
    """
    Transform a Person (with loaded relationships) into a CrisisScript.

    Ordering decisions made here:
      - Emergency contacts sorted by notify_order; first contact drives the script.
      - Doctor lines: allergies → medications → conditions.
        Allergies first because they are the highest-urgency safety signal.
    """
    # ── Primary contact ─────────────────────────────────────────────────────
    contacts = sorted(person.emergency_contacts, key=lambda c: c.notify_order)
    primary = contacts[0] if contacts else None

    # ── Doctor lines (allergies → medications → conditions) ─────────────────
    buckets: dict[FactType, list[str]] = {t: [] for t in FactType}
    for fact in person.medical_facts:
        buckets[fact.type].append(fact.value)

    doctor_lines: list[str] = []

    for allergy in buckets[FactType.allergy]:
        doctor_lines.append(f"They are allergic to {allergy}.")

    for med in buckets[FactType.medication]:
        doctor_lines.append(f"They take {med}.")

    for condition in buckets[FactType.condition]:
        doctor_lines.append(f"They have {condition}.")

    # ── Money guard-rail (insurance) ────────────────────────────────────────
    guard_rail = _build_guard_rail(person.insurance)

    return CrisisScript(
        person_name=person.full_name,
        call_name=primary.name if primary else "No contact listed",
        call_phone=primary.phone if primary else "",
        call_relation=primary.relation if primary else None,
        doctor_lines=doctor_lines,
        guard_rail=guard_rail,
    )


def _build_guard_rail(insurance) -> GuardRail | None:
    """
    Compose the money guard-rail from the insurance row. Pure templating — the
    `cashless` flag decides the instruction:
      - cashless  → "don't pay upfront" (the signature guard-rail line)
      - otherwise → "keep every bill for reimbursement"
    Returns None when there is no insurance on file (template omits the block).
    """
    if insurance is None:
        return None

    if insurance.cashless:
        headline = "Covered as cashless — don't pay upfront."
        detail = (
            f"Show this policy at the hospital desk: "
            f"{insurance.provider}, policy {insurance.policy_number}."
        )
    else:
        headline = f"Insured with {insurance.provider} — keep every bill for reimbursement."
        detail = f"Policy {insurance.policy_number}."

    hospital_line = None
    if insurance.hospital_preference:
        hospital_line = f"If there's a choice, prefer {insurance.hospital_preference}."

    return GuardRail(headline=headline, detail=detail, hospital_line=hospital_line)
