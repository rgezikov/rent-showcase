import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from listings.tests.factories import (
    CategoryFactory, ListingFactory, ListingPhotoFactory, BlockedDateRangeFactory
)

pytestmark = pytest.mark.django_db


class TestListingListView:
    def test_accessible_to_logged_out(self, client):
        assert client.get(reverse('listings:list')).status_code == 200

    def test_only_active_listings_shown(self, client):
        active = ListingFactory(is_active=True)
        inactive = ListingFactory(is_active=False)
        listings = client.get(reverse('listings:list')).context['listings']
        titles = [l.title for l in listings]
        assert active.title in titles
        assert inactive.title not in titles

    def test_keyword_filter(self, client):
        match = ListingFactory(title='Red Excavator')
        no_match = ListingFactory(title='Blue Ladder')
        listings = client.get(reverse('listings:list'), {'q': 'excavator'}).context['listings']
        titles = [l.title for l in listings]
        assert match.title in titles
        assert no_match.title not in titles

    def test_category_filter(self, client):
        cat = CategoryFactory()
        match = ListingFactory(category=cat)
        no_match = ListingFactory()
        listings = client.get(reverse('listings:list'), {'category': cat.slug}).context['listings']
        titles = [l.title for l in listings]
        assert match.title in titles
        assert no_match.title not in titles

    def test_location_filter(self, client):
        match = ListingFactory(location='Helsinki')
        no_match = ListingFactory(location='Tampere')
        listings = client.get(reverse('listings:list'), {'location': 'Helsinki'}).context['listings']
        titles = [l.title for l in listings]
        assert match.title in titles
        assert no_match.title not in titles


class TestListingDetailView:
    def test_accessible_to_logged_out(self, client):
        listing = ListingFactory()
        assert client.get(listing.get_absolute_url()).status_code == 200

    def test_logged_out_sees_login_prompt(self, client):
        listing = ListingFactory()
        response = client.get(listing.get_absolute_url())
        assert not response.context['is_owner']
        assert b'Log in' in response.content

    def test_owner_sees_manage_panel(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user)
        client.force_login(user)
        assert client.get(listing.get_absolute_url()).context['is_owner'] is True

    def test_inactive_listing_returns_404(self, client):
        listing = ListingFactory(is_active=False)
        assert client.get(listing.get_absolute_url()).status_code == 404


class TestListingCreateView:
    def _post_data(self, category):
        return {
            'title': 'Test Drill',
            'description': 'A drill for rent.',
            'category': category.pk,
            'location': 'Helsinki',
            'price_per_day': '15.00',
            'quantity': 1,
        }

    def test_requires_login(self, client):
        assert client.get(reverse('listings:create')).status_code == 302

    def test_creates_listing(self, client):
        user = UserFactory()
        cat = CategoryFactory()
        client.force_login(user)
        response = client.post(reverse('listings:create'), self._post_data(cat))
        assert response.status_code == 302
        assert user.listings.filter(title='Test Drill').exists()

    def test_sets_owner_to_current_user(self, client):
        user = UserFactory()
        cat = CategoryFactory()
        client.force_login(user)
        client.post(reverse('listings:create'), self._post_data(cat))
        assert user.listings.first().owner == user


class TestListingEditView:
    def test_owner_can_edit(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user)
        cat = CategoryFactory()
        client.force_login(user)
        client.post(reverse('listings:edit', kwargs={'pk': listing.pk}), {
            'title': 'Updated Title',
            'description': listing.description,
            'category': cat.pk,
            'location': listing.location,
            'price_per_day': '20.00',
            'quantity': 1,
        })
        listing.refresh_from_db()
        assert listing.title == 'Updated Title'

    def test_non_owner_gets_404(self, client):
        listing = ListingFactory()
        client.force_login(UserFactory())
        assert client.get(reverse('listings:edit', kwargs={'pk': listing.pk})).status_code == 404


class TestListingDeleteView:
    def test_owner_can_delete(self, client):
        from listings.models import Listing
        user = UserFactory()
        listing = ListingFactory(owner=user)
        pk = listing.pk
        client.force_login(user)
        client.post(reverse('listings:delete', kwargs={'pk': listing.pk}))
        assert not Listing.objects.filter(pk=pk).exists()

    def test_non_owner_gets_404(self, client):
        listing = ListingFactory()
        client.force_login(UserFactory())
        assert client.post(reverse('listings:delete', kwargs={'pk': listing.pk})).status_code == 404


class TestToggleActive:
    def test_deactivates_active_listing(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user, is_active=True)
        client.force_login(user)
        client.post(reverse('listings:toggle_active', kwargs={'pk': listing.pk}))
        listing.refresh_from_db()
        assert listing.is_active is False

    def test_activates_inactive_listing(self, client):
        user = UserFactory()
        listing = ListingFactory(owner=user, is_active=False)
        client.force_login(user)
        client.post(reverse('listings:toggle_active', kwargs={'pk': listing.pk}))
        listing.refresh_from_db()
        assert listing.is_active is True


class TestMyListings:
    def test_requires_login(self, client):
        assert client.get(reverse('listings:my_listings')).status_code == 302

    def test_shows_own_listings_only(self, client):
        user = UserFactory()
        active = ListingFactory(owner=user, is_active=True)
        inactive = ListingFactory(owner=user, is_active=False)
        other = ListingFactory()
        client.force_login(user)
        listings = client.get(reverse('listings:my_listings')).context['listings']
        titles = [l.title for l in listings]
        assert active.title in titles
        assert inactive.title in titles
        assert other.title not in titles


class TestBlockedDates:
    def test_owner_can_add(self, client):
        from listings.models import BlockedDateRange
        user = UserFactory()
        listing = ListingFactory(owner=user)
        client.force_login(user)
        client.post(
            reverse('listings:blocked_date_add', kwargs={'pk': listing.pk}),
            {'start_date': '2026-09-01', 'end_date': '2026-09-07'},
        )
        assert BlockedDateRange.objects.filter(listing=listing).exists()

    def test_non_owner_gets_404(self, client):
        listing = ListingFactory()
        client.force_login(UserFactory())
        response = client.post(
            reverse('listings:blocked_date_add', kwargs={'pk': listing.pk}),
            {'start_date': '2026-09-01', 'end_date': '2026-09-07'},
        )
        assert response.status_code == 404

    def test_owner_can_delete(self, client):
        from listings.models import BlockedDateRange
        user = UserFactory()
        blocked = BlockedDateRangeFactory(listing=ListingFactory(owner=user))
        client.force_login(user)
        client.post(reverse('listings:blocked_date_delete', kwargs={'pk': blocked.pk}))
        assert not BlockedDateRange.objects.filter(pk=blocked.pk).exists()


class TestPhotoDelete:
    def test_owner_can_delete_photo(self, client):
        from listings.models import ListingPhoto
        user = UserFactory()
        photo = ListingPhotoFactory(listing=ListingFactory(owner=user))
        client.force_login(user)
        client.post(reverse('listings:photo_delete', kwargs={'pk': photo.pk}))
        assert not ListingPhoto.objects.filter(pk=photo.pk).exists()

    def test_non_owner_gets_404(self, client):
        photo = ListingPhotoFactory()
        client.force_login(UserFactory())
        assert client.post(reverse('listings:photo_delete', kwargs={'pk': photo.pk})).status_code == 404
