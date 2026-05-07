import pytest
from django.core import mail, signing
from django.urls import reverse
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegisterView:
    def test_get(self, client):
        assert client.get(reverse('accounts:register')).status_code == 200

    def test_valid_post_redirects_to_sent(self, client):
        response = client.post(reverse('accounts:register'), {
            'email': 'new@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'account_type': 'person',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:verify_email_sent')

    def test_sends_verification_email(self, client):
        client.post(reverse('accounts:register'), {
            'email': 'new@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'account_type': 'person',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        })
        assert len(mail.outbox) == 1
        assert 'new@example.com' in mail.outbox[0].to

    def test_invalid_post_shows_form(self, client):
        response = client.post(reverse('accounts:register'), {})
        assert response.status_code == 200
        assert response.context['form'].errors


class TestEmailVerification:
    def _make_token(self, user):
        return signing.dumps({'pk': user.pk, 'email': user.email}, salt='email-verification')

    def test_valid_token_activates_user(self, client):
        user = UserFactory(is_active=False)
        response = client.get(reverse('accounts:verify_email', kwargs={'token': self._make_token(user)}))
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.is_active is True

    def test_bad_token_redirects_to_register(self, client):
        user = UserFactory(is_active=False)
        token = self._make_token(user) + 'corrupted'
        response = client.get(reverse('accounts:verify_email', kwargs={'token': token}))
        assert response.status_code == 302
        assert reverse('accounts:register') in response.url


class TestLoginView:
    def test_get(self, client):
        assert client.get(reverse('accounts:login')).status_code == 200

    def test_inactive_user_cannot_login(self, client):
        user = UserFactory(is_active=False)
        response = client.post(reverse('accounts:login'), {
            'username': user.email,
            'password': 'testpass123',
        })
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_wrong_password_rejected(self, client):
        user = UserFactory()
        response = client.post(reverse('accounts:login'), {
            'username': user.email,
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated


class TestProfileView:
    def test_logged_out_redirects(self, client):
        user = UserFactory()
        response = client.get(reverse('accounts:profile', kwargs={'pk': user.pk}))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_logged_in_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        assert client.get(reverse('accounts:profile', kwargs={'pk': user.pk})).status_code == 200

    def test_inactive_user_returns_404(self, client, user):
        inactive = UserFactory(is_active=False)
        client.force_login(user)
        assert client.get(reverse('accounts:profile', kwargs={'pk': inactive.pk})).status_code == 404


class TestProfileEditView:
    def test_requires_login(self, client):
        assert client.get(reverse('accounts:profile_edit')).status_code == 302

    def test_updates_profile(self, client):
        user = UserFactory(first_name='Old')
        client.force_login(user)
        client.post(reverse('accounts:profile_edit'), {
            'first_name': 'New',
            'last_name': user.last_name,
            'account_type': user.account_type,
            'company_name': '',
        })
        user.refresh_from_db()
        assert user.first_name == 'New'


class TestAccountDeleteView:
    def test_requires_login(self, client):
        assert client.get(reverse('accounts:account_delete')).status_code == 302

    def test_post_deletes_user_and_redirects(self, client):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = UserFactory()
        pk = user.pk
        client.force_login(user)
        response = client.post(reverse('accounts:account_delete'))
        assert response.status_code == 302
        assert not User.objects.filter(pk=pk).exists()
