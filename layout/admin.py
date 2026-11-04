from django.contrib import admin

from .models import LayoutPreference


@admin.register(LayoutPreference)
class LayoutPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "sidebar", "density")
    list_filter = ("theme", "sidebar", "density")
    search_fields = ("user__username", "user__email")
