/* feedback.js: toasts, loaders, the progress line, modals, confirm boxes and tabs.   window.Layout
 *
 *   Layout.toast("Saved")                       Layout.toast.success("Saved")  .error  .warning  .info
 *   Layout.toast("Saved", { type: "success", title: "Done", duration: 5000, position: "bottom-right" })
 *   var l = Layout.loading({ text: "Saving", place: "center", style: "dots" });   l.text("Almost done");  l.hide()
 *        place: center, fullscreen, top-left, top-right, bottom-left, bottom-right.  ms: hides by itself after that time
 *   Layout.progress.start()  /  Layout.progress.done()                the thin line at the top of the page
 *   var m = Layout.modal({ template: "#terms", title: "Terms", size: "lg", place: "right" });   m.close()
 *        size: sm, md, lg, full.  place: center, right (a panel sliding in from the side)
 *        tab: open on the tab with that data-tab (tabs inside the template)
 *   if (await Layout.confirm({ title: "Delete?", message: "This can't be undone.", confirm: "Delete", danger: true })) …
 *   await Layout.alert({ title: "Saved", message: "Your changes are live.", type: "success" })
 *
 * The same without writing JavaScript, as attributes:
 *   <button data-toast='{"message": "Saved", "type": "success"}'>
 *   <a href="…" data-confirm='{"title": "Leave?", "danger": true}'>           also on buttons and forms
 *   <a href="/terms/" data-modal="#terms-modal">  or  data-modal='{"template": "#terms-modal", "title": "Terms"}'
 *        (the link still works without JavaScript; the modal's content is a <template id="terms-modal"> in the page)
 *   <form data-loading='{"text": "Sending"}'>                                  also on links and buttons
 *   <div data-tabs><div role="tablist"><button role="tab" aria-controls="p1" aria-selected="true">…</button>…</div>
 *        <div id="p1" role="tabpanel">…</div>…</div>
 *
 * Content is only added as text or copied from a <template> in the page, never from an HTML string,
 * so nothing typed by a visitor can turn into code. Messages from Django arrive as toasts (drawn in layout/base.html).
 */
