/* LeadFinder UI: vanilla JS over the local JSON API, with GSAP + Flip for motion.
   Views: Next up (home), All leads, Follow-ups, Searches, Import & check, Settings.
   Rule: background work never moves what the user is looking at; new data is announced, then shown on request. */
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (name) => `<svg class="ic" aria-hidden="true"><use href="#i-${name}"/></svg>`;
const store = {
  get(k, d) { try { const v = localStorage.getItem("lf:" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("lf:" + k, JSON.stringify(v)); } catch { /* private mode: fine */ } },
};

async function api(path, body, opts = {}) {
  const init = body === undefined ? {} : { method: "POST", headers: { "Content-Type": opts.type || "application/json" }, body: opts.type ? body : JSON.stringify(body) };
  const r = await fetch(path, init);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(data.error || `Something went wrong (${r.status}). Try again.`); e.data = data; throw e; }
  return data;
}

/* ============================================================ motion
   One authored moment (a card opening into its profile), plus reflow, entrance and feedback.
   Content is always visible by default; with no GSAP or reduced motion, changes just happen. */
const M = (() => {
  const g = window.gsap, F = window.Flip;
  if (g && F) g.registerPlugin(F);
  if (g) g.ticker.lagSmoothing(0); // finish on time even when frames are slow, never freeze mid-move
  const ok = () => !!(g && F) && !matchMedia("(prefers-reduced-motion: reduce)").matches;
  const inView = (els) => els.filter((el) => { const r = el.getBoundingClientRect(); return r.bottom > -40 && r.top < innerHeight + 40; });
  return {
    ok,
    /* Record where things are, change the DOM, then glide them to where they ended up. */
    flip(targets, change, opts = {}) {
      if (!ok()) { change(); return null; }
      const st = F.getState(inView(targets), { props: "borderRadius" });
      change();
      return F.from(st, { duration: 0.45, ease: "expo.out", scale: false, simple: true, nested: true, ...opts });
    },
    /* Re-render a list and let surviving cards move to their new spots; new ones fade in. */
    reflow(container, change) {
      if (!ok()) { change(); return; }
      const st = F.getState(inView($$(".card", container)));
      change();
      const now = $$(".card", container);
      F.from(st, {
        targets: now, duration: 0.4, ease: "expo.out", scale: false, simple: true,
        onEnter: (els) => g.fromTo(inView(els), { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", stagger: { amount: 0.12 }, clearProps: "opacity,transform" }),
      });
    },
    enter(els, { y = 10, stagger = 0.04 } = {}) {
      els = [...els].filter(Boolean);
      if (!ok() || !els.length) return;
      g.fromTo(els, { opacity: 0, y }, { opacity: 1, y: 0, duration: 0.42, ease: "power3.out", stagger: { each: stagger, amount: Math.min(0.24, els.length * stagger) }, clearProps: "opacity,transform" });
    },
    leave(el) {
      if (!ok() || !el) return Promise.resolve();
      return new Promise((res) => g.to(el, { opacity: 0, scale: 0.96, duration: 0.2, ease: "power2.in", onComplete: res }));
    },
    pop(el) {
      if (!ok() || !el) return;
      g.fromTo(el, { opacity: 0, y: -6, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.22, ease: "power3.out", clearProps: "opacity,transform" });
    },
    nudge(el) {
      if (!ok() || !el) return;
      g.fromTo(el, { scale: 0.94 }, { scale: 1, duration: 0.3, ease: "expo.out", clearProps: "transform" });
    },
  };
})();

let toastTimer;
function toast(msg, { err = false, action = null, onAction = null } = {}) {
  const t = $("#toast"), b = $("#toast-action");
  $("#toast-text").textContent = msg;
  t.className = "toast" + (err ? " err" : "");
  b.hidden = !action;
  if (action) { b.textContent = action; b.onclick = () => { t.hidden = true; onAction && onAction(); }; }
  const was = t.hidden;
  t.hidden = false;
  if (was && M.ok()) gsap.fromTo(t, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", clearProps: "opacity,transform" });
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), action ? 8000 : err ? 6000 : 3200);
}

/* ============================================================ vocabulary */
const BUCKETS = [
  { id: "broken", label: "Website broken" },
  { id: "social", label: "Social page only" },
  { id: "none", label: "No website" },
  { id: "bad", label: "Weak website" },
  { id: "weak", label: "Could be better" },
  { id: "ok", label: "Good website" },
  { id: "unknown", label: "Couldn't check" },
  { id: "pending", label: "Checking…" },
];
const BLABEL = Object.fromEntries(BUCKETS.map((b) => [b.id, b.label]));
const COUNTRY = { GB: "United Kingdom", NG: "Nigeria", US: "United States" };
const SOURCE = { osm: "OpenStreetMap", tomtom: "TomTom", google: "Google Maps", csv: "Spreadsheet", manual: "Added by hand" };
const STATUS_LABEL = { new: "New", shortlisted: "Shortlisted", contacted: "Contacted", demo_sent: "Demo sent", replied: "Replied", won: "Won", lost: "Lost", not_fit: "Not a fit" };
const PIPE = [["new", "store"], ["shortlisted", "star"], ["contacted", "chat"], ["demo_sent", "ext"], ["replied", "mail"], ["won", "check"]];
const LINEAR = PIPE.map(([k]) => k);
const IN_QUEUE = new Set(["new", "shortlisted"]);

// Strength steps come from the server: quintiles of the leads waiting to be contacted, so the queue always shows real spread.
const level = (opp) => {
  if (opp == null) return 0;
  const [c5, c4, c3, c2] = state.status?.dye_cuts || [70, 60, 48, 35];
  return opp >= c5 ? 5 : opp >= c4 ? 4 : opp >= c3 ? 3 : opp >= c2 ? 2 : 1;
};
const STRENGTH = ["Not rated", "Weak", "Fair", "Good", "Strong", "Very strong"];
const strength = (L, { word = true } = {}) => { const n = level(L.opportunity); return `<span class="str s${n}${word ? "" : " bars"}" role="img" aria-label="Lead strength: ${STRENGTH[n].toLowerCase()}" title="Lead strength: ${STRENGTH[n].toLowerCase()}"><i></i><i></i><i></i><i></i><i></i>${word ? `<b>${STRENGTH[n]}</b>` : ""}</span>`; };
// OpenStreetMap, TomTom and spreadsheets often leave the website out; only their Google profile settles "no website".
const unverified = (L) => L.bucket === "none" && L.source !== "google" && L.google_check !== "no_site";
const LISTED_ON = { osm: "OpenStreetMap", tomtom: "TomTom" };
function noSiteNote(L) {
  const where = LISTED_ON[L.source] || "their listing";
  if (L.google_check === "no_site") return "Their Google profile has no website either.";
  if (L.google_check === "not_listed") return `No website on ${where}, none found under their name, and LeadFinder couldn't find them on Google Maps. Check their Google profile before saying they have none.`;
  if (L.guessed_at) return `No website on ${where}, and none found under their name. They may still have one: check their Google profile before saying they have none.`;
  return `No website on ${where}. LeadFinder is looking for one under their name now.`;
}
const siteFound = (L) => L.site_via === "google" ? "Found on their Google profile" : L.site_via === "guess" ? "Found by LeadFinder under their name" : L.site_via === "manual" ? "Added by you" : "";

/* The specific finding in a few words, so ten cards give ten different reasons to call. */
const REASONS = [
  [/domain doesn't work/i, "Domain expired"], [/doesn't respond|connection drops|won't load/i, "Doesn't load"],
  [/refuses connections/i, "Server down"], [/secure connection fails/i, "Security error"], [/page not found/i, "Page not found"],
  [/server error/i, "Server error"], [/parked|for sale/i, "Domain parked"], [/suspended|expired/i, "Hosting expired"],
  [/default page/i, "Blank server page"], [/coming soon|under construction/i, "Coming-soon page"], [/old free google/i, "Dead Google site"],
];
function reason(L) {
  const h = L.headline || "";
  if (L.bucket === "broken") return (REASONS.find(([rx]) => rx.test(h)) || [, "Website broken"])[1];
  if (L.bucket === "social") {
    const m = h.match(/(?:only has an? |forwards to an? )(.+)$/i);
    if (!m) return "Social page only";
    const what = m[1].replace(/ (page|listing|profile|channel|link page)$/i, "").replace(/^X\/Twitter/, "X");
    return /forwards/i.test(h) ? `Forwards to ${what}` : `${what} only`;
  }
  if (L.bucket === "none") return unverified(L) ? (L.guessed_at ? "No website found" : "No website listed") : "No website";
  if (L.bucket === "bad" || L.bucket === "weak") { const m = h.match(/^\d+ problems?: ([^,]+)/); return m ? m[1] : BLABEL[L.bucket]; }
  return BLABEL[L.bucket] || L.bucket;
}
function pill(L, label) {
  label = label || reason(L);
  return `<span class="pill p-${esc(L.bucket)}${unverified(L) ? " unv" : ""}" title="${L.bucket === "none" ? esc(noSiteNote(L)) : esc(BLABEL[L.bucket] || "")}"><span>${esc(label)}</span></span>`;
}
const hostOf = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u || ""; } };
const fmtDay = (t) => new Date(t * 1000).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
function dueLabel(t) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const d = new Date(t * 1000); d.setHours(0, 0, 0, 0);
  const days = Math.round((d - today) / 86400000);
  if (days < 0) return { text: days === -1 ? "1 day overdue" : `${-days} days overdue`, late: true };
  if (days === 0) return { text: "Due today", late: true };
  if (days === 1) return { text: "Due tomorrow", late: false };
  return { text: `Due ${fmtDay(t)}`, late: false };
}

