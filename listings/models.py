from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Listing(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name=_('owner'),
    )
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='listings',
        verbose_name=_('category'),
    )
    location = models.CharField(_('location'), max_length=100)

    price_per_day = models.DecimalField(_('price per day'), max_digits=10, decimal_places=2)
    price_per_weekend = models.DecimalField(_('price per weekend'), max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_week = models.DecimalField(_('price per week'), max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(_('price per month'), max_digits=10, decimal_places=2, null=True, blank=True)
    base_fee = models.DecimalField(_('base fee'), max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_fee = models.DecimalField(_('delivery fee'), max_digits=10, decimal_places=2, null=True, blank=True)
    deposit = models.DecimalField(_('refundable deposit'), max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_days = models.PositiveIntegerField(_('minimum rental period (days)'), null=True, blank=True)
    payment_methods = models.CharField(_('preferred payment methods'), max_length=200, blank=True)

    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    auto_accept = models.BooleanField(_('auto-accept bookings'), default=False)
    auto_accept_message = models.TextField(_('auto-accept message'), blank=True)

    is_active = models.BooleanField(_('active'), default=True)
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('listing')
        verbose_name_plural = _('listings')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('listings:detail', kwargs={'pk': self.pk})

    @property
    def cover_photo(self):
        return self.photos.first()


class ListingPhoto(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('listing'),
    )
    image = models.ImageField(_('image'), upload_to='listings/')
    order = models.PositiveIntegerField(_('order'), default=0)

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return f'Photo {self.pk} for {self.listing}'


class BlockedDateRange(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='blocked_dates',
        verbose_name=_('listing'),
    )
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f'{self.listing} blocked {self.start_date}–{self.end_date}'
