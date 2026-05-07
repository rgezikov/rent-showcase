import datetime
import factory
from factory.django import DjangoModelFactory
from accounts.tests.factories import UserFactory
from listings.models import Category, Listing, ListingPhoto, BlockedDateRange


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')


class ListingFactory(DjangoModelFactory):
    class Meta:
        model = Listing

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Listing {n}')
    description = factory.Faker('paragraph')
    category = factory.SubFactory(CategoryFactory)
    location = factory.Faker('city')
    price_per_day = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=1)
    quantity = 1
    is_active = True


class ListingPhotoFactory(DjangoModelFactory):
    class Meta:
        model = ListingPhoto

    listing = factory.SubFactory(ListingFactory)
    image = factory.django.ImageField(color='blue')
    order = factory.Sequence(lambda n: n)


class BlockedDateRangeFactory(DjangoModelFactory):
    class Meta:
        model = BlockedDateRange

    listing = factory.SubFactory(ListingFactory)
    start_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))
    end_date = factory.LazyAttribute(lambda o: o.start_date + datetime.timedelta(days=2))
