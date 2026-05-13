import pytest
from django.core import mail
from notifications.utils import create_notification
from notifications.models import Notification
from accounts.tests.factories import UserFactory
from bookings.tests.factories import BookingFactory


pytestmark = pytest.mark.django_db


class TestNotificationEmail:
    def setup_method(self):
        self.owner = UserFactory()
        self.renter = UserFactory()
        self.booking = BookingFactory(
            listing__owner=self.owner,
            renter=self.renter,
        )

    def test_email_sent_on_new_booking(self):
        create_notification(self.owner, Notification.NEW_BOOKING, self.booking)
        assert len(mail.outbox) == 1
        assert self.owner.email in mail.outbox[0].to

    def test_email_sent_on_confirmed(self):
        create_notification(self.renter, Notification.BOOKING_CONFIRMED, self.booking)
        assert len(mail.outbox) == 1
        assert self.renter.email in mail.outbox[0].to

    def test_email_sent_on_rejected(self):
        create_notification(self.renter, Notification.BOOKING_REJECTED, self.booking)
        assert len(mail.outbox) == 1

    def test_email_sent_on_cancelled(self):
        create_notification(self.owner, Notification.BOOKING_CANCELLED, self.booking)
        assert len(mail.outbox) == 1

    def test_email_sent_on_new_message(self):
        create_notification(self.renter, Notification.NEW_MESSAGE, self.booking)
        assert len(mail.outbox) == 1

    def test_email_subject_contains_event(self):
        create_notification(self.renter, Notification.BOOKING_CONFIRMED, self.booking)
        assert 'confirmed' in mail.outbox[0].subject.lower()

    def test_email_body_contains_listing_title(self):
        create_notification(self.owner, Notification.NEW_BOOKING, self.booking)
        assert self.booking.listing.title in mail.outbox[0].body

    def test_email_body_contains_booking_link(self):
        create_notification(self.owner, Notification.NEW_BOOKING, self.booking)
        assert self.booking.get_absolute_url() in mail.outbox[0].body
