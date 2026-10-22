/* LeadFinder UI: vanilla JS over the local JSON API.
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

let toastTimer;
function toast(msg, { err = false, action = null, onAction = null } = {}) {
  const t = $("#toast"), b = $("#toast-action");
  $("#toast-text").textContent = msg;
  t.className = "toast" + (err ? " err" : "");
  b.hidden = !action;
  if (action) { b.textContent = action; b.onclick = () => { t.hidden = true; onAction && onAction(); }; }
  t.hidden = false;
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
const STATUS_LABEL = { new: "New", shortlisted: "Shortlisted", contacted: "Contacted", demo_sent: "Demo sent", replied: "Replied", won: "Won", lost: "Lost", not_fit: "Not a fit" };
const IN_QUEUE = new Set(["new", "shortlisted"]);

// Steps come from the server: quintiles of the leads waiting to be contacted, so the queue always shows real spread.
const dye = (opp) => {
  if (opp == null) return 0;
  const [c5, c4, c3, c2] = state.status?.dye_cuts || [70, 60, 48, 35];
  return opp >= c5 ? 5 : opp >= c4 ? 4 : opp >= c3 ? 3 : opp >= c2 ? 2 : 1;
};
const DYE_WORD = ["not rated", "weak", "fair", "good", "strong", "very strong"];
const unverified = (L) => L.bucket === "none" && L.source === "osm";
function marker(L, label) {
  label = label || (unverified(L) ? "No website listed" : BLABEL[L.bucket] || L.bucket);
  return `<span class="mk mk-${esc(L.bucket)}">${esc(label)}</span>`;
}
/* The specific finding in a few words, so ten rows give ten different reasons to call. */
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
  if (L.bucket === "none") return unverified(L) ? "No website listed" : "No website";
  if (L.bucket === "bad" || L.bucket === "weak") { const m = h.match(/^\d+ problems?: ([^,]+)/); return m ? m[1] : BLABEL[L.bucket]; }
  return BLABEL[L.bucket] || L.bucket;
}
function swatch(L, cls = "sw") {
  const d = dye(L.opportunity);
  return `<i class="${cls} ${d ? "d" + d : "d0"}" role="img" aria-label="Lead strength: ${DYE_WORD[d]}"></i>`;
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

/* ============================================================ state & routing */
const state = {
  view: "next", area: store.get("area", ""), next: null, shownReady: null,
  leads: { filters: Object.assign({ bucket: [], q: "", area: "", country: "", category: "", status: "", search: "", min_reviews: "", has_phone: false, has_email: false, show_closed: false }, store.get("filters", {})),
    sort: store.get("sort", "opportunity"), rows: [], total: 0, sig: "" },
  follow: [], selected: { next: null, leads: null, followups: null }, lead: null,
  cats: [], groups: [], settings: {}, searches: [], status: null,
};
const VIEWS = ["next", "leads", "followups", "searches", "import", "settings"];

function show(view, { push = true } = {}) {
  if (!VIEWS.includes(view)) view = "next";
  state.view = view;
  $$(".nav a").forEach((a) => { if (a.dataset.view === view) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  $$(".view").forEach((v) => (v.hidden = v.id !== "view-" + view));
  $("#rail").classList.remove("open");
  $("#menu-btn").setAttribute("aria-expanded", "false");
  if (push && location.hash !== "#" + view) history.replaceState(null, "", "#" + view);
  if (view === "next") loadNext();
  if (view === "leads") loadLeads(true);
  if (view === "followups") loadFollowups();
  if (view === "searches") loadSearches();
  if (view === "settings") fillSettings();
}
window.addEventListener("hashchange", () => show(location.hash.slice(1), { push: false }));
$$(".nav a").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); show(a.dataset.view); }));
$("#menu-btn").addEventListener("click", () => {
  const open = $("#rail").classList.toggle("open");
  $("#menu-btn").setAttribute("aria-expanded", String(open));
});

/* theme */
function applyTheme(t) {
  if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  else document.documentElement.removeAttribute("data-theme");
}
applyTheme(store.get("theme", "system"));

