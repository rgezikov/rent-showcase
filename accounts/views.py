import json

from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .forms import RegistrationForm, EmailLoginForm, ProfileEditForm
from .models import SiteSettings

User = get_user_model()

_VERIFY_SALT = 'email-verification'
_VERIFY_MAX_AGE = 86400  # 24 hours


def _send_verification_email(request, user):
    token = signing.dumps({'pk': user.pk, 'email': user.email}, salt=_VERIFY_SALT)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': token})
    )
    subject = render_to_string('accounts/email/verification_subject.txt').strip()
    body = render_to_string('accounts/email/verification_body.txt', {
        'user': user,
        'verify_url': verify_url,
    })
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if not SiteSettings.get().registration_open:
        return render(request, 'accounts/registration_closed.html', status=403)
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            return redirect('accounts:verify_email_sent')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email_sent(request):
    return render(request, 'accounts/verify_email_sent.html')


def verify_email(request, token):
    try:
        data = signing.loads(token, salt=_VERIFY_SALT, max_age=_VERIFY_MAX_AGE)
    except signing.SignatureExpired:
        messages.error(request, _('The verification link has expired. Please register again.'))
        return redirect('accounts:register')
    except signing.BadSignature:
        messages.error(request, _('Invalid verification link.'))
        return redirect('accounts:register')

    user = get_object_or_404(User, pk=data['pk'], email=data['email'])
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=['is_active'])
    messages.success(request, _('Email verified! You can now log in.'))
    return redirect('accounts:login')


class EmailLoginView(LoginView):
    form_class = EmailLoginForm
    template_name = 'accounts/login.html'


class CustomLogoutView(LogoutView):
    next_page = 'home'


@login_required
def profile_view(request, pk):
    profile_user = get_object_or_404(User, pk=pk, is_active=True)
    return render(request, 'accounts/profile.html', {'profile_user': profile_user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated.'))
            return redirect('accounts:profile', pk=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def account_delete(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, _('Your account has been deleted.'))
        return redirect('home')
    return render(request, 'accounts/account_delete_confirm.html')


@login_required
def data_export(request):
    user = request.user

    profile = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'account_type': user.account_type,
        'company_name': user.company_name,
        'phone': user.phone,
        'location': user.location,
        'bio': user.bio,
        'date_joined': user.date_joined.isoformat(),
    }

    listings = [
        {
            'title': l.title,
            'description': l.description,
            'category': l.category.name if l.category else None,
            'location': l.location,
            'price_per_day': str(l.price_per_day),
            'is_active': l.is_active,
            'created_at': l.created_at.isoformat(),
        }
        for l in user.listings.all()
    ]

    bookings_as_renter = [
        {
            'listing': b.listing.title,
            'start_date': str(b.start_date),
            'end_date': str(b.end_date),
            'status': b.status,
            'total_price': str(b.total_price),
            'created_at': b.created_at.isoformat(),
        }
        for b in user.bookings.all()
    ]

    messages_sent = [
        {
            'booking': m.booking.listing.title,
            'body': m.body,
            'sent_at': m.created_at.isoformat(),
        }
        for m in user.sent_messages.filter(is_system=False)
    ]

    payload = {
        'profile': profile,
        'listings': listings,
        'bookings': bookings_as_renter,
        'messages': messages_sent,
    }

    response = HttpResponse(
        json.dumps(payload, indent=2, ensure_ascii=False),
        content_type='application/json',
    )
    response['Content-Disposition'] = 'attachment; filename="my-rent-showcase-data.json"'
    return response
