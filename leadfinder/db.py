"""SQLite storage: searches, leads (with their website grade and your pipeline notes), geocode cache."""
import json
import os
import re
import sqlite3
import threading
import time

from . import grader, urls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PATH = os.path.join(DATA, "leadfinder.db")
SHOTS = os.path.join(DATA, "shots")
lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS searches(
  id INTEGER PRIMARY KEY, source TEXT, category_id TEXT, category_label TEXT, keyword TEXT,
  location TEXT, place TEXT, country TEXT, depth INTEGER DEFAULT 1,
  status TEXT DEFAULT 'queued', found INTEGER DEFAULT 0, added INTEGER DEFAULT 0, message TEXT,
  created_at REAL, finished_at REAL);
CREATE TABLE IF NOT EXISTS leads(
  id INTEGER PRIMARY KEY, key TEXT UNIQUE, source TEXT, name TEXT, category TEXT, address TEXT, city TEXT, country TEXT,
  lat REAL, lon REAL, phone TEXT, phone_key TEXT, email TEXT, website TEXT, domain TEXT, gmaps_url TEXT, osm_url TEXT,
  rating REAL, reviews INTEGER, socials TEXT DEFAULT '{}', closed INTEGER DEFAULT 0,
  grade_status TEXT DEFAULT 'pending', bucket TEXT, score INTEGER, opportunity INTEGER, headline TEXT,
  issues TEXT DEFAULT '[]', grade TEXT, graded_at REAL, psi TEXT, psi_at REAL,
  status TEXT DEFAULT 'new', notes TEXT DEFAULT '', status_at REAL, created_at REAL, updated_at REAL);
