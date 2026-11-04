"""Numbers shown beside sidebar links (settings.LAYOUT menus → "badge": "layout.badges.new_users").
A badge is any function that takes the request and returns a number; 0 hides it. Add your own in any app."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone


def new_users(request):
    """People who joined in the last 7 days (only counted for staff who may see users)."""
    if not request.user.has_perm("auth.view_user"):
        return 0
    return get_user_model().objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
