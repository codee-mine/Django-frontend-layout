from django.urls import path

from . import views

app_name = "frontend"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("stories/", views.stories, name="stories"),
    path("stories/<slug:slug>/", views.story, name="story"),
    path("how-its-built/", views.guide, name="guide"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("services/", views.services, name="services"),
]
