"""The layout app: one skeleton, the layouts, public/private access, components, menus, preferences, security headers."""

import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.staticfiles import finders
from django.template import RequestContext, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .access import LAYOUT_ACCESS
from .models import LayoutPreference, preferences_for

ROOT = Path(settings.BASE_DIR)
User = get_user_model()
APPS = [p.name for p in ROOT.iterdir() if (p / "templates").is_dir()]          # every app with templates


def render_layout(layout, user=None, content="PAGE CONTENT"):
    """Draws a layout with a tiny page, as a view would (used for layouts no page uses yet, like auth.html)."""
    request = RequestFactory().get("/somewhere/")
    request.user = user or AnonymousUser()
    page = Template('{% extends "' + layout + '" %}{% block title %}T{% endblock %}{% block content %}' + content + '{% endblock %}')
    return page.render(RequestContext(request, {}))


class TemplateStructureTests(TestCase):
    def test_one_html_skeleton(self):
        found = [p.relative_to(ROOT).as_posix() for app in APPS
                 for p in (ROOT / app / "templates").rglob("*.html") if "<!doctype html" in p.read_text(encoding="utf-8").lower()]
        self.assertEqual(found, ["layout/templates/layout/base.html"])

    def test_layouts_extend_the_base(self):
        L = ROOT / "layout" / "templates" / "layout"
        for name, parent in (("public", "base"), ("user", "public"), ("auth", "base"), ("admin", "base"), ("plain", "base")):
            self.assertTrue((L / f"{name}.html").read_text(encoding="utf-8").startswith(f'{{% extends "layout/{parent}.html" %}}'), name)
        page_layouts = {"home": "public", "banner": "public", "band": "public", "detail": "public", "centered": "public",
                        "listing": "pages/band", "article": "pages/band", "legal": "pages/band"}
        for name, parent in page_layouts.items():
            self.assertTrue((L / "pages" / f"{name}.html").read_text(encoding="utf-8").startswith(f'{{% extends "layout/{parent}.html" %}}'), name)

    def test_app_pages_only_extend_layouts(self):
        for app in APPS:
            if app == "layout":
                continue
            for p in (ROOT / app / "templates").rglob("*.html"):
                m = re.search(r"""\{% extends ['"]([^'"]+)['"] %\}""", p.read_text(encoding="utf-8"))
                self.assertIsNotNone(m, p.name)
                self.assertTrue(m.group(1).startswith("layout/"), f"{p.name}: {m.group(1)}")

    def test_frontend_templates_live_in_frontend(self):
        self.assertTrue((ROOT / "frontend" / "templates" / "frontend" / "home.html").exists())
        self.assertFalse((ROOT / "pages").exists())

    def test_no_inline_scripts_or_styles(self):
        for p in ROOT.glob("*/templates/**/*.html"):
            src = p.read_text(encoding="utf-8")
            self.assertNotRegex(src, r"<script(?![^>]*\bsrc=)", p.name)
            self.assertNotIn("style=", src, p.name)
            self.assertNotRegex(src, r"\son[a-z]+=", p.name)

    def test_layout_templates_dont_depend_on_other_apps(self):
        for p in (ROOT / "layout" / "templates").rglob("*.html"):
            src = p.read_text(encoding="utf-8")
            for name in re.findall(r"""\{% url ['"]([^'"]+)['"]""", src):
                self.assertTrue(name.startswith("layout:"), f"{p.name} links to {name}")

    def test_static_files_exist_and_are_used(self):
        for path in ("layout/css/layout.css", "layout/js/layout.js", "layout/js/feedback.js", "layout/js/fields.js",
                     "layout/img/icons.svg", "layout/img/favicon.svg"):
            self.assertTrue(finders.find(path), path)
        html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertIn("/static/layout/css/layout.css", html)
        self.assertIn("viewport-fit=cover", html)


class LayoutUseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234")
        self.staff = User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True)

    def test_public_layout(self):
        r = self.client.get(reverse("frontend:about"))
        self.assertTemplateUsed(r, "layout/public.html")
        self.assertContains(r, 'class="site-header"')
        self.assertContains(r, 'class="site-footer"')
        self.assertContains(r, 'class="breadcrumbs"')
        self.assertNotContains(r, 'class="sidebar"')

    def test_user_layout(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("layout:preferences"))
        self.assertTemplateUsed(r, "layout/user.html")
        self.assertContains(r, 'aria-label="Your account"')
        self.assertContains(r, 'class="site-footer"')

    def test_auth_layout(self):
        html = render_layout("layout/auth.html")
        self.assertIn('class="auth-art"', html)
        self.assertIn("PAGE CONTENT", html)
        self.assertNotIn('class="site-header"', html)

    def test_admin_layout(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse("layout:staff_home"))
        self.assertTemplateUsed(r, "layout/admin.html")
        self.assertContains(r, 'class="site-header admin-header"')
        self.assertContains(r, 'aria-label="Staff area"')

    def test_a_page_can_hide_parts(self):
        html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertNotIn('class="breadcrumbs"', html)
        self.assertNotIn('class="page-header"', html)
        self.assertIn('class="hero"', html)

    def test_components(self):
        html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertEqual(html.count('class="card"'), 3)
        self.client.post(reverse("frontend:contact"), {"name": "Ann", "email": "ann@example.com", "message": "Hello", "phone_0": "NP", "phone_1": ""})
        html = self.client.get(reverse("frontend:contact")).content.decode()
        self.assertIn('class="toast toast--success"', html)


class AccessTests(TestCase):
    """Public layouts open for everyone; private ones need a signed-in person; the staff one needs active staff."""

    def setUp(self):
        self.user = User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234")
        self.staff = User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True)

    def test_views_check_access(self):
        prefs, staff_home = reverse("layout:preferences"), reverse("layout:staff_home")
        self.assertRedirects(self.client.get(prefs), f"{reverse('admin:login')}?next={prefs}", fetch_redirect_response=False)
        self.assertRedirects(self.client.get(staff_home), f"{reverse('admin:login')}?next={staff_home}", fetch_redirect_response=False)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(prefs).status_code, 200)
        self.assertEqual(self.client.get(staff_home).status_code, 403)        # signed in, but not staff
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(staff_home).status_code, 200)
        self.staff.is_active = False
        self.staff.save()
        self.assertNotEqual(self.client.get(staff_home).status_code, 200)

    def test_private_layouts_hide_content_even_if_a_view_forgets_its_check(self):
        self.assertEqual(set(LAYOUT_ACCESS), {"layout/user.html", "layout/admin.html"})
        html = render_layout("layout/user.html")                                # nobody signed in
        self.assertNotIn("PAGE CONTENT", html)
        self.assertIn("Please sign in", html)
        self.assertIn("PAGE CONTENT", render_layout("layout/user.html", self.user))
        html = render_layout("layout/admin.html", self.user)                    # signed in, not staff
        self.assertNotIn("PAGE CONTENT", html)
        self.assertNotIn('aria-label="Staff area"', html)
        self.assertIn("PAGE CONTENT", render_layout("layout/admin.html", self.staff))

    def test_public_layouts_show_content_to_everyone(self):
        for layout in ("layout/public.html", "layout/auth.html", "layout/plain.html", "layout/pages/band.html"):
            self.assertIn("PAGE CONTENT", render_layout(layout), layout)

    def test_links_to_missing_apps_are_left_out(self):
        conf = {**settings.LAYOUT, "ACCOUNT": {"LOGIN_URL": "accounts:login", "SIGNUP_URL": "accounts:signup",
                                               "LOGOUT_URL": "accounts:logout", "NAV": [{"label": "Orders", "url": "shop:orders"}]}}
        with self.settings(LAYOUT=conf):
            html = self.client.get(reverse("frontend:home")).content.decode()
            self.assertNotIn("Sign in", html)                                   # no sign-in page exists: no link
            self.client.force_login(self.user)
            html = self.client.get(reverse("frontend:home")).content.decode()
            self.assertNotIn("Orders", html)
            self.assertNotIn("Sign out", html)


