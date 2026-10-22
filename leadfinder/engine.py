"""Background work: runs searches one at a time, and checks websites in parallel."""
import base64
import collections
import json
import os
import queue
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from . import categories, db, geo, grader
from .sources import google, osm, tomtom

SETTINGS = os.path.join(db.DATA, "settings.json")
DEFAULTS = {"google_key": "", "tomtom_key": "", "auto_psi": False, "workers": 8, "my_name": "", "agency": "", "my_site": "", "my_phone": ""}


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            s.update(json.load(f))
    except (OSError, ValueError):
        pass
    return s


def save_settings(s):
    tmp = SETTINGS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    os.replace(tmp, SETTINGS)


class Engine:
    def __init__(self):
        self.searches = queue.Queue()
        workers = max(2, min(24, int(load_settings().get("workers") or 8)))
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="grade")
        self.psi_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="psi")
        self.lock = threading.Lock()
        self.inflight, self.psi_inflight = set(), set()
        self.current = None
        self.log = collections.deque(maxlen=60)
        self.graded_total = 0

    # ---------------------------------------------------------------- lifecycle
    def start(self):
        conn = db.connect()
        for (sid,) in conn.execute("SELECT id FROM searches WHERE status='queued' ORDER BY id"):
            self.searches.put(sid)
        conn.close()
        threading.Thread(target=self._search_loop, daemon=True, name="searches").start()
        self.enqueue_pending()

    def note(self, msg):
        self.log.appendleft({"at": time.time(), "msg": msg})
        print(time.strftime("%H:%M:%S"), msg, flush=True)

    def status(self):
        with self.lock:
            return {"searching": self.current, "queued_searches": self.searches.qsize(), "grading": len(self.inflight),
                    "psi": len(self.psi_inflight), "graded_total": self.graded_total, "log": list(self.log)[:15]}

    # ---------------------------------------------------------------- searches
    def queue_search(self, sid):
        self.searches.put(sid)

    def _search_loop(self):
        while True:
            sid = self.searches.get()
            try:
                self._run_search(sid)
            except Exception as e:
                traceback.print_exc()
                conn = db.connect()
                db.update_search(conn, sid, status="failed", message=str(e)[:400], finished_at=time.time())
                conn.close()
                self.note(f"Search #{sid} failed: {e}")
            finally:
                with self.lock:
                    self.current = None

    def _run_search(self, sid):
        conn = db.connect()
        try:
            s = dict(conn.execute("SELECT * FROM searches WHERE id=?", (sid,)).fetchone())
            cat = categories.get(s["category_id"]) if s["category_id"] != "custom" else categories.custom(s["keyword"] or "")
            if not cat:
                raise RuntimeError("Unknown business type.")
            label = f"{cat['label']} in {s['location']}"
            with self.lock:
                self.current = {"id": sid, "label": label, "step": "Finding the place on the map"}
            db.update_search(conn, sid, status="running", message="Finding the place")
            g = geo.geocode(s["location"])
            if not g:
                raise RuntimeError(f"Couldn't find \"{s['location']}\" on the map. Try adding the city or country, e.g. \"Yaba, Lagos\".")
            db.update_search(conn, sid, place=g["display"], country=g["country"])
            self.current["step"] = "Searching " + {"google": "Google", "tomtom": "TomTom"}.get(s["source"], "OpenStreetMap")
            calls = None
            if s["source"] == "google":
                key = load_settings().get("google_key")
                if not key:
                    raise RuntimeError("Add your Google API key in Settings first, or use OpenStreetMap (free).")
                leads, calls = google.search(key, cat["google"], g, s["depth"] or 1, log=lambda m: self.current.__setitem__("step", m),
                                            on_call=lambda: db.add_calls(conn, "google"))
            elif s["source"] == "tomtom":
                key = load_settings().get("tomtom_key")
                if not key:
                    raise RuntimeError("Add your free TomTom API key in Settings first.")
                leads, calls = tomtom.search(key, cat["tomtom"], g, log=lambda m: self.current.__setitem__("step", m),
                                             on_call=lambda: db.add_calls(conn, "tomtom"))
            else:
                leads = osm.search(cat["osm"], g, log=lambda m: self.current.__setitem__("step", m))
            added = 0
            for L in leads:
                L.setdefault("category", cat["label"])
                L["category"] = cat["label"]
                L["country"] = L.get("country") or g["country"]
                L["city"] = L.get("city") or g["city"]
                _, new = db.upsert_lead(conn, L, sid)
                added += new
            msg = f"{len(leads)} found, {added} new" + (f" · {calls} {'Google' if s['source'] == 'google' else 'TomTom'} requests" if calls else "")
            db.update_search(conn, sid, status="done", found=len(leads), added=added, message=msg, finished_at=time.time())
            self.note(f"{label}: {msg}")
        finally:
            conn.close()
        self.enqueue_pending()

    # ---------------------------------------------------------------- website grading
    def enqueue_pending(self):
        conn = db.connect()
        ids = [r[0] for r in conn.execute("SELECT id FROM leads WHERE grade_status='pending' ORDER BY id")]
        conn.close()
        self.enqueue(ids)

    def enqueue(self, ids, force=False):
        conn = db.connect()
        n = 0
        for lid in ids:
            with self.lock:
                if lid in self.inflight:
                    continue
                self.inflight.add(lid)
            if force:
                db.set_fields(conn, lid, grade_status="pending")
            self.pool.submit(self._grade, lid)
            n += 1
        conn.close()
        return n

    def _grade(self, lid):
        conn = db.connect()
        try:
            L = db.get_lead(conn, lid)
            if not L:
                return
            db.set_fields(conn, lid, grade_status="running")
            res = grader.grade(L["website"])
            psi = L["psi"] if L.get("psi") and L.get("psi", {}).get("url") == L["website"] else None
            self._store(conn, L, res, psi)
            with self.lock:
                self.graded_total += 1
            if load_settings().get("auto_psi") and res["kind"] == "site":
                self.run_psi([lid])
        except Exception as e:
            traceback.print_exc()
            db.set_fields(conn, lid, grade_status="done", bucket="unknown", headline=f"Check failed: {e}"[:200], graded_at=time.time())
        finally:
            conn.close()
            with self.lock:
                self.inflight.discard(lid)

    def _store(self, conn, L, res, psi):
        bucket, score, issues, headline = grader.finalize(res, psi)
        site = res.get("site") or {}
        emails = site.get("emails") or []
        has_contact = bool(L["phone"] or L["email"] or emails)
        uncertain = bucket == "none" and L["source"] == "osm"
        if uncertain:
            headline = "No website listed on OpenStreetMap (check Google before pitching)"
        has_email = bool(L["email"] or emails)
        contact = "both" if L["phone"] and has_email else "phone" if L["phone"] else "email" if has_email else "none"
        opp = grader.opportunity(bucket, score, L["reviews"], L["rating"], has_contact, L["closed"], uncertain, res=res, contact=contact)
        db.save_grade(conn, L["id"], res, bucket, score, issues, headline, opp,
                      email=emails[0] if emails else None, socials=site.get("socials"))

    # ---------------------------------------------------------------- Google PageSpeed (optional, slow)
    def run_psi(self, ids):
        n = 0
        for lid in ids:
            with self.lock:
                if lid in self.psi_inflight:
                    continue
                self.psi_inflight.add(lid)
            self.psi_pool.submit(self._psi, lid)
            n += 1
        return n

    def _psi(self, lid):
        conn = db.connect()
        try:
            L = db.get_lead(conn, lid)
            if not L or not L["grade"] or L["grade"].get("kind") != "site":
                return
            url = (L["grade"].get("site") or {}).get("final_url") or L["website"]
            out, shot = grader.pagespeed(url, load_settings().get("google_key") or None)
            out["url"], out["at"] = L["website"], time.time()
            if shot and shot.startswith("data:image"):
                with open(os.path.join(db.SHOTS, f"{lid}.jpg"), "wb") as f:
                    f.write(base64.b64decode(shot.split(",", 1)[1]))
            db.set_fields(conn, lid, psi=json.dumps(out), psi_at=time.time())
            if not out.get("error"):
                self._store(conn, db.get_lead(conn, lid), L["grade"], out)
            self.note(f"PageSpeed for {L['name']}: " + (out.get("error") or f"mobile performance {out.get('performance')}/100"))
        except Exception as e:
            traceback.print_exc()
            self.note(f"PageSpeed failed for lead {lid}: {e}")
        finally:
            conn.close()
            with self.lock:
                self.psi_inflight.discard(lid)
