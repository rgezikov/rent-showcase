import pytest
from django.core import mail


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_register_verify_login(page, live_server):
    base = live_server.url

    page.goto(f'{base}/accounts/register/')
    page.fill('#id_email', 'e2euser@example.com')
    page.fill('#id_first_name', 'Jane')
    page.fill('#id_last_name', 'Smith')
    page.select_option('#id_account_type', 'person')
    page.fill('#id_password1', 'strongpass123')
    page.fill('#id_password2', 'strongpass123')
    page.get_by_role('button', name='Create account').click()

    assert '/verify-email/sent/' in page.url

    assert len(mail.outbox) == 1
    # The verification URL is on its own line in the email body
    verify_url = next(
        line.strip() for line in mail.outbox[0].body.splitlines()
        if line.strip().startswith('http')
    )

    page.goto(verify_url)
    assert '/accounts/login/' in page.url

    page.fill('#id_username', 'e2euser@example.com')
    page.fill('#id_password', 'strongpass123')
    page.get_by_role('button', name='Log in').click()

    assert page.url == f'{base}/'


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_login_wrong_password_shows_error(page, live_server):
    from accounts.tests.factories import UserFactory
    UserFactory(email='user@example.com')

    page.goto(f'{live_server.url}/accounts/login/')
    page.fill('#id_username', 'user@example.com')
    page.fill('#id_password', 'wrongpassword')
    page.get_by_role('button', name='Log in').click()

    assert '/accounts/login/' in page.url
    assert page.locator('text=Please enter a correct').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_logout(page, live_server):
    from accounts.tests.factories import UserFactory
    UserFactory(email='logout@example.com')

    page.goto(f'{live_server.url}/accounts/login/')
    page.fill('#id_username', 'logout@example.com')
    page.fill('#id_password', 'testpass123')
    page.get_by_role('button', name='Log in').click()
    assert page.url == f'{live_server.url}/'

    page.get_by_role('button', name='Log out').click()
    assert page.url == f'{live_server.url}/'
    assert page.get_by_role('link', name='Log in').first.is_visible()