/* Where to see the business: its Google Business Profile first, then wherever LeadFinder found it. */
function placeQuery(L) { return [L.name, L.address || L.city, L.address ? "" : COUNTRY[L.country]].filter(Boolean).join(", "); }
function googleProfile(L) {
  const u = L.gmaps_url || "";
  const exact = !!u && !/\/maps\/search\//.test(u) && (L.source === "google" || L.source === "csv" || /[?&]cid=|place_id/.test(u));
  return exact
    ? { href: u, exact: true }
    : { href: "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(placeQuery(L)), exact: false };
}
function listings(L, site) {
  const out = [];
  const gp = googleProfile(L);
  out.push({ href: gp.href, ic: "store", gmb: true, title: gp.exact ? "Google Business Profile" : "Find their Google Business Profile",
    sub: gp.exact ? "Their listing on Google Maps, with photos and reviews" : "Searches Google Maps for this name and address. Pick the matching listing." });
  const pin = L.lat != null && L.lon != null ? `https://www.openstreetmap.org/?mlat=${L.lat}&mlon=${L.lon}#map=19/${L.lat}/${L.lon}` : "";
  if (L.source === "osm" && L.osm_url) out.push({ href: L.osm_url, ic: "map", title: "OpenStreetMap listing", sub: "Where LeadFinder found them, with any details mappers added" });
  if (L.source === "tomtom") out.push(pin
    ? { href: pin, ic: "map", title: "Found on TomTom", sub: "TomTom has no public business page, so this opens the map pin it gave" }
    : { ic: "map", title: "Found on TomTom", sub: "TomTom has no public business page" });
  if (L.source === "csv") out.push({ ic: "upload", title: "Imported from a spreadsheet", sub: (L.searches || []).map((s) => s.location).join(", ") || "CSV import" });
  if (L.source === "manual") out.push({ ic: "edit", title: "Added by hand", sub: "From Import & check" });
  if (L.website) out.push({ href: L.website, ic: "globe", title: "Their website", sub: hostOf(site.final_url || L.website) + (siteFound(L) ? ` · ${siteFound(L)}` : "") });
  for (const [k, v] of Object.entries(L.socials || {})) out.push({ href: v, ic: "chat", title: k[0].toUpperCase() + k.slice(1), sub: v.replace(/^https?:\/\/(www\.)?/, "") });
  out.push({ href: "https://www.google.com/search?q=" + encodeURIComponent([L.name, L.city].filter(Boolean).join(" ")), ic: "search", title: "Search Google", sub: "Find other listings, social pages or a website" });
  return out;
}

/* ============================================================ state & routing */
const FILTER_DEFAULTS = { bucket: [], q: "", area: "", country: "", category: "", status: "", source: "", search: "", min_reviews: "", has_phone: false, has_email: false, show_closed: false, hide_worked: false, hide_bucket: [] };
const state = {
  view: "next", area: store.get("area", ""), next: null, shownReady: null,
  density: store.get("density", "cards"),
  leads: { filters: Object.assign({}, FILTER_DEFAULTS, store.get("filters", {})), sort: store.get("sort", "opportunity"), rows: [], total: 0, sig: "", fx: null },
  follow: [], selected: { next: null, leads: null, followups: null }, open: { next: false, leads: false, followups: false }, lead: null,
  cats: [], groups: [], settings: {}, searches: [], status: null,
};
const VIEWS = ["next", "leads", "followups", "searches", "import", "settings"];

function show(view, { push = true } = {}) {
  if (!VIEWS.includes(view)) view = "next";
  const changed = state.view !== view;
  state.view = view;
  $$(".navlinks a").forEach((a) => { if (a.dataset.view === view) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  $$(".view").forEach((v) => (v.hidden = v.id !== "view-" + view));
  $("#nav").classList.remove("open");
  $("#menu-btn").setAttribute("aria-expanded", "false");
  if (push && location.hash !== "#" + view) history.replaceState(null, "", "#" + view);
  if (changed) M.enter([$(`#view-${view} .pagehead`)], { y: 6 });
  if (view === "next") loadNext();
  if (view === "leads") loadLeads(true);
  if (view === "followups") loadFollowups();
  if (view === "searches") loadSearches();
  if (view === "settings") fillSettings();
}
window.addEventListener("hashchange", () => show(location.hash.slice(1), { push: false }));
$$("[data-view]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); show(a.dataset.view); }));
$("#menu-btn").addEventListener("click", () => {
  const open = $("#nav").classList.toggle("open");
  $("#menu-btn").setAttribute("aria-expanded", String(open));
  if (open) M.pop($("#navlinks"));
});

/* theme: light / dark / follow the computer; the toggle sweeps the new theme in from the button */
const isDark = () => document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
function applyTheme(t) {
  if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  else document.documentElement.removeAttribute("data-theme");
  const d = isDark();
  $("#theme-toggle use").setAttribute("href", d ? "#i-sun" : "#i-moon");
  $("#theme-toggle").setAttribute("aria-label", d ? "Switch to light mode" : "Switch to dark mode");
  if ($("#theme-select")) $("#theme-select").value = store.get("theme", "system");
}
function setTheme(t, from) {
  store.set("theme", t);
  if (!document.startViewTransition || !M.ok() || !from) return applyTheme(t);
  const r = from.getBoundingClientRect();
  document.documentElement.style.setProperty("--vx", r.left + r.width / 2 + "px");
  document.documentElement.style.setProperty("--vy", r.top + r.height / 2 + "px");
  document.documentElement.classList.add("theme-sweep");
  document.startViewTransition(() => applyTheme(t)).finished.finally(() => document.documentElement.classList.remove("theme-sweep"));
}
$("#theme-toggle").addEventListener("click", (e) => setTheme(isDark() ? "light" : "dark", e.currentTarget));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyTheme(store.get("theme", "system")));

/* layout: navigation down the side or across the top; the page glides into its new frame */
function applyLayout(l) {
  l = l === "top" ? "top" : "side";
  document.documentElement.setAttribute("data-layout", l);
  $("#layout-toggle use").setAttribute("href", l === "top" ? "#i-layout-side" : "#i-layout-top");
  $("#layout-toggle").setAttribute("aria-label", l === "top" ? "Move navigation to the side" : "Move navigation to the top");
  if ($("#layout-select")) $("#layout-select").value = l;
}
function setLayout(l) {
  store.set("layout", l);
  const v = $(`#view-${state.view}`);
  const parts = [$("#nav"), ...$$(":scope > *", v), ...$$(".card", v).slice(0, 24)];
  M.flip(parts, () => applyLayout(l), { duration: 0.55, absolute: false });
}
$("#layout-toggle").addEventListener("click", () => setLayout(document.documentElement.dataset.layout === "top" ? "side" : "top"));

/* density: roomy cards or a compact list */
function applyDensity() {
  $$(".cards").forEach((c) => c.classList.toggle("compact", state.density === "compact"));
  $$(".density button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.d === state.density)));
}

/* ============================================================ cards */
function cardHTML(L, { due = false } = {}) {
  const meta = [L.category, L.city, SOURCE[L.source] ? `via ${SOURCE[L.source]}` : ""].filter(Boolean).join(" · ");
  const pills = [pill(L)];
  if (due && L.follow_up_at) {
    const d = dueLabel(L.follow_up_at);
    pills.push(`<span class="tag ${d.late ? "late" : ""}">${icon("clock")}${esc(d.text)}</span>`);
  } else if (L.status !== "new") pills.push(`<span class="tag">${esc(STATUS_LABEL[L.status])}</span>`);
  if (L.closed) pills.push(`<span class="tag">Closed</span>`);
  const gp = googleProfile(L);
  return `<li class="card" data-id="${L.id}" data-flip-id="c${L.id}" aria-current="false">
    <button class="card-open" type="button" data-id="${L.id}" aria-label="Open ${esc(L.name)}"></button>
    <div class="c-top"><h3 class="c-name">${esc(L.name)}</h3>${strength(L, { word: false })}</div>
    <p class="c-meta">${esc(meta)}</p>
    <div class="c-pills">${pills.join("")}</div>
    <div class="c-foot">
      <span class="c-contact"><span class="${L.phone ? "" : "off"}" title="${L.phone ? "Has a phone number" : "No phone number"}">${icon("phone")}</span><span class="${L.email ? "" : "off"}" title="${L.email ? "Has an email" : "No email"}">${icon("mail")}</span></span>
      <a class="gpill" href="${esc(gp.href)}" target="_blank" rel="noopener" title="${gp.exact ? "Open their Google Business Profile" : "Find their Google Business Profile on Google Maps"}" aria-label="Open Google profile for ${esc(L.name)}">${icon("store")}Google</a>
    </div></li>`;
}
function markSelected(container, id) {
  $$(".card", container).forEach((r) => r.setAttribute("aria-current", String(+r.dataset.id === id)));
}
function bindCards(container, view) {
  container.addEventListener("click", (e) => {
    const b = e.target.closest(".card-open");
    if (b) select(view, +b.dataset.id);
  });
  container.addEventListener("keydown", (e) => {
    if (!["ArrowDown", "ArrowUp"].includes(e.key) || !e.target.closest(".card-open")) return;
    const btns = $$(".card-open", container);
    const n = btns[btns.indexOf(document.activeElement) + (e.key === "ArrowDown" ? 1 : -1)];
    if (n) { e.preventDefault(); n.focus(); select(view, +n.dataset.id); }
  });
}
const pane = (view) => $(`#view-${view} [data-detail]`);
const board = (view) => $(`#view-${view} [data-board]`);

/* Open or close the lead panel beside the list. This is the board's one big move. */
function setOpen(view, open) {
  if (state.open[view] === open) return;
  state.open[view] = open;
  const b = board(view), v = $(`#view-${view}`);
  const targets = [...$$(".card", b), ...$$(".stats, .tabs, .toolbar, .activechips", v)];
  M.flip(targets, () => {
    b.classList.toggle("open", open);
    v.classList.toggle("has-open", open);
    pane(view).hidden = !open;
  });
  if (!open) { state.selected[view] = null; markSelected(b, -1); }
}

async function select(view, id) {
  state.selected[view] = id;
  markSelected(board(view), id);
  try {
    const L = await api("/api/lead?id=" + id);
    if (state.selected[view] !== id) return;
    state.lead = L;
    const opening = !state.open[view];
    renderDetail(view, L);
    setOpen(view, true);
    pane(view).scrollTop = 0;
    const say = $("#say-text", pane(view)); // size the draft now that the panel is visible
    if (say) { say.style.height = "auto"; say.style.height = Math.max(120, say.scrollHeight + 2) + "px"; }
    M.enter($$(".d-wrap > *, .d-col > *", pane(view)), { y: opening ? 18 : 10, stagger: 0.05 });
    if (opening) $(`.card[data-id="${id}"]`, board(view))?.scrollIntoView({ block: "nearest" });
  } catch (e) { toast(e.message, { err: true }); }
}
function closeDetail(view) {
  const id = state.selected[view];
  setOpen(view, false);
  $(`.card[data-id="${id}"] .card-open`, board(view))?.focus({ preventScroll: true });
}

/* ============================================================ next up */
async function loadNext({ animate = false } = {}) {
  let data, areas;
  try { [data, areas] = await Promise.all([api("/api/next?" + new URLSearchParams({ area: state.area })), api("/api/areas")]); }
  catch (e) { return toast(e.message, { err: true }); }
  state.next = data;
  state.shownReady = null; // the next status poll sets the baseline
  $("#next-notice").hidden = true;
  const chips = [`<button class="chip" type="button" data-area="" aria-pressed="${!state.area}">All areas</button>`]
    .concat(areas.slice(0, 8).map((a) => `<button class="chip" type="button" data-area="${esc(a.v)}" aria-pressed="${state.area === a.v}">${esc(a.v)}</button>`));
  $("#area-chips").innerHTML = chips.join("");
  $("#area-chips").hidden = areas.length < 2;
  $("#next-guide").textContent = data.queue.length
    ? `${data.queue.length} of ${data.ready.toLocaleString()} ready to contact${state.area ? " in " + state.area : ""}, strongest first.`
    : "";
  const render = () => {
    $("#next-follow").innerHTML = data.followups.length
      ? `<div class="follow-block"><p class="section-label">${icon("bell")}Follow-ups due <span class="muted">${data.followups.length}</span></p><ol class="cards">${data.followups.map((L) => cardHTML(L, { due: true })).join("")}</ol></div><p class="section-label">${icon("arrow")}New leads</p>` : "";
    $("#next-list").innerHTML = data.queue.map((L) => cardHTML(L)).join("");
    applyDensity();
  };
  if (animate) M.reflow($("#next-scroll"), render); else render();
  $("#next-end").textContent = data.queue.length ? (data.ready > data.queue.length
    ? "That's today's ten. Log or skip them and the next ones move up."
    : "That's everyone ready to contact here. Find leads in another area for more.") : "";
  const empty = !data.queue.length && !data.followups.length;
  $("#next-empty").hidden = !empty;
  if (empty) {
    $("#next-empty").innerHTML = `<h2>No one to contact ${state.area ? "in " + esc(state.area) + " " : ""}right now</h2>
      <p>Every lead here has been contacted, skipped for today, or is still being checked. Find businesses in a new area to fill the queue.</p>
      <button class="btn btn-lemon" type="button" data-open-find>${icon("search")}Find leads</button>`;
    $("[data-open-find]", $("#next-empty")).addEventListener("click", () => openFind());
    setOpen("next", false);
    return;
  }
  if (!animate) M.enter($$("#view-next .card").slice(0, 14), { y: 12, stagger: 0.03 });
  const cur = state.selected.next;
  if (cur != null) markSelected(board("next"), cur);
}
$("#area-chips").addEventListener("click", (e) => {
  const c = e.target.closest("[data-area]");
  if (!c) return;
  state.area = c.dataset.area; store.set("area", state.area);
  setOpen("next", false);
  loadNext({ animate: true });
});
$("#next-refresh").addEventListener("click", () => loadNext({ animate: true }));
bindCards($("#next-scroll"), "next");

/* A lead left the queue (logged or skipped): fold it away, let the rest close up, open the next one. */
async function leaveQueue(id) {
  const card = $(`#view-next .card[data-id="${id}"]`);
  const all = [...(state.next?.followups || []), ...(state.next?.queue || [])];
  const i = all.findIndex((l) => l.id === id);
  const after = all[i + 1] || all[i - 1];
  await M.leave(card);
  state.selected.next = after ? after.id : null;
  await loadNext({ animate: true });
  if (state.selected.next && $(`#view-next .card[data-id="${state.selected.next}"]`)) select("next", state.selected.next);
  else setOpen("next", false);
}

/* ============================================================ all leads */
function leadParams(extra = {}) {
  const f = state.leads.filters, p = new URLSearchParams();
  if (f.bucket.length) p.set("bucket", f.bucket.join(","));
  if (f.hide_bucket.length) p.set("hide_bucket", f.hide_bucket.join(","));
  for (const k of ["q", "area", "country", "category", "status", "source", "search", "min_reviews"]) if (f[k]) p.set(k, f[k]);
  for (const k of ["has_phone", "has_email", "show_closed", "hide_worked"]) if (f[k]) p.set(k, "1");
  p.set("sort", state.leads.sort);
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p;
}
const saveFilters = () => { store.set("filters", state.leads.filters); store.set("sort", state.leads.sort); };
function fillSelect(sel, items, current, allLabel, fmt = (v) => v) {
  let found = !current;
  const opts = [`<option value="">${esc(allLabel)}</option>`].concat(items.map((it) => {
    if (it.v === current) found = true;
    return `<option value="${esc(it.v)}"${it.v === current ? " selected" : ""}>${esc(fmt(it.v))} (${it.n})</option>`;
  }));
  if (!found) opts.push(`<option value="${esc(current)}" selected>${esc(fmt(current))}</option>`);
  sel.innerHTML = opts.join("");
}
async function loadLeads(reset, { keep = false, animate = false } = {}) {
  const L = state.leads;
  const limit = keep ? Math.max(100, L.rows.length) : 100;
  const offset = reset || keep ? 0 : L.rows.length;
  let res, fx, areas;
  try { [res, fx, areas] = await Promise.all([api("/api/leads?" + leadParams({ limit, offset })), api("/api/facets?" + leadParams()), api("/api/areas")]); }
  catch (e) { return toast(e.message, { err: true }); }
  const appended = !(reset || keep);
  L.rows = appended ? L.rows.concat(res.leads) : res.leads;
  L.total = res.total; L.fx = fx;
  L.sig = statusSig();
  $("#leads-notice").hidden = true;
  const f = L.filters;
  fillSelect($("#f-area"), areas, f.area, "All areas");
  fillSelect($("#f-country"), fx.country, f.country, "All countries", (v) => COUNTRY[v] || v);
  fillSelect($("#f-category"), fx.category, f.category, "All types");
  fillSelect($("#f-source"), fx.source || [], f.source, "Anywhere", (v) => SOURCE[v] || v);
  const cur = f.search;
  $("#f-search").innerHTML = `<option value="">Any search</option>` + state.searches.filter((x) => x.status === "done" || String(x.id) === cur)
    .map((x) => `<option value="${x.id}"${String(x.id) === cur ? " selected" : ""}>${esc(x.category_label)}, ${esc(x.location)}</option>`).join("");

  // pipeline tiles: each one is a filter
  const sc = Object.fromEntries((fx.status || []).map((s) => [s.v, s.n]));
  $("#pipeline").innerHTML = PIPE.map(([k, ic]) => `<button class="stat" type="button" data-status="${k}" aria-pressed="${f.status === k}">
    <i class="ico">${icon(ic)}</i><span><small>${esc(STATUS_LABEL[k])}</small><b>${(sc[k] || 0).toLocaleString()}</b></span></button>`).join("");

  // website-status tabs
  const counts = fx.buckets || {};
  const all = Object.entries(counts).filter(([b]) => !f.hide_bucket.includes(b)).reduce((a, [, n]) => a + n, 0);
  const tabs = [`<button class="tab" type="button" data-b="" aria-pressed="${!f.bucket.length}">All <small>${all.toLocaleString()}</small></button>`]
    .concat(BUCKETS.filter((b) => counts[b.id]).map((b) => `<button class="tab${f.hide_bucket.includes(b.id) ? " hidden-status" : ""}" type="button" data-b="${b.id}" aria-pressed="${f.bucket.includes(b.id)}" style="--c: var(--p-${b.id === "pending" ? "unknown" : b.id})"${f.hide_bucket.includes(b.id) ? ' title="Hidden by your clutter filter"' : ""}><i class="pdot"></i>${esc(b.id === "none" ? "No website" : b.label)} <small>${counts[b.id].toLocaleString()}</small></button>`));
  $("#buckets").innerHTML = tabs.join("");

  // clutter switches
  $("#hide-list").innerHTML = BUCKETS.filter((b) => b.id !== "pending").map((b) => `<label><input type="checkbox" data-hide="${b.id}"${f.hide_bucket.includes(b.id) ? " checked" : ""}> ${esc(b.label)}</label>`).join("");
  renderActiveChips();

  const render = () => {
    if (appended) $("#leads-list").insertAdjacentHTML("beforeend", res.leads.map((r) => cardHTML(r)).join(""));
    else $("#leads-list").innerHTML = L.rows.map((r) => cardHTML(r)).join("");
    applyDensity();
  };
  if (animate) M.reflow($("#leads-scroll"), render); else render();
  if (!animate && !appended && reset) M.enter($$("#leads-list .card").slice(0, 15), { y: 12, stagger: 0.025 });
  $("#count").textContent = L.total ? `${L.total.toLocaleString()} lead${L.total === 1 ? "" : "s"}${L.total !== fx.total_all ? ` of ${fx.total_all.toLocaleString()}` : ""}` : "";
  $("#more").hidden = L.rows.length >= L.total;
  $("#export").href = "/api/export.csv?" + leadParams();
  const empty = !L.total;
  $("#leads-empty").hidden = !empty;
  if (empty) $("#leads-empty").innerHTML = fx.total_all
    ? `<h2>No leads match</h2><p>Try fewer filters.</p><button class="btn btn-quiet" type="button" id="empty-clear">Clear filters</button>`
    : `<h2>No leads yet</h2><p>Pick a business type and a place, and LeadFinder pulls every match and checks each website.</p><button class="btn btn-lemon" type="button" id="empty-find">${icon("search")}Find leads</button>`;
  $("#empty-clear")?.addEventListener("click", clearFilters);
  $("#empty-find")?.addEventListener("click", () => openFind());
  if (state.selected.leads) markSelected($("#view-leads"), state.selected.leads);
}
function activeFilters() {
  const f = state.leads.filters, out = [];
  const add = (label, clear) => out.push({ label, clear });
  if (f.q) add(`“${f.q}”`, () => { f.q = ""; $("#f-q").value = ""; });
  if (f.status) add(STATUS_LABEL[f.status], () => (f.status = ""));
  for (const b of f.bucket) add(b === "none" ? "No website" : BLABEL[b], () => (f.bucket = f.bucket.filter((x) => x !== b)));
  if (f.area) add(f.area, () => (f.area = ""));
  if (f.country) add(COUNTRY[f.country] || f.country, () => (f.country = ""));
  if (f.category) add(f.category, () => (f.category = ""));
  if (f.source) add(`Found on ${SOURCE[f.source] || f.source}`, () => (f.source = ""));
  if (f.search) { const s = state.searches.find((x) => String(x.id) === f.search); add(s ? `${s.category_label}, ${s.location}` : "One search", () => (f.search = "")); }
  if (f.min_reviews) add(`${f.min_reviews}+ reviews`, () => { f.min_reviews = ""; $("#f-min_reviews").value = ""; });
  if (f.has_phone) add("Has phone", () => (f.has_phone = false));
  if (f.has_email) add("Has email", () => (f.has_email = false));
  if (f.show_closed) add("Including closed", () => (f.show_closed = false));
  if (f.hide_worked) add("Hiding contacted", () => (f.hide_worked = false));
  for (const b of f.hide_bucket) add(`Hiding ${BLABEL[b].toLowerCase()}`, () => (f.hide_bucket = f.hide_bucket.filter((x) => x !== b)));
  return out;
}
function renderActiveChips() {
  const list = activeFilters();
  $("#active-chips").innerHTML = list.map((x, i) => `<button class="chip" type="button" data-i="${i}" aria-label="Remove filter: ${esc(x.label)}">${esc(x.label)}${icon("x")}</button>`).join("")
    + (list.length > 1 ? `<button class="link" type="button" id="chips-clear" style="font-size:12.5px;margin-left:6px">Clear all</button>` : "");
  const n = list.filter((x) => !/^“/.test(x.label)).length;
  $("#filter-count").hidden = !n; $("#filter-count").textContent = n;
  $("#chips-clear")?.addEventListener("click", clearFilters);
  $$("#active-chips [data-i]").forEach((b) => b.addEventListener("click", () => { list[+b.dataset.i].clear(); refilter(); }));
}
function refilter() { saveFilters(); syncFilterInputs(); loadLeads(true, { animate: true }); }
function syncFilterInputs() {
  const f = state.leads.filters;
  for (const k of ["has_phone", "has_email", "show_closed", "hide_worked"]) $("#f-" + k).checked = !!f[k];
  $("#f-min_reviews").value = f.min_reviews;
}
function clearFilters() {
  Object.assign(state.leads.filters, structuredClone(FILTER_DEFAULTS));
  $("#f-q").value = "";
  refilter();
}
function toggleFilters(open) {
  const box = $("#filters");
  open = open ?? box.hidden;
  box.hidden = !open;
  $("#filters-btn").setAttribute("aria-expanded", String(open));
  if (open) M.pop(box);
}
function bindLeads() {
  const f = state.leads.filters;
  let qt;
  $("#f-q").value = f.q;
  $("#f-q").addEventListener("input", (e) => { clearTimeout(qt); qt = setTimeout(() => { f.q = e.target.value.trim(); saveFilters(); loadLeads(true, { animate: true }); }, 250); });
  for (const k of ["area", "country", "category", "source", "search", "min_reviews"]) $("#f-" + k).addEventListener("change", (e) => { f[k] = e.target.value; refilter(); });
  for (const k of ["has_phone", "has_email", "show_closed", "hide_worked"]) $("#f-" + k).addEventListener("change", (e) => { f[k] = e.target.checked; refilter(); });
  $("#hide-list").addEventListener("change", (e) => {
    const id = e.target.dataset.hide; if (!id) return;
    f.hide_bucket = e.target.checked ? [...new Set([...f.hide_bucket, id])] : f.hide_bucket.filter((x) => x !== id);
    f.bucket = f.bucket.filter((x) => !f.hide_bucket.includes(x));
    refilter();
  });
  syncFilterInputs();
  $("#sort").value = state.leads.sort;
  $("#sort").addEventListener("change", (e) => { state.leads.sort = e.target.value; saveFilters(); loadLeads(true, { animate: true }); });
  $("#clear-filters").addEventListener("click", clearFilters);
  $("#filters-btn").addEventListener("click", () => toggleFilters());
  $("#filters-done").addEventListener("click", () => { toggleFilters(false); $("#filters-btn").focus(); });
  document.addEventListener("click", (e) => { if (!$("#filters").hidden && !e.target.closest(".filterwrap")) toggleFilters(false); });
  $("#pipeline").addEventListener("click", (e) => {
    const t = e.target.closest("[data-status]"); if (!t) return;
    f.status = f.status === t.dataset.status ? "" : t.dataset.status;
    M.nudge(t); refilter();
  });
  $("#buckets").addEventListener("click", (e) => {
    const c = e.target.closest("[data-b]"); if (!c) return;
    const id = c.dataset.b, cur = f.bucket;
    if (!id) f.bucket = [];
    else f.bucket = e.ctrlKey || e.metaKey || e.shiftKey ? (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]) : (cur.length === 1 && cur[0] === id ? [] : [id]);
    if (id) f.hide_bucket = f.hide_bucket.filter((x) => x !== id); // asking to see a status un-hides it
    refilter();
  });
  $$(".density button").forEach((b) => b.addEventListener("click", () => {
    if (state.density === b.dataset.d) return;
    state.density = b.dataset.d; store.set("density", state.density);
    $$(".cards").forEach((c) => M.reflow(c.closest(".listcol") || c, applyDensity));
  }));
  $("#more").addEventListener("click", () => loadLeads(false));
  $("#leads-refresh").addEventListener("click", () => loadLeads(false, { keep: true, animate: true }));
  bindCards($("#leads-scroll"), "leads");
}

/* ============================================================ follow-ups */
async function loadFollowups() {
  let res;
  try { res = await api("/api/leads?" + new URLSearchParams({ followups: "1", sort: "followup", limit: 300 })); }
  catch (e) { return toast(e.message, { err: true }); }
  state.follow = res.leads;
  const groups = { "Overdue": [], "Today": [], "This week": [], "Later": [] };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  for (const L of res.leads) {
    const d = new Date(L.follow_up_at * 1000); d.setHours(0, 0, 0, 0);
    const days = Math.round((d - today) / 86400000);
    groups[days < 0 ? "Overdue" : days === 0 ? "Today" : days <= 7 ? "This week" : "Later"].push(L);
  }
  $("#follow-list").innerHTML = Object.entries(groups).filter(([, v]) => v.length)
    .map(([k, v]) => `<div class="follow-block"><p class="section-label">${esc(k)} <span class="muted">${v.length}</span></p><ol class="cards">${v.map((L) => cardHTML(L, { due: true })).join("")}</ol></div>`).join("");
  applyDensity();
  M.enter($$("#follow-list .card").slice(0, 14), { y: 12, stagger: 0.03 });
  $("#follow-empty").hidden = !!res.leads.length;
  $("#follow-empty").innerHTML = `<h2>Nothing to chase</h2><p>When you mark a lead Contacted or Demo sent, it shows up here 3 days later so it doesn't go cold.</p>`;
  if (!res.leads.length) { setOpen("followups", false); return; }
  const cur = state.selected.followups;
  if (cur != null && !res.leads.some((l) => l.id === cur)) setOpen("followups", false);
  else if (cur != null) markSelected($("#view-followups"), cur);
}
bindCards($("#follow-scroll"), "followups");

/* ============================================================ detail */
function waNumber(phone, country) {
  const raw = (phone || "").trim();
  let d = raw.replace(/\D/g, "");
  if (d.length < 7) return null;
  if (raw.startsWith("+")) return d;
  if (d.startsWith("00")) return d.slice(2);
  const cc = { NG: "234", GB: "44", US: "1" }[country];
  if (!cc) return d.length > 10 ? d : null;
  if (country === "US") return d.length === 10 ? "1" + d : d;
  if (d.startsWith(cc) && d.length > 10) return d;
  if (d.startsWith("0")) d = d.slice(1);
  return cc + d;
}
const gauge = (label, v) => v == null ? "" : `<div class="gauge ${v >= 90 ? "good" : v >= 50 ? "mid" : "poor"}"><b>${v}</b><span>${esc(label)}</span></div>`;

function renderDetail(view, L) {
  const p = pane(view);
  const g = L.grade || {}, site = g.site || {}, psi = L.psi;
  const email = L.email || site.emails?.[0] || "";
  const wa = waNumber(L.phone, L.country);
  const sub = [L.category, L.address || L.city, COUNTRY[L.country]].filter(Boolean).map(esc).join(" · ");
  const issues = (L.issues || []).filter((i) => (i.pts >= 5 || i.pts === 0) && !(i.title === "Very little content" && (site.words ?? 0) < 20));
  const pending = L.bucket === "pending";
  const kind = store.get("sayKind", wa && (L.country === "NG" || !email) ? "whatsapp" : email ? "email" : "whatsapp");
  const gp = googleProfile(L);
  const pinHref = L.lat != null && L.lon != null ? `https://www.openstreetmap.org/?mlat=${L.lat}&mlon=${L.lon}#map=19/${L.lat}/${L.lon}` : "";
  const srcHref = L.source === "osm" ? L.osm_url : L.source === "tomtom" ? pinHref : L.source === "google" ? gp.href : "";
  const facts = [];
  const f = (k, v) => v != null && v !== "" && facts.push(`<dt>${esc(k)}</dt><dd>${v}</dd>`);
  if (L.website) f("Website", `<a href="${esc(L.website)}" target="_blank" rel="noopener">${esc(L.website)}</a>`);
  if (L.website && L.site_via) f("Where the website came from", esc(L.site_via === "guess" ? `Not on their listing. LeadFinder found it under their name (matched by ${L.site_why || "name"})` : siteFound(L)));
  if (site.final_url && site.final_url !== site.input_url) f("Ends up at", esc(site.final_url));
  if (site.ms != null) f("Load time", `${(site.ms / 1000).toFixed(1)} seconds from this computer`);
  f("Built with", esc(site.builder || ""));
  f("Copyright year", site.copyright_year ? esc(site.copyright_year) : "");
  f("Words on homepage", site.words != null ? esc(site.words) : "");
  if (site.error) f("Error", esc(site.error));
  if (L.score != null) f("Website score", `${L.score} out of 100`);
  if (L.opportunity != null) f("Lead strength", `${STRENGTH[level(L.opportunity)]} (${L.opportunity} of 100: weak web presence × how busy they look × whether you can reach them)`);
  if (L.graded_at) f("Checked", new Date(L.graded_at * 1000).toLocaleString());
  if (L.searches?.length) f("Found by", L.searches.map((s) => esc(`${s.category_label}, ${s.location}`)).join("; "));
  const followDate = L.follow_up_at ? new Date(L.follow_up_at * 1000).toISOString().slice(0, 10) : "";
  const headFacts = [
    ["Phone", L.phone ? `<a href="tel:${esc(L.phone.replace(/[^\d+]/g, ""))}">${esc(L.phone)}</a>` : `<span class="muted">Not listed</span>`],
    ["Email", email ? `<a href="mailto:${esc(email)}">${esc(email)}</a>` : `<span class="muted">Not listed</span>`],
    ["Website", L.website ? `<a href="${esc(L.website)}" target="_blank" rel="noopener">${esc(hostOf(L.website))}</a>` : `<span class="muted">None found</span>`],
  ];
  if (L.reviews != null) headFacts.push(["Google reviews", `<span class="stars">${icon("star")}${esc(L.rating ?? "No rating")} from ${L.reviews}</span>`]);
  const li = L.status in STATUS_LABEL ? LINEAR.indexOf(L.status) : -1;
  const listed = listings(L, site);

  p.innerHTML = `<div class="d-wrap" data-flip-id="detail">
    <div class="tile d-head">
      <div class="d-top">
        <button class="iconbtn d-close" type="button" aria-label="Close lead">${icon("x")}</button>
        ${srcHref ? `<a class="src-pill" href="${esc(srcHref)}" target="_blank" rel="noopener" title="Open where LeadFinder found them">${icon(L.source === "google" ? "store" : "map")}Found on ${esc(SOURCE[L.source] || L.source)}<svg class="ic go" aria-hidden="true"><use href="#i-ext"/></svg></a>`
          : `<span class="src-pill">${icon("upload")}${L.source === "manual" ? "Added by hand" : "From a spreadsheet"}</span>`}
        <span class="spacer"></span>${strength(L)}
      </div>
      <div><h2 class="d-name">${esc(L.name)}</h2></div>
      <p class="d-sub">${sub}${L.closed ? " · <b>Permanently closed</b>" : ""}</p>
      <div class="d-pills">${pending ? `<span class="pill p-pending"><span>Checking their website…</span></span>` : pill(L)}${L.status !== "new" ? `<span class="tag">${esc(STATUS_LABEL[L.status])}</span>` : ""}</div>
      <dl class="d-facts">${headFacts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
      <div class="acts">
        ${wa ? `<a class="btn btn-lemon" id="act-wa" target="_blank" rel="noopener">${icon("chat")}WhatsApp</a>` : ""}
        ${L.phone ? `<a class="btn ${wa ? "btn-quiet" : "btn-lemon"}" href="tel:${esc(L.phone.replace(/[^\d+]/g, ""))}">${icon("phone")}Call</a>` : ""}
        ${email ? `<a class="btn ${wa || L.phone ? "btn-quiet" : "btn-lemon"}" id="act-mail">${icon("mail")}Email</a>` : ""}
        <a class="btn btn-quiet" href="${esc(gp.href)}" target="_blank" rel="noopener">${icon("store")}${gp.exact ? "Google profile" : "Find on Google"}</a>
        <span class="spacer"></span>
        ${L.website ? `<a class="iconbtn" href="${esc(L.website)}" target="_blank" rel="noopener" title="Open their website" aria-label="Open their website">${icon("globe")}</a>` : ""}
        ${IN_QUEUE.has(L.status) ? `<button class="iconbtn" type="button" id="act-skip" title="Skip for today" aria-label="Skip for today">${icon("clock")}</button>` : ""}
      </div>
      ${!L.phone && !email ? `<p class="guide">No phone or email on record. Their Google profile or social page usually has one.</p>` : ""}
    </div>
    <div class="d-cols">
      <div class="d-col">
        <section class="tile"><h3>Why them</h3>
          ${pending ? `<p class="guide">Their website is being checked now. This updates by itself.</p>` : issues.length
            ? `<ul class="why">${issues.slice(0, 5).map((i) => `<li class="${esc(i.sev)}"><b>${esc(i.title)}</b><p>${esc(i.pitch)}</p></li>`).join("")}</ul>`
            : `<p class="guide">${L.bucket === "ok" ? "Their website is in good shape. Pitch automations instead: instant replies to missed calls, booking, review requests." : (unverified(L) ? "If they really have no website, people searching for them find competitors first." : "No website, not even on Google. People searching for them find competitors first.")}</p>`}
          ${unverified(L) ? `<p class="caution">${esc(noSiteNote(L))} <button class="linkbtn" type="button" id="act-find">Look again</button></p>` : ""}
        </section>
        <section class="tile"><h3>Where they're listed</h3>
          <div class="listed">${listed.map((x) => x.href
            ? `<a href="${esc(x.href)}" target="_blank" rel="noopener"><i class="lic${x.gmb ? " gmb" : ""}">${icon(x.ic)}</i><span><b>${esc(x.title)}</b><small>${esc(x.sub)}</small></span><svg class="ic go" aria-hidden="true"><use href="#i-ext"/></svg></a>`
            : `<div class="row-static"><i class="lic">${icon(x.ic)}</i><span><b>${esc(x.title)}</b><small>${esc(x.sub)}</small></span></div>`).join("")}</div>
          <div class="mapbox" id="mapbox"><button class="btn btn-quiet btn-sm" type="button" id="map-show">${icon("map")}Show Google map here</button></div>
        </section>
      </div>
      <div class="d-col">
        <section class="tile say"><h3>What to say</h3>
          <div class="seg" role="tablist" aria-label="Message type">
            <button type="button" role="tab" data-k="whatsapp">WhatsApp</button><button type="button" role="tab" data-k="email">Email</button><button type="button" role="tab" data-k="call">Call script</button></div>
          <input type="text" class="say-subject" id="say-subject" aria-label="Email subject">
          <textarea class="say-text" id="say-text" aria-label="Message"></textarea>
          <div class="btnrow"><button class="btn btn-quiet btn-sm" type="button" id="copy-say">${icon("copy")}Copy</button><span class="hint">Edit before sending, and replace [DEMO LINK] with your mock-up.</span></div>
          <p class="rule" id="say-rule" hidden></p>
        </section>
        <section class="tile"><h3>Log it <span class="saved" id="saved" hidden>Saved</span></h3>
          <div class="track" id="statusrow" role="group" aria-label="Pipeline status">${LINEAR.map((k, i) => `<button type="button" data-s="${k}" aria-pressed="${L.status === k}" class="${li > i ? "past" : ""}">${L.status === k ? icon("check") : ""}${esc(STATUS_LABEL[k])}</button>`).join("")}</div>
          <div class="track-alt"><span>Or close it:</span>${["lost", "not_fit"].map((k) => `<button class="chip" type="button" data-s="${k}" aria-pressed="${L.status === k}">${esc(STATUS_LABEL[k])}</button>`).join("")}</div>
          <div class="logrow">
            <label>Follow up on<input type="date" id="follow-date" value="${followDate}"></label>
            <label>Notes<textarea id="notes" placeholder="Who you spoke to, what they said, demo link">${esc(L.notes || "")}</textarea></label>
          </div>
        </section>
      </div>
    </div>
    <details class="tile more-info"><summary>Website details and tools</summary><div class="mi-body">
      <dl class="facts">${facts.join("") || "<dt>Nothing yet</dt><dd>Their website hasn't been checked.</dd>"}</dl>
      ${psi && !psi.error ? `<div class="gauges">${gauge("Speed on phones", psi.performance)}${gauge("Search basics", psi.seo)}${gauge("Accessibility", psi.accessibility)}${gauge("Best practices", psi.best_practices)}</div>` : ""}
      ${psi && psi.error ? `<p class="guide" style="margin-top:12px">${esc(psi.error)}</p>` : ""}
      ${L.shot ? `<a href="/shots/${L.id}.jpg?${L.psi_at || ""}" target="_blank" rel="noopener"><img class="shot" src="/shots/${L.id}.jpg?${L.psi_at || ""}" alt="Their site on a phone"></a>` : ""}
      <div class="btnrow" style="margin-top:16px">
        <button class="btn btn-quiet btn-sm" type="button" id="act-regrade">${icon("refresh")}Check website again</button>
        ${g.kind === "site" ? `<button class="btn btn-quiet btn-sm" type="button" id="act-psi">${icon("gauge")}Run Google speed test</button>` : ""}
        <button class="btn btn-quiet btn-sm" type="button" id="act-site">${icon("edit")}${L.website ? "Change website" : "Add a website"}</button>
        <button class="btn btn-quiet btn-sm" type="button" id="act-delete">${icon("trash")}Delete lead</button>
      </div>
      <div class="inline-edit" id="site-edit" hidden><input type="text" id="site-input" value="${esc(L.website || "")}" placeholder="www.example.com" aria-label="Website address"><button class="btn btn-lemon btn-sm" type="button" id="site-save">Save and check</button></div>
    </div></details>
  </div>`;

  /* wire up */
  $(".d-close", p).addEventListener("click", () => closeDetail(view));
  $("#map-show", p).addEventListener("click", () => {
    const q = encodeURIComponent(placeQuery(L));
    $("#mapbox", p).innerHTML = `<iframe title="Google map of ${esc(L.name)}" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=${q}&z=16&output=embed"></iframe>
      <p class="hint mapnote">Map from Google. Open the profile above for photos, hours and reviews.</p>`;
    M.enter([$("#mapbox iframe", p)], { y: 6 });
  });
  const setKind = (k) => {
    store.set("sayKind", k);
    $$(".say .seg button", p).forEach((b) => b.setAttribute("aria-selected", String(b.dataset.k === k)));
    renderSay(p, L, k, wa, email);
  };
  $$(".say .seg button", p).forEach((b) => b.addEventListener("click", () => setKind(b.dataset.k)));
  setKind(kind);
  $("#act-skip", p)?.addEventListener("click", async () => {
    try { await api("/api/lead/update", { id: L.id, skip: true }); } catch (e) { return toast(e.message, { err: true }); }
    toast(`${L.name} skipped until tomorrow.`, { action: "Undo", onAction: async () => { await api("/api/lead/update", { id: L.id, skip: false }); refreshAll(); } });
    if (view === "next") leaveQueue(L.id); else select(view, L.id);
  });
  $$("[data-s]", p).forEach((b) => b.addEventListener("click", async () => {
    const prev = { status: L.status, follow_up_at: L.follow_up_at };
    const s = b.dataset.s;
    if (s === prev.status) return;
    M.nudge(b);
    let upd;
    try { upd = await api("/api/lead/update", { id: L.id, status: s }); } catch (e) { return toast(e.message, { err: true }); }
    const msg = upd.follow_up_at && !prev.follow_up_at ? `Logged as ${STATUS_LABEL[s].toLowerCase()}. Follow-up set for ${fmtDay(upd.follow_up_at)}.` : `Logged as ${STATUS_LABEL[s].toLowerCase()}.`;
    toast(msg, { action: "Undo", onAction: async () => { await api("/api/lead/update", { id: L.id, status: prev.status, follow_up_at: prev.follow_up_at }); refreshAll(); } });
    refreshCounts();
    if (view === "next" && IN_QUEUE.has(prev.status) !== IN_QUEUE.has(s) || (view === "next" && state.next?.followups.some((x) => x.id === L.id) && !upd.follow_up_at)) leaveQueue(L.id);
    else if (view === "followups" && !upd.follow_up_at) { setOpen("followups", false); loadFollowups(); }
    else { state.lead = upd; patchDetailStatus(p, upd); patchCard(view, upd); }
  }));
  $("#follow-date", p).addEventListener("change", async (e) => {
    const v = e.target.value ? new Date(e.target.value + "T09:00:00").getTime() / 1000 : null;
    try { await api("/api/lead/update", { id: L.id, follow_up_at: v }); flashSaved(p); refreshCounts(); } catch (err) { toast(err.message, { err: true }); }
  });
  let nt;
  $("#notes", p).addEventListener("input", (e) => {
    clearTimeout(nt);
    nt = setTimeout(async () => { try { await api("/api/lead/update", { id: L.id, notes: e.target.value }); flashSaved(p); } catch (err) { toast(err.message, { err: true }); } }, 600);
  });
  $("#act-find", p)?.addEventListener("click", async () => { await api("/api/find-sites", { id: L.id }); toast("Looking for their website…"); poll(true); });
  $("#act-regrade", p).addEventListener("click", async () => { await api("/api/lead/regrade", { id: L.id }); toast("Checking their website again…"); select(view, L.id); });
  $("#act-psi", p)?.addEventListener("click", async () => { await api("/api/lead/psi", { id: L.id }); toast("Google speed test started. It takes up to a minute."); });
  $("#act-site", p).addEventListener("click", () => { $("#site-edit", p).hidden = false; $("#site-input", p).focus(); });
  $("#site-save", p).addEventListener("click", async () => {
    try { await api("/api/lead/update", { id: L.id, website: $("#site-input", p).value }); toast("Saved. Checking the website…"); select(view, L.id); }
    catch (e) { toast(e.message, { err: true }); }
  });
  $("#act-delete", p).addEventListener("click", async () => {
    try { await api("/api/lead/delete", { id: L.id }); } catch (e) { return toast(e.message, { err: true }); }
    toast(`${L.name} deleted.`, { action: "Undo", onAction: async () => { await api("/api/lead/restore", { id: L.id }); refreshAll(); } });
    setOpen(view, false);
    refreshAll();
  });
}
/* Status changed but the lead stays here: update the track and pills in place, keeping notes and the draft as typed. */
function patchDetailStatus(p, L) {
  const li = LINEAR.indexOf(L.status);
  $$("#statusrow button", p).forEach((b, i) => {
    const on = b.dataset.s === L.status;
    b.setAttribute("aria-pressed", String(on));
    b.className = li > i ? "past" : "";
    b.innerHTML = (on ? icon("check") : "") + esc(STATUS_LABEL[b.dataset.s]);
  });
  $$(".track-alt [data-s]", p).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.s === L.status)));
  const pills = $(".d-pills", p);
  if (pills) pills.innerHTML = (L.bucket === "pending" ? `<span class="pill p-pending"><span>Checking their website…</span></span>` : pill(L)) + (L.status !== "new" ? `<span class="tag">${esc(STATUS_LABEL[L.status])}</span>` : "");
  if (L.follow_up_at) $("#follow-date", p).value = new Date(L.follow_up_at * 1000).toISOString().slice(0, 10);
}
function flashSaved(p) { const s = $("#saved", p); if (s) { s.hidden = false; setTimeout(() => (s.hidden = true), 1400); } }
function patchCard(view, L) {
  const old = $(`#view-${view} .card[data-id="${L.id}"]`);
  if (!old) return;
  const tmp = document.createElement("div");
  tmp.innerHTML = cardHTML(L, { due: view === "followups" });
  old.replaceWith(tmp.firstElementChild);
  markSelected($(`#view-${view}`), L.id);
}
function refreshAll() {
  refreshCounts();
  if (state.view === "next") loadNext({ animate: true });
  if (state.view === "leads") loadLeads(false, { keep: true, animate: true });
  if (state.view === "followups") loadFollowups();
}