CREATE INDEX IF NOT EXISTS ix_leads_bucket ON leads(bucket);
CREATE INDEX IF NOT EXISTS ix_leads_domain ON leads(domain);
CREATE INDEX IF NOT EXISTS ix_leads_phone ON leads(phone_key);
CREATE INDEX IF NOT EXISTS ix_leads_grade ON leads(grade_status);
CREATE TABLE IF NOT EXISTS lead_searches(lead_id INTEGER, search_id INTEGER, PRIMARY KEY(lead_id, search_id));
CREATE TABLE IF NOT EXISTS geocache(q TEXT PRIMARY KEY, data TEXT, at REAL);
CREATE TABLE IF NOT EXISTS api_usage(provider TEXT, month TEXT, calls INTEGER DEFAULT 0, PRIMARY KEY(provider, month));
"""

STATUSES = ["new", "shortlisted", "contacted", "demo_sent", "replied", "won", "lost", "not_fit"]


def connect():
    conn = sqlite3.connect(PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init():
    os.makedirs(SHOTS, exist_ok=True)
    conn = connect()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    have = {r[1] for r in conn.execute("PRAGMA table_info(leads)")}
    # site_via: where LeadFinder found a website the listing didn't have ('guess' or 'google'); site_why: the proof.
    # guessed_at: when we tried their likely domains. google_check: what their Google profile showed
    # ('site', 'no_site', or 'not_listed'), checked at google_checked_at.
    for col, decl in (("follow_up_at", "REAL"), ("skip_until", "REAL"), ("hidden_at", "REAL"), ("site_via", "TEXT"),
                      ("site_why", "TEXT"), ("guessed_at", "REAL"), ("google_check", "TEXT"), ("google_checked_at", "REAL")):
        if col not in have:
            conn.execute(f"ALTER TABLE leads ADD COLUMN {col} {decl}")
    # Deleted leads can be restored for a day, then they go for good.
    conn.execute("DELETE FROM lead_searches WHERE lead_id IN (SELECT id FROM leads WHERE hidden_at < ?)", (time.time() - 86400,))
    conn.execute("DELETE FROM leads WHERE hidden_at < ?", (time.time() - 86400,))
    # A grade interrupted by closing the app is simply redone.
    conn.execute("UPDATE leads SET grade_status='pending' WHERE grade_status='running'")
    # Searches cut off by closing the app run again when it restarts.
    conn.execute("UPDATE searches SET status='queued', message='Resuming after restart' WHERE status='running'")
    conn.commit()
    return conn


def phone_key(p):
    d = re.sub(r"\D", "", p or "")
    return d[-10:] if len(d) >= 7 else None


def site_key(website):
    """The domain we de-duplicate on, or None for profile/link pages (many businesses share facebook.com)."""
    kind, _, u = grader.classify(website)
    if kind in ("site", "free", "gone"):
        h = urls.host(u)
        return urls.bare(h) + (urllib_path(u) if kind == "free" else "")
    return None


def urllib_path(u):
    import urllib.parse
    return urllib.parse.urlsplit(u).path.rstrip("/")


FIELDS = ["source", "name", "category", "address", "city", "country", "lat", "lon", "phone", "email", "website",
          "gmaps_url", "osm_url", "rating", "reviews", "closed"]
REFRESH = {"rating", "reviews", "closed", "gmaps_url"}  # newer data wins for these


def upsert_lead(conn, L, search_id=None):
    """Insert or merge a lead. Returns (lead_id, is_new)."""
    now = time.time()
    L = dict(L)
    L["website"] = urls.normalize(L.get("website") or "")
    socials = L.pop("socials", None) or {}
    if not L["website"]:  # no website but a Facebook/Instagram link: grade that, so it lands in "social only"
        for k in ("facebook", "instagram", "tiktok"):
            if socials.get(k):
                L["website"] = urls.normalize(socials[k])
                break
    dom = site_key(L["website"])
    pk = phone_key(L.get("phone"))
    with lock:
        row = conn.execute("SELECT * FROM leads WHERE key=?", (L["key"],)).fetchone()
        if row is None and dom:
            row = conn.execute("SELECT * FROM leads WHERE domain=?", (dom,)).fetchone()
        if row is None and pk:
            row = conn.execute("SELECT * FROM leads WHERE phone_key=?", (pk,)).fetchone()
        if row:
            upd = {}
            for f in FIELDS:
                new, old = L.get(f), row[f]
                if new in (None, ""):
                    continue
                if old in (None, "") or (f in REFRESH and new != old):
                    upd[f] = new
            # A real website beats a social link we stored earlier.
            if L["website"] and row["website"] and L["website"] != row["website"]:
                if grader.classify(row["website"])[0] == "link" and grader.classify(L["website"])[0] != "link":
                    upd["website"] = L["website"]
            if "website" in upd:
                upd["domain"] = site_key(upd["website"])
                upd["grade_status"] = "pending"
            if pk and not row["phone_key"]:
                upd["phone_key"] = pk
            old_soc = json.loads(row["socials"] or "{}")
            merged = {**socials, **old_soc}
            if merged != old_soc:
                upd["socials"] = json.dumps(merged)
            if upd:
                upd["updated_at"] = now
                conn.execute(f"UPDATE leads SET {', '.join(k + '=?' for k in upd)} WHERE id=?", [*upd.values(), row["id"]])
            lid, new = row["id"], False
        else:
            cols = ["key"] + FIELDS + ["domain", "phone_key", "socials", "created_at", "updated_at"]
            vals = [L["key"]] + [L.get(f) for f in FIELDS] + [dom, pk, json.dumps(socials), now, now]
            vals[cols.index("closed")] = 1 if L.get("closed") else 0
            cur = conn.execute(f"INSERT INTO leads({','.join(cols)}) VALUES({','.join('?' * len(cols))})", vals)
            lid, new = cur.lastrowid, True
        if search_id:
            conn.execute("INSERT OR IGNORE INTO lead_searches VALUES(?,?)", (lid, search_id))
        conn.commit()
    return lid, new


def get_lead(conn, lid):
    r = conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    for k, default in (("socials", {}), ("issues", []), ("grade", None), ("psi", None)):
        try:
            d[k] = json.loads(d[k]) if d[k] else default
        except ValueError:
            d[k] = default
    d["bucket"] = d["bucket"] or ("pending" if d["grade_status"] in ("pending", "running") else "unknown")
    d["searches"] = [dict(x) for x in conn.execute(
        "SELECT s.id, s.category_label, s.location, s.source FROM searches s JOIN lead_searches ls ON ls.search_id=s.id WHERE ls.lead_id=?", (lid,))]
    d["shot"] = os.path.exists(os.path.join(SHOTS, f"{lid}.jpg"))
    return d


def save_grade(conn, lid, res, bucket, score, issues, headline, opp, email=None, socials=None):
    with lock:
        upd = {"grade_status": "done", "bucket": bucket, "score": score, "issues": json.dumps(issues), "headline": headline,
               "opportunity": opp, "grade": json.dumps(res), "graded_at": time.time()}
        row = conn.execute("SELECT email, socials FROM leads WHERE id=?", (lid,)).fetchone()
        if email and not row["email"]:
            upd["email"] = email
        if socials:
            upd["socials"] = json.dumps({**socials, **json.loads(row["socials"] or "{}")})
        conn.execute(f"UPDATE leads SET {', '.join(k + '=?' for k in upd)} WHERE id=?", [*upd.values(), lid])
        conn.commit()


def set_fields(conn, lid, **kw):
    with lock:
        conn.execute(f"UPDATE leads SET {', '.join(k + '=?' for k in kw)} WHERE id=?", [*kw.values(), lid])
        conn.commit()


# ------------------------------------------------------------------ querying
SORTS = {
    "opportunity": "opportunity DESC NULLS LAST, COALESCE(reviews,0) DESC, name",
    "reviews": "COALESCE(reviews,-1) DESC, opportunity DESC",
    "score": "CASE WHEN score IS NULL THEN -1 ELSE score END ASC, opportunity DESC",
    "name": "name COLLATE NOCASE",
    "newest": "created_at DESC",
    "updated": "COALESCE(status_at, 0) DESC, created_at DESC",
    "followup": "follow_up_at ASC",
}
BUCKET_SQL = "COALESCE(bucket, CASE WHEN grade_status IN ('pending','running') THEN 'pending' ELSE 'unknown' END)"


def _where(p, skip=None):
    w, a = ["1=1"], []
    if skip != "bucket" and p.get("bucket"):
        bs = [b for b in p["bucket"].split(",") if b]
        w.append(f"{BUCKET_SQL} IN ({','.join('?' * len(bs))})")
        a += bs
    for f in ("country", "category", "status", "source"):
        if skip != f and p.get(f):
            w.append(f"{f}=?")
            a.append(p[f])
    if skip != "bucket" and p.get("hide_bucket"):  # statuses the user switched off to cut clutter
        hs = [b for b in p["hide_bucket"].split(",") if b]
        w.append(f"{BUCKET_SQL} NOT IN ({','.join('?' * len(hs))})")
        a += hs
    if skip != "status" and p.get("hide_worked") == "1":  # only leads nobody has contacted yet
        w.append("status IN ('new','shortlisted')")
    if p.get("q"):
        like = f"%{p['q'].strip()}%"
        w.append("(name LIKE ? OR address LIKE ? OR website LIKE ? OR notes LIKE ? OR city LIKE ? OR phone LIKE ?)")
        a += [like] * 6
    if p.get("has_phone") == "1":
        w.append("COALESCE(phone,'')<>''")
    if p.get("has_email") == "1":
        w.append("COALESCE(email,'')<>''")
    if p.get("min_reviews"):
        w.append("COALESCE(reviews,0)>=?")
        a.append(int(p["min_reviews"]))
    if p.get("search"):
        w.append("id IN (SELECT lead_id FROM lead_searches WHERE search_id=?)")
        a.append(int(p["search"]))
    if p.get("show_closed") != "1":
        w.append("closed=0")
    if p.get("followups") == "1":
        w.append("follow_up_at IS NOT NULL AND status IN ('contacted','demo_sent','replied')")
    if p.get("area"):
        w.append("id IN (SELECT ls.lead_id FROM lead_searches ls JOIN searches s ON s.id=ls.search_id WHERE s.location=?)")
        a.append(p["area"])
    w.append("hidden_at IS NULL")
    return " AND ".join(w), a


LIST_COLS = f"""id, name, category, city, country, address, phone, email, website, rating, reviews, {BUCKET_SQL} AS bucket,
    score, opportunity, headline, status, closed, source, follow_up_at, skip_until, gmaps_url, osm_url, lat, lon,
    site_via, google_check, guessed_at"""


def query_leads(conn, p, limit=100, offset=0):
    w, a = _where(p)
    order = SORTS.get(p.get("sort") or "opportunity", SORTS["opportunity"])
    rows = [dict(r) for r in conn.execute(f"SELECT {LIST_COLS} FROM leads WHERE {w} ORDER BY {order} LIMIT ? OFFSET ?", a + [limit, offset])]
    total = conn.execute(f"SELECT COUNT(*) FROM leads WHERE {w}", a).fetchone()[0]
    return rows, total


def facets(conn, p):
    out = {}
    w, a = _where(p, skip="bucket")
    out["buckets"] = {r[0]: r[1] for r in conn.execute(f"SELECT {BUCKET_SQL}, COUNT(*) FROM leads WHERE {w} GROUP BY 1", a)}
    for f in ("country", "category", "status", "source"):
        w, a = _where(p, skip=f)
        out[f] = [{"v": r[0], "n": r[1]} for r in conn.execute(
            f"SELECT {f}, COUNT(*) FROM leads WHERE {w} AND COALESCE({f},'')<>'' GROUP BY 1 ORDER BY 2 DESC", a)]
    out["total_all"] = conn.execute("SELECT COUNT(*) FROM leads WHERE hidden_at IS NULL").fetchone()[0]
    return out


# ------------------------------------------------------------------ searches
def add_search(conn, **kw):
    kw.setdefault("created_at", time.time())
    with lock:
        cur = conn.execute(f"INSERT INTO searches({','.join(kw)}) VALUES({','.join('?' * len(kw))})", list(kw.values()))
        conn.commit()
        return cur.lastrowid


def update_search(conn, sid, **kw):
    with lock:
        conn.execute(f"UPDATE searches SET {', '.join(k + '=?' for k in kw)} WHERE id=?", [*kw.values(), sid])
        conn.commit()


def list_searches(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM searches ORDER BY id DESC LIMIT 500")]


def delete_search(conn, sid, with_leads=False):
    with lock:
        if with_leads:  # only leads that no other search found, and that you haven't started working
            conn.execute("""DELETE FROM leads WHERE status='new' AND COALESCE(notes,'')='' AND id IN
                (SELECT lead_id FROM lead_searches WHERE search_id=?) AND id NOT IN
                (SELECT lead_id FROM lead_searches WHERE search_id<>?)""", (sid, sid))
            conn.execute("DELETE FROM lead_searches WHERE lead_id NOT IN (SELECT id FROM leads)")
        conn.execute("DELETE FROM lead_searches WHERE search_id=?", (sid,))
        conn.execute("DELETE FROM searches WHERE id=?", (sid,))
        conn.commit()


def _month():
    return time.strftime("%Y-%m", time.gmtime())


def add_calls(conn, provider, n=1):
    with lock:
        conn.execute("""INSERT INTO api_usage(provider, month, calls) VALUES(?, ?, ?)
                        ON CONFLICT(provider, month) DO UPDATE SET calls = calls + ?""", (provider, _month(), n, n))
        conn.commit()


def calls_this_month(conn, provider):
    r = conn.execute("SELECT calls FROM api_usage WHERE provider=? AND month=?", (provider, _month())).fetchone()
    return r[0] if r else 0


def stats(conn):
    r = conn.execute("SELECT COUNT(*) total, SUM(grade_status IN ('pending','running')) pending FROM leads WHERE hidden_at IS NULL").fetchone()
    due = conn.execute("""SELECT COUNT(*) FROM leads WHERE hidden_at IS NULL AND follow_up_at <= ?
                          AND status IN ('contacted','demo_sent','replied')""", (end_of_today(),)).fetchone()[0]
    return {"leads": r["total"] or 0, "pending": r["pending"] or 0, "followups_due": due}


def end_of_today():
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 23, 59, 59, 0, 0, -1))


QUEUE_WHERE = """hidden_at IS NULL AND closed=0 AND status IN ('new','shortlisted')
    AND bucket IS NOT NULL AND bucket NOT IN ('ok','unknown') AND COALESCE(skip_until,0) < ?"""


def next_up(conn, area=None, limit=10):
    """Today's queue: follow-ups due first, then the strongest leads not yet contacted or skipped today."""
    now = time.time()
    extra, args = "", []
    if area:
        extra = " AND id IN (SELECT ls.lead_id FROM lead_searches ls JOIN searches s ON s.id=ls.search_id WHERE s.location=?)"
        args = [area]
    due = [dict(r) for r in conn.execute(f"""SELECT {LIST_COLS} FROM leads WHERE hidden_at IS NULL AND follow_up_at <= ?
        AND status IN ('contacted','demo_sent','replied'){extra} ORDER BY follow_up_at LIMIT 20""", [end_of_today()] + args)]
    q = [dict(r) for r in conn.execute(f"""SELECT {LIST_COLS} FROM leads WHERE {QUEUE_WHERE}{extra}
        ORDER BY status='shortlisted' DESC, opportunity DESC, COALESCE(reviews,0) DESC, id LIMIT ?""", [now] + args + [limit])]
    ready = conn.execute(f"SELECT COUNT(*) FROM leads WHERE {QUEUE_WHERE}{extra}", [now] + args).fetchone()[0]
    return {"followups": due, "queue": q, "ready": ready}


