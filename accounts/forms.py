from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User

WIDGET_CLASS = {'class': 'mt-1 block w-full rounded-md'}


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs=WIDGET_CLASS),
    )
    password2 = forms.CharField(
        label=_('Confirm password'),
        widget=forms.PasswordInput(attrs=WIDGET_CLASS),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'account_type',
                  'company_name', 'phone', 'location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('password1', 'password2'):
                field.widget.attrs.update(WIDGET_CLASS)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['company_name'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('An account with this email already exists.'))
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Passwords do not match.'))
        return p2

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('account_type') == User.COMPANY and not cleaned_data.get('company_name'):
            self.add_error('company_name', _('Company name is required for company accounts.'))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        base = user.email.split('@')[0][:100]
        username, n = base, 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user.username = username
        user.email = user.email.lower()
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={**WIDGET_CLASS, 'autofocus': True}),
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs=WIDGET_CLASS),
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                _('Please verify your email address before logging in. Check your inbox.'),
                code='inactive',
            )


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'company_name',
                  'phone', 'location', 'avatar', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(WIDGET_CLASS)
        self.fields['company_name'].required = False
