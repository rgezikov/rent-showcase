import datetime
from decimal import Decimal

import pytest

from bookings.models import Booking
from bookings.tests.factories import BookingFactory
from listings.tests.factories import ListingFactory

pytestmark = pytest.mark.django_db

today = datetime.date.today
delta = datetime.timedelta


class TestIsAvailable:
    def test_available_when_no_bookings(self):
        listing = ListingFactory(quantity=1)
        assert Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_unavailable_when_overlap(self):
        listing = ListingFactory(quantity=1)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=today() + delta(7),
            end_date=today() + delta(9),
            quantity=1,
        )
        assert not Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_available_with_quantity_remaining(self):
        listing = ListingFactory(quantity=3)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=today() + delta(7),
            end_date=today() + delta(9),
            quantity=2,
        )
        assert Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_unavailable_when_quantity_exceeded(self):
        listing = ListingFactory(quantity=2)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=today() + delta(7),
            end_date=today() + delta(9),
            quantity=2,
        )
        assert not Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_pending_booking_does_not_block(self):
        listing = ListingFactory(quantity=1)
        BookingFactory(
            listing=listing,
            status=Booking.PENDING,
            start_date=today() + delta(7),
            end_date=today() + delta(9),
            quantity=1,
        )
        assert Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_non_overlapping_is_available(self):
        listing = ListingFactory(quantity=1)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=today() + delta(1),
            end_date=today() + delta(3),
            quantity=1,
        )
        assert Booking.is_available(listing, today() + delta(7), today() + delta(9), 1)

    def test_adjacent_dates_are_available(self):
        listing = ListingFactory(quantity=1)
        BookingFactory(
            listing=listing,
            status=Booking.CONFIRMED,
            start_date=today() + delta(1),
            end_date=today() + delta(5),
            quantity=1,
        )
        # Starts the day after existing booking ends
        assert Booking.is_available(listing, today() + delta(6), today() + delta(9), 1)


class TestCalculatePrice:
    def test_price_per_day(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'))
        start = today() + delta(7)
        end = start + delta(2)  # 3 days
        assert Booking.calculate_price(listing, start, end) == Decimal('30.00')

    def test_weekend_price(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), price_per_weekend=Decimal('15.00'))
        start = today() + delta(7)
        end = start + delta(1)  # 2 days
        assert Booking.calculate_price(listing, start, end) == Decimal('15.00')

    def test_week_price(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), price_per_week=Decimal('50.00'))
        start = today() + delta(7)
        end = start + delta(6)  # 7 days
        assert Booking.calculate_price(listing, start, end) == Decimal('50.00')

    def test_week_plus_extra_days(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), price_per_week=Decimal('50.00'))
        start = today() + delta(7)
        end = start + delta(8)  # 9 days = 1 week + 2 days
        assert Booking.calculate_price(listing, start, end) == Decimal('70.00')

    def test_base_fee_added(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), base_fee=Decimal('5.00'))
        start = today() + delta(7)
        end = start  # 1 day
        assert Booking.calculate_price(listing, start, end) == Decimal('15.00')

    def test_no_weekend_price_falls_back_to_daily(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), price_per_weekend=None)
        start = today() + delta(7)
        end = start + delta(1)  # 2 days
        assert Booking.calculate_price(listing, start, end) == Decimal('20.00')

    def test_delivery_fee_added(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), delivery_fee=Decimal('8.00'))
        start = today() + delta(7)
        end = start  # 1 day
        assert Booking.calculate_price(listing, start, end) == Decimal('18.00')

    def test_deposit_not_included_in_price(self):
        listing = ListingFactory(price_per_day=Decimal('10.00'), deposit=Decimal('50.00'))
        start = today() + delta(7)
        end = start  # 1 day
        assert Booking.calculate_price(listing, start, end) == Decimal('10.00')
