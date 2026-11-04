"""The website's pages. Each view gets the data a page needs and renders its template.
The template extends a layout (header, menus, footer) and writes its own content in HTML."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from layout import countries

from .forms import ContactForm

# Sample content for the listing and detail layouts. In a real site this would come from a model.
STORIES = [
    {"slug": "one-layout", "title": "One layout for every page", "date": "4 Nov 2026", "image": "layout/img/scene-1.svg",
     "summary": "Why the header, footer and menus live in a single app.",
     "body": ["Every page on this site draws its header, menus and footer from the layout app.",
              "When the design changes, it changes in one place, and every page follows."]},
    {"slug": "picture-banners", "title": "Picture banners", "date": "28 Oct 2026", "image": "layout/img/scene-2.svg",
     "summary": "A banner with a heading and breadcrumbs, ready for any page.",
     "body": ["The banner layout puts a picture behind the page heading.", "Pages only choose the picture and the words."]},
    {"slug": "your-own-theme", "title": "Your own theme", "date": "20 Oct 2026", "image": "layout/img/scene-3.svg",
     "summary": "Visitors can pick light or dark, and compact spacing.",
     "body": ["Signed-in visitors choose a theme under Layout preferences.", "Only fixed choices are accepted, so nothing unsafe reaches the page."]},
    {"slug": "staff-area", "title": "A separate staff area", "date": "12 Oct 2026", "image": "layout/img/scene-4.svg",
     "summary": "Staff get their own layout with a dark side menu.",
     "body": ["The staff area has its own header and side menu.", "Every staff page checks permissions on the server."]},
    {"slug": "secure-by-default", "title": "Secure by default", "date": "3 Oct 2026", "image": "layout/img/scene-5.svg",
     "summary": "A strict content security policy, CSRF tokens and safe cookies.",
     "body": ["No inline scripts or styles are used anywhere, so a strict policy can block them all.",
              "Secrets live in the .env file, never in the code."]},
    {"slug": "small-screens", "title": "Made for small screens", "date": "25 Sep 2026", "image": "layout/img/scene-6.svg",
     "summary": "Menus fold away and columns stack on phones.",
     "body": ["The header turns into a menu button on phones.", "Side boxes move under the main column."]},
]


def _crumbs(*items):
    return [("Home", reverse("frontend:home")), *items]


def home(request):
    return render(request, "frontend/home.html", {"stories": STORIES[:3]})


def services(request):
    return render(request, "frontend/services.html", {"breadcrumbs": _crumbs(("Services", None))})


def about(request):
    return render(request, "frontend/about.html", {"breadcrumbs": _crumbs(("About", None))})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Demo: the message isn't stored or sent anywhere. Connect it to email or a model when needed.
        messages.success(request, "Thanks, your message has been received.")
        return redirect("frontend:contact")
    return render(request, "frontend/contact.html", {
        "form": form,
        "countries": countries.COUNTRIES,                                          # for the phone's country list
        "phone_country": request.POST.get("phone_0") or countries.default_code(),  # the country picked
        "breadcrumbs": _crumbs(("Contact", None)),
    })


def stories(request):
    page_obj = Paginator(STORIES, 4).get_page(request.GET.get("page"))   # get_page copes with missing or bad numbers
    return render(request, "frontend/stories.html", {"page_obj": page_obj, "breadcrumbs": _crumbs(("Stories", None))})


def story(request, slug):
    item = next((s for s in STORIES if s["slug"] == slug), None)
    if item is None:
        raise Http404("No such story")
    others = [s for s in STORIES if s["slug"] != slug][:2]
    return render(request, "frontend/story.html", {"story": item, "others": others,
                                                "breadcrumbs": _crumbs(("Stories", reverse("frontend:stories")), (item["title"], None))})


def guide(request):
    return render(request, "frontend/guide.html", {"breadcrumbs": _crumbs(("How it's built", None))})


def privacy(request):
    return render(request, "frontend/privacy.html", {"breadcrumbs": _crumbs(("Privacy", None))})


def terms(request):
    return render(request, "frontend/terms.html", {"breadcrumbs": _crumbs(("Terms", None))})
