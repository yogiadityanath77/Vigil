"""
test_notify.py — unit tests for app/services/notify.py.

Pure: no DB, no HTTP. We build plain EmergencyContact instances (no session)
and verify message composition + ordering + graceful no-location handling.
"""
import uuid

from app.models.person import EmergencyContact
from app.services.notify import (
    NotificationMessage,
    build_notification_messages,
    maps_link,
)


def _contact(name: str, phone: str, relation: str | None = None, notify_order: int = 1) -> EmergencyContact:
    return EmergencyContact(
        id=uuid.uuid4(),
        name=name,
        phone=phone,
        relation=relation,
        notify_order=notify_order,
    )


class TestMapsLink:
    def test_builds_link_with_coords(self):
        assert maps_link(17.4, 78.5) == "https://www.google.com/maps?q=17.4,78.5"

    def test_none_when_lat_missing(self):
        assert maps_link(None, 78.5) is None

    def test_none_when_lng_missing(self):
        assert maps_link(17.4, None) is None


class TestBuildNotificationMessages:
    def test_one_message_per_contact(self):
        msgs = build_notification_messages(
            "Priya Sharma",
            [_contact("Rahul", "111"), _contact("Asha", "222")],
            secure_link="http://x/c/abc",
            map_link="http://maps/x",
        )
        assert len(msgs) == 2
        assert all(isinstance(m, NotificationMessage) for m in msgs)

    def test_message_names_person_and_links(self):
        msgs = build_notification_messages(
            "Priya Sharma",
            [_contact("Rahul", "111")],
            secure_link="http://x/c/abc",
            map_link="https://maps/here",
        )
        body = msgs[0].body
        assert "Priya Sharma" in body
        assert "https://maps/here" in body
        assert "http://x/c/abc" in body

    def test_ordered_by_notify_order(self):
        msgs = build_notification_messages(
            "P",
            [
                _contact("Second", "2", notify_order=2),
                _contact("First", "1", notify_order=1),
            ],
            secure_link="link",
            map_link=None,
        )
        assert [m.contact_name for m in msgs] == ["First", "Second"]

    def test_no_location_degrades_gracefully(self):
        msgs = build_notification_messages(
            "P", [_contact("Rahul", "111")], secure_link="link", map_link=None
        )
        body = msgs[0].body
        assert "not shared" in body
        assert "maps" not in body.lower()

    def test_no_contacts_gives_empty_list(self):
        msgs = build_notification_messages(
            "P", [], secure_link="link", map_link="http://m"
        )
        assert msgs == []