/* ============================================================ list rows */
function rowHTML(L, { due = false } = {}) {
  const meta = [L.category, L.city].filter(Boolean).join(" · ");
  let side = marker(L, reason(L));
  if (due && L.follow_up_at) {
    const d = dueLabel(L.follow_up_at);
    side = `<span class="due-tag ${d.late ? "" : "ok"}">${icon("clock")}${esc(d.text)}</span><span class="tag">${esc(STATUS_LABEL[L.status])}</span>`;
  } else if (!IN_QUEUE.has(L.status)) side += `<span class="tag">${esc(STATUS_LABEL[L.status])}</span>`;
  else if (L.status === "shortlisted") side += `<span class="tag">Shortlisted</span>`;
  return `<li><button class="row" type="button" data-id="${L.id}" aria-current="false">${swatch(L)}
    <span><span class="rname">${esc(L.name)}</span><span class="rmeta">${esc(meta)}${L.closed ? " · Closed" : ""}</span></span>
    <span class="rside">${side}</span></button></li>`;
}
function markSelected(container, id) {
  $$(".row", container).forEach((r) => r.setAttribute("aria-current", String(+r.dataset.id === id)));
}
function bindRows(container, view) {
  container.addEventListener("click", (e) => {
    const b = e.target.closest(".row");
    if (b) select(view, +b.dataset.id);
  });
  container.addEventListener("keydown", (e) => {
    if (!["ArrowDown", "ArrowUp"].includes(e.key)) return;
    const rows = $$(".row", container);
    const i = rows.indexOf(document.activeElement);
    const n = rows[i + (e.key === "ArrowDown" ? 1 : -1)];
    if (n) { e.preventDefault(); n.focus(); select(view, +n.dataset.id); }
  });
}
const pane = (view) => $(`#view-${view} [data-detail]`);

async function select(view, id, { quiet = false } = {}) {
  state.selected[view] = id;
  markSelected($(`#view-${view}`), id);
  try {
    const L = await api("/api/lead?id=" + id);
    if (state.selected[view] !== id) return;
    state.lead = L;
    renderDetail(view, L, { quiet });
    if (!quiet) pane(view).classList.add("open");
  } catch (e) { toast(e.message, { err: true }); }
}

/* ============================================================ next up */
async function loadNext({ keepSelection = true } = {}) {
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
    ? `${data.queue.length} of ${data.ready.toLocaleString()} ready to contact${state.area ? " in " + state.area : ""}. Strongest first.`
    : "";
  $("#next-follow").innerHTML = data.followups.length
    ? `<p class="section-label">${icon("bell")}Follow-ups due</p><ol class="rows">${data.followups.map((L) => rowHTML(L, { due: true })).join("")}</ol><p class="section-label">${icon("arrow")}New leads</p>` : "";
  $("#next-list").innerHTML = data.queue.map((L) => rowHTML(L)).join("");
  $("#next-end").textContent = data.queue.length ? (data.ready > data.queue.length
    ? "That's today's ten. Log or skip them and the next ones move up."
    : "That's everyone ready to contact here. Find leads in another area for more.") : "";
  const empty = !data.queue.length && !data.followups.length;
  $("#next-empty").hidden = !empty;
  if (empty) {
    $("#next-empty").innerHTML = `<h2>No one to contact ${state.area ? "in " + esc(state.area) + " " : ""}right now</h2>
      <p>Every lead here has been contacted, skipped for today, or is still being checked. Find businesses in a new area to fill the queue.</p>
      <button class="btn btn-primary" type="button" data-open-find>${icon("search")}Find leads</button>`;
    $("[data-open-find]", $("#next-empty")).addEventListener("click", () => openFind());
    pane("next").innerHTML = "";
    return;
  }
  const all = [...data.followups, ...data.queue];
  const cur = state.selected.next;
  const target = keepSelection && all.some((l) => l.id === cur) ? cur : all[0].id;
  if (target !== cur || !pane("next").querySelector(".d-wrap")) select("next", target, { quiet: true });
  else markSelected($("#view-next"), cur);
}
$("#area-chips").addEventListener("click", (e) => {
  const c = e.target.closest("[data-area]");
  if (!c) return;
  state.area = c.dataset.area; store.set("area", state.area);
  loadNext({ keepSelection: false });
});
$("#next-refresh").addEventListener("click", () => loadNext());
bindRows($("#next-scroll"), "next");

