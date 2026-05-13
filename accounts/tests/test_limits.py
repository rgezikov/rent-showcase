import pytest
from django.urls import reverse
from django.utils.translation import gettext as _
from accounts.models import SiteSettings
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory, CategoryFactory
from bookings.tests.factories import BookingFactory
from bookings.models import Booking


pytestmark = pytest.mark.django_db


class TestGetMaxActiveListings:
    def test_uses_site_default(self):
        user = UserFactory()
        s = SiteSettings.get()
        s.max_active_listings = 15
        s.save()
        assert user.get_max_active_listings() == 15

    def test_per_user_override_takes_precedence(self):
        user = UserFactory(max_active_listings_override=5)
        s = SiteSettings.get()
        s.max_active_listings = 20
        s.save()
        assert user.get_max_active_listings() == 5

    def test_blank_override_falls_back_to_site_default(self):
        user = UserFactory(max_active_listings_override=None)
        s = SiteSettings.get()
        s.max_active_listings = 20
        s.save()
        assert user.get_max_active_listings() == 20


class TestGetMaxPendingBookings:
    def test_uses_site_default(self):
        user = UserFactory()
        s = SiteSettings.get()
        s.max_pending_bookings = 8
        s.save()
        assert user.get_max_pending_bookings() == 8

    def test_per_user_override_takes_precedence(self):
        user = UserFactory(max_pending_bookings_override=3)
        s = SiteSettings.get()
        s.max_pending_bookings = 10
        s.save()
        assert user.get_max_pending_bookings() == 3


class TestListingCreateLimit:
    def test_blocked_when_limit_reached(self, client):
        user = UserFactory(max_active_listings_override=2)
        client.force_login(user)
        ListingFactory(owner=user, is_active=True)
        ListingFactory(owner=user, is_active=True)
        response = client.get(reverse('listings:create'))
        assert response.status_code == 302
        assert response.url == reverse('listings:my_listings')

    def test_allowed_when_below_limit(self, client):
        user = UserFactory(max_active_listings_override=5)
        client.force_login(user)
        ListingFactory(owner=user, is_active=True)
        response = client.get(reverse('listings:create'))
        assert response.status_code == 200

    def test_inactive_listings_not_counted(self, client):
        user = UserFactory(max_active_listings_override=1)
        client.force_login(user)
        ListingFactory(owner=user, is_active=False)
        response = client.get(reverse('listings:create'))
        assert response.status_code == 200


class TestBookingCreateLimit:
    def test_blocked_when_limit_reached(self, client):
        user = UserFactory(max_pending_bookings_override=1)
        client.force_login(user)
        listing = ListingFactory()
        BookingFactory(renter=user, status=Booking.PENDING)
        response = client.get(reverse('bookings:create', kwargs={'listing_pk': listing.pk}))
        assert response.status_code == 302

    def test_allowed_when_below_limit(self, client):
        user = UserFactory(max_pending_bookings_override=3)
        client.force_login(user)
        listing = ListingFactory()
        BookingFactory(renter=user, status=Booking.PENDING)
        response = client.get(reverse('bookings:create', kwargs={'listing_pk': listing.pk}))
        assert response.status_code == 200

    def test_confirmed_bookings_not_counted(self, client):
        user = UserFactory(max_pending_bookings_override=1)
        client.force_login(user)
        listing = ListingFactory()
        BookingFactory(renter=user, status=Booking.CONFIRMED)
        response = client.get(reverse('bookings:create', kwargs={'listing_pk': listing.pk}))
        assert response.status_code == 200
