from django.apps import AppConfig


class LayoutConfig(AppConfig):
    """The single source of truth for the site's shared look: layouts, partials, components, CSS, JS, images."""
    name = "layout"
    default_auto_field = "django.db.models.BigAutoField"
