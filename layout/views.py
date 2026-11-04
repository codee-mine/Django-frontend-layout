"""
The layout app's own pages (under /layout/):
    preferences   each signed-in person's layout choices (theme, sidebar, spacing)      layout/user.html, private
    staff_home    the start page of the staff area, an example of layout/admin.html      staff only
    gallery       every reusable part in action (and gallery_plain: the plain layout)     DEBUG or staff
    docs          the guide: how to use the layouts in new pages and apps                  DEBUG or staff
Other apps add their own pages with the same layouts (see layout/access.py for who may open what).
"""

import re
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.shortcuts import redirect, render
from django.utils import timezone

from .access import dev_or_staff, private, staff_only
from . import countries
from .forms import LayoutPreferenceForm, PhoneField
from .models import LayoutPreference


@private
def preferences(request):
    pref, _ = LayoutPreference.objects.get_or_create(user=request.user)
    form = LayoutPreferenceForm(request.POST or None, instance=pref)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your layout preferences are saved.")
        return redirect("layout:preferences")
    return render(request, "layout/screens/preferences.html", {"form": form, "breadcrumbs": [("Your account", None), ("Layout preferences", None)]})


@staff_only
def staff_home(request):
    User = get_user_model()
    week_ago = timezone.now() - timedelta(days=7)
    stats = [("People", User.objects.count()), ("New this week", User.objects.filter(date_joined__gte=week_ago).count()),
             ("Staff", User.objects.filter(is_staff=True).count()), ("Own layout choices", LayoutPreference.objects.count())]
    recent = User.objects.order_by("-date_joined")[:5] if request.user.has_perm("auth.view_user") else []
    return render(request, "layout/screens/staff_home.html", {"stats": stats, "recent": recent, "breadcrumbs": [("Staff area", None), ("Dashboard", None)]})


class DemoForm(forms.Form):
    """The server-side check for the gallery's demo form (its fields are written out in screens/gallery.html)."""
    name = forms.CharField(max_length=40, min_length=2)
    email = forms.EmailField()
    website = forms.URLField(required=False)
    phone = PhoneField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    city = forms.CharField(required=False, help_text="Any field can have its own icon.")
    agree = forms.BooleanField(label="I agree to the terms")



@dev_or_staff
def gallery(request):
    if request.method == "POST" and request.POST.get("form") in ("signin", "register"):
        messages.info(request, "Gallery only: the account modal isn't connected to accounts here, so nothing was sent.")
        return redirect("layout:gallery")
    form = DemoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        messages.success(request, "The form is valid. Nothing was saved: this is only the gallery.")
        return redirect("layout:gallery")
    return render(request, "layout/screens/gallery.html", {
        "form": form,
        "countries": countries.COUNTRIES,
        "phone_country": request.POST.get("phone_0") or countries.default_code(),
        "breadcrumbs": [("Layout", None), ("Gallery", None)],
    })


@dev_or_staff
def gallery_plain(request):
    return render(request, "layout/screens/plain_example.html")


@dev_or_staff
def docs(request):
    """The layout guide. The icon list is read from the icon file itself, so it is always complete."""
    path = finders.find("layout/img/icons.svg")
    icons = re.findall(r'<symbol id="([a-z0-9-]+)"', open(path, encoding="utf-8").read()) if path else []
    return render(request, "layout/screens/docs.html", {"icons": icons, "breadcrumbs": [("Layout", None), ("Docs", None)]})
