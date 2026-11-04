/* fields.js: form fields written in a page as <div class="field" data-field data-type="…"> (see the docs, Forms and fields).
   - ✕ clears a field (shown only when it has text); password fields also have the eye to show or hide the password
   - phone fields (layout.forms.PhoneField): a searchable country-code picker; digits are checked for that country
   - each field is checked when you leave it and again while you fix it, with the same messages the server uses
     (read from data-msg-… on the field); a form with problems isn't sent: the first one gets focus and a toast explains.
   The server always checks again, so forms keep working, and stay safe, without JavaScript.
   Layout.fields.init(element) sets up fields added later (feedback.js calls it for modals);
   Layout.fields.validate(form) → { ok, invalid: [fields] }. */
(function () {
  "use strict";
  var doc = document;
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/, URL_RE = /^https?:\/\/[^\s.]+\.\S+$/i;

  function wrap(n) { return n && n.closest ? n.closest("[data-field]") : null; }
  function control(w) { return w.querySelector("[data-phone] input") || w.querySelector("input:not([type=hidden]), textarea, select"); }
  function country(w) { var s = w.querySelector("[data-phone-country]"); return s ? s.options[s.selectedIndex] : null; }
  function filled(c) { return c.type === "checkbox" ? c.checked : !!(c.value || "").trim(); }

  function check(w) {
    var c = control(w);
    if (!c) return true;
    var type = w.getAttribute("data-type"), v = (c.value || "").trim(), msg = "";
    if (type === "checkbox") { if (c.required && !c.checked) msg = w.getAttribute("data-msg-required"); }
    else if (!v) { if (c.required) msg = w.getAttribute("data-msg-required") || "This field is required."; }
    else if (type === "email" && !EMAIL.test(v)) msg = w.getAttribute("data-msg-invalid") || "Enter a valid email address.";
    else if (type === "url" && !URL_RE.test(v)) msg = w.getAttribute("data-msg-invalid") || "Enter a valid URL.";
    else if (type === "phone") {                              // same rule and message as layout.forms.PhoneField
      var o = country(w), digits = v.replace(/\D/g, "").replace(/^0+/, ""), min = +o.getAttribute("data-min"), max = +o.getAttribute("data-max");
      if (/[^\d\s\-()+]/.test(v)) msg = "Use digits, spaces and dashes only.";
      else if (digits.length < min || digits.length > max) msg = (w.getAttribute("data-msg-invalid") || "Enter a valid phone number for {country} ({digits} digits).")
        .replace("{country}", o.getAttribute("data-name")).replace("{digits}", min === max ? String(min) : min + "–" + max);
    }
    else if (c.minLength > 0 && v.length < c.minLength) msg = "Ensure this value has at least " + c.minLength + " characters (it has " + v.length + ").";
    else if (c.maxLength > 0 && v.length > c.maxLength) msg = "Ensure this value has at most " + c.maxLength + " characters (it has " + v.length + ").";
    else if (type === "number" && c.validity && !c.validity.valid) msg = c.validationMessage || "Enter a number.";
    var match = w.getAttribute("data-match");
    if (!msg && match) { var other = doc.getElementById(match); if (other && other.value !== c.value) msg = "The two password fields didn’t match."; }
    show(w, msg || "");
    return !msg;
  }
  function show(w, msg) {
    var c = control(w), err = w.querySelector(".field__error");
    w.classList.toggle("is-invalid", !!msg);
    w.classList.toggle("is-valid", !msg && filled(c));
    if (msg) c.setAttribute("aria-invalid", "true"); else c.removeAttribute("aria-invalid");
    if (err) err.textContent = msg;
  }
  function validate(target) {
    var list = target.matches && target.matches("[data-field]") ? [target] : Array.prototype.slice.call(target.querySelectorAll("[data-field]"));
    var bad = list.filter(function (w) { return !check(w); });
    return { ok: !bad.length, invalid: bad };
  }
  function syncClear(w) {
    var b = w.querySelector("[data-field-clear]"), c = control(w);
    if (b && c) b.hidden = !(c.value || "").length || c.disabled || c.readOnly;
  }
  /* ---------- phone: a searchable country-code picker over the plain list (the list still works without JS) ---------- */
  function picker(box) {
    if (box.hasAttribute("data-ready")) return;
    box.setAttribute("data-ready", "");
    var select = box.querySelector("[data-phone-country]"), w = wrap(box), input = control(w), id = select.id + "-list", active = -1;
    var btn = doc.createElement("button"), panel = doc.createElement("div"), search = doc.createElement("input"), list = doc.createElement("ul");
    btn.type = "button"; btn.className = "phone__btn";
    btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false"); btn.setAttribute("aria-controls", id);
    panel.className = "phone__panel"; panel.hidden = true;
    search.type = "search"; search.className = "phone__search"; search.placeholder = "Search country or code";
    search.setAttribute("aria-label", "Search countries"); search.setAttribute("aria-controls", id); search.autocomplete = "off";
    list.className = "phone__list"; list.id = id; list.setAttribute("role", "listbox"); list.setAttribute("aria-label", "Countries");
    panel.appendChild(search); panel.appendChild(list);
    select.classList.add("visually-hidden"); select.tabIndex = -1; select.setAttribute("aria-hidden", "true");
    box.insertBefore(btn, select.nextSibling); box.appendChild(panel);

    function label() {
      var o = select.options[select.selectedIndex], min = o.getAttribute("data-min"), max = o.getAttribute("data-max");
      btn.textContent = "";
      var code = doc.createElement("span"); code.className = "phone__code"; code.textContent = o.value;
      var dial = doc.createElement("span"); dial.textContent = "+" + o.getAttribute("data-dial");
      btn.appendChild(code); btn.appendChild(dial);
      btn.setAttribute("aria-label", "Country: " + o.getAttribute("data-name") + " (+" + o.getAttribute("data-dial") + "). Change");
      input.placeholder = (min === max ? max : min + "–" + max) + " digits";
    }
    function render(q) {
      q = (q || "").toLowerCase().replace(/^\+/, "");
      list.textContent = ""; active = -1;
      Array.prototype.forEach.call(select.options, function (o, i) {
        var name = o.getAttribute("data-name"), dial = o.getAttribute("data-dial");
        if (q && name.toLowerCase().indexOf(q) === -1 && dial.indexOf(q) !== 0 && o.value.toLowerCase() !== q) return;
        var li = doc.createElement("li"), n = doc.createElement("span"), d = doc.createElement("small");
        li.setAttribute("role", "option"); li.id = id + "-" + o.value; li.setAttribute("data-index", i);
        li.setAttribute("aria-selected", String(i === select.selectedIndex));
        n.textContent = name; d.textContent = "+" + dial;
        li.appendChild(n); li.appendChild(d); list.appendChild(li);
      });
      if (!list.children.length) { var none = doc.createElement("li"); none.className = "phone__none"; none.textContent = "No country matches"; list.appendChild(none); }
    }
    function move(i) {
      var items = list.querySelectorAll("[role=option]"); if (!items.length) return;
      active = (i + items.length) % items.length;
      items.forEach(function (li, n) { li.classList.toggle("is-active", n === active); });
      items[active].scrollIntoView({ block: "nearest" });
      search.setAttribute("aria-activedescendant", items[active].id);
    }
    function open() {
      panel.hidden = false; btn.setAttribute("aria-expanded", "true"); search.value = ""; render("");
      var sel = list.querySelector('[aria-selected="true"]');
      if (sel) move(Array.prototype.indexOf.call(list.children, sel));
      search.focus();
    }
    function close(focusButton) { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); if (focusButton) btn.focus(); }
    function choose(i) {
      select.selectedIndex = +i; select.dispatchEvent(new Event("change", { bubbles: true }));
      label(); close(false); input.focus();
      if (w.hasAttribute("data-touched") || input.value) check(w);
    }
    btn.addEventListener("click", function () { if (panel.hidden) open(); else close(true); });
    search.addEventListener("input", function () { render(search.value); move(0); });
    search.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(active - 1); }
      else if (e.key === "Enter") { e.preventDefault(); var li = list.querySelectorAll("[role=option]")[active]; if (li) choose(li.getAttribute("data-index")); }
      else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(true); }
      else if (e.key === "Tab") close(false);
    });
    list.addEventListener("mousedown", function (e) { e.preventDefault(); });          // keep focus in the search box
    list.addEventListener("click", function (e) { var li = e.target.closest("[role=option]"); if (li) choose(li.getAttribute("data-index")); });
    doc.addEventListener("click", function (e) { if (!panel.hidden && !box.contains(e.target)) close(false); });
    label();
  }

  function init(root) {
    (root || doc).querySelectorAll("[data-phone]").forEach(picker);
    (root || doc).querySelectorAll("[data-field]").forEach(function (w) {
      syncClear(w);
      var c = control(w), err = w.querySelector(".field__error");
      if (c && err && err.id) {                               // screen readers read the error with the field
        var ids = (c.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
        if (ids.indexOf(err.id) === -1) { ids.push(err.id); c.setAttribute("aria-describedby", ids.join(" ")); }
      }
    });
  }

  doc.addEventListener("input", function (e) {
    var w = wrap(e.target); if (!w) return;
    if (w.getAttribute("data-type") === "phone" && e.target === control(w)) {
      var cleaned = e.target.value.replace(/[^\d\s\-()+]/g, "");      // digits, spaces, dashes and brackets only
      if (cleaned !== e.target.value) e.target.value = cleaned;
    }
    syncClear(w);
    if (w.classList.contains("is-invalid") || w.hasAttribute("data-touched")) check(w);
    var twin = e.target.id && doc.querySelector('[data-field][data-match="' + e.target.id + '"][data-touched]');
    if (twin) check(twin);
  });
  doc.addEventListener("focusout", function (e) {
    var w = wrap(e.target);
    if (!w || w.contains(e.relatedTarget)) return;
    var c = control(w);
    if (c && (filled(c) || w.hasAttribute("data-touched"))) { w.setAttribute("data-touched", ""); check(w); }
  });
  doc.addEventListener("change", function (e) { var w = wrap(e.target); if (w && w.getAttribute("data-type") === "checkbox") check(w); });
  doc.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var clear = e.target.closest("[data-field-clear]");
    if (clear) { var c = control(wrap(clear)); c.value = ""; c.dispatchEvent(new Event("input", { bubbles: true })); c.focus(); }
    var eye = e.target.closest("[data-field-eye]");
    if (eye) {
      var input = control(wrap(eye)), showing = input.type === "password";
      input.type = showing ? "text" : "password";
      eye.setAttribute("aria-pressed", String(showing));
      eye.setAttribute("aria-label", showing ? "Hide password" : "Show password");
      var use = eye.querySelector("use");
      if (use) use.setAttribute("href", use.getAttribute("href").replace(/#.*$/, showing ? "#eye-off" : "#eye"));
      input.focus();
    }
  });

  doc.addEventListener("submit", function (e) {                // checked first (capture), before loaders or confirm boxes
    var form = e.target;
    if (!form.querySelector("[data-field]")) return;
    form.querySelectorAll("[data-field]").forEach(function (w) { w.setAttribute("data-touched", ""); });
    var result = validate(form);
    if (result.ok) return;
    e.preventDefault(); e.stopImmediatePropagation();
    var first = result.invalid[0];
    control(first).focus({ preventScroll: true });
    first.scrollIntoView({ block: "center", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    if (window.Layout && Layout.toast) {
      var n = result.invalid.length;
      Layout.toast.error(n === 1 ? "Please check the highlighted field." : "Please check the " + n + " highlighted fields.", { title: "Almost there" });
    }
  }, true);

  init(doc);
  window.Layout = Object.assign(window.Layout || {}, { fields: { init: init, validate: validate } });
})();
