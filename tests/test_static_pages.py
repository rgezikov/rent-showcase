import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def _set_language(client, lang):
    client.post(reverse('set_language'), {'language': lang, 'next': '/'})


PAGES = [
    ('about', 'about'),
    ('help', 'help'),
    ('privacy', 'privacy'),
    ('terms', 'terms'),
]


class TestStaticPagesAnonymous:
    @pytest.mark.parametrize('name,_', PAGES)
    def test_returns_200(self, client, name, _):
        response = client.get(reverse(name))
        assert response.status_code == 200

    @pytest.mark.parametrize('name,_', PAGES)
    def test_extends_base(self, client, name, _):
        response = client.get(reverse(name))
        content = response.content.decode()
        assert 'Rent Showcase' in content
        assert '<footer' in content


class TestStaticPagesEnglish:
    def setup_method(self):
        pass

    def test_about_english(self, client):
        _set_language(client, 'en')
        response = client.get(reverse('about'))
        content = response.content.decode()
        assert 'About Rent Showcase' in content
        assert 'peer-to-peer' in content

    def test_help_english(self, client):
        _set_language(client, 'en')
        response = client.get(reverse('help'))
        content = response.content.decode()
        assert 'How to rent equipment' in content
        assert 'How to list equipment for rent' in content

    def test_privacy_english(self, client):
        _set_language(client, 'en')
        response = client.get(reverse('privacy'))
        content = response.content.decode()
        assert 'Privacy Policy' in content
        assert 'GDPR' in content
        assert 'privacy@rent-showcase.fi' in content

    def test_terms_english(self, client):
        _set_language(client, 'en')
        response = client.get(reverse('terms'))
        content = response.content.decode()
        assert 'Terms of Service' in content
        assert 'Governing law' in content


class TestStaticPagesFinnish:
    def test_about_finnish(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('about'))
        content = response.content.decode()
        assert 'Rent Showcase' in content
        assert 'vuokraus' in content

    def test_help_finnish(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('help'))
        content = response.content.decode()
        assert 'vuokrata laitteita' in content
        assert 'ilmoittaa laite vuokralle' in content

    def test_privacy_finnish(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('privacy'))
        content = response.content.decode()
        assert 'Tietosuojaseloste' in content
        assert 'tietosuojavaltuutetulle' in content

    def test_terms_finnish(self, client):
        _set_language(client, 'fi')
        response = client.get(reverse('terms'))
        content = response.content.decode()
        assert 'Käyttöehdot' in content
        assert 'Sovellettava laki' in content


class TestFooterLinks:
    def test_footer_contains_all_links(self, client):
        response = client.get(reverse('home'))
        content = response.content.decode()
        assert '/about/' in content
        assert '/help/' in content
        assert '/privacy/' in content
        assert '/terms/' in content
