"""JSON API + static file server (stdlib only)."""
import csv
import io
import json
import mimetypes
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import categories, db, finder, grader, urls
from .engine import load_settings, save_settings
from .sources import csvimport, google, tomtom

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
ENGINE = None
COUNTRY_NAMES = {"GB": "United Kingdom", "NG": "Nigeria", "US": "United States"}


def _params(qs):
    return {k: v[-1] for k, v in urllib.parse.parse_qs(qs, keep_blank_values=True).items()}


def _public_settings():
    s = load_settings()
    for name in ("google_key", "tomtom_key", "apify_token"):
        k = s.get(name) or ""
        s[name] = ""
        s[name + "_set"] = bool(k)
        s[name + "_hint"] = ("…" + k[-4:]) if k else ""
    return s


class Handler(BaseHTTPRequestHandler):
    server_version = "LeadFinder/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body, default=str)).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if "json" in (self.headers.get("Content-Type") or ""):
            return json.loads(raw or b"{}")
        return raw

    def _static(self, path):
        if path.startswith("/shots/"):
            full = os.path.normpath(os.path.join(db.SHOTS, os.path.basename(path)))
            base = db.SHOTS
        else:
            path = "index.html" if path in ("", "/") else path.lstrip("/")
            full, base = os.path.normpath(os.path.join(WEB, path)), WEB
        if not full.startswith(base) or not os.path.isfile(full):
            return self._send(404, {"error": "Not found"})
        with open(full, "rb") as f:
            self._send(200, f.read(), mimetypes.guess_type(full)[0] or "application/octet-stream")

    # ---------------------------------------------------------------- GET
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        p = _params(u.query)
        conn = db.connect()
        try:
            if u.path == "/api/leads":
                rows, total = db.query_leads(conn, p, limit=min(int(p.get("limit", 100)), 500), offset=int(p.get("offset", 0)))
                return self._send(200, {"leads": rows, "total": total})
            if u.path == "/api/next":
                return self._send(200, db.next_up(conn, p.get("area") or None, min(int(p.get("limit", 10)), 50)))
            if u.path == "/api/areas":
                return self._send(200, db.areas(conn))
            if u.path == "/api/facets":
                return self._send(200, db.facets(conn, p))
            if u.path == "/api/lead":
                lead = db.get_lead(conn, int(p.get("id", 0)))
                return self._send(200 if lead else 404, lead or {"error": "That lead no longer exists."})
            if u.path == "/api/status":
                s = ENGINE.status()
                s.update(db.stats(conn))
                s["google"] = {"used": db.calls_this_month(conn, "google"), "free": google.FREE_PER_MONTH}
                s["dye_cuts"] = db.dye_cuts(conn)
                s["ready"] = conn.execute(f"SELECT COUNT(*) FROM leads WHERE {db.QUEUE_WHERE}", (time.time(),)).fetchone()[0]
                s["tomtom"] = {"used": db.calls_this_month(conn, "tomtom"), "free": tomtom.FREE_PER_MONTH}
                s["apify"] = {"checked": db.calls_this_month(conn, "apify"), "set": bool(load_settings().get("apify_token"))}
                s["lookup"] = db.lookup_counts(conn)
                return self._send(200, s)
            if u.path == "/api/searches":
                return self._send(200, db.list_searches(conn))
            if u.path == "/api/categories":
                return self._send(200, {"groups": categories.GROUPS, "categories": categories.public(), "statuses": db.STATUSES})
            if u.path == "/api/settings":
                return self._send(200, _public_settings())
            if u.path == "/api/export.csv":
                return self._export(conn, p)
            return self._static(u.path)
        except Exception as e:
            return self._send(500, {"error": str(e)})
        finally:
            conn.close()

    def _export(self, conn, p):
        rows, _ = db.query_leads(conn, p, limit=20000, offset=0)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Business", "Website status", "Site score", "Opportunity", "Summary", "Type", "Address", "City", "Country",
                    "Phone", "Email", "Website", "Google Maps", "Rating", "Reviews", "Pitch points", "Pipeline status", "Notes"])
        labels = {"none": "No website", "social": "Social/listing page only", "broken": "Broken website", "bad": "Bad website",
                  "weak": "Needs work", "ok": "Decent website", "unknown": "Couldn't check", "pending": "Not checked yet"}
        for r in rows:
            full = conn.execute("SELECT issues, gmaps_url, notes FROM leads WHERE id=?", (r["id"],)).fetchone()
            issues = json.loads(full["issues"] or "[]")
            pitch = " | ".join(i["pitch"] for i in issues if i["pts"] >= 5 or i["pts"] == 0)[:2000]
            w.writerow([r["name"], labels.get(r["bucket"], r["bucket"]), "" if r["score"] is None else r["score"], r["opportunity"] or "",
                        r["headline"] or "", r["category"], r["address"], r["city"], COUNTRY_NAMES.get(r["country"], r["country"]),
                        r["phone"], r["email"], r["website"], full["gmaps_url"], r["rating"] or "", "" if r["reviews"] is None else r["reviews"],
                        pitch, r["status"].replace("_", " "), full["notes"]])
        name = f"leads-{time.strftime('%Y-%m-%d')}.csv"
        return self._send(200, buf.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8",
                          {"Content-Disposition": f'attachment; filename="{name}"'})

    # ---------------------------------------------------------------- POST
    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        conn = db.connect()
        try:
            if u.path == "/api/import":
                return self._import(conn, _params(u.query))
            b = self._body()
            if u.path == "/api/search":
                return self._search(conn, b)
            if u.path == "/api/searches/rerun":
                s = conn.execute("SELECT * FROM searches WHERE id=?", (b["id"],)).fetchone()
                if not s:
                    return self._send(404, {"error": "Search not found"})
                sid = db.add_search(conn, source=s["source"], category_id=s["category_id"], category_label=s["category_label"],
                                    keyword=s["keyword"], location=s["location"], depth=s["depth"], status="queued")
                ENGINE.queue_search(sid)
                return self._send(200, {"id": sid})
            if u.path == "/api/searches/delete":
                db.delete_search(conn, int(b["id"]), bool(b.get("with_leads")))
                return self._send(200, {"ok": True})
            if u.path == "/api/lead/update":
                kw = {}
                if "status" in b:
                    if b["status"] not in db.STATUSES:
                        return self._send(400, {"error": "Unknown status"})
                    kw.update(status=b["status"], status_at=time.time())
                    # Contacted or demo sent: chase in 3 days unless a date was given. Finished leads need no chasing.
                    if b["status"] in ("contacted", "demo_sent") and "follow_up_at" not in b:
                        kw["follow_up_at"] = db.end_of_today() + 3 * 86400
                    elif b["status"] in ("won", "lost", "not_fit", "new", "shortlisted"):
                        kw["follow_up_at"] = None
                if "follow_up_at" in b:
                    kw["follow_up_at"] = float(b["follow_up_at"]) if b["follow_up_at"] else None
                if "skip" in b:
                    kw["skip_until"] = db.end_of_today() if b["skip"] else None
                if "notes" in b:
                    kw["notes"] = str(b["notes"])[:10000]
                if "website" in b:
                    kw.update(website=urls.normalize(b["website"]), domain=db.site_key(b["website"]), grade_status="pending",
                              site_via="manual" if b["website"] else None, site_why=None)
                if kw:
                    db.set_fields(conn, int(b["id"]), **kw)
                if "website" in b:
                    ENGINE.enqueue([int(b["id"])], force=True)
                return self._send(200, db.get_lead(conn, int(b["id"])))
            if u.path == "/api/lead/regrade":
                ids = b.get("ids") or ([b["id"]] if b.get("id") else [])
                if b.get("all"):
                    ids = [r[0] for r in conn.execute("SELECT id FROM leads")]
                return self._send(200, {"queued": ENGINE.enqueue([int(i) for i in ids], force=True)})
            if u.path == "/api/find-sites":  # look again for websites the listings left out
                if b.get("id"):
                    db.set_fields(conn, int(b["id"]), guessed_at=None, google_check=None)
                    return self._send(200, {"queued": ENGINE.find([int(b["id"])])})
                ENGINE.apify_error = None
                return self._send(200, {"queued": ENGINE.enqueue_lookups()})
            if u.path == "/api/apify-usage":
                tok = load_settings().get("apify_token")
                u2 = finder.apify_usage(tok) if tok else None
                return self._send(200, {"used": u2[0], "limit": u2[1]} if u2 else {})
            if u.path == "/api/lead/psi":
                ids = b.get("ids") or [b["id"]]
                return self._send(200, {"queued": ENGINE.run_psi([int(i) for i in ids])})
            if u.path == "/api/lead/delete":  # hidden for a day so it can be undone
                db.set_fields(conn, int(b["id"]), hidden_at=time.time())
                return self._send(200, {"ok": True})
            if u.path == "/api/lead/restore":
                db.set_fields(conn, int(b["id"]), hidden_at=None)
                return self._send(200, {"ok": True})
            if u.path == "/api/check-url":
                site = urls.normalize(b.get("url", ""))
                nm = (b.get("name") or "").strip() or urls.bare(urls.host(site)) or "Manual lead"
                if not site and not b.get("name"):
                    return self._send(400, {"error": "Enter a website address (or at least a business name)."})
                lid, _ = db.upsert_lead(conn, {"key": "m:" + (site or nm).lower(), "source": "manual", "name": nm, "website": site,
                                               "category": (b.get("category") or "Added by hand").strip(), "country": b.get("country") or "",
                                               "phone": b.get("phone") or "", "city": b.get("city") or ""})
                ENGINE.enqueue([lid], force=True)
                return self._send(200, {"id": lid})
            if u.path == "/api/settings":
                s = load_settings()
                for k in ("auto_psi", "my_name", "agency", "my_site", "my_phone", "workers"):
                    if k in b:
                        s[k] = b[k]
                for name in ("google_key", "tomtom_key", "apify_token"):
                    if b.get(name):
                        s[name] = b[name].strip()
                    if b.get("clear_" + name):
                        s[name] = ""
                s["workers"] = max(2, min(24, int(s.get("workers") or 8)))
                save_settings(s)
                if b.get("apify_token"):
                    ENGINE.apify_error = None
                    ENGINE.enqueue_lookups()  # check the "No website" leads against Google
                return self._send(200, _public_settings())
            return self._send(404, {"error": "Unknown endpoint"})
        except KeyError as e:
            return self._send(400, {"error": f"Missing field: {e}"})
        except Exception as e:
            return self._send(500, {"error": str(e)})
        finally:
            conn.close()

    def _search(self, conn, b):
        locations = [x.strip() for x in str(b.get("locations") or "").replace(";", "\n").splitlines() if x.strip()]
        cats = b.get("categories") or []
        keyword = (b.get("keyword") or "").strip()
        source = b.get("source") if b.get("source") in ("google", "tomtom") else "osm"
        depth = max(1, min(4, int(b.get("depth") or 1)))
        if not locations:
            return self._send(400, {"error": "Enter at least one place, e.g. \"Leeds\" or \"Lekki, Lagos\"."})
        jobs = [(c, None) for c in cats if categories.get(c)]
        if keyword:
            if not categories.custom(keyword):
                return self._send(400, {"error": "Type a business type using letters, e.g. \"braids\" or \"cake, bakery\"."})
            jobs.append(("custom", keyword))
        if not jobs:
            return self._send(400, {"error": "Pick at least one business type, or type your own."})
        if source == "google" and not load_settings().get("google_key"):
            return self._send(400, {"error": "Google needs your API key. Add it in Settings, or search OpenStreetMap (free)."})
        if source == "tomtom" and not load_settings().get("tomtom_key"):
            return self._send(400, {"error": "TomTom needs your free API key. Add it in Settings."})
        if source == "google":
            est = google.requests_estimate(depth) * len(jobs) * len(locations)
            used = db.calls_this_month(conn, "google")
            left = max(0, google.FREE_PER_MONTH - used)
            if est > left and not b.get("confirm_over"):
                return self._send(409, {"needs_confirm": True, "error":
                    f"This batch could use up to {est} Google requests, but only {left} of your {google.FREE_PER_MONTH} free requests "
                    f"are left this month. Beyond that Google charges (about $35 per 1,000). Most searches use fewer than the maximum. Run it anyway?"})
        if len(jobs) * len(locations) > 60:
            return self._send(400, {"error": "That's more than 60 searches at once. Split it into smaller batches."})
        ids = []
        for loc in locations:
            for cid, kw in jobs:
                label = categories.custom(kw)["label"] if cid == "custom" else categories.get(cid)["label"]
                sid = db.add_search(conn, source=source, category_id=cid, category_label=label, keyword=kw, location=loc, depth=depth, status="queued")
                ENGINE.queue_search(sid)
                ids.append(sid)
        est = google.requests_estimate(depth) * len(ids) if source == "google" else None
        return self._send(200, {"ids": ids, "google_requests_max": est})

    def _import(self, conn, p):
        raw = self._body()
        text = raw.decode("utf-8-sig", "replace") if isinstance(raw, bytes) else str(raw)
        leads, err = csvimport.parse(text, p.get("category") or "Imported", p.get("country") or "")
        if err:
            return self._send(400, {"error": err})
        sid = db.add_search(conn, source="csv", category_id="import", category_label=p.get("category") or "Imported",
                            location=p.get("filename") or "CSV import", status="done", found=len(leads), finished_at=time.time())
        added = 0
        for L in leads:
            _, new = db.upsert_lead(conn, L, sid)
            added += new
        db.update_search(conn, sid, added=added, message=f"{len(leads)} rows, {added} new")
        ENGINE.enqueue_pending()
        return self._send(200, {"rows": len(leads), "added": added, "search": sid})


def serve(host, port, engine):
    global ENGINE
    ENGINE = engine
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"LeadFinder running at http://{host}:{port}  (Ctrl+C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
