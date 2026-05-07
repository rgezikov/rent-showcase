from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Booking(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (CONFIRMED, _('Confirmed')),
        (REJECTED, _('Rejected')),
        (CANCELLED, _('Cancelled')),
        (COMPLETED, _('Completed')),
    ]

    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('listing'),
    )
    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('renter'),
    )
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    note = models.TextField(_('note'), blank=True)
    status = models.CharField(
        _('status'), max_length=20, choices=STATUS_CHOICES, default=PENDING,
    )
    total_price = models.DecimalField(
        _('total price'), max_digits=10, decimal_places=2, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')
        ordering = ['-created_at']

    def __str__(self):
        return f'Booking #{self.pk} — {self.listing} ({self.status})'

    def get_absolute_url(self):
        return reverse('bookings:detail', kwargs={'pk': self.pk})

    @classmethod
    def is_available(cls, listing, start_date, end_date, quantity, exclude_pk=None):
        qs = cls.objects.filter(
            listing=listing,
            status=cls.CONFIRMED,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        booked = qs.aggregate(total=Sum('quantity'))['total'] or 0
        return (booked + quantity) <= listing.quantity

    @staticmethod
    def calculate_price(listing, start_date, end_date):
        days = (end_date - start_date).days + 1

        if days >= 28 and listing.price_per_month:
            months = days // 30
            remaining = days % 30
            price = listing.price_per_month * months + listing.price_per_day * remaining
        elif days >= 7 and listing.price_per_week:
            weeks = days // 7
            remaining = days % 7
            price = listing.price_per_week * weeks + listing.price_per_day * remaining
        elif days == 2 and listing.price_per_weekend:
            price = listing.price_per_weekend
        else:
            price = listing.price_per_day * days

        if listing.base_fee:
            price += listing.base_fee

        return price.quantize(Decimal('0.01'))