/* ============================================================ outreach copy */
function pitchParts(L) {
  const s = state.settings;
  const me = s.my_name || "[your name]";
  const sign = [s.my_name || "[Your name]", s.agency, s.my_site, s.my_phone].filter(Boolean).join("\n");
  const place = L.city || "your area";
  const cat = (L.category || "businesses").toLowerCase();
  const domain = hostOf(L.website);
  const an = (w) => (/^[aeiou]/i.test(w) ? "an " : "a ") + w;
  const linkLabel = L.grade?.site?.link_page || "social media page";
  const praise = L.reviews >= 10 && L.rating
    ? `I came across ${L.name} on Google. ${L.rating} stars from ${L.reviews} reviews is impressive; your customers clearly rate you.`
    : `I came across ${L.name} while looking at ${cat} in ${place}.`;
  const real = (L.issues || []).filter((i) => !(i.title === "Very little content" && (L.grade?.site?.words ?? 0) < 20));
  const top = real.filter((i) => i.pts >= 5).slice(0, 3);
  let problem, subject, short;
  switch (L.bucket) {
    case "none":
      subject = `Website for ${L.name}?`;
      problem = `I noticed you don't have a website yet. That means when people search Google for ${cat} in ${place}, they find your competitors first, and some never see you.`;
      short = `I noticed you don't have a website yet, so people searching for ${cat} in ${place} find your competitors first.`;
      break;
    case "social":
      subject = `Quick idea for ${L.name}`;
      problem = `I noticed your website link goes to ${an(linkLabel)}. That works, but a proper website shows up on Google, looks more established, and lets customers enquire or book any time, even when you're busy.`;
      short = `I noticed your website link goes to ${an(linkLabel)}. A proper site would bring you more customers from Google.`;
      break;
    case "broken":
      subject = "Your website isn't working";
      problem = `Quick heads-up: your website${domain ? ` (${domain})` : ""} isn't working right now. ${L.headline ? L.headline + "." : ""} Anyone who clicks through from Google or your listing hits a dead end, and those are customers who were ready to contact you.`;
      short = `Quick heads-up: your website${domain ? ` (${domain})` : ""} isn't loading right now, so customers clicking through from Google hit a dead end.`;
      break;
    case "bad": case "weak":
      subject = `A few things on ${domain || "your website"}`;
      problem = `I had a look at ${domain || "your website"} and spotted a few things that are probably costing you enquiries:\n\n` + (top.length ? top : real.slice(0, 3)).map((i) => `• ${i.pitch}`).join("\n");
      short = `I had a look at ${domain || "your website"} and noticed: ${(top[0]?.pitch || "a few things that could bring you more enquiries.").replace(/^Your /, "your ")}`;
      break;
    case "ok":
      subject = `Idea to win more customers for ${L.name}`;
      problem = "Your website looks solid. One idea: a couple of simple automations, like an instant text back when you miss a call and automatic Google review requests, usually bring in extra work every month with no extra effort from you.";
      short = "Your website looks good. I set up simple automations (instant replies to missed calls, automatic review requests) that bring local businesses extra customers.";
      break;
    default:
      subject = `Quick idea for ${L.name}`;
      problem = `I had a look at how ${L.name} shows up online and have a couple of ideas that could bring in more enquiries.`;
      short = problem;
  }
  const offer = L.bucket === "ok"
    ? "Would a 10-minute call this week be useful? I can show you exactly how it would work for you."
    : "I've put together a quick mock-up of what a new site could look like for you: [DEMO LINK]\n\nIf you like it, I can have it live within a week. No obligation either way.";
  return { me, sign, praise, problem, subject, short, offer, top, real, place, cat };
}
function renderSay(p, L, kind, wa, email) {
  const x = pitchParts(L), subj = $("#say-subject", p), text = $("#say-text", p), rule = $("#say-rule", p);
  subj.hidden = kind !== "email";
  if (kind === "email") {
    subj.value = x.subject;
    text.value = `Hi there,\n\n${x.praise}\n\n${x.problem}\n\n${x.offer}\n\nBest,\n${x.sign}\n\nP.S. If this isn't useful, just reply "no thanks" and I won't contact you again.`;
  } else if (kind === "whatsapp") {
    text.value = pitchWhatsApp(L);
  } else {
    const points = (x.top.length ? x.top : x.real.slice(0, 3)).map((i) => `   • ${i.pitch}`).join("\n");
    text.value = `OPENER\n"Hi, is that the owner? My name's ${x.me}${state.settings.agency ? `, I run ${state.settings.agency}` : ""}. I help ${x.cat} in ${x.place} get more customers online. Have you got two minutes?"\n\n` +
      `WHY YOU'RE CALLING\n"${x.problem.split("\n")[0]}"\n` + (points ? `\nPOINTS TO MENTION\n${points}\n` : "") +
      `\nTHE ASK\n"I've already mocked up what a new site could look like for you. Can I send it on WhatsApp or email? It's free to look at."\n\n` +
      `IF THEY SAY…\n• "We get enough work from word of mouth" → "That's great. Most new customers still check you on Google before they call, so this makes sure they pick you."\n` +
      `• "How much?" → "It depends on what you need. Let me send the mock-up first, and if you like it I'll give you a fixed price."\n• "Send me an email" → confirm the address, send it within the hour, and follow up in 2 days.`;
  }
  const links = () => {
    const a = $("#act-wa", p); if (a && wa) a.href = `https://wa.me/${wa}?text=${encodeURIComponent(kind === "whatsapp" ? text.value : pitchWhatsApp(L))}`;
    const m = $("#act-mail", p); if (m && email) m.href = `mailto:${email}?subject=${encodeURIComponent(kind === "email" ? subj.value : x.subject)}&body=${encodeURIComponent(kind === "email" ? text.value : `Hi there,\n\n${x.praise}\n\n${x.problem}\n\n${x.offer}\n\nBest,\n${x.sign}`)}`;
  };
  const fit = () => { text.style.height = "auto"; text.style.height = Math.max(120, text.scrollHeight + 2) + "px"; };
  fit();
  links(); text.oninput = () => { links(); fit(); }; subj.oninput = links;
  $("#copy-say", p).onclick = async () => {
    const all = kind === "email" ? `Subject: ${subj.value}\n\n${text.value}` : text.value;
    try { await navigator.clipboard.writeText(all); toast("Copied"); } catch { text.select(); document.execCommand("copy"); toast("Copied"); }
  };
  rule.hidden = !(kind === "email" && (L.country === "GB" || L.country === "US"));
  if (L.country === "GB") rule.textContent = "UK rule: you can cold-email limited companies if you include an opt-out, as above. Sole traders and partnerships need consent first, so call them or visit instead.";
  if (L.country === "US") rule.textContent = "US rule: cold email to businesses is allowed if you say who you are, include your postal address, and honour opt-outs. Don't cold-text US mobile numbers.";
}
function pitchWhatsApp(L) {
  const x = pitchParts(L);
  return `Hi! I'm ${x.me}${state.settings.agency ? ` from ${state.settings.agency}` : ""}. ${x.short} ${L.bucket === "ok" ? "Can I send you a quick example?" : "I made a quick mock-up of a new site for you. Can I send it over?"}`;
}

