import json
import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory
from bookings.tests.factories import BookingFactory


pytestmark = pytest.mark.django_db


class TestDataExport:
    def test_requires_login(self, client):
        response = client.get(reverse('accounts:data_export'))
        assert response.status_code == 302

    def test_returns_json_file(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse('accounts:data_export'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        assert 'attachment' in response['Content-Disposition']

    def test_contains_profile_data(self, client):
        user = UserFactory(first_name='Test', location='Helsinki')
        client.force_login(user)
        response = client.get(reverse('accounts:data_export'))
        data = json.loads(response.content)
        assert data['profile']['first_name'] == 'Test'
        assert data['profile']['location'] == 'Helsinki'
        assert data['profile']['email'] == user.email

    def test_contains_listings(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user, title='My Camera')
        client.force_login(user)
        response = client.get(reverse('accounts:data_export'))
        data = json.loads(response.content)
        assert any(l['title'] == 'My Camera' for l in data['listings'])

    def test_contains_bookings(self, client):
        user = UserFactory()
        booking = BookingFactory(renter=user)
        client.force_login(user)
        response = client.get(reverse('accounts:data_export'))
        data = json.loads(response.content)
        assert len(data['bookings']) == 1

    def test_does_not_include_other_users_data(self, client):
        user = UserFactory()
        other = UserFactory()
        ListingFactory(owner=other)
        BookingFactory(renter=other)
        client.force_login(user)
        response = client.get(reverse('accounts:data_export'))
        data = json.loads(response.content)
        assert data['listings'] == []
        assert data['bookings'] == []
