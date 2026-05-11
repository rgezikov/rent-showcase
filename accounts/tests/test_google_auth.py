import pytest
from unittest.mock import MagicMock, patch
from django.test import RequestFactory
from accounts.adapters import SocialAccountAdapter
from accounts.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def _make_sociallogin(email='google@example.com', given_name='Jane', family_name='Smith'):
    """Build a minimal mock sociallogin as allauth would provide."""
    user = UserFactory.build(
        email=email,
        first_name='',
        last_name='',
        account_type='person',
        is_active=False,
    )
    user.pk = None

    account = MagicMock()
    account.extra_data = {
        'email': email,
        'given_name': given_name,
        'family_name': family_name,
    }

    sociallogin = MagicMock()
    sociallogin.account = account
    sociallogin.user = user
    return sociallogin


class TestSocialAccountAdapter:
    def setup_method(self):
        self.adapter = SocialAccountAdapter()
        self.request = RequestFactory().get('/')

    def test_save_user_sets_person_account_type(self):
        sociallogin = _make_sociallogin()
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.save_user',
                   return_value=UserFactory(
                       email='google@example.com',
                       first_name='',
                       last_name='',
                       account_type='person',
                       is_active=False,
                   )) as mock_save:
            user = self.adapter.save_user(self.request, sociallogin)
            assert user.account_type == 'person'

    def test_save_user_sets_active(self):
        sociallogin = _make_sociallogin()
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.save_user',
                   return_value=UserFactory(
                       email='google@example.com',
                       is_active=False,
                       account_type='person',
                   )):
            user = self.adapter.save_user(self.request, sociallogin)
            assert user.is_active is True

    def test_save_user_copies_name_from_google(self):
        sociallogin = _make_sociallogin(given_name='Jane', family_name='Smith')
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.save_user',
                   return_value=UserFactory(
                       email='google@example.com',
                       first_name='',
                       last_name='',
                       account_type='person',
                       is_active=True,
                   )):
            user = self.adapter.save_user(self.request, sociallogin)
            assert user.first_name == 'Jane'
            assert user.last_name == 'Smith'

    def test_save_user_does_not_overwrite_existing_name(self):
        sociallogin = _make_sociallogin(given_name='Jane', family_name='Smith')
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.save_user',
                   return_value=UserFactory(
                       email='google@example.com',
                       first_name='Existing',
                       last_name='Name',
                       account_type='person',
                       is_active=True,
                   )):
            user = self.adapter.save_user(self.request, sociallogin)
            assert user.first_name == 'Existing'
            assert user.last_name == 'Name'

    def test_is_open_for_signup_respects_site_settings(self):
        from accounts.models import SiteSettings
        settings = SiteSettings.get()

        settings.registration_open = True
        settings.save()
        assert self.adapter.is_open_for_signup(self.request, MagicMock()) is True

        settings.registration_open = False
        settings.save()
        assert self.adapter.is_open_for_signup(self.request, MagicMock()) is False
