from django.test import TestCase
from django.urls import reverse

from .views import STORIES


class PageTests(TestCase):
    def test_public_pages_open_without_signing_in(self):
        for name in ("frontend:home", "frontend:about", "frontend:contact", "frontend:stories", "frontend:guide", "frontend:privacy",
                     "frontend:terms", "frontend:services"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_contact_form_checks_fields(self):
        r = self.client.post(reverse("frontend:contact"), {"name": "", "email": "nope", "message": ""})
        self.assertContains(r, "This field is required.")
        self.assertContains(r, "Enter a valid email address.")

    def test_404_uses_the_centered_layout(self):
        with self.settings(DEBUG=False):
            r = self.client.get("/no-such-page/")
        self.assertEqual(r.status_code, 404)
        self.assertTemplateUsed(r, "layout/pages/centered.html")
        self.assertContains(r, 'class="centered"', status_code=404)


class PageLayoutTests(TestCase):
    """Each page layout is used by at least one page and draws its own part."""

    def check(self, url, layout, marker, nav="solid"):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        self.assertTemplateUsed(r, f"layout/pages/{layout}.html")
        self.assertTemplateUsed(r, "layout/public.html")
        self.assertContains(r, marker)
        self.assertContains(r, f'data-nav="{nav}"')
        return r

    def test_home_hero(self):
        self.check(reverse("frontend:home"), "home", 'class="hero"', nav="transparent")

    def test_banner(self):
        r = self.check(reverse("frontend:about"), "banner", 'class="banner"', nav="transparent")
        self.assertContains(r, 'class="breadcrumbs"')
        self.assertNotContains(r, 'class="page-header"')

    def test_listing_and_pages(self):
        r = self.check(reverse("frontend:stories"), "listing", 'class="band"')
        self.assertEqual(r.content.decode().count('class="card"'), 4)
        self.assertContains(r, 'rel="next"')
        r = self.client.get(reverse("frontend:stories"), {"page": "2"})
        self.assertEqual(r.content.decode().count('class="card"'), len(STORIES) - 4)
        self.assertEqual(self.client.get(reverse("frontend:stories"), {"page": "nonsense"}).status_code, 200)

    def test_detail(self):
        self.check(reverse("frontend:story", args=[STORIES[0]["slug"]]), "detail", 'class="photo-header"', nav="transparent")
        self.assertEqual(self.client.get(reverse("frontend:story", args=["no-such-story"])).status_code, 404)

    def test_article(self):
        self.check(reverse("frontend:guide"), "article", 'class="prose"')

    def test_legal(self):
        r = self.check(reverse("frontend:privacy"), "legal", 'class="toc"')
        self.assertContains(r, 'href="#collect"')
        self.check(reverse("frontend:terms"), "legal", 'class="toc"')

    def test_footer_menu(self):
        r = self.client.get(reverse("frontend:home"))
        self.assertContains(r, 'aria-label="Information"')
        self.assertContains(r, reverse("frontend:privacy"))
