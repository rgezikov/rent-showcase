import pytest


def _login(page, base_url, email, password='testpass123'):
    page.goto(f'{base_url}/accounts/login/')
    page.fill('#id_username', email)
    page.fill('#id_password', password)
    page.get_by_role('button', name='Log in').click()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_owner_and_renter_exchange_messages(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    from bookings.tests.factories import BookingFactory
    from bookings.models import Booking

    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    booking = BookingFactory(
        listing=ListingFactory(owner=owner),
        renter=renter,
        status=Booking.CONFIRMED,
    )
    booking_url = f'{live_server.url}{booking.get_absolute_url()}'

    # Renter sends a message
    _login(page, live_server.url, 'renter@example.com')
    page.goto(booking_url)
    page.fill('textarea', 'Is the equipment available early?')
    page.get_by_role('button', name='Send').click()

    assert page.locator('text=Is the equipment available early?').is_visible()

    # Owner replies
    _login(page, live_server.url, 'owner@example.com')
    page.goto(booking_url)
    assert page.locator('text=Is the equipment available early?').is_visible()
    page.fill('textarea', 'Yes, from 8am!')
    page.get_by_role('button', name='Send').click()

    assert page.locator('text=Yes, from 8am!').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_disclaimer_visible_in_thread(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    from bookings.tests.factories import BookingFactory
    from bookings.models import Booking

    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    booking = BookingFactory(
        listing=ListingFactory(owner=owner),
        renter=renter,
        status=Booking.CONFIRMED,
    )

    _login(page, live_server.url, 'renter@example.com')
    page.goto(f'{live_server.url}{booking.get_absolute_url()}')

    assert page.locator('text=Be cautious').is_visible()
