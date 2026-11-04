from django import forms

from layout.forms import PhoneField


class ContactForm(forms.Form):
    name = forms.CharField(max_length=80)
    email = forms.EmailField(max_length=120)
    phone = PhoneField(required=False, help_text="Optional. Pick your country, then type your number.")
    message = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))
