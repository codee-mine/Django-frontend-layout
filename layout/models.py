"""
A user's own layout choices. Only fixed choices: no free text reaches a template, a class name or a file path.
"""

from django.conf import settings
from django.db import models


class LayoutPreference(models.Model):
    THEMES = [("light", "Light"), ("dark", "Dark")]
    SIDEBARS = [("expanded", "Expanded"), ("collapsed", "Collapsed (icons only)")]
    DENSITIES = [("comfortable", "Comfortable"), ("compact", "Compact")]
    DEFAULTS = {"theme": "light", "sidebar": "expanded", "density": "comfortable"}

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="layout_preference")
    theme = models.CharField(max_length=10, choices=THEMES, default="light")
    sidebar = models.CharField(max_length=10, choices=SIDEBARS, default="expanded")
    density = models.CharField(max_length=12, choices=DENSITIES, default="comfortable")

    def __str__(self):
        return f"Layout preference of {self.user}"


def allowed(field, value):
    """True when `value` is one of the choices of LayoutPreference.<field>."""
    return value in {v for v, _ in LayoutPreference._meta.get_field(field).choices}


def preferences_for(user):
    """The layout choices for this user: the defaults, then their group's (settings.LAYOUT["GROUP_DEFAULTS"]),
    then their own saved ones. Anything not in the fixed choices is ignored."""
    prefs = dict(LayoutPreference.DEFAULTS)
    if not getattr(user, "is_authenticated", False):
        return prefs
    groups = set(user.groups.values_list("name", flat=True))
    for group, values in settings.LAYOUT.get("GROUP_DEFAULTS", {}).items():
        if group in groups:
            prefs.update({k: v for k, v in values.items() if k in prefs and allowed(k, v)})
            break
    own = LayoutPreference.objects.filter(user=user).first()
    if own:
        prefs.update(theme=own.theme, sidebar=own.sidebar, density=own.density)
    return prefs
