"""
Forms and form fields that come with the layout.

    LayoutPreferenceForm   each person's layout choices (theme, sidebar, spacing)
    PhoneField             a phone number with a country-code picker; any app can use it:

        from layout.forms import PhoneField
        class ContactForm(forms.Form):
            phone = PhoneField(required=False)

    The page writes the two inputs itself (a country list named phone_0 and a number box named phone_1; see
    frontend/templates/frontend/contact.html). The value is saved as "+<dialling code><number>", e.g. "+9779812345678".
    The number of digits is checked for the chosen country (layout/countries.py) here, and while typing by fields.js.
"""

import re

from django import forms
from django.core.exceptions import ValidationError

from . import countries
from .models import LayoutPreference


class LayoutPreferenceForm(forms.ModelForm):
    """The user's own layout choices (Layout preferences). Only the model's fixed choices are accepted."""

    class Meta:
        model = LayoutPreference
        fields = ["theme", "sidebar", "density"]
        widgets = {"theme": forms.RadioSelect, "sidebar": forms.RadioSelect, "density": forms.RadioSelect}


class PhoneWidget(forms.MultiWidget):
    """Reads the two inputs a page writes for a phone number: <select name="phone_0"> and <input name="phone_1">."""

    def __init__(self, attrs=None):
        super().__init__([forms.Select(choices=[(c[0], c[1]) for c in countries.COUNTRIES]), forms.TextInput()], attrs)

    def decompress(self, value):
        return [countries.default_code(), value or ""]


class PhoneField(forms.MultiValueField):
    widget = PhoneWidget
    default_error_messages = {
        "invalid": "Enter a valid phone number for {country} ({digits} digits).",
        "characters": "Use digits, spaces and dashes only.",
    }

    def __init__(self, **kwargs):
        fields = (forms.ChoiceField(choices=[(c[0], c[1]) for c in countries.COUNTRIES], required=False),
                  forms.CharField(max_length=24, required=False))
        super().__init__(fields, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        code, number = (list(data_list) + ["", ""])[:2]
        number = (number or "").strip()
        if not number:
            if self.required:
                raise ValidationError(self.error_messages["required"], code="required")
            return ""
        if re.search(r"[^\d\s\-()+]", number):
            raise ValidationError(self.error_messages["characters"], code="characters")
        country = countries.get(code)
        digits = re.sub(r"\D", "", number).lstrip("0")         # a leading trunk 0 isn't part of the international number
        low, high = country[3], country[4]
        if not low <= len(digits) <= high:
            span = str(low) if low == high else f"{low}–{high}"
            raise ValidationError(self.error_messages["invalid"].format(country=country[1], digits=span), code="invalid")
        return f"+{country[2]}{digits}"
