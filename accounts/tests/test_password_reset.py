import pytest
from django.core import mail
from django.urls import reverse
from accounts.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


class TestPasswordResetRequest:
    def test_get_returns_200(self, client):
        assert client.get(reverse('accounts:password_reset')).status_code == 200

    def test_valid_email_sends_email(self, client):
        user = UserFactory()
        client.post(reverse('accounts:password_reset'), {'email': user.email})
        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_unknown_email_sends_no_email(self, client):
        client.post(reverse('accounts:password_reset'), {'email': 'nobody@example.com'})
        assert len(mail.outbox) == 0

    def test_unknown_email_still_redirects_to_done(self, client):
        response = client.post(reverse('accounts:password_reset'), {'email': 'nobody@example.com'})
        assert response.status_code == 302
        assert response.url == reverse('accounts:password_reset_done')

    def test_google_user_no_usable_password_sends_no_email(self, client):
        user = UserFactory()
        user.set_unusable_password()
        user.save()
        client.post(reverse('accounts:password_reset'), {'email': user.email})
        assert len(mail.outbox) == 0


class TestPasswordResetDone:
    def test_returns_200(self, client):
        assert client.get(reverse('accounts:password_reset_done')).status_code == 200

    def test_contains_google_hint(self, client):
        response = client.get(reverse('accounts:password_reset_done'))
        assert 'Google' in response.content.decode()


class TestPasswordResetConfirm:
    def _get_reset_url(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

    def test_valid_link_returns_200(self, client):
        user = UserFactory()
        response = client.get(self._get_reset_url(user))
        assert response.status_code in (200, 302)

    def test_invalid_token_shows_error(self, client):
        response = client.get(
            reverse('accounts:password_reset_confirm',
                    kwargs={'uidb64': 'invalid', 'token': 'invalid'})
        )
        assert response.status_code == 200
        assert 'invalid' in response.content.decode().lower() or 'expired' in response.content.decode().lower()


class TestPasswordResetComplete:
    def test_returns_200(self, client):
        assert client.get(reverse('accounts:password_reset_complete')).status_code == 200
