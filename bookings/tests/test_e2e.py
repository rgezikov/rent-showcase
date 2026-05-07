import datetime
import pytest

today = datetime.date.today
delta = datetime.timedelta


def _login(page, base_url, email, password='testpass123'):
    page.goto(f'{base_url}/accounts/login/')
    page.fill('#id_username', email)
    page.fill('#id_password', password)
    page.get_by_role('button', name='Log in').click()


def _book(page, base_url, listing_pk, days_ahead=7, duration=2):
    start = today() + delta(days_ahead)
    end = start + delta(duration)
    page.goto(f'{base_url}/bookings/create/{listing_pk}/')
    # Use flatpickr's API to set dates (page.fill bypasses its event listeners)
    page.evaluate(f"document.getElementById('id_start_date')._flatpickr.setDate('{start.isoformat()}')")
    page.evaluate(f"document.getElementById('id_end_date')._flatpickr.setDate('{end.isoformat()}')")
    page.get_by_role('button', name='Send request').click()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_renter_requests_owner_confirms(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    listing = ListingFactory(owner=owner, auto_accept=False)

    # Renter submits request
    _login(page, live_server.url, 'renter@example.com')
    _book(page, live_server.url, listing.pk)
    assert '/bookings/' in page.url
    assert page.locator('span:has-text("Pending")').is_visible()

    booking_url = page.url

    # Owner confirms
    _login(page, live_server.url, 'owner@example.com')
    page.goto(booking_url)
    page.get_by_role('button', name='Confirm').click()
    assert page.locator('span:has-text("Confirmed")').is_visible()

    # Renter sees confirmed
    _login(page, live_server.url, 'renter@example.com')
    page.goto(booking_url)
    assert page.locator('span:has-text("Confirmed")').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_auto_accept_flow(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    listing = ListingFactory(owner=owner, auto_accept=True, auto_accept_message='Your booking is confirmed!')

    _login(page, live_server.url, 'renter@example.com')
    _book(page, live_server.url, listing.pk)

    assert page.locator('span:has-text("Confirmed")').is_visible()
    assert page.locator('text=Your booking is confirmed!').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_owner_rejects_request(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    listing = ListingFactory(owner=owner, auto_accept=False)

    _login(page, live_server.url, 'renter@example.com')
    _book(page, live_server.url, listing.pk)
    booking_url = page.url

    _login(page, live_server.url, 'owner@example.com')
    page.goto(booking_url)
    page.get_by_role('button', name='Reject').click()
    assert page.locator('span:has-text("Rejected")').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_renter_cancels_confirmed_booking(page, live_server):
    from accounts.tests.factories import UserFactory
    from listings.tests.factories import ListingFactory
    owner = UserFactory(email='owner@example.com')
    renter = UserFactory(email='renter@example.com')
    listing = ListingFactory(owner=owner, auto_accept=True, auto_accept_message='Confirmed!')

    _login(page, live_server.url, 'renter@example.com')
    _book(page, live_server.url, listing.pk)
    booking_url = page.url

    page.on('dialog', lambda d: d.accept())
    page.get_by_role('button', name='Cancel booking').click()
    assert page.locator('span:has-text("Cancelled")').is_visible()
