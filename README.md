# Layout project

A Django project built around **one `layout` app** that holds every reusable layout, the shared CSS, JavaScript and
pictures. Other apps pick a layout for each page and write the page's own content in plain HTML.

- **Layouts:** public, auth and plain are open to everyone; user is private (signed in); admin is for staff.
  Page layouts on top of public: home, banner, band, listing, detail, article, legal, centered.
- **Every screen:** phones, tablets, laptops, desktops and TVs.
- **The full guide is the docs page, `/layout/docs/`**, which covers making a new page or app, every layout and block,
  forms, toasts, modals, menus, settings and security.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS / Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env             # then set DJANGO_SECRET_KEY, and DJANGO_DEBUG=True on your computer
python manage.py migrate
python manage.py createsuperuser   # a staff account (it signs in at /admin/ until an accounts app exists)
python manage.py runserver
python manage.py test              # 62 tests
```

| Address | What |
|---|---|
| `/` | home page (home layout) |
| `/about/` `/contact/` `/services/` | banner layout |
| `/stories/` · `/stories/<slug>/` | listing layout · detail layout |
| `/how-its-built/` | article layout |
| `/privacy/` `/terms/` | legal layout |
| any missing page, 403, 500 | centered layout |
| `/layout/preferences/` | each person's layout choices: **private** (user layout) |
| `/layout/staff/` | staff start page: **staff only** (admin layout) |
| `/layout/docs/` · `/layout/gallery/` | the guide · every part in action. Open while `DJANGO_DEBUG=True`, otherwise staff only |
| `/admin/` | Django's admin, also the sign-in page for now |

## How it fits together

```
layout/                       everything shared
  templates/layout/
    base.html                 the one HTML skeleton (head, styles, scripts, loader, toasts)
    public.html  user.html  auth.html  admin.html  plain.html     the main layouts (public.html holds the site
                              header and footer, admin.html the staff header, base.html the loader and toasts)
    pages/                    page layouts: home banner band listing detail article legal centered
    partials/                 only pieces shared by several layouts: icon, logo, navbar, profile_menu, sidebar,
                              breadcrumbs, private_notice, auth_modal
    screens/                  the layout app's own pages: preferences, staff start, gallery, docs
  templates/403.html 404.html 500.html
  static/layout/
    css/layout.css            every style; colours and sizes are variables at the top
    js/layout.js              header menu, header on scroll, sidebar
    js/feedback.js            toasts, loaders, progress line, modals, confirm boxes, tabs
    js/fields.js              field ✕ and eye buttons, phone country picker, live error messages
    img/                      favicon.svg (also the logo), icons.svg (all icons), scene-1…6.svg pictures
  access.py                   @public, @private, @staff_only, @dev_or_staff
  context_processors.py       the `layout` variable every template gets (site name, menus, links, settings)
  models.py  forms.py         each person's layout choices; PhoneField (checks a phone number per country)
  countries.py  badges.py  views.py  urls.py  admin.py  tests.py  tests_dynamic.py
frontend/                     the public website
  templates/frontend/         its pages: each extends a layout and writes its content (sections too) in HTML
  views.py  urls.py  forms.py  tests.py
config/                       settings.py (LAYOUT: site name, links, menus, toasts, loader…), urls.py, env.py
```

**How a page is drawn:** the view checks who may open it and renders the template. The template extends a layout
and writes its content. The layout adds the header, menus and footer, and `base.html` adds the rest. Change a layout
and every page using it changes; a page changes only itself.

## Security notes

- Access is checked in every view (`@public`, `@private`, `@staff_only`, `@permission_required`). The private
  layouts also hide their content from the wrong visitor, as a second line of defence.
- Templates rely on Django's autoescaping: no `mark_safe`, no custom template tags, no user-chosen templates.
- Forms use CSRF tokens, and the server checks every form again; signing out is a POST.
- A strict Content Security Policy allows only this site's own files. No inline scripts or styles are used.
- Toasts and dialogs only ever add text, and modals copy a `<template>` already in the page.
- Secrets come from `.env` (ignored by git). With `DJANGO_DEBUG=False`, production turns on HTTPS-only cookies,
  HSTS and the HTTPS redirect. Before going live, run `python manage.py check --deploy` and `python manage.py collectstatic`.
- The contact form is a demo: it shows a thank-you message but doesn't store or send anything.
