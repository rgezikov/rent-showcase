import pytest
from listings.forms import BlockedDateRangeForm, ListingForm
from listings.tests.factories import CategoryFactory

pytestmark = pytest.mark.django_db


class TestBlockedDateRangeForm:
    def test_valid_range(self):
        assert BlockedDateRangeForm(data={'start_date': '2026-08-01', 'end_date': '2026-08-05'}).is_valid()

    def test_same_day_is_valid(self):
        assert BlockedDateRangeForm(data={'start_date': '2026-08-01', 'end_date': '2026-08-01'}).is_valid()

    def test_end_before_start_is_invalid(self):
        assert not BlockedDateRangeForm(data={'start_date': '2026-08-05', 'end_date': '2026-08-01'}).is_valid()


class TestListingForm:
    def _data(self, **kwargs):
        cat = CategoryFactory()
        return {
            'title': 'Test Drill',
            'description': 'A powerful drill for rent.',
            'category': cat.pk,
            'location': 'Helsinki',
            'price_per_day': '15.00',
            'quantity': 1,
            **kwargs,
        }

    def test_valid_minimal(self):
        assert ListingForm(data=self._data()).is_valid()

    def test_auto_accept_requires_message(self):
        form = ListingForm(data=self._data(auto_accept=True, auto_accept_message=''))
        assert not form.is_valid()
        assert 'auto_accept_message' in form.errors

    def test_auto_accept_with_message_is_valid(self):
        form = ListingForm(data=self._data(auto_accept=True, auto_accept_message='Confirmed!'))
        assert form.is_valid()

    def test_no_auto_accept_message_not_required(self):
        form = ListingForm(data=self._data(auto_accept=False, auto_accept_message=''))
        assert form.is_valid()
