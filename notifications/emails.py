from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Notification

SUBJECTS = {
    Notification.NEW_BOOKING:         'New booking request — Rent Showcase',
    Notification.BOOKING_CONFIRMED:   'Booking confirmed — Rent Showcase',
    Notification.BOOKING_REJECTED:    'Booking rejected — Rent Showcase',
    Notification.BOOKING_CANCELLED:   'Booking cancelled — Rent Showcase',
    Notification.NEW_MESSAGE:         'New message — Rent Showcase',
}


def send_notification_email(notification):
    from django.contrib.sites.models import Site
    try:
        domain = Site.objects.get(pk=1).domain
    except Exception:
        domain = 'rent.respobit.eu'

    body = render_to_string('notifications/email/notification.txt', {
        'notification': notification,
        'booking': notification.booking,
        'listing': notification.booking.listing,
        'domain': domain,
    })
    send_mail(
        subject=SUBJECTS.get(notification.event_type, 'Notification — Rent Showcase'),
        message=body,
        from_email=None,
        recipient_list=[notification.recipient.email],
        fail_silently=True,
    )
