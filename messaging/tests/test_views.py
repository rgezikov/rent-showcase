import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory
from bookings.tests.factories import BookingFactory
from messaging.models import Message

pytestmark = pytest.mark.django_db


class TestSendMessage:
    def test_requires_login(self, client):
        booking = BookingFactory()
        response = client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': 'Hello!'},
        )
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_owner_can_send(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner))
        client.force_login(owner)
        client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': 'Hello renter!'},
        )
        assert Message.objects.filter(booking=booking, sender=owner, body='Hello renter!').exists()

    def test_renter_can_send(self, client):
        renter = UserFactory()
        booking = BookingFactory(renter=renter)
        client.force_login(renter)
        client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': 'Hello owner!'},
        )
        assert Message.objects.filter(booking=booking, sender=renter, body='Hello owner!').exists()

    def test_stranger_gets_404(self, client):
        booking = BookingFactory()
        client.force_login(UserFactory())
        response = client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': 'Hello!'},
        )
        assert response.status_code == 404

    def test_redirects_to_booking_detail(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner))
        client.force_login(owner)
        response = client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': 'Hi!'},
        )
        assert response.status_code == 302
        assert booking.get_absolute_url() in response.url

    def test_empty_body_not_saved(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner))
        client.force_login(owner)
        client.post(
            reverse('messaging:send', kwargs={'booking_pk': booking.pk}),
            {'body': ''},
        )
        assert not Message.objects.filter(booking=booking, is_system=False).exists()


class TestDisclaimer:
    def test_disclaimer_in_booking_detail(self, client):
        owner = UserFactory()
        booking = BookingFactory(listing=ListingFactory(owner=owner))
        client.force_login(owner)
        response = client.get(booking.get_absolute_url())
        assert b'cautious' in response.content.lower()