/* A lead left the queue (logged or skipped): lift it out, then bring up the next one. */
async function leaveQueue(id) {
  const row = $(`#view-next .row[data-id="${id}"]`);
  const all = [...(state.next?.followups || []), ...(state.next?.queue || [])];
  const i = all.findIndex((l) => l.id === id);
  const after = all[i + 1] || all[i - 1];
  if (row) { row.classList.add("leaving"); await new Promise((r) => setTimeout(r, 200)); }
  state.selected.next = after ? after.id : null;
  await loadNext();
  if (state.selected.next) select("next", state.selected.next, { quiet: true });
}

/* ============================================================ all leads */
function leadParams(extra = {}) {
  const f = state.leads.filters, p = new URLSearchParams();
  if (f.bucket.length) p.set("bucket", f.bucket.join(","));
  for (const k of ["q", "area", "country", "category", "status", "search", "min_reviews"]) if (f[k]) p.set(k, f[k]);
  for (const k of ["has_phone", "has_email", "show_closed"]) if (f[k]) p.set(k, "1");
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
async function loadLeads(reset, { keep = false } = {}) {
  const L = state.leads;
  const limit = keep ? Math.max(100, L.rows.length) : 100;
  const offset = reset || keep ? 0 : L.rows.length;
  let res, fx, areas;
  try { [res, fx, areas] = await Promise.all([api("/api/leads?" + leadParams({ limit, offset })), api("/api/facets?" + leadParams()), api("/api/areas")]); }
  catch (e) { return toast(e.message, { err: true }); }
  L.rows = reset || keep ? res.leads : L.rows.concat(res.leads);
  L.total = res.total;
  L.sig = statusSig();
  $("#leads-notice").hidden = true;
  const f = L.filters;
  fillSelect($("#f-area"), areas, f.area, "All areas");
  fillSelect($("#f-country"), fx.country, f.country, "All countries", (v) => COUNTRY[v] || v);
  fillSelect($("#f-category"), fx.category, f.category, "All types");
  fillSelect($("#f-status"), fx.status, f.status, "Any status", (v) => STATUS_LABEL[v] || v);
  const cur = f.search;
  $("#f-search").innerHTML = `<option value="">Any search</option>` + state.searches.filter((x) => x.status === "done" || String(x.id) === cur)
    .map((x) => `<option value="${x.id}"${String(x.id) === cur ? " selected" : ""}>${esc(x.category_label)}, ${esc(x.location)}</option>`).join("");
  const counts = fx.buckets || {};
  $("#buckets").innerHTML = BUCKETS.filter((b) => counts[b.id]).map((b) =>
    `<button class="chip" type="button" data-b="${b.id}" aria-pressed="${f.bucket.includes(b.id)}"><span class="mk mk-${b.id}">${esc(b.id === "none" ? "No website listed" : b.label)}</span><small>${counts[b.id].toLocaleString()}</small></button>`).join("");
  const nf = ["q", "area", "country", "category", "status", "search", "min_reviews"].filter((k) => f[k]).length + ["has_phone", "has_email", "show_closed"].filter((k) => f[k]).length;
  $("#filter-count").hidden = !nf; $("#filter-count").textContent = nf;
  $("#leads-list").innerHTML = L.rows.map((r) => rowHTML(r)).join("");
  $("#count").textContent = L.total ? `${L.total.toLocaleString()} lead${L.total === 1 ? "" : "s"}${L.total !== fx.total_all ? ` of ${fx.total_all.toLocaleString()}` : ""}` : "";
  $("#more").hidden = L.rows.length >= L.total;
  $("#export").href = "/api/export.csv?" + leadParams();
  const empty = !L.total;
  $("#leads-empty").hidden = !empty;
  if (empty) $("#leads-empty").innerHTML = fx.total_all
    ? `<h2>No leads match</h2><p>Try fewer filters.</p><button class="btn btn-quiet" type="button" id="empty-clear">Clear filters</button>`
    : `<h2>No leads yet</h2><p>Pick a business type and a place, and LeadFinder pulls every match and checks each website.</p><button class="btn btn-primary" type="button" id="empty-find">${icon("search")}Find leads</button>`;
  $("#empty-clear")?.addEventListener("click", clearFilters);
  $("#empty-find")?.addEventListener("click", () => openFind());
  if (state.selected.leads) markSelected($("#view-leads"), state.selected.leads);
  else if (!pane("leads").innerHTML) pane("leads").innerHTML = detailEmpty();
}
function clearFilters() {
  Object.assign(state.leads.filters, { bucket: [], q: "", area: "", country: "", category: "", status: "", search: "", min_reviews: "", has_phone: false, has_email: false, show_closed: false });
  $("#f-q").value = ""; $("#f-min_reviews").value = "";
  for (const k of ["has_phone", "has_email", "show_closed"]) $("#f-" + k).checked = false;
  saveFilters(); loadLeads(true);
}
function bindLeads() {
  const f = state.leads.filters;
  let qt;
  $("#f-q").value = f.q;
  $("#f-q").addEventListener("input", (e) => { clearTimeout(qt); qt = setTimeout(() => { f.q = e.target.value.trim(); saveFilters(); loadLeads(true); }, 250); });
  for (const k of ["area", "country", "category", "status", "search", "min_reviews"]) $("#f-" + k).addEventListener("change", (e) => { f[k] = e.target.value; saveFilters(); loadLeads(true); });
  for (const k of ["has_phone", "has_email", "show_closed"]) {
    $("#f-" + k).checked = !!f[k];
    $("#f-" + k).addEventListener("change", (e) => { f[k] = e.target.checked; saveFilters(); loadLeads(true); });
  }
  $("#f-min_reviews").value = f.min_reviews;
  $("#sort").value = state.leads.sort;
  $("#sort").addEventListener("change", (e) => { state.leads.sort = e.target.value; saveFilters(); loadLeads(true); });
  $("#clear-filters").addEventListener("click", clearFilters);
  $("#filters-btn").addEventListener("click", () => {
    const box = $("#filters"); box.hidden = !box.hidden;
    $("#filters-btn").setAttribute("aria-expanded", String(!box.hidden));
  });
  $("#buckets").addEventListener("click", (e) => {
    const c = e.target.closest("[data-b]"); if (!c) return;
    const id = c.dataset.b, cur = f.bucket;
    f.bucket = e.ctrlKey || e.metaKey || e.shiftKey ? (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]) : (cur.length === 1 && cur[0] === id ? [] : [id]);
    saveFilters(); loadLeads(true);
  });
  $("#more").addEventListener("click", () => loadLeads(false));
  $("#leads-refresh").addEventListener("click", () => loadLeads(false, { keep: true }));
  bindRows($("#view-leads .scroll"), "leads");
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
    .map(([k, v]) => `<p class="section-label">${esc(k)} <span class="muted">${v.length}</span></p><ol class="rows">${v.map((L) => rowHTML(L, { due: true })).join("")}</ol>`).join("");
  $("#follow-empty").hidden = !!res.leads.length;
  $("#follow-empty").innerHTML = `<h2>Nothing to chase</h2><p>When you mark a lead Contacted or Demo sent, it shows up here 3 days later so it doesn't go cold.</p>`;
  const cur = state.selected.followups;
  if (!res.leads.length) { state.selected.followups = null; pane("followups").innerHTML = ""; return; }
  if (!res.leads.some((l) => l.id === cur)) select("followups", res.leads[0].id, { quiet: true });
  else markSelected($("#view-followups"), cur);
}
bindRows($("#view-followups .scroll"), "followups");

