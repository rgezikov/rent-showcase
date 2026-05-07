import datetime
import pytest
from bookings.forms import BookingForm
from listings.tests.factories import ListingFactory

pytestmark = pytest.mark.django_db

today = datetime.date.today
delta = datetime.timedelta


def _form(listing, **kwargs):
    start = today() + delta(7)
    data = {
        'start_date': start.isoformat(),
        'end_date': (start + delta(2)).isoformat(),
        'quantity': 1,
        **kwargs,
    }
    return BookingForm(listing, data=data)


class TestBookingForm:
    def test_valid(self):
        assert _form(ListingFactory()).is_valid()

    def test_end_before_start(self):
        start = today() + delta(7)
        listing = ListingFactory()
        form = BookingForm(listing, data={
            'start_date': (start + delta(2)).isoformat(),
            'end_date': start.isoformat(),
            'quantity': 1,
        })
        assert not form.is_valid()

    def test_start_in_past(self):
        listing = ListingFactory()
        form = BookingForm(listing, data={
            'start_date': (today() - delta(1)).isoformat(),
            'end_date': today().isoformat(),
            'quantity': 1,
        })
        assert not form.is_valid()

    def test_unavailable_dates_rejected(self):
        from bookings.models import Booking
        from bookings.tests.factories import BookingFactory
        listing = ListingFactory(quantity=1)
        start = today() + delta(7)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=start,
            end_date=start + delta(2),
            quantity=1,
        )
        form = _form(listing, start_date=start.isoformat(), end_date=(start + delta(2)).isoformat())
        assert not form.is_valid()

    def test_quantity_field_hidden_for_single_unit(self):
        listing = ListingFactory(quantity=1)
        form = BookingForm(listing)
        from django.forms import HiddenInput
        assert isinstance(form.fields['quantity'].widget, HiddenInput)

    def test_quantity_field_visible_for_multi_unit(self):
        listing = ListingFactory(quantity=5)
        form = BookingForm(listing)
        from django.forms import HiddenInput
        assert not isinstance(form.fields['quantity'].widget, HiddenInput)