class MenuTests(TestCase):
    def test_links_users_may_not_open_are_left_out(self):
        staff = User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True)
        self.client.force_login(staff)
        people = reverse("admin:auth_user_changelist")
        self.assertNotIn(people, self.client.get(reverse("layout:staff_home")).content.decode())
        staff.user_permissions.add(Permission.objects.get(codename="view_user"))
        self.assertIn(people, self.client.get(reverse("layout:staff_home")).content.decode())

    def test_staff_only_menu_items(self):
        user = User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234")
        self.client.force_login(user)
        self.assertNotIn(reverse("layout:staff_home"), self.client.get(reverse("frontend:home")).content.decode())

    def test_active_link_is_marked(self):
        html = self.client.get(reverse("frontend:about")).content.decode()
        self.assertIn(f'href="{reverse("frontend:about")}" aria-current="page"', html)

    def test_anonymous_visitors_get_sign_in_links(self):
        html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertIn(reverse("admin:login"), html)
        self.assertNotIn("profile-menu", html)


class PreferenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234")

    def test_defaults_group_then_own(self):
        self.assertEqual(preferences_for(self.user)["sidebar"], "expanded")
        self.user.groups.add(Group.objects.create(name="Editors"))
        self.assertEqual(preferences_for(self.user)["sidebar"], "collapsed")
        LayoutPreference.objects.create(user=self.user, sidebar="expanded", theme="dark")
        self.assertEqual(preferences_for(self.user)["sidebar"], "expanded")
        self.assertEqual(preferences_for(self.user)["theme"], "dark")

    def test_preferences_change_the_page(self):
        LayoutPreference.objects.create(user=self.user, theme="dark", sidebar="collapsed", density="compact")
        self.client.force_login(self.user)
        html = self.client.get(reverse("layout:preferences")).content.decode()
        self.assertIn('data-theme="dark"', html)
        self.assertIn('data-density="compact"', html)
        self.assertIn("sidebar-collapsed", html)

    def test_only_fixed_choices_are_accepted(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("layout:preferences"), {"theme": '"><script>x</script>', "sidebar": "expanded", "density": "compact"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Select a valid choice")
        self.assertFalse(LayoutPreference.objects.filter(user=self.user, density="compact").exists())
        self.client.post(reverse("layout:preferences"), {"theme": "dark", "sidebar": "collapsed", "density": "compact"})
        self.assertEqual(LayoutPreference.objects.get(user=self.user).theme, "dark")

    def test_bad_group_defaults_are_ignored(self):
        self.user.groups.add(Group.objects.create(name="Editors"))
        with self.settings(LAYOUT={**settings.LAYOUT, "GROUP_DEFAULTS": {"Editors": {"theme": "../../evil", "sidebar": "collapsed"}}}):
            prefs = preferences_for(self.user)
        self.assertEqual(prefs["theme"], "light")
        self.assertEqual(prefs["sidebar"], "collapsed")


class SecurityTests(TestCase):
    def test_security_headers(self):
        r = self.client.get(reverse("frontend:home"))
        self.assertIn("script-src 'self'", r["Content-Security-Policy"])
        self.assertEqual(r["X-Frame-Options"], "DENY")
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")

    def test_content_is_escaped(self):
        user = User.objects.create_user("x", "x@example.com", "a-long-pass-1234", first_name="<b>bold</b>")
        self.client.force_login(user)
        html = self.client.get(reverse("layout:preferences")).content.decode()
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", html)
        self.assertNotIn("<b>bold</b>", html)
