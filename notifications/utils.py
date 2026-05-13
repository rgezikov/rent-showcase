from .models import Notification


def create_notification(recipient, event_type, booking):
    notification = Notification.objects.create(
        recipient=recipient,
        event_type=event_type,
        booking=booking,
    )
    from .emails import send_notification_email
    send_notification_email(notification)
