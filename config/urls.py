"""Addresses: the layout app's own pages, Django's admin, and the public website (frontend).
A future app gets its own line here, e.g. path("accounts/", include("accounts.urls"))."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("layout/", include("layout.urls")),                   # layout preferences (private), staff start page (staff)
    path("admin/", admin.site.urls),
    path("", include("frontend.urls")),                        # the website
]
