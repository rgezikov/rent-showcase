import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory
from notifications.models import Notification
from notifications.tests.factories import NotificationFactory

pytestmark = pytest.mark.django_db


class TestNotificationList:
    def test_requires_login(self, client):
        assert client.get(reverse('notifications:list')).status_code == 302

    def test_shows_own_notifications(self, client):
        user = UserFactory()
        own = NotificationFactory(recipient=user)
        other = NotificationFactory()
        client.force_login(user)
        response = client.get(reverse('notifications:list'))
        pks = [n.pk for n in response.context['notifications']]
        assert own.pk in pks
        assert other.pk not in pks

    def test_unread_count_in_context(self, client):
        user = UserFactory()
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=True)
        client.force_login(user)
        response = client.get(reverse('notifications:list'))
        assert response.context['unread_notification_count'] == 2


class TestNotificationGoto:
    def test_marks_as_read_and_redirects_to_booking(self, client):
        user = UserFactory()
        notif = NotificationFactory(recipient=user, is_read=False)
        client.force_login(user)
        response = client.get(reverse('notifications:goto', kwargs={'pk': notif.pk}))
        assert response.status_code == 302
        assert notif.booking.get_absolute_url() in response.url
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_other_user_gets_404(self, client):
        notif = NotificationFactory()
        client.force_login(UserFactory())
        assert client.get(reverse('notifications:goto', kwargs={'pk': notif.pk})).status_code == 404


class TestMarkAllRead:
    def test_marks_all_unread_as_read(self, client):
        user = UserFactory()
        n1 = NotificationFactory(recipient=user, is_read=False)
        n2 = NotificationFactory(recipient=user, is_read=False)
        client.force_login(user)
        client.post(reverse('notifications:mark_all_read'))
        n1.refresh_from_db()
        n2.refresh_from_db()
        assert n1.is_read and n2.is_read

    def test_does_not_affect_other_users(self, client):
        user = UserFactory()
        other_notif = NotificationFactory(is_read=False)
        client.force_login(user)
        client.post(reverse('notifications:mark_all_read'))
        other_notif.refresh_from_db()
        assert not other_notif.is_read

    def test_requires_post(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse('notifications:mark_all_read'))
        assert response.status_code == 302  # redirects without marking
