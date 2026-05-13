from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from bookings.models import Booking
from notifications.models import Notification
from notifications.utils import create_notification
from .forms import MessageForm
from .models import Message


@login_required
def send_message(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)

    is_participant = request.user == booking.listing.owner or request.user == booking.renter
    if not is_participant:
        raise Http404

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                booking=booking,
                sender=request.user,
                body=form.cleaned_data['body'],
            )
            recipient = booking.renter if request.user == booking.listing.owner else booking.listing.owner
            create_notification(recipient, Notification.NEW_MESSAGE, booking)

    return redirect('bookings:detail', pk=booking_pk)


@login_required
def message_list(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)
    if request.user not in (booking.renter, booking.listing.owner):
        raise Http404
    return render(request, 'messaging/messages_partial.html', {
        'booking': booking,
        'messages_list': booking.messages.all(),
    })