/* ============================================================ find dialog */
const find = { market: "", picked: new Set(store.get("pickedCats", [])) };
function renderCatList() {
  const q = $("#cat-filter").value.trim().toLowerCase();
  $("#catlist").innerHTML = state.groups.map((g) => {
    const items = state.cats.filter((c) => c.group === g && (!find.market || c.markets.includes(find.market)) && (!q || c.label.toLowerCase().includes(q)));
    if (!items.length) return "";
    return `<div class="catgroup"><h4>${esc(g)}</h4><div class="items">${items.map((c) =>
      `<label><input type="checkbox" value="${c.id}"${find.picked.has(c.id) ? " checked" : ""}> ${esc(c.label)}<span class="mkts">${c.markets.join(" ")}</span></label>`).join("")}</div></div>`;
  }).join("") || `<p class="guide">No types match. Type your own below.</p>`;
}
function updateFindSummary() {
  const locs = $("#locations").value.split(/\n|;/).map((x) => x.trim()).filter(Boolean);
  const types = find.picked.size + ($("#keyword").value.trim() ? 1 : 0);
  const src = $('input[name="source"]:checked').value;
  $("#depth-field").hidden = src !== "google";
  let msg;
  const n = types * locs.length;
  if (!types) msg = "Pick at least one business type.";
  else if (!locs.length) msg = "Add at least one place.";
  else {
    msg = `${types} type${types > 1 ? "s" : ""} × ${locs.length} place${locs.length > 1 ? "s" : ""} = <b>${n} search${n > 1 ? "es" : ""}</b>`;
    if (src === "google") { const d = +$("#depth").value, g = state.status?.google || { used: 0, free: 1000 }; msg += `, up to ${n * d * d * 3} Google requests (${Math.max(0, g.free - g.used)} free left this month)`; }
    else if (src === "tomtom") msg += `, about ${n * 2} to ${n * 6} TomTom requests (free)`;
    else msg += `, about ${Math.max(1, Math.round(n * 0.75))} min on OpenStreetMap`;
  }
  $("#find-summary").innerHTML = msg;
  $("#find-go").disabled = !(types && locs.length) || n > 60;
}
function openFind(preset) {
  const d = $("#find"), s = state.settings;
  const tt = !!s.tomtom_key_set, gk = !!s.google_key_set, tu = state.status?.tomtom || { used: 0, free: 2500 };
  $("#src-tomtom input").disabled = !tt;
  $("#tomtom-note").innerHTML = tt ? `Free. Many more businesses than OpenStreetMap. ${Math.max(0, tu.free - tu.used).toLocaleString()} free searches left this month.` : `Free key, no card. <a href="#settings" data-go-settings>Add your key in Settings</a>.`;
  $("#src-google input").disabled = !gk;
  $("#google-note").innerHTML = gk ? "Most complete, with ratings and reviews. Paid past Google's free amount." : `Needs a paid Google key. <a href="#settings" data-go-settings>Settings</a>`;
  $$("[data-go-settings]", d).forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); d.close(); show("settings"); }));
  const ok = { osm: true, tomtom: tt, google: gk };
  const pref = store.get("source", tt ? "tomtom" : "osm");
  $(`input[name="source"][value="${ok[pref] ? pref : tt ? "tomtom" : "osm"}"]`).checked = true;
  $("#locations").value = preset?.loc ?? store.get("locations", "");
  if (preset?.cat) find.picked = new Set([preset.cat]);
  renderCatList(); updateFindSummary();
  d.showModal();
  if (M.ok()) gsap.fromTo($(".dialog-inner", d), { opacity: 0, y: 14, scale: 0.98 }, { opacity: 1, y: 0, scale: 1, duration: 0.32, ease: "power3.out", clearProps: "opacity,transform" });
}
function bindFind() {
  $$("[data-open-find]").forEach((b) => b.addEventListener("click", () => openFind()));
  $$("#market button").forEach((b) => b.addEventListener("click", () => {
    find.market = b.dataset.v;
    $$("#market button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
    renderCatList();
  }));
  $("#cat-filter").addEventListener("input", renderCatList);
  $("#catlist").addEventListener("change", (e) => {
    if (e.target.type !== "checkbox") return;
    if (e.target.checked) find.picked.add(e.target.value); else find.picked.delete(e.target.value);
    store.set("pickedCats", [...find.picked]); updateFindSummary();
  });
  for (const el of ["#locations", "#keyword", "#depth"]) $(el).addEventListener("input", updateFindSummary);
  $$('input[name="source"]').forEach((r) => r.addEventListener("change", updateFindSummary));
  $("#find-go").addEventListener("click", async () => {
    const src = $('input[name="source"]:checked').value;
    const body = { categories: [...find.picked], keyword: $("#keyword").value.trim(), locations: $("#locations").value, source: src, depth: +$("#depth").value };
    $("#find-go").disabled = true;
    try {
      let r;
      try { r = await api("/api/search", body); }
      catch (e) { if (!e.data?.needs_confirm || !confirm(e.message)) throw e; r = await api("/api/search", { ...body, confirm_over: true }); }
      store.set("locations", $("#locations").value); store.set("source", src);
      $("#find").close(); $("#keyword").value = "";
      toast(`${r.ids.length} search${r.ids.length > 1 ? "es" : ""} started. New leads join the queue as they're checked.`);
      poll(true);
    } catch (e) { toast(e.message, { err: true }); } finally { updateFindSummary(); }
  });
}

/* ============================================================ searches */
function ago(t) {
  if (!t) return "";
  const s = Date.now() / 1000 - t;
  if (s < 60) return "Just now";
  if (s < 3600) return Math.round(s / 60) + " min ago";
  if (s < 86400) return Math.round(s / 3600) + " hours ago";
  return new Date(t * 1000).toLocaleDateString();
}
const STATUS_WORD = { queued: "Waiting", running: "Searching", done: "Done", failed: "Didn't finish" };
async function loadSearches() {
  try { state.searches = await api("/api/searches"); } catch (e) { return toast(e.message, { err: true }); }
  if (state.view !== "searches") return;
  $("#searches-empty").hidden = state.searches.length > 0;
  $("#searches-table tbody").innerHTML = state.searches.map((s) => `<tr>
    <td>${esc(ago(s.created_at))}</td><td>${esc(s.category_label)}</td>
    <td>${esc(s.location)}${s.place && s.place !== s.location ? `<div class="sub" title="${esc(s.place)}">${esc(s.place.split(",").slice(0, 2).join(","))}</div>` : ""}</td>
    <td>${esc(SOURCE[s.source] || s.source)}</td>
    <td><span class="st ${esc(s.status)}">${esc(STATUS_WORD[s.status] || s.status)}</span>${s.message ? `<div class="sub">${esc(s.message)}</div>` : ""}</td>
    <td class="num">${s.found ?? ""}</td><td class="num">${s.added ?? ""}</td>
    <td class="acts-cell">${s.status === "done" ? `<button class="link" data-view-s="${s.id}">View leads</button>` : ""}${s.source !== "csv" ? `<button class="link" data-rerun="${s.id}">Run again</button>` : ""}<button class="link" data-del="${s.id}">Delete</button></td></tr>`).join("");
}
$("#searches-table").addEventListener("click", async (e) => {
  const t = e.target;
  try {
    if (t.dataset.viewS) {
      Object.assign(state.leads.filters, { bucket: [], search: t.dataset.viewS }); saveFilters(); show("leads");
    } else if (t.dataset.rerun) {
      await api("/api/searches/rerun", { id: +t.dataset.rerun }); toast("Search queued"); loadSearches(); poll(true);
    } else if (t.dataset.del) {
      const dlg = $("#del-search");
      dlg.returnValue = "";
      dlg.showModal();
      dlg.addEventListener("close", async function once() {
        dlg.removeEventListener("close", once);
        if (dlg.returnValue !== "keep" && dlg.returnValue !== "all") return;
        await api("/api/searches/delete", { id: +t.dataset.del, with_leads: dlg.returnValue === "all" });
        if (state.leads.filters.search === t.dataset.del) { state.leads.filters.search = ""; saveFilters(); }
        toast("Search deleted."); loadSearches(); refreshCounts();
      });
    }
  } catch (err) { toast(err.message, { err: true }); }
});

/* ============================================================ import & check */
function bindImport() {
  const file = $("#import-file");
  let text = null, name = "";
  const take = async (f) => {
    if (!f) return;
    text = await f.text(); name = f.name;
    $("#drop-text").innerHTML = `<b>${esc(f.name)}</b>, ${Math.max(0, text.split(/\r?\n/).filter(Boolean).length - 1)} rows`;
    $("#import-go").disabled = false;
  };
  file.addEventListener("change", () => take(file.files[0]));
  const drop = $("#drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); take(e.dataTransfer.files[0]); });
  $("#import-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!text) return;
    const fd = new FormData(e.target);
    try {
      const r = await api("/api/import?" + new URLSearchParams({ filename: name, category: fd.get("category") || "", country: fd.get("country") || "" }), text, { type: "text/csv" });
      $("#import-result").textContent = `Imported ${r.rows} rows, ${r.added} of them new. Their websites are being checked now.`;
      poll(true);
    } catch (err) { $("#import-result").textContent = err.message; }
  });
  $("#check-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/check-url", Object.fromEntries(new FormData(e.target)));
      e.target.reset(); toast("Added. Checking the website…");
      show("leads"); setTimeout(() => select("leads", r.id), 300);
    } catch (err) { toast(err.message, { err: true }); }
  });
}

