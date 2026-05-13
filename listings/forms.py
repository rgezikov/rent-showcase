from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Listing, BlockedDateRange

WIDGET_CLASS = {'class': 'mt-1 block w-full rounded-md'}
PRICE_ATTRS = {**WIDGET_CLASS, 'step': '0.01', 'min': '0'}


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'category', 'location',
            'price_per_day', 'price_per_weekend', 'price_per_week', 'price_per_month',
            'base_fee', 'delivery_fee', 'deposit', 'minimum_days', 'payment_methods',
            'quantity', 'auto_accept', 'auto_accept_message',
        ]
        widgets = {
            'description': forms.Textarea(attrs={**WIDGET_CLASS, 'rows': 5}),
            'auto_accept_message': forms.Textarea(attrs={**WIDGET_CLASS, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('auto_accept',):
                field.widget.attrs.update(WIDGET_CLASS)
        for name in ('price_per_day', 'price_per_weekend', 'price_per_week',
                     'price_per_month', 'base_fee', 'delivery_fee', 'deposit'):
            self.fields[name].widget.attrs.update({'step': '0.01', 'min': '0'})

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('auto_accept') and not cleaned_data.get('auto_accept_message'):
            self.add_error('auto_accept_message', _('Please provide a message to send when auto-accepting bookings.'))
        return cleaned_data


class MultipleFileInput(forms.widgets.Input):
    input_type = 'file'
    needs_multipart_form = True
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True, 'accept': 'image/*'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)

    def value_omitted_from_data(self, data, files, name):
        return name not in files


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        return [super(MultipleFileField, self).clean(f, initial) for f in data] if data else []


class PhotoUploadForm(forms.Form):
    images = MultipleFileField(label=_('Photos'), required=False)


class BlockedDateRangeForm(forms.ModelForm):
    class Meta:
        model = BlockedDateRange
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={**WIDGET_CLASS, 'placeholder': 'yyyy-mm-dd'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={**WIDGET_CLASS, 'placeholder': 'yyyy-mm-dd'}, format='%Y-%m-%d'),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError(_('End date must be on or after start date.'))
        return cleaned_data
