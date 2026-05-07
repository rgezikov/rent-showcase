import datetime
import pytest

today = datetime.date.today
delta = datetime.timedelta


def _login(page, base_url, email, password='testpass123'):
    page.goto(f'{base_url}/accounts/login/')
    page.fill('#id_username', email)
    page.fill('#id_password', password)
    page.get_by_role('button', name='Log in').click()
    assert page.url == f'{base_url}/'


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_create_listing_appears_on_browse(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import CategoryFactory
    UserFactory(email='owner@example.com')
    CategoryFactory(name='Electronics', slug='electronics')

    _login(page, live_server.url, 'owner@example.com')

    page.goto(f'{live_server.url}/listings/create/')
    page.fill('#id_title', 'Nikon Camera')
    page.fill('#id_description', 'Great camera for rent.')
    page.select_option('#id_category', label='Electronics')
    page.fill('#id_location', 'Helsinki')
    page.fill('#id_price_per_day', '25.00')
    page.get_by_role('button', name='Create listing').click()

    assert '/listings/' in page.url

    page.goto(f'{live_server.url}/listings/')
    assert page.locator('text=Nikon Camera').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_auto_accept_message_field_toggles(page, live_server):
    from accounts.tests.factories import UserFactory
    UserFactory(email='owner@example.com')

    _login(page, live_server.url, 'owner@example.com')
    page.goto(f'{live_server.url}/listings/create/')

    message_field = page.locator('#auto-accept-message-field')
    assert message_field.is_hidden()

    page.check('#id_auto_accept')
    assert message_field.is_visible()

    page.uncheck('#id_auto_accept')
    assert message_field.is_hidden()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_browse_keyword_filter(page, live_server):
    from listings.tests.factories import ListingFactory
    ListingFactory(title='Red Excavator')
    ListingFactory(title='Blue Ladder')

    page.goto(f'{live_server.url}/listings/')
    page.fill('input[name=q]', 'Excavator')
    page.get_by_role('button', name='Search').click()

    assert page.locator('text=Red Excavator').is_visible()
    assert not page.locator('text=Blue Ladder').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_logged_out_sees_no_owner_contact(page, live_server):
    from listings.tests.factories import ListingFactory
    listing = ListingFactory()

    page.goto(f'{live_server.url}{listing.get_absolute_url()}')

    assert page.get_by_role('main').get_by_role('link', name='Log in').is_visible()
    assert not page.locator('text=Edit').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_date_filter_excludes_booked_listing(page, live_server):
    from bookings.models import Booking
    from bookings.tests.factories import BookingFactory
    from listings.tests.factories import ListingFactory

    start = today() + delta(7)
    end = today() + delta(9)
    booked = ListingFactory(title='Booked Drill', quantity=1)
    available = ListingFactory(title='Free Hammer')
    BookingFactory(listing=booked, status=Booking.CONFIRMED, start_date=start, end_date=end, quantity=1)

    page.goto(f'{live_server.url}/listings/')
    page.evaluate(f"document.querySelector('input[name=from_date]')._flatpickr.setDate('{start.isoformat()}')")
    page.evaluate(f"document.querySelector('input[name=to_date]')._flatpickr.setDate('{end.isoformat()}')")
    page.get_by_role('button', name='Search').click()

    assert page.locator('text=Free Hammer').is_visible()
    assert not page.locator('text=Booked Drill').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_owner_deactivates_listing(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    user = UserFactory(email='owner@example.com')
    listing = ListingFactory(owner=user, is_active=True)

    _login(page, live_server.url, 'owner@example.com')
    page.goto(f'{live_server.url}/listings/mine/')
    page.locator('button:has-text("Deactivate")').first.click()

    page.goto(f'{live_server.url}/listings/')
    assert not page.locator(f'text={listing.title}').is_visible()
