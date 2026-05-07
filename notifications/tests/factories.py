import factory
from factory.django import DjangoModelFactory
from accounts.tests.factories import UserFactory
from bookings.tests.factories import BookingFactory
from notifications.models import Notification


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    event_type = Notification.NEW_BOOKING
    booking = factory.SubFactory(BookingFactory)
    is_read = False
