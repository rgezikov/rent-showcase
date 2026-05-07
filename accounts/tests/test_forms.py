import pytest
from accounts.forms import RegistrationForm
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _reg_data(**kwargs):
    return {
        'email': 'new@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'account_type': 'person',
        'password1': 'strongpass123',
        'password2': 'strongpass123',
        **kwargs,
    }


class TestRegistrationForm:
    def test_valid_person(self):
        assert RegistrationForm(data=_reg_data()).is_valid()

    def test_valid_company(self):
        form = RegistrationForm(data=_reg_data(account_type='company', company_name='Acme Corp'))
        assert form.is_valid()

    def test_duplicate_email_rejected(self):
        UserFactory(email='existing@example.com')
        form = RegistrationForm(data=_reg_data(email='existing@example.com'))
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_password_mismatch(self):
        form = RegistrationForm(data=_reg_data(password2='different'))
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_company_without_name_rejected(self):
        form = RegistrationForm(data=_reg_data(account_type='company', company_name=''))
        assert not form.is_valid()
        assert 'company_name' in form.errors

    def test_first_name_required(self):
        form = RegistrationForm(data=_reg_data(first_name=''))
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_last_name_required(self):
        form = RegistrationForm(data=_reg_data(last_name=''))
        assert not form.is_valid()
        assert 'last_name' in form.errors
