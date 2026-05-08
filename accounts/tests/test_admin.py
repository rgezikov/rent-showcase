import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    return UserFactory(is_staff=True, is_superuser=True)


class TestAdminAccess:
    def test_non_staff_redirected(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse('admin:index'))
        assert response.status_code == 302

    def test_staff_can_access(self, client, staff):
        client.force_login(staff)
        assert client.get(reverse('admin:index')).status_code == 200


class TestBlockUserAction:
    def test_block_sets_inactive(self, client, staff):
        target = UserFactory(is_active=True)
        client.force_login(staff)
        client.post(reverse('admin:accounts_user_changelist'), {
            'action': 'block_users',
            '_selected_action': [target.pk],
        })
        target.refresh_from_db()
        assert target.is_active is False

    def test_block_prevents_login(self, client, staff):
        target = UserFactory(is_active=True)
        client.force_login(staff)
        client.post(reverse('admin:accounts_user_changelist'), {
            'action': 'block_users',
            '_selected_action': [target.pk],
        })
        client.logout()
        response = client.post(reverse('accounts:login'), {
            'username': target.email,
            'password': 'testpass123',
        })
        assert not response.wsgi_request.user.is_authenticated

    def test_cannot_block_self(self, client, staff):
        client.force_login(staff)
        client.post(reverse('admin:accounts_user_changelist'), {
            'action': 'block_users',
            '_selected_action': [staff.pk],
        })
        staff.refresh_from_db()
        assert staff.is_active is True

    def test_unblock_sets_active(self, client, staff):
        target = UserFactory(is_active=False)
        client.force_login(staff)
        client.post(reverse('admin:accounts_user_changelist'), {
            'action': 'unblock_users',
            '_selected_action': [target.pk],
        })
        target.refresh_from_db()
        assert target.is_active is True


class TestRegistrationToggle:
    def test_registration_open_by_default(self, client):
        assert client.get(reverse('accounts:register')).status_code == 200

    def test_registration_closed_returns_403(self, client):
        from accounts.models import SiteSettings
        SiteSettings.objects.create(pk=1, registration_open=False)
        assert client.get(reverse('accounts:register')).status_code == 403

    def test_admin_can_toggle_registration(self, client, staff):
        from accounts.models import SiteSettings
        client.force_login(staff)
        # Create settings via admin
        client.post(reverse('admin:accounts_sitesettings_add'), {
            'registration_open': '',  # unchecked = False
        })
        assert SiteSettings.get().registration_open is False