def dye_cuts(conn):
    """Lead-strength steps are relative to the leads actually waiting to be contacted: the top fifth of the
    distinct scores in the pool is the deepest dye, and so on. Equal scores always share a step."""
    # Graded over the distinct scores present, so a thousand identical scores can't flatten every step into one.
    vals = sorted({r[0] for r in conn.execute(f"SELECT opportunity FROM leads WHERE {QUEUE_WHERE} AND opportunity IS NOT NULL",
                                               (time.time(),))}, reverse=True)
    if len(vals) < 5:
        return (vals + [0] * 4)[:4] if vals else [70, 60, 48, 35]
    return [vals[int(len(vals) * q) - 1] for q in (0.2, 0.4, 0.6, 0.8)]


def areas(conn):
    return [{"v": r[0], "n": r[1]} for r in conn.execute("""SELECT s.location, COUNT(DISTINCT ls.lead_id) FROM searches s
        JOIN lead_searches ls ON ls.search_id=s.id JOIN leads l ON l.id=ls.lead_id
        WHERE s.source<>'csv' AND l.hidden_at IS NULL GROUP BY s.location ORDER BY 2 DESC""")]


# ------------------------------------------------------------------ website finder
NEEDS_GUESS = "hidden_at IS NULL AND bucket='none' AND COALESCE(website,'')='' AND guessed_at IS NULL AND source<>'google'"
NEEDS_GOOGLE = "hidden_at IS NULL AND bucket='none' AND COALESCE(website,'')='' AND google_check IS NULL AND source<>'google'"


