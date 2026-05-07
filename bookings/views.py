from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from listings.models import Listing
from notifications.models import Notification
from notifications.utils import create_notification
from .forms import BookingForm
from .models import Booking


@login_required
def booking_create(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk, is_active=True)

    if listing.owner == request.user:
        messages.error(request, _('You cannot book your own listing.'))
        return redirect('listings:detail', pk=listing_pk)

    if request.method == 'POST':
        form = BookingForm(listing, request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.listing = listing
            booking.renter = request.user
            booking.total_price = Booking.calculate_price(
                listing, form.cleaned_data['start_date'], form.cleaned_data['end_date']
            )

            if listing.auto_accept:
                booking.status = Booking.CONFIRMED
                booking.save()
                _post_auto_accept_message(booking, listing)
                create_notification(listing.owner, Notification.NEW_BOOKING, booking)
                create_notification(request.user, Notification.BOOKING_CONFIRMED, booking)
                messages.success(request, _('Booking confirmed automatically.'))
            else:
                booking.save()
                create_notification(listing.owner, Notification.NEW_BOOKING, booking)
                messages.success(request, _('Booking request sent. The owner will respond shortly.'))

            return redirect('bookings:detail', pk=booking.pk)
    else:
        form = BookingForm(listing)

    return render(request, 'bookings/booking_form.html', {
        'form': form,
        'listing': listing,
    })


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    is_owner = request.user == booking.listing.owner
    is_renter = request.user == booking.renter

    if not (is_owner or is_renter):
        from django.http import Http404
        raise Http404

    from messaging.forms import MessageForm
    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'is_owner': is_owner,
        'is_renter': is_renter,
        'message_form': MessageForm(),
    })


@login_required
def booking_confirm(request, pk):
    booking = get_object_or_404(Booking, pk=pk, listing__owner=request.user, status=Booking.PENDING)
    if request.method == 'POST':
        booking.status = Booking.CONFIRMED
        booking.save(update_fields=['status', 'updated_at'])
        create_notification(booking.renter, Notification.BOOKING_CONFIRMED, booking)
        messages.success(request, _('Booking confirmed.'))
        return redirect('bookings:detail', pk=pk)
    return redirect('bookings:detail', pk=pk)


@login_required
def booking_reject(request, pk):
    booking = get_object_or_404(Booking, pk=pk, listing__owner=request.user, status=Booking.PENDING)
    if request.method == 'POST':
        booking.status = Booking.REJECTED
        booking.save(update_fields=['status', 'updated_at'])
        create_notification(booking.renter, Notification.BOOKING_REJECTED, booking)
        messages.success(request, _('Booking rejected.'))
        return redirect('bookings:detail', pk=pk)
    return redirect('bookings:detail', pk=pk)


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    is_owner = request.user == booking.listing.owner
    is_renter = request.user == booking.renter

    if not (is_owner or is_renter):
        from django.http import Http404
        raise Http404

    cancellable = booking.status in (Booking.PENDING, Booking.CONFIRMED)
    if request.method == 'POST' and cancellable:
        booking.status = Booking.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        if is_renter:
            create_notification(booking.listing.owner, Notification.BOOKING_CANCELLED, booking)
        else:
            create_notification(booking.renter, Notification.BOOKING_CANCELLED, booking)
        messages.success(request, _('Booking cancelled.'))
        return redirect('bookings:detail', pk=pk)

    return redirect('bookings:detail', pk=pk)


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects
        .filter(renter=request.user)
        .select_related('listing', 'listing__owner')
        .prefetch_related('listing__photos')
    )
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def booking_requests(request):
    pending = (
        Booking.objects
        .filter(listing__owner=request.user, status=Booking.PENDING)
        .select_related('listing', 'renter')
    )
    active = (
        Booking.objects
        .filter(listing__owner=request.user, status=Booking.CONFIRMED)
        .select_related('listing', 'renter')
    )
    return render(request, 'bookings/booking_requests.html', {
        'pending': pending,
        'active': active,
    })


def _post_auto_accept_message(booking, listing):
    if listing.auto_accept_message:
        from messaging.models import Message
        Message.objects.create(
            booking=booking,
            sender=listing.owner,
            body=listing.auto_accept_message,
            is_system=True,
        )
