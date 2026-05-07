import pytest
from listings.tests.factories import ListingFactory, ListingPhotoFactory

pytestmark = pytest.mark.django_db


class TestCoverPhoto:
    def test_returns_first_photo(self):
        listing = ListingFactory()
        photo1 = ListingPhotoFactory(listing=listing, order=0)
        ListingPhotoFactory(listing=listing, order=1)
        assert listing.cover_photo == photo1

    def test_returns_none_when_no_photos(self):
        assert ListingFactory().cover_photo is None


class TestGetAbsoluteUrl:
    def test_contains_pk(self):
        listing = ListingFactory()
        assert f'/listings/{listing.pk}/' in listing.get_absolute_url()