/* ============================================================ settings */
async function loadSettings() { try { state.settings = await api("/api/settings"); } catch { /* server starting */ } }
function fillSettings() {
  const s = state.settings, me = $("#me-form"), kf = $("#key-form");
  for (const k of ["my_name", "agency", "my_site", "my_phone"]) me.elements[k].value = s[k] || "";
  kf.elements.google_key.value = ""; kf.elements.auto_psi.checked = !!s.auto_psi; kf.elements.workers.value = s.workers || 8;
  $("#key-state").textContent = s.google_key_set ? `(saved, ends ${s.google_key_hint})` : "(not set)";
  $("#tomtom-form").elements.tomtom_key.value = "";
  $("#tomtom-state").textContent = s.tomtom_key_set ? `(saved, ends ${s.tomtom_key_hint})` : "(not set)";
  $("#apify-form").elements.apify_token.value = "";
  $("#apify-state").textContent = s.apify_token_set ? `(saved, ends ${s.apify_token_hint})` : "(not set)";
  if (s.apify_token_set) api("/api/apify-usage", {}).then((u) => { state.apifyUsd = u; renderStatus(state.status || {}); }).catch(() => {});
  $("#theme-select").value = store.get("theme", "system");
  $("#layout-select").value = document.documentElement.dataset.layout;
}
function bindSettings() {
  const save = async (body, msg = "Saved") => { try { state.settings = await api("/api/settings", body); fillSettings(); toast(msg); } catch (e) { toast(e.message, { err: true }); } };
  $("#me-form").addEventListener("submit", (e) => { e.preventDefault(); save(Object.fromEntries(new FormData(e.target))); });
  $("#key-form").addEventListener("submit", (e) => { e.preventDefault(); const f = e.target.elements; save({ google_key: f.google_key.value.trim(), auto_psi: f.auto_psi.checked, workers: +f.workers.value || 8 }); });
  $("#tomtom-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const k = e.target.elements.tomtom_key.value.trim();
    if (!k) return toast("Paste your TomTom key first.", { err: true });
    save({ tomtom_key: k }, "TomTom key saved. Choose TomTom when you find leads.");
  });
  $("#clear-tomtom").addEventListener("click", () => confirm("Remove the saved TomTom key from this computer?") && save({ clear_tomtom_key: true }, "Key removed"));
  $("#apify-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const k = e.target.elements.apify_token.value.trim();
    if (!k) return toast("Paste your Apify token first.", { err: true });
    save({ apify_token: k }, "Apify token saved. Checking your No website leads against Google now.");
    poll(true);
  });
  $("#clear-apify").addEventListener("click", () => confirm("Remove the saved Apify token from this computer?") && save({ clear_apify_token: true }, "Token removed"));
  $("#find-sites").addEventListener("click", async () => { const r = await api("/api/find-sites", {}); toast(r.queued ? `Looking for websites for ${r.queued.toLocaleString()} leads` : "Every No website lead has already been checked"); poll(true); });
  $("#clear-key").addEventListener("click", () => confirm("Remove the saved Google key from this computer?") && save({ clear_google_key: true }, "Key removed"));
  $("#theme-select").addEventListener("change", (e) => setTheme(e.target.value, e.target));
  $("#layout-select").addEventListener("change", (e) => setLayout(e.target.value));
  $("#regrade-all").addEventListener("click", async () => {
    if (!confirm("Check every website again? This runs in the background and can take a while for big lists.")) return;
    const r = await api("/api/lead/regrade", { all: true }); toast(`${r.queued} websites queued`); poll(true);
  });
}

