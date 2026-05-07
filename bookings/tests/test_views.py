import datetime
import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory
from bookings.models import Booking
from bookings.tests.factories import BookingFactory

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


class TestBookingCreate:
    def test_requires_login(self, client):
        listing = ListingFactory()
        assert client.get(reverse('bookings:create', kwargs={'listing_pk': listing.pk})).status_code == 302

    def test_owner_cannot_book_own_listing(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user)
        client.force_login(user)
        response = client.post(
            reverse('bookings:create', kwargs={'listing_pk': listing.pk}),
            _booking_post(listing),
        )
        assert not Booking.objects.filter(listing=listing).exists()
        assert response.status_code == 302

    def test_creates_pending_booking(self, client):
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner)
        client.force_login(renter)
        client.post(
            reverse('bookings:create', kwargs={'listing_pk': listing.pk}),
            _booking_post(listing),
        )
        booking = Booking.objects.get(listing=listing, renter=renter)
        assert booking.status == Booking.PENDING

    def test_auto_accept_confirms_immediately(self, client):
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner, auto_accept=True, auto_accept_message='Welcome!')
        client.force_login(renter)
        client.post(
            reverse('bookings:create', kwargs={'listing_pk': listing.pk}),
            _booking_post(listing),
        )
        booking = Booking.objects.get(listing=listing, renter=renter)
        assert booking.status == Booking.CONFIRMED

    def test_auto_accept_posts_message(self, client):
        from messaging.models import Message
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner, auto_accept=True, auto_accept_message='All set!')
        client.force_login(renter)
        client.post(
            reverse('bookings:create', kwargs={'listing_pk': listing.pk}),
            _booking_post(listing),
        )
        booking = Booking.objects.get(listing=listing, renter=renter)
        assert Message.objects.filter(booking=booking, is_system=True).exists()

    def test_price_is_calculated(self, client):
        from decimal import Decimal
        owner = UserFactory()
        renter = UserFactory()
        listing = ListingFactory(owner=owner, price_per_day=Decimal('10.00'))
        client.force_login(renter)
        client.post(
            reverse('bookings:create', kwargs={'listing_pk': listing.pk}),
            _booking_post(listing),
        )
        booking = Booking.objects.get(listing=listing, renter=renter)
        assert booking.total_price is not None


class TestBookingDetail:
    def test_owner_can_view(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner))
        client.force_login(owner)
        assert client.get(booking.get_absolute_url()).status_code == 200

    def test_renter_can_view(self, client):
        renter = UserFactory()
        booking = BookingFactory(renter=renter)
        client.force_login(renter)
        assert client.get(booking.get_absolute_url()).status_code == 200

    def test_stranger_gets_404(self, client):
        booking = BookingFactory()
        client.force_login(UserFactory())
        assert client.get(booking.get_absolute_url()).status_code == 404

    def test_unauthenticated_redirects_to_login(self, client):
        booking = BookingFactory()
        response = client.get(booking.get_absolute_url())
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


class TestBookingConfirm:
    def test_owner_confirms_pending(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), status=Booking.PENDING)
        client.force_login(owner)
        client.post(reverse('bookings:confirm', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        assert booking.status == Booking.CONFIRMED

    def test_non_owner_gets_404(self, client):
        booking = BookingFactory(status=Booking.PENDING)
        client.force_login(UserFactory())
        assert client.post(reverse('bookings:confirm', kwargs={'pk': booking.pk})).status_code == 404

    def test_cannot_confirm_non_pending(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), status=Booking.CONFIRMED)
        client.force_login(owner)
        assert client.post(reverse('bookings:confirm', kwargs={'pk': booking.pk})).status_code == 404


class TestBookingReject:
    def test_owner_rejects_pending(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), status=Booking.PENDING)
        client.force_login(owner)
        client.post(reverse('bookings:reject', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        assert booking.status == Booking.REJECTED

    def test_non_owner_gets_404(self, client):
        booking = BookingFactory(status=Booking.PENDING)
        client.force_login(UserFactory())
        assert client.post(reverse('bookings:reject', kwargs={'pk': booking.pk})).status_code == 404


class TestBookingCancel:
    def test_renter_cancels_confirmed(self, client):
        renter = UserFactory()
        booking = BookingFactory(renter=renter, status=Booking.CONFIRMED)
        client.force_login(renter)
        client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        assert booking.status == Booking.CANCELLED

    def test_owner_cancels_confirmed(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner), status=Booking.CONFIRMED)
        client.force_login(owner)
        client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        assert booking.status == Booking.CANCELLED

    def test_renter_cancels_pending(self, client):
        renter = UserFactory()
        booking = BookingFactory(renter=renter, status=Booking.PENDING)
        client.force_login(renter)
        client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        assert booking.status == Booking.CANCELLED

    def test_stranger_gets_404(self, client):
        booking = BookingFactory(status=Booking.CONFIRMED)
        client.force_login(UserFactory())
        assert client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk})).status_code == 404


class TestMyBookings:
    def test_requires_login(self, client):
        assert client.get(reverse('bookings:my_bookings')).status_code == 302

    def test_shows_renter_bookings(self, client):
        renter = UserFactory()
        booking = BookingFactory(renter=renter)
        other = BookingFactory()
        client.force_login(renter)
        response = client.get(reverse('bookings:my_bookings'))
        pks = [b.pk for b in response.context['bookings']]
        assert booking.pk in pks
        assert other.pk not in pks


class TestBookingRequests:
    def test_requires_login(self, client):
        assert client.get(reverse('bookings:requests')).status_code == 302

    def test_shows_pending_for_owner(self, client):
        owner = UserFactory()
        listing = ListingFactory(owner=owner)
        pending = BookingFactory(listing=listing, status=Booking.PENDING)
        other = BookingFactory(status=Booking.PENDING)
        client.force_login(owner)
        response = client.get(reverse('bookings:requests'))
        pks = [b.pk for b in response.context['pending']]
        assert pending.pk in pks
        assert other.pk not in pks
