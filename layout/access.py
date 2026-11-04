"""
Who may open a page. The layout a page uses only decides how it looks; access is always checked in the view:

    from layout.access import public, private, staff_only

    @public                  # anyone            → layout/public.html, layout/pages/*.html, layout/auth.html
    def about(request): …

    @private                 # signed-in people  → layout/user.html
    def orders(request): …

    @staff_only              # active staff      → layout/admin.html
    def reports(request): …

Class-based views: PrivateMixin, StaffMixin. For a Django permission add
@permission_required("app.codename", raise_exception=True) under the decorator.

Safety net: user.html and admin.html also refuse to draw their content for the wrong visitor (a notice is shown
instead), so a view that forgot its decorator still doesn't leak a private page.
"""

from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import Http404

LAYOUT_ACCESS = {                   # which layouts need what (used by the tests and the docs)
    "layout/user.html": "private",
    "layout/admin.html": "staff",
}


def public(view):
    """Marks a view as open to everyone. Changes nothing: it makes the choice visible when reading the code."""
    view.layout_access = "public"
    return view


def private(view):
    """Signed-in people only; others go to the sign-in page (settings.LOGIN_URL)."""
    wrapped = login_required(view)
    wrapped.layout_access = "private"
    return wrapped


def is_staff(user):
    return user.is_authenticated and user.is_active and user.is_staff


def staff_only(view):
    """Active staff only. Not signed in: the sign-in page. Signed in but not staff: 403."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_staff(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    wrapper.layout_access = "staff"
    return wrapper


def dev_or_staff(view):
    """Developer pages (the layout gallery): open while DEBUG is on, otherwise only for active staff; others get 404."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not (settings.DEBUG or is_staff(request.user)):
            raise Http404
        return view(request, *args, **kwargs)
    wrapper.layout_access = "dev"
    return wrapper


class PrivateMixin(LoginRequiredMixin):
    """For class-based views: signed-in people only."""


class StaffMixin(AccessMixin):
    """For class-based views: active staff only (others: sign-in page or 403)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_staff(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
