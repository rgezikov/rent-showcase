from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md',
                'placeholder': _('Write a message…'),
            }),
        }
        labels = {'body': ''}