/* ============================================================ live status */
const statusSig = () => { const s = state.status || {}; const k = s.lookup || {}; return [s.graded_total, s.leads, k.to_guess, k.to_google].join("|"); };
async function refreshCounts() {
  try { const s = await api("/api/status"); renderStatus(s); } catch { /* next poll retries */ }
}
function renderStatus(s) {
  state.status = s;
  $("#n-leads").textContent = s.leads ? s.leads.toLocaleString() : "";
  $("#n-follow").textContent = s.followups_due || "";
  $("#n-next").textContent = s.ready ? s.ready.toLocaleString() : "";
  const busy = !!(s.searching || s.queued_searches || s.grading || s.psi || s.pending || s.finding);
  $("#work-dot").className = "dot" + (busy ? " live" : "");
  let txt;
  if (s.searching) txt = `${s.searching.label}: ${s.searching.step}` + (s.queued_searches ? ` (${s.queued_searches} more waiting)` : "");
  else if (s.queued_searches) txt = `${s.queued_searches} searches waiting`;
  else if (s.grading || s.pending) txt = `Checking websites, ${s.pending} to go`;
  else if (s.psi) txt = "Running Google speed tests";
  else if (s.apify_batch && !s.lookup?.to_guess) txt = `Checking ${s.apify_batch} Google profiles, ${(s.lookup?.to_google || 0).toLocaleString()} to go`;
  else if (s.finding) txt = `Looking for missing websites, ${(s.lookup?.to_guess || 0).toLocaleString()} to go`;
  else txt = s.leads ? "Up to date" : "Ready";
  $("#work-text").textContent = txt;
  $("#work").title = (s.log || []).map((l) => `${new Date(l.at * 1000).toLocaleTimeString()}  ${l.msg}`).join("\n");
  const tu = $("#tomtom-usage"); if (tu && s.tomtom) tu.textContent = `TomTom searches used this month: ${s.tomtom.used.toLocaleString()} of about ${s.tomtom.free.toLocaleString()} free.`;
  const su = $("#apify-usage");
  if (su && s.apify && s.lookup) {
    const k = s.lookup, found = k.found_guess + k.found_google;
    su.textContent = [found ? `Websites found so far: ${found.toLocaleString()} (${k.found_guess.toLocaleString()} by name, ${k.found_google.toLocaleString()} from Google profiles).` : "",
      k.google_no_site ? `${k.google_no_site.toLocaleString()} confirmed with no website on Google.` : "",
      s.apify.set && s.apify.checked ? `Google profiles checked this month: ${s.apify.checked.toLocaleString()}.` : "",
      s.apify.set && state.apifyUsd?.used != null ? `Apify credit used this month: $${(+state.apifyUsd.used).toFixed(2)} of $${(+(state.apifyUsd.limit || 5)).toFixed(2)}.` : "",
      s.apify_error ? `Paused: ${s.apify_error}` : ""].filter(Boolean).join(" ");
  }
  const gu = $("#google-usage"); if (gu && s.google) gu.textContent = `Google requests used this month: ${s.google.used} of ${s.google.free} free.`;
  return busy;
}
let pollTimer, lastSearchSig = "";
async function poll(soon = false) {
  clearTimeout(pollTimer);
  if (soon) { pollTimer = setTimeout(poll, 500); return; }
  let s;
  try { s = await api("/api/status"); } catch {
    $("#work-dot").className = "dot off"; $("#work-text").textContent = "LeadFinder isn't running. Start it with start.bat.";
    pollTimer = setTimeout(poll, 5000); return;
  }
  const prevGraded = state.status?.graded_total;
  const busy = renderStatus(s);
  const searchSig = [s.searching?.id, s.queued_searches].join("|");
  if (searchSig !== lastSearchSig) { lastSearchSig = searchSig; loadSearches(); }
  // Announce new data; never reshuffle what's on screen.
  if (state.view === "next") {
    if (state.shownReady == null) state.shownReady = s.ready;
    else if (s.ready > state.shownReady) $("#next-notice").hidden = false;
    else state.shownReady = Math.min(state.shownReady, s.ready);
  }
  if (state.view === "leads" && state.leads.sig && statusSig() !== state.leads.sig) $("#leads-notice").hidden = false;
  // The open lead was still being checked: update just its panel.
  if (state.lead && state.lead.bucket === "pending" && s.graded_total !== prevGraded) {
    const v = state.view;
    if (state.selected[v] === state.lead.id && state.open[v]) select(v, state.lead.id);
  }
  pollTimer = setTimeout(poll, busy ? 2500 : 8000);
}

