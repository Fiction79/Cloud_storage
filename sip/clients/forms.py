# clients/forms.py
from django import forms
from .models import ClientProfile
from django.conf import settings
import os

class ClientProfileInlineForm(forms.ModelForm):
    quota_gb = forms.IntegerField(label="Quota (GB)", required=False, initial=5)

    class Meta:
        model = ClientProfile
        fields = ['quota_limit']  # Use the actual field name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert bytes to GB for display
        if self.instance.pk and self.instance.quota_limit:
            self.fields['quota_gb'].initial = self.instance.quota_limit // (1024**3)

    def clean(self):
        cleaned_data = super().clean()
        quota_gb = cleaned_data.get('quota_gb', 5)
        # Store as bytes in the actual field
        cleaned_data['quota_limit'] = quota_gb * 1024**3
        return cleaned_data