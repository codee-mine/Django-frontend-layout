from django.urls import path

from . import views

app_name = "layout"
urlpatterns = [
    path("preferences/", views.preferences, name="preferences"),
    path("staff/", views.staff_home, name="staff_home"),
    path("gallery/", views.gallery, name="gallery"),
    path("gallery/plain/", views.gallery_plain, name="gallery_plain"),
    path("docs/", views.docs, name="docs"),
]
