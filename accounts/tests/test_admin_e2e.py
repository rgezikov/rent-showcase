import pytest


@pytest.mark.django_db(transaction=True)
@pytest.mark.e2e
def test_admin_blocks_user_prevents_login(page, live_server):
    from accounts.tests.factories import UserFactory

    staff = UserFactory(email='admin@example.com', is_staff=True, is_superuser=True)
    target = UserFactory(email='target@example.com')

    # Log in to admin
    page.goto(f'{live_server.url}/admin/')
    page.fill('#id_username', 'admin@example.com')
    page.fill('#id_password', 'testpass123')
    page.get_by_role('button', name='Log in').click()

    # Navigate to user list and block the target
    page.goto(f'{live_server.url}/admin/accounts/user/')
    page.locator(f'input[name="_selected_action"][value="{target.pk}"]').check()
    page.select_option('select[name="action"]', 'block_users')
    page.get_by_role('button', name='Go').click()

    # Confirm target cannot log in
    page.goto(f'{live_server.url}/accounts/login/')
    page.fill('#id_username', 'target@example.com')
    page.fill('#id_password', 'testpass123')
    page.get_by_role('button', name='Log in').click()
    assert '/accounts/login/' in page.url
