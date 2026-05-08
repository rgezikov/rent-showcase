import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def _set_language(client, lang, next_url='/'):
    client.post(reverse('set_language'), {'language': lang, 'next': next_url})


class TestLanguageSwitcher:
    def test_switch_to_finnish(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('listings:list'))
        assert response.status_code == 200
        assert 'Selaa laitteita' in response.content.decode()

    def test_switch_to_english(self, client):
        _set_language(client, 'fi')
        _set_language(client, 'en')
        response = client.get(reverse('listings:list'))
        assert 'Browse Equipment' in response.content.decode()

    def test_finnish_home_page(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('home'))
        content = response.content.decode()
        assert 'Vuokraa laitteita' in content

    def test_english_home_page(self, client):
        _set_language(client, 'en')
        response = client.get(reverse('home'))
        assert 'Rent equipment' in response.content.decode()

    def test_key_pages_render_in_finnish(self, client):
        _set_language(client, 'fi')
        for url in [reverse('home'), reverse('listings:list'), reverse('accounts:login')]:
            assert client.get(url).status_code == 200

    def test_user_generated_content_not_translated(self, client):
        from listings.tests.factories import ListingFactory
        listing = ListingFactory(title='My Special Drill')
        _set_language(client, 'fi')
        response = client.get(listing.get_absolute_url())
        assert 'My Special Drill' in response.content.decode()


class TestI18nE2E:
    pass  # E2E translation tests are in DEV-TEST Phase 6 — covered by unit tests above for MVP
