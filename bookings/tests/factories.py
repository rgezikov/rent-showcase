import datetime
import factory
from factory.django import DjangoModelFactory
from accounts.tests.factories import UserFactory
from listings.tests.factories import ListingFactory
from bookings.models import Booking


class BookingFactory(DjangoModelFactory):
    class Meta:
        model = Booking

    listing = factory.SubFactory(ListingFactory)
    renter = factory.SubFactory(UserFactory)
    start_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))
    end_date = factory.LazyAttribute(lambda o: o.start_date + datetime.timedelta(days=2))
    quantity = 1
    status = Booking.PENDING
    total_price = factory.LazyAttribute(
        lambda o: Booking.calculate_price(o.listing, o.start_date, o.end_date)
    )
