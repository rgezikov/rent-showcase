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
