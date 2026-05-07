import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Booking

WIDGET_CLASS = {'class': 'mt-1 block w-full rounded-md'}


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'quantity', 'note']
        widgets = {
            'start_date': forms.DateInput(attrs={**WIDGET_CLASS, 'placeholder': 'yyyy-mm-dd'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={**WIDGET_CLASS, 'placeholder': 'yyyy-mm-dd'}, format='%Y-%m-%d'),
            'note': forms.Textarea(attrs={**WIDGET_CLASS, 'rows': 3}),
        }

    def __init__(self, listing, *args, **kwargs):
        self.listing = listing
        super().__init__(*args, **kwargs)
        self.fields['note'].required = False
        if listing.quantity == 1:
            self.fields['quantity'].widget = forms.HiddenInput()
            self.fields['quantity'].initial = 1
        else:
            self.fields['quantity'].widget.attrs.update(WIDGET_CLASS)
            self.fields['quantity'].widget.attrs.update({'min': 1, 'max': listing.quantity})

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        qty = cleaned_data.get('quantity') or 1

        if start and end:
            if end < start:
                raise forms.ValidationError(_('End date must be on or after start date.'))
            if start < datetime.date.today():
                raise forms.ValidationError(_('Start date cannot be in the past.'))
            if not Booking.is_available(self.listing, start, end, qty):
                raise forms.ValidationError(_('The requested dates are not available for this listing.'))

        return cleaned_data
