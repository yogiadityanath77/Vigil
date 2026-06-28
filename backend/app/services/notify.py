"""
notify.py — compose the "Notify family" messages.

Pure, like transform.py: no DB, no HTTP, no side effects. Inputs are plain
values (person name, contacts, the two links); output is plain data ready to
render or "send". The actual send is simulated elsewhere; this module only
turns facts into the words each contact would receive.

The message is intentionally LIGHT (prototype-spec.md): it names the person,
gives a location map link, and a *secure link* for the richer details — the
sensitive data never rides in the message body itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.person import EmergencyContact


def maps_link(lat: float | None, lng: float | None) -> str | None:
    """A Google Maps link for the coordinates, or None if location is absent."""
    if lat is None or lng is None:
        return None
    return f"https://www.google.com/maps?q={lat},{lng}"


@dataclass
class NotificationMessage:
    """One composed message destined for a single contact."""

    contact_name: str
    contact_phone: str
    contact_relation: str | None
    body: str


def build_notification_messages(
    person_name: str,
    contacts: list["EmergencyContact"],
    secure_link: str,
    map_link: str | None,
) -> list[NotificationMessage]:
    """
    Compose one light message per contact, ordered by notify_order.

    Location line is omitted when no map_link is available (responder denied the
    geolocation prompt) — the message degrades gracefully rather than lying about
    a location it doesn't have.
    """
    location_line = (
        f"Location: {map_link}. " if map_link else "Location: not shared. "
    )
    body = (
        f"Emergency — {person_name} may need help right now. "
        f"{location_line}"
        f"Details: {secure_link}"
    )

    ordered = sorted(contacts, key=lambda c: c.notify_order)
    return [
        NotificationMessage(
            contact_name=c.name,
            contact_phone=c.phone,
            contact_relation=c.relation,
            body=body,
        )
        for c in ordered
    ]
