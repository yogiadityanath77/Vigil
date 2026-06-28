"""
Pydantic schemas for the public crisis surface (Slice 7).

Separate from the coordinator write schemas: this is the responder-facing side.
Currently just the "Notify family" request/response.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NotifyRequest(BaseModel):
    """
    Body for POST /c/{slug}/notify. Both coordinates are optional — the
    responder may deny the browser geolocation prompt, and the notify must still
    succeed. They are sent together or not at all; ranges are validated so a
    malformed coordinate can't be stored.
    """

    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class NotifiedContact(BaseModel):
    name: str
    phone: str
    relation: str | None
    message: str


class NotifyResponse(BaseModel):
    person_name: str
    triggered_at: datetime
    location_shared: bool
    map_link: str | None
    secure_link: str
    contacts: list[NotifiedContact]
