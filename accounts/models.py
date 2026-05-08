from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    PERSON = 'person'
    COMPANY = 'company'
    ACCOUNT_TYPE_CHOICES = [
        (PERSON, _('Person')),
        (COMPANY, _('Company')),
    ]

    email = models.EmailField(_('email address'), unique=True)

    account_type = models.CharField(
        _('account type'),
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default=PERSON,
    )
    company_name = models.CharField(_('company name'), max_length=200, blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True)
    bio = models.TextField(_('bio'), blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    @property
    def is_company(self):
        return self.account_type == self.COMPANY

    @property
    def display_name(self):
        if self.is_company and self.company_name:
            return self.company_name
        return self.get_full_name() or self.username


class SiteSettings(models.Model):
    registration_open = models.BooleanField(
        _('registration open'),
        default=True,
        help_text=_('Uncheck to prevent new user registrations.'),
    )

    class Meta:
        verbose_name = _('site settings')
        verbose_name_plural = _('site settings')

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
