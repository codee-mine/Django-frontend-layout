"""
Project settings. Secrets and anything that differs between computers come from .env (see .env.example).
The layout's own settings (site name, menus, group defaults) are in LAYOUT at the end.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

from .env import env_bool, env_list, load_env

BASE_DIR = Path(__file__).resolve().parent.parent
load_env(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY (at least 32 characters) in .env.")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",          # Django's own /admin/ (also used for signing in until an accounts app exists)
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "layout",                        # every shared layout, partial, component, CSS, JS and image
    "frontend",                      # the public website: its pages
    # Future apps (accounts, shop, blog…) go here and use the same layouts. See layout/access.py for public/private.
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "layout.context_processors.layout",      # the `layout` variable: site name, menus, the user's preferences
    ]},
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# No accounts app yet: Django's admin sign-in is used (staff only). An accounts app later sets these to its own pages.
LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Production: file names with a content hash (after `collectstatic`), so browsers never keep a stale file.
MANIFEST_STATIC = not DEBUG and "test" not in sys.argv
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage" if MANIFEST_STATIC
                    else "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# ---------------------------------------------------------------- security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    if env_bool("DJANGO_BEHIND_PROXY"):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Content Security Policy: only this site's own files; no inline scripts or styles anywhere.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
}

# ---------------------------------------------------------------- the layout (layout/context_processors.py reads this)
# Menu items: {"label", "url" (a URL name), "icon" (from layout/static/layout/img/icons.svg)}, and optionally
# "perm" (a permission the user must have) or "groups" (names; the user must be in one). Items a user may not
# see are left out on the server; the views themselves are protected too.
LAYOUT = {
    "SITE_NAME": "Example Site",
    "DESCRIPTION": "A simple, secure Django site built on one shared layout.",
    # Where the logo goes, and the start page of the staff area (URL names or paths; a missing page falls back to "/").
    "HOME_URL": "frontend:home",
    "ADMIN_HOME_URL": "layout:staff_home",
    # Signing in and out, and the signed-in person's menu (top right). A link to a page that doesn't exist yet is left out,
    # so a future accounts app only has to set its own URL names here (e.g. "LOGIN_URL": "accounts:login").
    "ACCOUNT": {
        "LOGIN_URL": "admin:login",
        "SIGNUP_URL": "",                     # e.g. "accounts:signup" once an accounts app exists
        "LOGOUT_URL": "admin:logout",
        "PASSWORD_RESET_URL": "",             # e.g. "accounts:password_reset"
        "MODAL": True,                        # "Sign in" opens the sign-in / register modal (False: go to the page)
        "NAV": [
            {"label": "Layout preferences", "url": "layout:preferences"},
            {"label": "Staff area", "url": "layout:staff_home", "staff": True},
        ],
    },
    "PUBLIC_NAV": [
        {"label": "Home", "url": "frontend:home", "icon": "home"},
        {"label": "About", "url": "frontend:about", "icon": "info"},
        {"label": "Services", "url": "frontend:services", "icon": "layers"},
        {"label": "Stories", "url": "frontend:stories", "icon": "file"},
        {"label": "Contact", "url": "frontend:contact", "icon": "mail"},
    ],
    # Second footer column (legal pages and the like).
    "FOOTER_NAV": [
        {"label": "How it's built", "url": "frontend:guide"},
        {"label": "Privacy", "url": "frontend:privacy"},
        {"label": "Terms", "url": "frontend:terms"},
    ],
    # Sidebar menus. An item is a link {"label", "url", "icon", "perm"?, "groups"?, "staff"?, "badge"?},
    # a heading {"heading": "…"}, or a group that opens {"label", "icon", "children": [links]}.
    # "badge" names a function(request) returning a number shown beside the link (0 hides it).
    # USER_NAV: the private user layout. Future apps add their links here (orders, profile…).
    "USER_NAV": [
        {"heading": "Settings"},
        {"label": "Layout preferences", "url": "layout:preferences", "icon": "sliders"},
    ],
    # ADMIN_NAV: the staff layout.
    "ADMIN_NAV": [
        {"label": "Dashboard", "url": "layout:staff_home", "icon": "home"},
        {"heading": "Manage"},
        {"label": "People", "url": "admin:auth_user_changelist", "icon": "users", "perm": "auth.view_user", "badge": "layout.badges.new_users"},
        {"label": "View the website", "url": "frontend:home", "icon": "globe"},
        {"label": "Layout", "icon": "layers", "children": [
            {"label": "Layout gallery", "url": "layout:gallery", "icon": "image"},
            {"label": "Layout docs", "url": "layout:docs", "icon": "file"},
        ]},
        {"heading": "You"},
        {"label": "Layout preferences", "url": "layout:preferences", "icon": "sliders"},
        {"label": "Django admin", "url": "admin:index", "icon": "settings"},
    ],
    # Messages (saved, signed in…) appear as toasts. POSITION: top-left, top-center, top-right, bottom-left,
    # bottom-center, bottom-right. DURATION in milliseconds (0 = stays until closed).
    "TOASTS": {"POSITION": "top-right", "DURATION": 4000},
    # PAGE: a loader covers the page until it is ready. STYLE: spinner, dots, pulse (the logo).
    # NAVIGATE: what shows while the next page loads: bar (thin line at the top), loader, none.
    "LOADER": {"PAGE": True, "STYLE": "pulse", "TEXT": "Loading", "NAVIGATE": "bar"},
    # Phone fields: the country picked at first (ISO code from layout/countries.py).
    "PHONE_DEFAULT_COUNTRY": "NP",
    # Layout choices used when a user hasn't chosen their own (Layout preferences), per group, first match wins.
    "GROUP_DEFAULTS": {
        "Editors": {"sidebar": "collapsed"},
    },
}
