import pytest


def _login(page, base_url, email, password='testpass123'):
    page.goto(f'{base_url}/accounts/login/')
    page.fill('#id_username', email)
    page.fill('#id_password', password)
    page.get_by_role('button', name='Log in').click()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_bell_badge_shows_unread_count(page, live_server):
    from accounts.tests.factories import UserFactory
    from notifications.tests.factories import NotificationFactory

    user = UserFactory(email='user@example.com')
    NotificationFactory(recipient=user, is_read=False)
    NotificationFactory(recipient=user, is_read=False)

    _login(page, live_server.url, 'user@example.com')
    assert page.locator('span.bg-red-500:has-text("2")').is_visible()


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_clicking_notification_marks_as_read(page, live_server):
    from accounts.tests.factories import UserFactory
    from notifications.tests.factories import NotificationFactory

    user = UserFactory(email='user@example.com')
    notif = NotificationFactory(recipient=user, is_read=False)

    _login(page, live_server.url, 'user@example.com')
    page.goto(f'{live_server.url}/notifications/')

    page.locator(f'a[href*="/notifications/{notif.pk}/goto/"]').click()

    notif.refresh_from_db()
    assert notif.is_read is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_mark_all_read_clears_badge(page, live_server):
    from accounts.tests.factories import UserFactory
    from notifications.tests.factories import NotificationFactory

    user = UserFactory(email='user@example.com')
    NotificationFactory(recipient=user, is_read=False)
    NotificationFactory(recipient=user, is_read=False)

    _login(page, live_server.url, 'user@example.com')
    page.goto(f'{live_server.url}/notifications/')
    page.get_by_role('button', name='Mark all as read').click()

    assert not page.locator('a[href="/notifications/"] span.bg-red-500').is_visible()