/* ============================================================ boot */
(async function boot() {
  const qp = new URLSearchParams(location.search); // ?theme= and ?layout= open the app that way without saving
  applyTheme(qp.get("theme") || store.get("theme", "system"));
  applyLayout(qp.get("layout") || store.get("layout", "side"));
  bindLeads(); bindFind(); bindImport(); bindSettings();
  applyDensity();
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || document.querySelector("dialog[open]")) return;
    if (!$("#filters").hidden) { toggleFilters(false); $("#filters-btn").focus(); return; }
    if (state.open[state.view]) closeDetail(state.view);
  });
  try { const c = await api("/api/categories"); state.cats = c.categories; state.groups = c.groups; } catch { toast("Can't reach LeadFinder. Is it running?", { err: true }); }
  const qa = new URLSearchParams(location.search).get("area");
  if (qa !== null) { state.area = qa; store.set("area", qa); }
  await Promise.all([loadSettings(), refreshCounts(), loadSearches()]);
  show(location.hash.slice(1) || "next", { push: false });
  if (qp.get("lead") && ["next", "leads", "followups"].includes(state.view)) select(state.view, +qp.get("lead")); // ?lead=ID opens that lead
  requestAnimationFrame(() => requestAnimationFrame(() => document.documentElement.classList.remove("booting")));
  poll();
})();
