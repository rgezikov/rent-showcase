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

    max_active_listings_override = models.PositiveIntegerField(
        _('max active listings override'),
        null=True, blank=True,
        help_text=_('Leave blank to use the site-wide default.'),
    )
    max_pending_bookings_override = models.PositiveIntegerField(
        _('max pending bookings override'),
        null=True, blank=True,
        help_text=_('Leave blank to use the site-wide default.'),
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_max_active_listings(self):
        if self.max_active_listings_override is not None:
            return self.max_active_listings_override
        return SiteSettings.get().max_active_listings

    def get_max_pending_bookings(self):
        if self.max_pending_bookings_override is not None:
            return self.max_pending_bookings_override
        return SiteSettings.get().max_pending_bookings

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
    max_active_listings = models.PositiveIntegerField(
        _('max active listings per user'),
        default=20,
        help_text=_('Maximum number of active listings a user can have. Per-user overrides take precedence.'),
    )
    max_pending_bookings = models.PositiveIntegerField(
        _('max pending bookings per user'),
        default=10,
        help_text=_('Maximum number of pending booking requests a user can have at once. Per-user overrides take precedence.'),
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
