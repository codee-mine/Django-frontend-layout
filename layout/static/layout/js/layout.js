/* layout.js: the layout's own behaviour. No inline scripts anywhere (the security policy blocks them).
   - the header's menu button on small screens             [data-menu-toggle]
   - the header turns solid once the page moves             (.is-scrolled: a see-through header over a picture)
   - the sidebar: fold to icons (remembered in this browser), slide-in panel on phones
                                                            [data-sidebar-collapse] [data-sidebar-open] [data-sidebar-close]
   Toasts, loaders, modals: feedback.js.  Field icons and live checks: fields.js. */
(function () {
  "use strict";
  var doc = document, body = doc.body;

  /* header */
  var header = doc.querySelector(".site-header");
  function onScroll() { if (header) header.classList.toggle("is-scrolled", window.scrollY > 40); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* sidebar */
  var KEY = "layout-sidebar", sidebar = doc.querySelector("[data-sidebar]");
  var opener = doc.querySelector("[data-sidebar-open]"), backdrop = doc.querySelector(".sidebar-backdrop");
  function store(value) { try { if (value) localStorage.setItem(KEY, value); else localStorage.removeItem(KEY); } catch (e) { /* private mode */ } }
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function fold(on, remember) {
    body.classList.toggle("sidebar-collapsed", on);
    body.classList.toggle("sidebar-expanded", !on);
    var b = doc.querySelector("[data-sidebar-collapse]");
    if (b) { b.setAttribute("aria-pressed", String(on)); b.setAttribute("aria-label", on ? "Unfold the menu" : "Fold the menu"); }
    if (remember) store(on ? "collapsed" : "expanded");
  }
  function drawer(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    if (backdrop) backdrop.hidden = !open;
    if (opener) opener.setAttribute("aria-expanded", String(open));
    doc.documentElement.classList.toggle("is-locked", open);
    if (open) { var first = sidebar.querySelector("a, summary, button"); if (first) first.focus(); }
    else if (opener && sidebar.contains(doc.activeElement)) opener.focus();
  }
  if (sidebar) {
    var saved = stored();      // the user's own choice in this browser wins over the saved preference
    fold(saved ? saved === "collapsed" : body.classList.contains("sidebar-collapsed"), false);
  }

  doc.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var toggle = e.target.closest("[data-menu-toggle]");
    if (toggle) {
      var menu = doc.getElementById(toggle.getAttribute("aria-controls"));
      var open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      if (menu) menu.classList.toggle("is-open", open);
      if (header) header.classList.toggle("is-open", open);
    }
    if (e.target.closest("[data-sidebar-collapse]")) fold(!body.classList.contains("sidebar-collapsed"), true);
    if (e.target.closest("[data-sidebar-open]")) drawer(true);
    if (e.target.closest("[data-sidebar-close]")) drawer(false);
  });
  doc.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebar && sidebar.classList.contains("is-open")) drawer(false);
  });
  doc.addEventListener("submit", function (e) {               // saving Layout preferences: the saved choice applies again
    if (e.target.hasAttribute("data-preferences")) store(null);
  });
})();
