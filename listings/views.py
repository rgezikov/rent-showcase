import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from .forms import ListingForm, PhotoUploadForm, BlockedDateRangeForm
from .models import Category, Listing, ListingPhoto, BlockedDateRange


def listing_list(request):
    listings = Listing.objects.filter(is_active=True).select_related('category', 'owner')

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    location = request.GET.get('location', '').strip()
    from_date_raw = request.GET.get('from_date', '').strip()
    to_date_raw = request.GET.get('to_date', '').strip()

    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    if category_slug:
        listings = listings.filter(category__slug=category_slug)
    if location:
        listings = listings.filter(location__icontains=location)

    from_date = to_date = None
    if from_date_raw and to_date_raw:
        try:
            from_date = datetime.date.fromisoformat(from_date_raw)
            to_date = datetime.date.fromisoformat(to_date_raw)
            if from_date <= to_date:
                from bookings.models import Booking
                blocked_ids = BlockedDateRange.objects.filter(
                    start_date__lte=to_date,
                    end_date__gte=from_date,
                ).values_list('listing_id', flat=True)
                listings = listings.exclude(pk__in=blocked_ids)
                available_pks = [
                    l.pk for l in listings
                    if Booking.is_available(l, from_date, to_date, 1)
                ]
                listings = listings.filter(pk__in=available_pks)
        except ValueError:
            from_date = to_date = None

    categories = Category.objects.all()
    return render(request, 'listings/listing_list.html', {
        'listings': listings,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
        'selected_location': location,
        'from_date': from_date_raw,
        'to_date': to_date_raw,
    })


def listing_detail(request, pk):
    from bookings.models import Booking
    listing = get_object_or_404(Listing, pk=pk, is_active=True)
    blocked_dates = listing.blocked_dates.all()
    booked_dates = Booking.objects.filter(
        listing=listing, status=Booking.CONFIRMED
    ).order_by('start_date')
    blocked_form = None
    photo_form = None

    is_owner = request.user.is_authenticated and request.user == listing.owner

    if not is_owner:
        Listing.objects.filter(pk=listing.pk).update(view_count=models.F('view_count') + 1)

    if is_owner:
        blocked_form = BlockedDateRangeForm()
        photo_form = PhotoUploadForm()

    return render(request, 'listings/listing_detail.html', {
        'listing': listing,
        'blocked_dates': blocked_dates,
        'booked_dates': booked_dates,
        'blocked_form': blocked_form,
        'photo_form': photo_form,
        'is_owner': is_owner,
    })


@login_required
def listing_create(request):
    active_count = request.user.listings.filter(is_active=True).count()
    if active_count >= request.user.get_max_active_listings():
        messages.error(request, _(
            'You have reached the maximum number of active listings (%(max)s).'
        ) % {'max': request.user.get_max_active_listings()})
        return redirect('listings:my_listings')

    if request.method == 'POST':
        form = ListingForm(request.POST)
        photo_form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid() and photo_form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            _save_photos(photo_form.cleaned_data['images'], listing)
            messages.success(request, _('Listing created.'))
            return redirect('listings:detail', pk=listing.pk)
    else:
        form = ListingForm()
        photo_form = PhotoUploadForm()
    return render(request, 'listings/listing_form.html', {
        'form': form,
        'photo_form': photo_form,
        'action': _('Create listing'),
    })


@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        photo_form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid() and photo_form.is_valid():
            form.save()
            _save_photos(photo_form.cleaned_data['images'], listing)
            messages.success(request, _('Listing updated.'))
            return redirect('listings:detail', pk=listing.pk)
    else:
        form = ListingForm(instance=listing)
        photo_form = PhotoUploadForm()
    return render(request, 'listings/listing_form.html', {
        'form': form,
        'photo_form': photo_form,
        'listing': listing,
        'action': _('Edit listing'),
    })


@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == 'POST':
        listing.delete()
        messages.success(request, _('Listing deleted.'))
        return redirect('listings:my_listings')
    return render(request, 'listings/listing_delete_confirm.html', {'listing': listing})


@login_required
def listing_toggle_active(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == 'POST':
        listing.is_active = not listing.is_active
        listing.save(update_fields=['is_active'])
        status = _('activated') if listing.is_active else _('deactivated')
        messages.success(request, _(f'Listing {status}.'))
    return redirect('listings:my_listings')


@login_required
def my_listings(request):
    from bookings.models import Booking
    listings = (
        Listing.objects
        .filter(owner=request.user)
        .prefetch_related('photos')
        .annotate(
            total_requests=Count('bookings'),
            confirmed_bookings=Count(
                'bookings',
                filter=models.Q(bookings__status__in=[Booking.CONFIRMED, Booking.COMPLETED])
            ),
            total_revenue=Sum(
                'bookings__total_price',
                filter=models.Q(bookings__status__in=[Booking.CONFIRMED, Booking.COMPLETED])
            ),
        )
    )
    return render(request, 'listings/my_listings.html', {'listings': listings})


@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(ListingPhoto, pk=pk, listing__owner=request.user)
    listing_pk = photo.listing_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
    return redirect('listings:detail', pk=listing_pk)


@login_required
def blocked_date_add(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = BlockedDateRangeForm(request.POST)
        if form.is_valid():
            blocked = form.save(commit=False)
            blocked.listing = listing
            blocked.save()
            messages.success(request, _('Dates blocked.'))
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    return redirect('listings:detail', pk=pk)


@login_required
def blocked_date_delete(request, pk):
    blocked = get_object_or_404(BlockedDateRange, pk=pk, listing__owner=request.user)
    listing_pk = blocked.listing_id
    if request.method == 'POST':
        blocked.delete()
    return redirect('listings:detail', pk=listing_pk)


def _save_photos(images, listing):
    for image in images:
        ListingPhoto.objects.create(listing=listing, image=image)
