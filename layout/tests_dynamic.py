"""Tests for the dynamic parts: sections in pages, menus with groups and badges, toasts, loader, fields, the account modal, docs."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from layout.context_processors import _menu


class SectionTests(TestCase):
    """Sections are written in the page itself: no separate section files or builder."""

    def test_sections_live_in_their_pages(self):
        from pathlib import Path
        root = Path(settings.BASE_DIR)
        self.assertFalse((root / "layout/sections.py").exists())
        self.assertFalse((root / "layout/templates/layout/sections").exists())
        self.assertFalse((root / "frontend/models.py").exists())
        r = self.client.get(reverse("frontend:services"))
        for marker in ('class="steps"', 'class="plans"', 'class="faq"', 'class="gallery"', 'class="text-image'):
            self.assertContains(r, marker)
        r = self.client.get(reverse("frontend:home"))
        for marker in ('class="features"', 'class="numbers"', 'class="quotes"', 'section--dark'):
            self.assertContains(r, marker)

    def test_site_addresses(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.assertEqual(self.client.get("/our-story/").status_code, 404)      # no pages built in the admin any more


class MenuTests(TestCase):
    def request(self, user):
        from django.test import RequestFactory
        r = RequestFactory().get("/staff/")
        r.user = user
        return r

    def test_groups_headings_and_badges(self):
        boss = User.objects.create_superuser("boss", "boss@example.com", "a-long-pass-1234")
        items = _menu(settings.LAYOUT["ADMIN_NAV"], self.request(boss))
        self.assertIn({"heading": "Manage"}, items)
        users = next(i for i in items if i.get("label") == "People")
        self.assertEqual(users["badge"], 1)                                   # boss joined this week
        group = next(i for i in items if i.get("label") == "Layout")
        self.assertEqual(len(group["children"]), 2)                          # gallery and docs

    def test_empty_groups_and_lonely_headings_are_dropped(self):
        plain = User.objects.create_user("p", "p@example.com", "a-long-pass-1234", is_staff=True)
        items = _menu([{"label": "G", "children": [{"label": "X", "url": "admin:index", "perm": "auth.change_user"}]},
                       {"label": "Home", "url": "frontend:home"}, {"heading": "Nothing below"}], self.request(plain))
        self.assertEqual([i.get("label") for i in items], ["Home"])

    def test_sidebar_draws_groups(self):
        boss = User.objects.create_superuser("boss", "boss@example.com", "a-long-pass-1234")
        self.client.force_login(boss)
        r = self.client.get(reverse("layout:staff_home"))
        for marker in ('class="sidebar__group"', 'class="sidebar__heading"', 'class="badge"', "data-sidebar-collapse", "data-sidebar-open"):
            self.assertContains(r, marker)


class FeedbackTests(TestCase):
    def test_messages_are_toasts(self):
        self.client.post(reverse("frontend:contact"), {"name": "Ann", "email": "ann@example.com", "message": "Hi", "phone_0": "NP", "phone_1": ""})
        r = self.client.get(reverse("frontend:contact"))
        self.assertContains(r, 'class="toast toast--success"')
        self.assertContains(r, 'data-position="top-right"')

    @override_settings(LAYOUT={**settings.LAYOUT, "TOASTS": {"POSITION": "x\" onload=\"bad", "DURATION": "5000"},
                               "LOADER": {"PAGE": False, "STYLE": "<b>", "NAVIGATE": "nope"}})
    def test_bad_settings_fall_back_to_safe_choices(self):
        r = self.client.get(reverse("frontend:about"))
        self.assertContains(r, 'data-position="top-right"')
        self.assertContains(r, 'data-duration="5000"')
        self.assertContains(r, 'data-navigate="bar"')
        self.assertNotContains(r, "data-page-loader")

    def test_page_loader_and_progress_line(self):
        r = self.client.get(reverse("frontend:about"))
        self.assertContains(r, "data-page-loader")
        self.assertContains(r, "data-progress")

    def test_sign_out_asks_first(self):
        self.client.force_login(User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234"))
        self.assertContains(self.client.get(reverse("layout:preferences")), "data-confirm=")


class FieldTests(TestCase):
    def setUp(self):                      # the gallery is for staff (or anyone while DEBUG is on)
        self.client.force_login(User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True))

    def test_icons_and_end_buttons(self):
        r = self.client.get(reverse("layout:gallery"))
        self.assertContains(r, "icons.svg#mail")             # email
        self.assertContains(r, "icons.svg#lock")             # password
        self.assertContains(r, "data-field-eye")
        self.assertContains(r, "icons.svg#map")              # set in the form: fields["city"].icon
        self.assertContains(r, "icons.svg#globe")            # an icon at the end
        self.assertContains(r, "data-field-clear")

    def test_password_has_clear_and_eye(self):
        html = self.client.get(reverse("layout:gallery")).content.decode()
        end = html.split('id="id_password"', 1)[1].split("</span>\n  </div>", 1)[0]
        self.assertIn("data-field-clear", end)
        self.assertIn("data-field-eye", end)
        self.assertIn('data-field-clear aria-label="Clear password" hidden', end)   # ✕ only once there is text

    def test_pages_write_their_own_fields(self):
        """No generic form helper: each page has its fields written out (simple to read and change)."""
        from pathlib import Path
        root = Path(settings.BASE_DIR)
        self.assertFalse((root / "layout/templates/layout/components").exists())
        contact = (root / "frontend/templates/frontend/contact.html").read_text(encoding="utf-8")
        for name in ('name="name"', 'name="email"', 'name="phone_0"', 'name="phone_1"', 'name="message"'):
            self.assertIn(name, contact)

    def test_server_errors_show_under_fields_and_on_top(self):
        r = self.client.post(reverse("layout:gallery"), {"name": "a", "email": "nope"})
        self.assertContains(r, 'class="form-errors"')
        self.assertContains(r, "Enter a valid email address.")
        self.assertContains(r, 'class="field is-invalid"')

    def test_plain_layout(self):
        r = self.client.get(reverse("layout:gallery_plain"))
        self.assertTemplateUsed(r, "layout/plain.html")
        self.assertNotContains(r, 'class="site-header"')
        self.assertNotContains(r, 'class="site-footer"')


class PhoneFieldTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True))

    def form(self, data):
        from django import forms
        from layout.forms import PhoneField

        class F(forms.Form):
            phone = PhoneField()
        return F(data)

    def test_number_is_checked_for_the_country(self):
        f = self.form({"phone_0": "NP", "phone_1": "981-234 5678"})
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data["phone"], "+9779812345678")
        f = self.form({"phone_0": "GB", "phone_1": "07700 900123"})          # a leading 0 is dropped
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data["phone"], "+447700900123")
        f = self.form({"phone_0": "IN", "phone_1": "12345"})
        self.assertFalse(f.is_valid())
        self.assertIn("Enter a valid phone number for India (10 digits).", f.errors["phone"])
        self.assertFalse(self.form({"phone_0": "NP", "phone_1": "98<script>"}).is_valid())
        self.assertIn("This field is required.", self.form({"phone_0": "NP", "phone_1": ""}).errors["phone"])

    def test_unknown_country_falls_back(self):
        f = self.form({"phone_0": "ZZ", "phone_1": "9812345678"})
        self.assertFalse(f.is_valid())                                       # not in the list

    def test_widget_has_the_picker_data(self):
        r = self.client.get(reverse("layout:gallery"))
        self.assertContains(r, "data-phone-country")
        self.assertContains(r, 'data-dial="977"')
        self.assertContains(r, 'value="NP" data-name="Nepal" data-dial="977" data-min="8" data-max="10" selected')
        self.assertContains(r, 'for="id_phone_1"')
        self.assertContains(r, 'type="tel"')

    def test_value_is_shown_again_after_an_error(self):
        r = self.client.post(reverse("layout:gallery"), {"phone_0": "IN", "phone_1": "98765"})
        self.assertContains(r, 'value="IN" data-name="India" data-dial="91" data-min="10" data-max="10" selected')
        self.assertContains(r, 'value="98765"')


class AuthModalTests(TestCase):
    def test_public_pages_carry_the_sign_in_modal(self):
        html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertIn('<template id="auth-modal">', html)
        self.assertIn('"tab": "signin"', html)                      # "Sign in" opens it
        self.assertIn(f'action="{reverse("admin:login")}"', html)   # posts to the current sign-in page
        self.assertIn('id="auth-modal-username"', html)             # its own ids: no clash with forms on the page
        self.assertNotIn('role="tablist" aria-label="Account"', html)   # no sign-up page yet: no Register tab
        self.assertNotIn("Create account", html)

    def test_register_tab_appears_once_a_signup_page_exists(self):
        with self.settings(LAYOUT={**settings.LAYOUT, "ACCOUNT": {**settings.LAYOUT["ACCOUNT"], "SIGNUP_URL": "/join/"}}):
            html = self.client.get(reverse("frontend:home")).content.decode()
        self.assertIn('action="/join/"', html)
        self.assertIn('"tab": "register"', html)
        self.assertIn('data-match="auth-modal-password1"', html)
        self.assertNotIn("Required. 150 characters", html)          # long help texts are shortened in the modal

    def test_only_layouts_that_need_it_carry_it(self):
        sam = User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True)
        self.client.force_login(sam)
        self.assertNotContains(self.client.get(reverse("frontend:home")), 'id="auth-modal"')   # signed in
        self.assertNotContains(self.client.get(reverse("layout:gallery_plain")), 'id="auth-modal"')  # plain layout
        self.client.logout()
        with self.settings(LAYOUT={**settings.LAYOUT, "ACCOUNT": {**settings.LAYOUT["ACCOUNT"], "MODAL": False}}):
            self.assertNotContains(self.client.get(reverse("frontend:home")), 'id="auth-modal"')

    def test_gallery_shows_both_tabs_and_is_not_public(self):
        self.assertEqual(self.client.get(reverse("layout:gallery")).status_code, 404)      # DEBUG off, not staff
        self.client.force_login(User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True))
        html = self.client.get(reverse("layout:gallery")).content.decode()
        self.assertIn('<template id="demo-auth-modal">', html)
        self.assertIn('id="demo-auth-modal-register"', html)
        r = self.client.post(reverse("layout:gallery"), {"form": "register"}, follow=True)
        self.assertContains(r, "nothing was sent")

    def test_signing_in_from_the_modal_works(self):
        User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True)
        r = self.client.post(reverse("admin:login"), {"username": "sam", "password": "a-long-pass-1234", "next": "/services/"})
        self.assertRedirects(r, "/services/", fetch_redirect_response=False)


class DocsTests(TestCase):
    def test_docs_are_for_developers_and_staff_only(self):
        self.assertEqual(self.client.get(reverse("layout:docs")).status_code, 404)        # DEBUG off, not staff
        user = User.objects.create_user("ann", "ann@example.com", "a-long-pass-1234")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("layout:docs")).status_code, 404)
        with self.settings(DEBUG=True):
            self.assertEqual(self.client.get(reverse("layout:docs")).status_code, 200)

    def test_docs_cover_every_topic(self):
        self.client.force_login(User.objects.create_user("sam", "sam@example.com", "a-long-pass-1234", is_staff=True))
        r = self.client.get(reverse("layout:docs"))
        self.assertTemplateUsed(r, "layout/pages/legal.html")
        html = r.content.decode()
        for part in ("start", "how", "choose", "new-page", "new-app", "access", "blocks", "page-layouts", "shells",
                     "components", "forms", "phone", "messages", "loading", "modals", "account", "menus", "sections",
                     "settings", "look", "screens", "security", "icons", "files", "faq"):
            self.assertIn(f'id="{part}"', html, part)
            if part != "phone":
                self.assertIn(f'href="#{part}"', html, part)                 # listed in the contents
        self.assertIn("{% extends \"layout/pages/banner.html\" %}", html)   # examples shown as text, not run
        self.assertIn("icons.svg#star", html)                                # icon list read from the icon file
        self.assertNotIn("<slug:slug>", html)
