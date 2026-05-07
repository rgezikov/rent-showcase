import datetime
import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory
from bookings.models import Booking
from bookings.tests.factories import BookingFactory
from notifications.models import Notification

pytestmark = pytest.mark.django_db

today = datetime.date.today
delta = datetime.timedelta


def _booking_post(listing, **kwargs):
    start = today() + delta(7)
    return {
        'start_date': start.isoformat(),
        'end_date': (start + delta(2)).isoformat(),
        'quantity': 1,
        **kwargs,
    }


class TestBookingTriggers:
    def test_new_booking_notifies_owner(self, client):
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner, auto_accept=False)
        client.force_login(renter)
        client.post(reverse('bookings:create', kwargs={'listing_pk': listing.pk}), _booking_post(listing))
        assert Notification.objects.filter(recipient=owner, event_type=Notification.NEW_BOOKING).exists()

    def test_auto_accept_notifies_owner_and_renter(self, client):
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner, auto_accept=True, auto_accept_message='Welcome!')
        client.force_login(renter)
        client.post(reverse('bookings:create', kwargs={'listing_pk': listing.pk}), _booking_post(listing))
        assert Notification.objects.filter(recipient=owner, event_type=Notification.NEW_BOOKING).exists()
        assert Notification.objects.filter(recipient=renter, event_type=Notification.BOOKING_CONFIRMED).exists()

    def test_confirm_notifies_renter(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter, status=Booking.PENDING)
        client.force_login(owner)
        client.post(reverse('bookings:confirm', kwargs={'pk': booking.pk}))
        assert Notification.objects.filter(recipient=renter, event_type=Notification.BOOKING_CONFIRMED).exists()

    def test_reject_notifies_renter(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter, status=Booking.PENDING)
        client.force_login(owner)
        client.post(reverse('bookings:reject', kwargs={'pk': booking.pk}))
        assert Notification.objects.filter(recipient=renter, event_type=Notification.BOOKING_REJECTED).exists()

    def test_renter_cancel_notifies_owner(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter, status=Booking.CONFIRMED)
        client.force_login(renter)
        client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        assert Notification.objects.filter(recipient=owner, event_type=Notification.BOOKING_CANCELLED).exists()

    def test_owner_cancel_notifies_renter(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter, status=Booking.CONFIRMED)
        client.force_login(owner)
        client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        assert Notification.objects.filter(recipient=renter, event_type=Notification.BOOKING_CANCELLED).exists()


class TestMessageTrigger:
    def test_renter_message_notifies_owner(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter)
        client.force_login(renter)
        client.post(reverse('messaging:send', kwargs={'booking_pk': booking.pk}), {'body': 'Hello!'})
        assert Notification.objects.filter(recipient=owner, event_type=Notification.NEW_MESSAGE).exists()

    def test_owner_message_notifies_renter(self, client):
        owner = UserFactory()
        renter = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), renter=renter)
        client.force_login(owner)
        client.post(reverse('messaging:send', kwargs={'booking_pk': booking.pk}), {'body': 'Hello renter!'})
        assert Notification.objects.filter(recipient=renter, event_type=Notification.NEW_MESSAGE).exists()
