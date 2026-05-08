import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    return UserFactory(is_staff=True, is_superuser=True)


class TestListingAdminActions:
    def test_deactivate_action(self, client, staff):
        listing = ListingFactory(is_active=True)
        client.force_login(staff)
        client.post(reverse('admin:listings_listing_changelist'), {
            'action': 'deactivate_listings',
            '_selected_action': [listing.pk],
        })
        listing.refresh_from_db()
        assert listing.is_active is False

    def test_activate_action(self, client, staff):
        listing = ListingFactory(is_active=False)
        client.force_login(staff)
        client.post(reverse('admin:listings_listing_changelist'), {
            'action': 'activate_listings',
            '_selected_action': [listing.pk],
        })
        listing.refresh_from_db()
        assert listing.is_active is True

    def test_deactivated_listing_hidden_from_browse(self, client, staff):
        listing = ListingFactory(is_active=True)
        client.force_login(staff)
        client.post(reverse('admin:listings_listing_changelist'), {
            'action': 'deactivate_listings',
            '_selected_action': [listing.pk],
        })
        client.logout()
        listings = client.get(reverse('listings:list')).context['listings']
        assert listing.pk not in [l.pk for l in listings]
