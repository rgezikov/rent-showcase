import pytest
from notifications.models import Notification
from notifications.tests.factories import NotificationFactory

pytestmark = pytest.mark.django_db


class TestGetText:
    def test_new_booking(self):
        n = NotificationFactory(event_type=Notification.NEW_BOOKING)
        assert 'booking request' in n.get_text().lower()

    def test_confirmed(self):
        n = NotificationFactory(event_type=Notification.BOOKING_CONFIRMED)
        assert 'confirmed' in n.get_text().lower()

    def test_rejected(self):
        n = NotificationFactory(event_type=Notification.BOOKING_REJECTED)
        assert 'rejected' in n.get_text().lower()

    def test_cancelled(self):
        n = NotificationFactory(event_type=Notification.BOOKING_CANCELLED)
        assert 'cancelled' in n.get_text().lower()

    def test_new_message(self):
        n = NotificationFactory(event_type=Notification.NEW_MESSAGE)
        assert 'message' in n.get_text().lower()

    def test_includes_listing_title(self):
        n = NotificationFactory(event_type=Notification.NEW_BOOKING)
        assert n.booking.listing.title in n.get_text()


class TestGetLink:
    def test_returns_booking_url(self):
        n = NotificationFactory()
        assert n.get_link() == n.booking.get_absolute_url()