(function () {
  "use strict";
  var doc = document, body = doc.body;
  var ICONS = body.getAttribute("data-icons") || "";
  var TYPES = ["success", "info", "warning", "error"];
  var POSITIONS = ["top-left", "top-center", "top-right", "bottom-left", "bottom-center", "bottom-right"];
  var TYPE_ICON = { success: "check", info: "info", warning: "alert", error: "alert", danger: "trash" };

  function el(tag, cls, text) { var n = doc.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function icon(name) {
    var ns = "http://www.w3.org/2000/svg", svg = doc.createElementNS(ns, "svg"), use = doc.createElementNS(ns, "use");
    svg.setAttribute("class", "icon"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("focusable", "false");
    use.setAttribute("href", ICONS + "#" + (/^[a-z0-9-]+$/.test(name) ? name : "info"));
    svg.appendChild(use); return svg;
  }
  function json(value) { try { return JSON.parse(value || "{}") || {}; } catch (e) { return {}; } }
  function pick(value, list, fallback) { return list.indexOf(value) !== -1 ? value : fallback; }
  function template(selector) {          // only "#id": the content of a <template> already in the page
    return /^#[A-Za-z][\w-]*$/.test(selector || "") ? doc.getElementById(selector.slice(1)) : null;
  }
  // Toasts and loaders go in the browser's top layer (a "popover"), so they appear ABOVE an open modal, not behind it.
  // Showing one again moves it to the top. Browsers without popovers simply keep the normal stacking.
  function onTop(n) {
    if (!n.showPopover) return;
    if (!n.hasAttribute("popover")) n.setAttribute("popover", "manual");
    try { if (n.matches(":popover-open")) n.hidePopover(); n.showPopover(); } catch (e) { /* not in the page yet */ }
  }
  // An open modal makes everything outside it unclickable, so while one is open the toasts live inside it.
  function host() { var open = doc.querySelectorAll("dialog[open]"); return open.length ? open[open.length - 1] : body; }
  function raiseAll() { doc.querySelectorAll(".toasts, .loading").forEach(function (n) { if (n.children.length) onTop(n); }); }
  var locks = 0;
  function lock(on) { locks = Math.max(0, locks + (on ? 1 : -1)); doc.documentElement.classList.toggle("is-locked", locks > 0); }

  /* ------------------------------------------------------------------ toasts */
  var home = doc.querySelector("[data-toasts]");
  var TIME = home ? parseInt(home.getAttribute("data-duration"), 10) : 4000;
  if (isNaN(TIME)) TIME = 4000;

  function stack(position) {
    var pos = pick(position, POSITIONS, home ? home.getAttribute("data-position") : "top-right");
    var s = home && home.getAttribute("data-position") === pos ? home : doc.querySelector('.toasts[data-position="' + pos + '"]');
    if (!s) { s = el("div", "toasts"); s.setAttribute("data-position", pos); }
    if (s.parentNode !== host()) host().appendChild(s);
    return s;
  }
  function arm(t, ms) {                  // timer (paused while the pointer or focus is on it) and the close button
    var timer = null, left = ms, started = 0;
    function close() { clearTimeout(timer); t.classList.add("is-leaving"); setTimeout(function () { t.remove(); }, 250); }
    function run() { if (left > 0 && !timer) { started = Date.now(); timer = setTimeout(close, left); t.classList.remove("is-paused"); } }
    function pause() { if (!timer) return; clearTimeout(timer); timer = null; left -= Date.now() - started; t.classList.add("is-paused"); }
    if (ms > 0) { t.style.setProperty("--toast-time", ms + "ms"); t.classList.add("is-timed"); }
    var x = t.querySelector("[data-toast-close]");
    if (x) x.addEventListener("click", close);
    t.addEventListener("mouseenter", pause); t.addEventListener("focusin", pause);
    t.addEventListener("mouseleave", run); t.addEventListener("focusout", run);
    run();
    return close;
  }
  function toast(message, opts) {
    if (message && typeof message === "object") { opts = message; message = opts.message; }
    opts = opts || {};
    var type = pick(opts.type, TYPES, "info");
    var t = el("div", "toast toast--" + type);
    t.setAttribute("role", type === "error" ? "alert" : "status");
    var ic = el("span", "toast__icon"); ic.appendChild(icon(opts.icon || TYPE_ICON[type])); t.appendChild(ic);
    var text = el("div", "toast__body");
    if (opts.title) text.appendChild(el("strong", "toast__title", opts.title));
    text.appendChild(el("p", "toast__message", message || ""));
    t.appendChild(text);
    var x = el("button", "toast__close"); x.type = "button"; x.setAttribute("data-toast-close", ""); x.setAttribute("aria-label", "Dismiss");
    x.appendChild(icon("x")); t.appendChild(x);
    var bar = el("span", "toast__time"); bar.setAttribute("aria-hidden", "true"); t.appendChild(bar);
    var s = stack(opts.position), bottom = /^bottom/.test(s.getAttribute("data-position"));
    if (bottom) s.appendChild(t); else s.insertBefore(t, s.firstChild);
    while (s.children.length > 4) (bottom ? s.firstElementChild : s.lastElementChild).remove();   // at most 4 at once
    onTop(s);
    var ms = opts.duration != null ? +opts.duration : TIME;
    return { el: t, close: arm(t, ms > 0 ? ms : 0) };
  }
  TYPES.forEach(function (type) {
    toast[type] = function (message, opts) { return toast(message, Object.assign({}, opts || {}, { type: type })); };
  });
  doc.querySelectorAll(".toasts .toast").forEach(function (t) { arm(t, TIME); });   // messages from the server
  if (home && home.children.length) onTop(home);

  /* ------------------------------------------------------------------ loaders */
  var PLACES = ["center", "fullscreen", "top-left", "top-right", "bottom-left", "bottom-right"];
  function spinner(style) {
    var s = el("span", "spinner spinner--" + style + " spinner--md"); s.setAttribute("aria-hidden", "true");
    if (style === "dots") for (var i = 0; i < 3; i++) s.appendChild(el("span"));
    return s;
  }
  function loading(opts) {
    if (typeof opts === "string") opts = { text: opts };
    opts = opts || {};
    doc.querySelectorAll(".loading").forEach(function (n) { n._hide(); });     // one at a time
    var place = pick(opts.place, PLACES, "center"), covers = place === "center" || place === "fullscreen";
    var w = el("div", "loading loading--" + place);
    w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
    var box = el("div", "loading__box");
    box.appendChild(spinner(pick(opts.style, ["spinner", "dots"], "spinner")));
    var text = el("p", "loading__text", opts.text || "Loading");
    box.appendChild(text); w.appendChild(box); body.appendChild(w); onTop(w);
    if (covers) lock(true);
    var gone = false, timer = opts.ms ? setTimeout(hide, +opts.ms) : null;
    function hide() { if (gone) return; gone = true; clearTimeout(timer); w.remove(); if (covers) lock(false); }
    w._hide = hide;
    return { el: w, hide: hide, text: function (t) { text.textContent = t; } };
  }

  /* ------------------------------------------------------------------ progress line + page loader */
  var line = doc.querySelector("[data-progress]"), value = 0, ticker = null;
  function setLine(v) { if (!line) return; value = Math.max(value, Math.min(1, v)); line.classList.add("is-on"); line.style.transform = "scaleX(" + value.toFixed(3) + ")"; }
  var progress = {
    start: function () { clearInterval(ticker); value = 0; setLine(0.08); ticker = setInterval(function () { if (value < 0.9) setLine(value + (0.9 - value) * 0.08); }, 200); },
    done: function () {
      clearInterval(ticker); if (!line) return; setLine(1);
      setTimeout(function () { line.classList.remove("is-on"); value = 0; line.style.transform = "scaleX(0)"; }, 300);
    }
  };
  var pageLoader = doc.querySelector("[data-page-loader]");
  function pageReady() { if (pageLoader) pageLoader.classList.add("is-done"); }
  if (doc.readyState === "complete") pageReady(); else window.addEventListener("load", pageReady);
  setTimeout(pageReady, 3000);                                 // never longer than this, even if a picture is slow
  function navigating() {                                       // the next page is on its way (settings: LOADER → NAVIGATE)
    var mode = body.getAttribute("data-navigate");
    if (mode === "loader" && pageLoader) { pageLoader.classList.add("is-again"); pageLoader.classList.remove("is-done"); }
    else if (mode !== "none") progress.start();
  }
  window.addEventListener("pageshow", function (e) {          // back/forward: undo what the last click started
    progress.done(); pageReady();
    if (e.persisted) {
      doc.querySelectorAll(".loading").forEach(function (n) { n._hide(); });
      doc.querySelectorAll('[aria-busy="true"]').forEach(function (b) { b.disabled = false; b.removeAttribute("aria-busy"); });
    }
  });

  /* ------------------------------------------------------------------ modals and confirm boxes */
  function opened(d, onClose) {          // shared by modals and dialogs: open, lock the page, close once, give focus back
    var opener = doc.activeElement, done = false;
    function close() {
      if (done) return; done = true;
      if (d.open) d.close();
      d.querySelectorAll(".toasts").forEach(function (s) { body.appendChild(s); if (s.children.length) onTop(s); });   // toasts go back
      d.remove(); lock(false);
      if (opener && opener.focus) opener.focus();
      if (onClose) onClose();
    }
    d.addEventListener("close", close);
    d.addEventListener("click", function (e) {
      var r = d.getBoundingClientRect();
      var outside = e.target === d && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom);
      if (outside || e.target.closest("[data-modal-close]")) close();          // the dark backdrop, or a close button
    });
    body.appendChild(d); d.showModal(); lock(true);
    doc.querySelectorAll(".toasts").forEach(function (s) { if (s.children.length) d.appendChild(s); });   // clickable inside it
    raiseAll();                                               // toasts already showing stay above the new modal
    return close;
  }
  function modal(opts) {
    if (typeof opts === "string") opts = { template: opts };
    opts = opts || {};
    var d = el("dialog", "modal modal--" + pick(opts.size, ["sm", "md", "lg", "full"], "md") + " modal--" + pick(opts.place, ["center", "right"], "center"));
    var head = el("div", "modal__head"), id = "modal-" + Math.random().toString(36).slice(2);
    if (opts.title) { var h = el("h2", "modal__title", opts.title); h.id = id; head.appendChild(h); d.setAttribute("aria-labelledby", id); }
    else d.setAttribute("aria-label", opts.label || "Dialog");
    var x = el("button", "modal__close"); x.type = "button"; x.setAttribute("data-modal-close", ""); x.setAttribute("aria-label", "Close");
    x.appendChild(icon("x")); head.appendChild(x); d.appendChild(head);
    var content = el("div", "modal__body"), tpl = template(opts.template);
    if (tpl && tpl.content) content.appendChild(doc.importNode(tpl.content, true));
    else if (opts.text) content.appendChild(el("p", null, opts.text));
    d.appendChild(content);
    var close = opened(d, opts.onClose);
    if (window.Layout && Layout.fields) Layout.fields.init(content);
    var tab = opts.tab && /^[\w-]+$/.test(opts.tab) ? content.querySelector('[role="tab"][data-tab="' + opts.tab + '"]') : null;
    if (tab) selectTab(tab);                                  // open on a chosen tab, e.g. "register"
    var field = "input:not([type=hidden]):enabled, select:enabled, textarea:enabled";      // :enabled also skips disabled fieldsets
    var panel = content.querySelector('[role="tabpanel"]:not([hidden])');
    var first = panel ? (panel.querySelector(field) || content.querySelector('[role="tab"][aria-selected="true"]'))
                      : content.querySelector(field + ", button:enabled, a[href]");
    (first || x).focus();
    return { el: d, close: close };
  }
  function dialog(opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      var type = pick(opts.type, TYPES.concat("danger"), "info"), result = opts.cancelValue;
      var d = el("dialog", "modal modal--sm modal--center dialog dialog--" + type), id = "dialog-" + Math.random().toString(36).slice(2);
      var ic = el("span", "dialog__icon"); ic.appendChild(icon(TYPE_ICON[type])); d.appendChild(ic);
      var h = el("h2", "dialog__title", opts.title || ""); h.id = id; d.appendChild(h); d.setAttribute("aria-labelledby", id);
      if (opts.message) { var m = el("p", "dialog__message", opts.message); m.id = id + "-m"; d.appendChild(m); d.setAttribute("aria-describedby", m.id); }
      var foot = el("div", "dialog__buttons"), close;
      (opts.buttons || []).forEach(function (b) {
        var btn = el("button", "button" + (b.variant ? " button--" + b.variant : ""), b.label); btn.type = "button";
        btn.addEventListener("click", function () { result = b.value; close(); });
        foot.appendChild(btn);
      });
      d.appendChild(foot);
      close = opened(d, function () { resolve(result); });
      foot.firstChild.focus();
    });
  }
  function confirmBox(opts) {
    opts = typeof opts === "string" ? { message: opts } : (opts || {});
    return dialog({ title: opts.title || "Are you sure?", message: opts.message, type: opts.danger ? "danger" : (opts.type || "warning"), cancelValue: false,
      buttons: [{ label: opts.confirm || "Continue", value: true, variant: opts.danger ? "danger" : "" },
                { label: opts.cancel || "Cancel", value: false, variant: "outline" }] });
  }
  function alertBox(opts) {
    opts = typeof opts === "string" ? { message: opts } : (opts || {});
    return dialog({ title: opts.title || "Notice", message: opts.message, type: opts.type, cancelValue: true,
      buttons: [{ label: opts.ok || "OK", value: true }] });
  }

  /* ------------------------------------------------------------------ tabs */
  function selectTab(tab) {
    tab.closest('[role="tablist"]').querySelectorAll('[role="tab"]').forEach(function (t) {
      var on = t === tab, panel = doc.getElementById(t.getAttribute("aria-controls"));
      t.setAttribute("aria-selected", String(on)); t.tabIndex = on ? 0 : -1;
      if (panel) panel.hidden = !on;
    });
  }
  doc.querySelectorAll('[data-tabs] [role="tab"][aria-selected="true"]').forEach(selectTab);
  doc.addEventListener("keydown", function (e) {
    var t = e.target.closest && e.target.closest('[data-tabs] [role="tab"]');
    if (!t || (e.key !== "ArrowRight" && e.key !== "ArrowLeft")) return;
    var tabs = Array.prototype.slice.call(t.closest('[role="tablist"]').querySelectorAll('[role="tab"]'));
    var next = tabs[(tabs.indexOf(t) + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length];
    selectTab(next); next.focus(); e.preventDefault();
  });

  /* ------------------------------------------------------------------ attributes (data-…) */
  doc.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var c = e.target.closest("a[data-confirm], button[data-confirm]");
    if (c && !c._confirmed) {                                    // ask first; the click runs again after "yes"
      e.preventDefault(); e.stopImmediatePropagation();
      confirmBox(json(c.getAttribute("data-confirm"))).then(function (ok) {
        if (!ok) return;
        if (c.tagName === "A") { navigating(); location.href = c.href; return; }
        c._confirmed = true; c.click(); c._confirmed = false;
      });
      return;
    }
    var tab = e.target.closest('[data-tabs] [role="tab"]');
    if (tab) selectTab(tab);
    var t = e.target.closest("[data-toast]");
    if (t) { e.preventDefault(); toast(json(t.getAttribute("data-toast"))); }
    var m = e.target.closest("[data-modal]");
    if (m) {
      var raw = m.getAttribute("data-modal"), mo = raw.charAt(0) === "{" ? json(raw) : { template: raw };
      if (template(mo.template)) { e.preventDefault(); modal(mo); }       // no template: the link opens normally
    }
    var l = e.target.closest("a[data-loading], button[data-loading]:not([type=submit])");
    if (l && !e.defaultPrevented) loading(json(l.getAttribute("data-loading")));
  }, true);

  doc.addEventListener("click", function (e) {                  // a link to another page: show progress
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if ((a.target && a.target !== "_self") || a.hasAttribute("download") || a.hasAttribute("data-loading") || a.origin !== location.origin) return;
    if (a.pathname === location.pathname && a.search === location.search) return;   // same page (or a #part of it)
    navigating();
  });

  doc.addEventListener("submit", function (e) {
    var f = e.target, button = e.submitter;
    if (f.hasAttribute("data-confirm") && !f._confirmed) {
      e.preventDefault();
      confirmBox(json(f.getAttribute("data-confirm"))).then(function (ok) {
        if (!ok) return;
        f._confirmed = true;
        if (f.requestSubmit) f.requestSubmit(button && button.form === f ? button : undefined); else f.submit();
        f._confirmed = false;
      });
      return;
    }
    if (e.defaultPrevented || f.target === "_blank") return;
    if (f.hasAttribute("data-loading")) loading(json(f.getAttribute("data-loading"))); else navigating();
    if (button) setTimeout(function () { button.disabled = true; button.setAttribute("aria-busy", "true"); }, 0);   // not sent twice
  });

  window.Layout = Object.assign(window.Layout || {}, {
    toast: toast, loading: loading, progress: progress, modal: modal,
    confirm: confirmBox, alert: alertBox, dialog: dialog, tabs: { select: selectTab }
  });
})();
