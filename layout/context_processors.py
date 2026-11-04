"""
Gives every template one variable, `layout`:
    layout.site_name, layout.description
    layout.home_url, admin_home_url, login_url, signup_url, logout_url    ("" when that page doesn't exist yet)
    layout.public_nav / footer_nav / user_nav / admin_nav / account_nav   menu items this user may see (see _menu)
    layout.account_modal   True when "Sign in" should open the account modal (signed-out visitors only)
    layout.toasts    position and duration of toast messages
    layout.loader    the page loader (on/off, style, text) and what shows while the next page loads
    layout.prefs     theme, sidebar, density (see models.preferences_for)
Everything comes from settings.LAYOUT. Values with fixed choices are checked here, so a typo can't reach a class name.
Hiding a link is only for tidiness: every view checks permissions itself.
"""

from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string

from .models import preferences_for

TOAST_POSITIONS = ["top-left", "top-center", "top-right", "bottom-left", "bottom-center", "bottom-right"]
LOADER_STYLES = ["spinner", "dots", "pulse"]
NAVIGATE = ["bar", "loader", "none"]


def _choice(value, choices, default):
    return value if value in choices else default


def _url(name):
    """A URL name (or a path starting with /) → the address, or "" when that page doesn't exist (yet)."""
    if not name:
        return ""
    if str(name).startswith("/"):
        return str(name)
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def _can_see(item, user):
    if item.get("staff") and not (user.is_authenticated and user.is_active and user.is_staff):
        return False
    if item.get("perm") and not user.has_perm(item["perm"]):
        return False
    if item.get("groups") and not (user.is_authenticated and user.groups.filter(name__in=item["groups"]).exists()):
        return False
    return True


def _badge(item, request):
    """Optional "badge": "app.module.function": called with the request, shown when it returns a number above 0."""
    if not item.get("badge"):
        return 0
    try:
        value = int(import_string(item["badge"])(request) or 0)
    except (ImportError, TypeError, ValueError):
        return 0
    return value if value > 0 else 0


def _menu(items, request):
    """Menu items from settings → what the templates draw. An item is one of:
         {"label", "url": "url-name", "icon", "perm"?, "groups"?, "badge"?}       a link
         {"heading": "Manage"}                                                    a small heading
         {"label", "icon", "children": [links…]}                                  a group that opens (sidebars)
    Links the user may not see, and groups left empty, are dropped."""
    out = []
    for item in items:
        if not _can_see(item, request.user):
            continue
        if "heading" in item:
            out.append({"heading": item["heading"]})
            continue
        if "children" in item:
            children = _menu(item["children"], request)
            if children:
                out.append({"label": item["label"], "icon": item.get("icon", "layers"), "children": children,
                            "active": any(c.get("active") for c in children)})
            continue
        try:
            url = reverse(item["url"])
        except NoReverseMatch:
            continue
        out.append({"label": item["label"], "url": url, "icon": item.get("icon", "dot"), "badge": _badge(item, request),
                    "active": request.path == url or (url != "/" and request.path.startswith(url))})
    while out and "heading" in out[-1]:          # no heading without links under it
        out.pop()
    return out


def layout(request):
    conf = settings.LAYOUT
    user = request.user
    toasts = conf.get("TOASTS", {})
    loader = conf.get("LOADER", {})
    account = conf.get("ACCOUNT", {})
    login_url = _url(account.get("LOGIN_URL", settings.LOGIN_URL))
    modal = account.get("MODAL", True) and login_url and not user.is_authenticated
    return {"layout": {
        "site_name": conf.get("SITE_NAME", "Site"),
        "description": conf.get("DESCRIPTION", ""),
        "home_url": _url(conf.get("HOME_URL")) or "/",
        "admin_home_url": _url(conf.get("ADMIN_HOME_URL")) or "/",
        "login_url": login_url,
        "password_reset_url": _url(account.get("PASSWORD_RESET_URL")),
        "account_modal": bool(modal),                   # "Sign in" opens the account modal (public pages)
        "signup_url": _url(account.get("SIGNUP_URL")),
        "logout_url": _url(account.get("LOGOUT_URL")),
        "account_nav": _menu(account.get("NAV", []), request) if user.is_authenticated else [],
        "public_nav": _menu(conf.get("PUBLIC_NAV", []), request),
        "footer_nav": _menu(conf.get("FOOTER_NAV", []), request),
        "user_nav": _menu(conf.get("USER_NAV", []), request) if user.is_authenticated else [],
        "admin_nav": _menu(conf.get("ADMIN_NAV", []), request) if user.is_authenticated and user.is_staff else [],
        "toasts": {"position": _choice(toasts.get("POSITION"), TOAST_POSITIONS, "top-right"),
                   "duration": max(0, min(int(toasts.get("DURATION", 4000)), 60000))},
        "loader": {"page": bool(loader.get("PAGE", True)),
                   "style": _choice(loader.get("STYLE"), LOADER_STYLES, "pulse"),
                   "text": str(loader.get("TEXT", "Loading")),
                   "navigate": _choice(loader.get("NAVIGATE"), NAVIGATE, "bar")},
        "prefs": preferences_for(user),
    }}