def lookup_ids(conn):
    """Leads still marked 'No website' that haven't had their likely web addresses tried yet."""
    return [r[0] for r in conn.execute(f"SELECT id FROM leads WHERE {NEEDS_GUESS} ORDER BY opportunity DESC, id")]


def google_queue(conn, limit):
    """The next batch for the Google profile check: name already tried, strongest first, one country per batch."""
    w = f"{NEEDS_GOOGLE} AND guessed_at IS NOT NULL AND closed=0"
    top = conn.execute(f"SELECT country FROM leads WHERE {w} ORDER BY opportunity DESC LIMIT 1").fetchone()
    if not top:
        return []
    rows = conn.execute(f"SELECT id FROM leads WHERE {w} AND COALESCE(country,'')=? ORDER BY opportunity DESC, id LIMIT ?",
                        (top[0] or "", limit)).fetchall()
    return [get_lead(conn, r[0]) for r in rows]


def lookup_counts(conn):
    r = conn.execute(f"""SELECT SUM({NEEDS_GUESS}), SUM({NEEDS_GOOGLE}),
        SUM(site_via='guess'), SUM(site_via='google'), SUM(google_check='no_site') FROM leads""").fetchone()
    return {"to_guess": r[0] or 0, "to_google": r[1] or 0, "found_guess": r[2] or 0, "found_google": r[3] or 0,
            "google_no_site": r[4] or 0}
