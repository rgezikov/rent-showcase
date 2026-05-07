from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    NEW_BOOKING = 'new_booking'
    BOOKING_CONFIRMED = 'booking_confirmed'
    BOOKING_REJECTED = 'booking_rejected'
    BOOKING_CANCELLED = 'booking_cancelled'
    NEW_MESSAGE = 'new_message'

    EVENT_TYPES = [
        (NEW_BOOKING, _('New booking request')),
        (BOOKING_CONFIRMED, _('Booking confirmed')),
        (BOOKING_REJECTED, _('Booking rejected')),
        (BOOKING_CANCELLED, _('Booking cancelled')),
        (NEW_MESSAGE, _('New message')),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('recipient'),
    )
    event_type = models.CharField(_('event type'), max_length=30, choices=EVENT_TYPES)
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('booking'),
    )
    is_read = models.BooleanField(_('read'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')

    def __str__(self):
        return f'{self.get_event_type_display()} → {self.recipient}'

    def get_text(self):
        title = self.booking.listing.title
        renter_name = self.booking.renter.get_full_name() or self.booking.renter.display_name
        if self.event_type == self.NEW_BOOKING:
            return _('New booking request for "%(title)s" from %(name)s') % {'title': title, 'name': renter_name}
        if self.event_type == self.BOOKING_CONFIRMED:
            return _('Your booking for "%(title)s" was confirmed') % {'title': title}
        if self.event_type == self.BOOKING_REJECTED:
            return _('Your booking for "%(title)s" was rejected') % {'title': title}
        if self.event_type == self.BOOKING_CANCELLED:
            return _('Booking for "%(title)s" was cancelled') % {'title': title}
        if self.event_type == self.NEW_MESSAGE:
            return _('New message in your booking for "%(title)s"') % {'title': title}
        return ''

    def get_link(self):
        return self.booking.get_absolute_url()