/* ============================================================ detail */
function detailEmpty() {
  return `<div class="detail-empty"><i class="sw d4"></i><p>Pick a lead to see why they're worth contacting and what to say.</p></div>`;
}
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

function renderDetail(view, L, { quiet = false } = {}) {
  const p = pane(view);
  const g = L.grade || {}, site = g.site || {}, psi = L.psi;
  const email = L.email || site.emails?.[0] || "";
  const wa = waNumber(L.phone, L.country);
  const meta = [L.category, L.address || L.city, COUNTRY[L.country]].filter(Boolean).map(esc);
  if (L.phone) meta.push(esc(L.phone));
  if (L.reviews != null) meta.push(`<span class="star">${icon("star")}${esc(L.rating ?? "No rating")} from ${L.reviews} reviews</span>`);
  if (L.closed) meta.push("<b>Permanently closed</b>");
  const issues = (L.issues || []).filter((i) => i.pts >= 5 || i.pts === 0);
  const pending = L.bucket === "pending";
  const kind = store.get("sayKind", wa && (L.country === "NG" || !email) ? "whatsapp" : email ? "email" : "whatsapp");
  const facts = [];
  const f = (k, v) => v != null && v !== "" && facts.push(`<dt>${esc(k)}</dt><dd>${v}</dd>`);
  if (L.website) f("Website", `<a href="${esc(L.website)}" target="_blank" rel="noopener">${esc(L.website)}</a>`);
  if (site.final_url && site.final_url !== site.input_url) f("Ends up at", esc(site.final_url));
  if (site.ms != null) f("Load time", `${(site.ms / 1000).toFixed(1)} seconds from this computer`);
  f("Built with", esc(site.builder || ""));
  f("Copyright year", site.copyright_year ? esc(site.copyright_year) : "");
  f("Words on homepage", site.words != null ? esc(site.words) : "");
  if (site.error) f("Error", esc(site.error));
  if (L.score != null) f("Website score", `${L.score} out of 100`);
  if (L.opportunity != null) f("Lead strength", `${DYE_WORD[dye(L.opportunity)]} (${L.opportunity} of 100: weak web presence × how busy they look × whether you can reach them)`);
  if (L.graded_at) f("Checked", new Date(L.graded_at * 1000).toLocaleString());
  if (L.searches?.length) f("Found by", L.searches.map((s) => esc(`${s.category_label}, ${s.location}`)).join("; "));
  for (const [k, v] of Object.entries(L.socials || {})) f(k[0].toUpperCase() + k.slice(1), `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(v.replace(/^https?:\/\/(www\.)?/, ""))}</a>`);
  if (email) f("Email", `<a href="mailto:${esc(email)}">${esc(email)}</a>`);
  if (L.phone) f("Phone", esc(L.phone));
  const followDate = L.follow_up_at ? new Date(L.follow_up_at * 1000).toISOString().slice(0, 10) : "";

  p.innerHTML = `<div class="d-wrap">
    <div class="d-head">${`<span class="bigsw"><i class="d${dye(L.opportunity) || 1}"></i></span>`}
      <div><h2>${esc(L.name)}</h2><div class="d-meta">${meta.map((m) => `<span>${m}</span>`).join("")}</div>
        <div class="d-meta">${pending ? `<span class="mk mk-pending">Checking their website…</span>` : marker(L, reason(L))}${L.status !== "new" ? `<span class="tag">${esc(STATUS_LABEL[L.status])}</span>` : ""}</div></div>
      <button class="iconbtn d-close" type="button" aria-label="Close details">${icon("x")}</button></div>
    <div class="acts">
      ${wa ? `<a class="btn btn-primary" id="act-wa" target="_blank" rel="noopener">${icon("chat")}WhatsApp</a>` : ""}
      ${L.phone ? `<a class="btn ${wa ? "btn-quiet" : "btn-primary"}" href="tel:${esc(L.phone.replace(/[^\d+]/g, ""))}">${icon("phone")}Call</a>` : ""}
      ${email ? `<a class="btn btn-quiet" id="act-mail">${icon("mail")}Email</a>` : ""}
      ${L.website ? `<a class="btn btn-quiet" href="${esc(L.website)}" target="_blank" rel="noopener">${icon("ext")}Open their site</a>` : ""}
      ${IN_QUEUE.has(L.status) ? `<button class="btn btn-text skip" type="button" id="act-skip">${icon("clock")}Skip for today</button>` : ""}
      ${!L.phone && !email ? `<span class="guide">No phone or email on record. Try their Google listing or social page.</span>` : ""}
    </div>
    <section class="sec"><h3>Why them</h3>
      ${pending ? `<p class="guide">Their website is being checked now. This updates by itself.</p>` : issues.length
        ? `<ul class="why">${issues.slice(0, 5).map((i) => `<li class="${esc(i.sev)}"><b>${esc(i.title)}</b><p>${esc(i.pitch)}</p></li>`).join("")}</ul>`
        : `<p class="guide">${L.bucket === "ok" ? "Their website is in good shape. Pitch automations instead: instant replies to missed calls, booking, review requests." : "No website on their listing. People searching for them find competitors first."}</p>`}
      ${unverified(L) ? `<p class="caution" style="margin-top:12px">OpenStreetMap has no website for them, but they may still have one. <a href="https://www.google.com/search?q=${encodeURIComponent(L.name + " " + (L.city || ""))}" target="_blank" rel="noopener">Search Google first</a> before saying they have none.</p>` : ""}
    </section>
    <section class="sec"><h3>What to say</h3>
      <div class="seg" role="tablist" aria-label="Message type">
        <button type="button" role="tab" data-k="whatsapp">WhatsApp</button><button type="button" role="tab" data-k="email">Email</button><button type="button" role="tab" data-k="call">Call script</button></div>
      <input type="text" class="say-subject" id="say-subject" aria-label="Email subject">
      <textarea class="say-text" id="say-text" aria-label="Message"></textarea>
      <div class="btnrow"><button class="btn btn-quiet btn-sm" type="button" id="copy-say">${icon("copy")}Copy</button><span class="guide">Edit before sending, and replace [DEMO LINK] with your mock-up.</span></div>
      <p class="rule" id="say-rule" hidden></p>
    </section>
    <section class="sec"><h3>Log it <span class="saved" id="saved" hidden>Saved</span></h3>
      <div class="statusrow" id="statusrow">${Object.entries(STATUS_LABEL).map(([k, v]) => `<button class="chip" type="button" data-s="${k}" aria-pressed="${L.status === k}">${esc(v)}</button>`).join("")}</div>
      <div class="logrow">
        <label>Follow up on<input type="date" id="follow-date" value="${followDate}"></label>
        <label class="notes">Notes<textarea id="notes" placeholder="Who you spoke to, what they said, demo link">${esc(L.notes || "")}</textarea></label>
      </div>
    </section>
    <details class="more-info"><summary>Website details and tools</summary>
      <dl class="facts">${facts.join("")}</dl>
      ${psi && !psi.error ? `<div class="gauges">${gauge("Speed on phones", psi.performance)}${gauge("Search basics", psi.seo)}${gauge("Accessibility", psi.accessibility)}${gauge("Best practices", psi.best_practices)}</div>` : ""}
      ${psi && psi.error ? `<p class="guide" style="margin-top:12px">${esc(psi.error)}</p>` : ""}
      ${L.shot ? `<a href="/shots/${L.id}.jpg?${L.psi_at || ""}" target="_blank" rel="noopener"><img class="shot" src="/shots/${L.id}.jpg?${L.psi_at || ""}" alt="Their site on a phone"></a>` : ""}
      <div class="btnrow" style="margin-top:16px">
        <button class="btn btn-quiet btn-sm" type="button" id="act-regrade">${icon("refresh")}Check website again</button>
        ${g.kind === "site" ? `<button class="btn btn-quiet btn-sm" type="button" id="act-psi">${icon("gauge")}Run Google speed test</button>` : ""}
        <button class="btn btn-quiet btn-sm" type="button" id="act-site">${icon("edit")}${L.website ? "Change website" : "Add a website"}</button>
        <button class="btn btn-quiet btn-sm" type="button" id="act-delete">${icon("trash")}Delete lead</button>
      </div>
      <div class="inline-edit" id="site-edit" hidden><input type="text" id="site-input" value="${esc(L.website || "")}" placeholder="www.example.com" aria-label="Website address"><button class="btn btn-primary btn-sm" type="button" id="site-save">Save and check</button></div>
    </details>
  </div>`;

  /* wire up */
  $(".d-close", p).addEventListener("click", () => p.classList.remove("open"));
  const setKind = (k) => {
    store.set("sayKind", k);
    $$(".seg button", p).forEach((b) => b.setAttribute("aria-selected", String(b.dataset.k === k)));
    renderSay(p, L, k, wa, email);
  };
  $$(".seg button", p).forEach((b) => b.addEventListener("click", () => setKind(b.dataset.k)));
  setKind(kind);
  $("#act-skip", p)?.addEventListener("click", async () => {
    try { await api("/api/lead/update", { id: L.id, skip: true }); } catch (e) { return toast(e.message, { err: true }); }
    toast(`${L.name} skipped until tomorrow.`, { action: "Undo", onAction: async () => { await api("/api/lead/update", { id: L.id, skip: false }); refreshAll(); } });
    if (view === "next") leaveQueue(L.id); else select(view, L.id, { quiet: true });
  });
  $$("#statusrow .chip", p).forEach((b) => b.addEventListener("click", async () => {
    const prev = { status: L.status, follow_up_at: L.follow_up_at };
    const s = b.dataset.s;
    let upd;
    try { upd = await api("/api/lead/update", { id: L.id, status: s }); } catch (e) { return toast(e.message, { err: true }); }
    const msg = upd.follow_up_at && !prev.follow_up_at ? `Logged as ${STATUS_LABEL[s].toLowerCase()}. Follow-up set for ${fmtDay(upd.follow_up_at)}.` : `Logged as ${STATUS_LABEL[s].toLowerCase()}.`;
    toast(msg, { action: "Undo", onAction: async () => { await api("/api/lead/update", { id: L.id, status: prev.status, follow_up_at: prev.follow_up_at }); refreshAll(); } });
    refreshCounts();
    if (view === "next" && IN_QUEUE.has(prev.status) !== IN_QUEUE.has(s) || (view === "next" && state.next?.followups.some((x) => x.id === L.id) && !upd.follow_up_at)) leaveQueue(L.id);
    else if (view === "followups" && !upd.follow_up_at) { state.selected.followups = null; loadFollowups(); }
    else { state.lead = upd; renderDetail(view, upd, { quiet: true }); patchRow(view, upd); }
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
  $("#act-regrade", p).addEventListener("click", async () => { await api("/api/lead/regrade", { id: L.id }); toast("Checking their website again…"); select(view, L.id, { quiet: true }); });
  $("#act-psi", p)?.addEventListener("click", async () => { await api("/api/lead/psi", { id: L.id }); toast("Google speed test started. It takes up to a minute."); });
  $("#act-site", p).addEventListener("click", () => { $("#site-edit", p).hidden = false; $("#site-input", p).focus(); });
  $("#site-save", p).addEventListener("click", async () => {
    try { const upd = await api("/api/lead/update", { id: L.id, website: $("#site-input", p).value }); renderDetail(view, upd, { quiet: true }); toast("Saved. Checking the website…"); }
    catch (e) { toast(e.message, { err: true }); }
  });
  $("#act-delete", p).addEventListener("click", async () => {
    try { await api("/api/lead/delete", { id: L.id }); } catch (e) { return toast(e.message, { err: true }); }
    toast(`${L.name} deleted.`, { action: "Undo", onAction: async () => { await api("/api/lead/restore", { id: L.id }); refreshAll(); } });
    p.innerHTML = detailEmpty(); p.classList.remove("open"); state.selected[view] = null;
    refreshAll();
  });
}
function flashSaved(p) { const s = $("#saved", p); if (s) { s.hidden = false; setTimeout(() => (s.hidden = true), 1400); } }
function patchRow(view, L) {
  const old = $(`#view-${view} .row[data-id="${L.id}"]`);
  if (!old) return;
  const tmp = document.createElement("div");
  tmp.innerHTML = rowHTML(L, { due: view === "followups" });
  old.parentElement.replaceWith(tmp.firstElementChild);
  markSelected($(`#view-${view}`), L.id);
}
function refreshAll() {
  refreshCounts();
  if (state.view === "next") loadNext();
  if (state.view === "leads") loadLeads(false, { keep: true });
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
  const top = (L.issues || []).filter((i) => i.pts >= 5).slice(0, 3);
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
      problem = `I had a look at ${domain || "your website"} and spotted a few things that are probably costing you enquiries:\n\n` + (top.length ? top : (L.issues || []).slice(0, 3)).map((i) => `• ${i.pitch}`).join("\n");
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
  return { me, sign, praise, problem, subject, short, offer, top, place, cat };
}
function renderSay(p, L, kind, wa, email) {
  const x = pitchParts(L), subj = $("#say-subject", p), text = $("#say-text", p), rule = $("#say-rule", p);
  subj.hidden = kind !== "email";
  if (kind === "email") {
    subj.value = x.subject;
    text.value = `Hi there,\n\n${x.praise}\n\n${x.problem}\n\n${x.offer}\n\nBest,\n${x.sign}\n\nP.S. If this isn't useful, just reply "no thanks" and I won't contact you again.`;
  } else if (kind === "whatsapp") {
    text.value = `Hi! I'm ${x.me}${state.settings.agency ? ` from ${state.settings.agency}` : ""}. ${x.short} ${L.bucket === "ok" ? "Can I send you a quick example?" : "I made a quick mock-up of a new site for you. Can I send it over?"}`;
  } else {
    const points = (x.top.length ? x.top : (L.issues || []).slice(0, 3)).map((i) => `   • ${i.pitch}`).join("\n");
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
  const fit = () => { text.style.height = "auto"; text.style.height = Math.max(96, text.scrollHeight + 2) + "px"; };
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
    <td>${esc({ osm: "OpenStreetMap", google: "Google", tomtom: "TomTom", csv: "Spreadsheet" }[s.source] || s.source)}</td>
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
  $("#theme-select").value = store.get("theme", "system");
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
  $("#clear-key").addEventListener("click", () => confirm("Remove the saved Google key from this computer?") && save({ clear_google_key: true }, "Key removed"));
  $("#theme-select").addEventListener("change", (e) => { store.set("theme", e.target.value); applyTheme(e.target.value); });
  $("#regrade-all").addEventListener("click", async () => {
    if (!confirm("Check every website again? This runs in the background and can take a while for big lists.")) return;
    const r = await api("/api/lead/regrade", { all: true }); toast(`${r.queued} websites queued`); poll(true);
  });
}

/* ============================================================ live status */
const statusSig = () => { const s = state.status || {}; return [s.graded_total, s.leads].join("|"); };
async function refreshCounts() {
  try { const s = await api("/api/status"); renderStatus(s); } catch { /* next poll retries */ }
}
function renderStatus(s) {
  state.status = s;
  $("#n-leads").textContent = s.leads ? s.leads.toLocaleString() : "";
  $("#n-follow").textContent = s.followups_due || "";
  $("#n-next").textContent = s.ready ? s.ready.toLocaleString() : "";
  const busy = !!(s.searching || s.queued_searches || s.grading || s.psi || s.pending);
  $("#work-dot").className = "dot" + (busy ? " live" : "");
  let txt;
  if (s.searching) txt = `${s.searching.label}: ${s.searching.step}` + (s.queued_searches ? ` (${s.queued_searches} more waiting)` : "");
  else if (s.queued_searches) txt = `${s.queued_searches} searches waiting`;
  else if (s.grading || s.pending) txt = `Checking websites, ${s.pending} to go`;
  else if (s.psi) txt = "Running Google speed tests";
  else txt = s.leads ? "Up to date" : "Ready";
  $("#work-text").textContent = txt;
  $("#work").title = (s.log || []).map((l) => `${new Date(l.at * 1000).toLocaleTimeString()}  ${l.msg}`).join("\n");
  const tu = $("#tomtom-usage"); if (tu && s.tomtom) tu.textContent = `TomTom searches used this month: ${s.tomtom.used.toLocaleString()} of about ${s.tomtom.free.toLocaleString()} free.`;
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
    if (state.selected[v] === state.lead.id) select(v, state.lead.id, { quiet: true });
  }
  pollTimer = setTimeout(poll, busy ? 2500 : 8000);
}

/* ============================================================ boot */
(async function boot() {
  bindLeads(); bindFind(); bindImport(); bindSettings();
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") $$(".detail.open").forEach((d) => d.classList.remove("open")); });
  try { const c = await api("/api/categories"); state.cats = c.categories; state.groups = c.groups; } catch { toast("Can't reach LeadFinder. Is it running?", { err: true }); }
  const qa = new URLSearchParams(location.search).get("area");
  if (qa !== null) { state.area = qa; store.set("area", qa); }
  await Promise.all([loadSettings(), refreshCounts(), loadSearches()]);
  show(location.hash.slice(1) || "next", { push: false });
  poll();
})();
