from .models import Notification


def create_notification(recipient, event_type, booking):
    Notification.objects.create(
        recipient=recipient,
        event_type=event_type,
        booking=booking,
    )
