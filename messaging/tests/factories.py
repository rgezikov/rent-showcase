import factory
from factory.django import DjangoModelFactory
from accounts.tests.factories import UserFactory
from bookings.tests.factories import BookingFactory
from messaging.models import Message


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    booking = factory.SubFactory(BookingFactory)
    sender = factory.SubFactory(UserFactory)
    body = factory.Faker('sentence')
    is_system = False
