import pytest
from accounts.tests.factories import UserFactory, CompanyUserFactory

pytestmark = pytest.mark.django_db


class TestDisplayName:
    def test_company_returns_company_name(self):
        user = CompanyUserFactory(company_name='Acme Corp')
        assert user.display_name == 'Acme Corp'

    def test_person_returns_full_name(self):
        user = UserFactory(first_name='John', last_name='Doe')
        assert user.display_name == 'John Doe'

    def test_falls_back_to_username_when_no_name(self):
        user = UserFactory(first_name='', last_name='')
        assert user.display_name == user.username

    def test_company_without_name_falls_back_to_full_name(self):
        user = CompanyUserFactory(company_name='', first_name='Jane', last_name='Smith')
        assert user.display_name == 'Jane Smith'


class TestIsCompany:
    def test_company_account(self):
        user = CompanyUserFactory()
        assert user.is_company is True

    def test_person_account(self):
        user = UserFactory()
        assert user.is_company is False
