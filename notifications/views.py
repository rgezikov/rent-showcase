from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Notification


@login_required
def notification_list(request):
    notifications = (
        request.user.notifications
        .select_related('booking__listing')
    )
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@login_required
def notification_goto(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return redirect(notification.get_link())


@login_required
def unread_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return render(request, 'notifications/badge_fragment.html', {
        'unread_notification_count': count,
    })


@login_required
def notification_mark_all_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications:list')
