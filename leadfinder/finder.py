"""Looks for a website when the listing didn't have one.

OpenStreetMap and TomTom often leave the website out even when the business has one, so before a lead is
called "No website" we look for it two ways:

1. Free, no key: guess the obvious domains from the business name (cbwplumbing.co.uk, ...) and only accept one
   whose page shows the business's phone number, or its name together with its town or postcode.
2. With an Apify token (apify.com, $5 of free credit a month, no card): look the business up on Google Maps with
   Apify's Google Maps Scraper and take the website from its Google Business Profile. This also gives its rating,
   review count and exact profile link. Lookups go in batches, one Google listing per business, about $0.004 each.
"""
import json
import math
import re
import socket
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from . import net

APIFY = "https://api.apify.com/v2"
ACTOR = "compass~crawler-google-places"  # Apify's own Google Maps Scraper
APIFY_FREE_USD = 5.0
BATCH = 40

LEGAL = {"ltd", "limited", "llp", "plc", "llc", "inc", "co", "company", "nig", "nigeria", "uk", "gb", "the"}
FILLER = {"and", "of", "services", "service", "solutions", "enterprises", "enterprise", "international", "global", "group"}
TLDS = {"GB": [".co.uk", ".com", ".uk"], "NG": [".com.ng", ".ng", ".com"], "US": [".com", ".net"]}
POSTCODE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b", re.I)
PHONEISH = re.compile(r"(?:\+|\b)[\d][\d\s().\-]{7,18}\d")


def _ascii(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def words(name):
    s = _ascii(name).replace("&", " and ").replace("'", "").replace("’", "")
    return [w for w in re.split(r"[^a-z0-9]+", s) if w]


def compact(s):
    return re.sub(r"[^a-z0-9]", "", _ascii(s).replace("&", "and"))


def core_name(name):
    """The distinctive part of the name: 'CBW Plumbing and Heating Ltd' -> 'cbwplumbingheating'."""
    return "".join(w for w in words(name) if w not in LEGAL and w not in FILLER)


def candidates(name, country):
    w = words(name)
    keep = [x for x in w if x not in LEGAL]
    core = [x for x in keep if x not in FILLER]
    slugs = []
    for parts in (keep, core, core[:2] if len(core) >= 3 else [], w):
        s = "".join(parts)
        if 5 <= len(s) <= 40 and s not in slugs:
            slugs.append(s)
    if len(core) >= 2 and "-".join(core) not in slugs:
        slugs.append("-".join(core))
    hosts = []
    for s in slugs[:4]:
        for t in TLDS.get(country or "", [".com"]):
            hosts.append(s + t)
    return hosts


def _resolves(host):
    try:
        socket.getaddrinfo(host, 80, proto=socket.IPPROTO_TCP)
        return True
    except OSError:
        return False


def _text(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def _title(html):
    bits = re.findall(r"(?is)<title[^>]*>(.*?)</title>", html or "")[:1]
    bits += re.findall(r'(?i)<meta[^>]+property=["\']og:(?:site_name|title)["\'][^>]+content=["\']([^"\']+)', html or "")
    bits += re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html or "")[:2]
    return " ".join(_text(b) for b in bits)


def phone_tail(p):
    d = re.sub(r"\D", "", p or "")
    return d[-9:] if len(d) >= 9 else ""


def has_phone(text, tail):
    return bool(tail) and any(re.sub(r"\D", "", m).endswith(tail) for m in PHONEISH.findall(text))


def other_phones(text, tail):
    """The page lists phone numbers and none of them is theirs: it's another business (e.g. a roofer who bought
    portsmouthroofingsolutions.com for the keywords)."""
    if not tail:
        return False
    nums = [re.sub(r"\D", "", m) for m in PHONEISH.findall(text) if m.strip()[:1] in "+0"]
    nums = [n for n in nums if 10 <= len(n) <= 13]
    return bool(nums) and not any(n.endswith(tail) for n in nums)


def places(L):
    """Town and postcode words that should appear on their own site."""
    out = [compact(L.get("city"))]
    m = POSTCODE.search(L.get("address") or "")
    if m:
        out.append(compact(m.group(1) + m.group(2)))
        out.append(compact(m.group(1)))
    return [x for x in out if len(x) >= 3]


def verify(L, page):
    """Why this page is the business's own site ('phone' or 'name and town'), or '' if we can't be sure."""
    html = page.get("html") or ""
    if not html or (page.get("status") or 0) >= 400:
        return ""
    text = _text(html)
    if has_phone(text, phone_tail(L.get("phone"))):
        return "phone"
    if other_phones(text, phone_tail(L.get("phone"))):
        return ""
    head, body = compact(_title(html)), compact(text)
    if name_in(L, head) and any(p in body for p in places(L)):
        return "name and town"
    return ""


def name_in(L, head):
    """Their full name is in the page's title, site name or main heading."""
    core = core_name(L.get("name"))
    return len(core) >= 6 and core in head


def guess(L, log=None):
    """Try the obvious domains. Returns {'url', 'evidence'} or None."""
    hosts = candidates(L.get("name"), L.get("country"))
    if not hosts:
        return None
    with ThreadPoolExecutor(max_workers=6) as ex:
        live = [h for h, ok in zip(hosts, ex.map(_resolves, hosts)) if ok]
    for h in live:
        page = net.get_page(f"https://{h}/", timeout=12, max_bytes=800_000)
        if page.get("error") and not page.get("html"):
            page = net.get_page(f"http://{h}/", timeout=12, max_bytes=800_000)
        why = verify(L, page)
        if not why and page.get("html") and name_in(L, compact(_title(page["html"]))):
            # Their name is on it but the phone or town isn't on the home page: many small sites keep those on the contact page.
            for path in ("contact", "contact-us"):
                sub = net.get_page(urllib.parse.urljoin(page["final_url"], path), timeout=10, max_bytes=500_000)
                if (sub.get("status") or 0) >= 400:
                    continue
                t = compact(_text(sub.get("html")))
                tail = phone_tail(L.get("phone"))
                if has_phone(_text(sub.get("html")), tail):
                    why = "phone"
                elif other_phones(_text(sub.get("html")), tail) or other_phones(_text(page["html"]), tail):
                    break
                elif any(p in t for p in places(L)):
                    why = "name and town"
                if why:
                    break
        if why:
            return {"url": page.get("final_url") or f"https://{h}/", "evidence": why}
    return None


# ------------------------------------------------------------------ Google Maps via Apify
def _dist_m(a, b, c, d):
    if None in (a, b, c, d):
        return None
    p = math.pi / 180
    x = (d - b) * p * math.cos((a + c) * p / 2)
    return 6371000 * math.hypot(x, (c - a) * p)


def _similar(a, b):
    ca, cb = core_name(a), core_name(b)
    if ca and cb and (ca in cb or cb in ca):
        return True
    wa = {w for w in words(a) if w not in LEGAL and w not in FILLER}
    wb = {w for w in words(b) if w not in LEGAL and w not in FILLER}
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= 0.5


def match_place(L, results):
    """The Google listing that is this business: a similar name plus the same phone, map spot, postcode or town."""
    tail = phone_tail(L.get("phone"))
    for r in results:
        if not _similar(L.get("name"), r.get("title")):
            continue
        if tail and phone_tail(r.get("phone")) == tail:
            return r
        dist = _dist_m(L.get("lat"), L.get("lon"), r.get("lat"), r.get("lon"))
        if dist is not None and dist < 600:
            return r
        pc = POSTCODE.search(L.get("address") or "")
        if pc and compact(pc.group(0)) in compact(r.get("address")):
            return r
        if dist is None and compact(L.get("city")) and compact(L.get("city")) in compact(r.get("address")):
            return r
    return None


def search_text(L):
    return ", ".join(x for x in (L.get("name"), L.get("address") or L.get("city")) if x)


def _place(item):
    """Apify's result in the shape match_place and the engine use."""
    loc = item.get("location") or {}
    pid = item.get("placeId") or ""
    return {"title": item.get("title") or "", "address": item.get("address") or "", "website": item.get("website") or "",
            "phone": item.get("phoneUnformatted") or item.get("phone") or "", "lat": loc.get("lat"), "lon": loc.get("lng"),
            "rating": item.get("totalScore"), "reviews": item.get("reviewsCount"),
            "closed": bool(item.get("permanentlyClosed")),
            "url": f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else (item.get("url") or ""),
            "search": item.get("searchString") or ""}


class ApifyError(RuntimeError):
    pass


def _apify(path, token, data=None, timeout=60):
    try:
        return net.api_json(APIFY + path, data=data, timeout=timeout, retries=1,
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    except net.ApiError as e:
        body = (e.body or "").lower()
        if e.code == 401:
            raise ApifyError("Apify refused the token. Copy your API token again from Apify (Settings > API & Integrations).")
        if e.code in (402, 403) and ("limit" in body or "usage" in body or "credit" in body or "payment" in body):
            raise ApifyError("Your free Apify credit for this month is used up. Lookups start again next month.")
        raise ApifyError(f"Apify error {e.code}: {(e.body or '')[:160]}")


def apify_usage(token):
    """(used, limit) in US dollars this month, or None if Apify doesn't say."""
    try:
        d = _apify("/users/me/limits", token, timeout=20).get("data") or {}
        return (d.get("current") or {}).get("monthlyUsageUsd"), (d.get("limits") or {}).get("maxMonthlyUsageUsd")
    except Exception:
        return None


def google_lookup_batch(token, leads, log=None):
    """Look a batch of leads (same country) up on Google Maps. Returns {lead id: place or None}.
    None means Google Maps had no listing that matches them."""
    texts = {}
    for L in leads:
        texts.setdefault(search_text(L), []).append(L)
    body = {"searchStringsArray": list(texts), "maxCrawledPlacesPerSearch": 1, "language": "en",
            "scrapePlaceDetailPage": False, "scrapeContacts": False, "maxImages": 0, "maxReviews": 0, "maxQuestions": 0}
    cc = (leads[0].get("country") or "").upper()
    if cc:
        body["countryCode"] = "gb" if cc == "GB" else cc.lower()
    # maxItems caps what Apify can charge for this run: one listing per business.
    run = _apify(f"/acts/{ACTOR}/runs?maxItems={len(texts)}", token, data=json.dumps(body)).get("data") or {}
    rid, ds = run.get("id"), run.get("defaultDatasetId")
    if not rid:
        raise ApifyError("Apify didn't start the lookup.")
    started = time.time()
    status = run.get("status")
    while status in ("READY", "RUNNING", None):
        if time.time() - started > 1800:
            raise ApifyError("The Apify lookup took over 30 minutes; it will be retried.")
        time.sleep(10)
        status = (_apify(f"/actor-runs/{rid}", token, timeout=30).get("data") or {}).get("status")
        if log:
            log(f"Checking {len(leads)} businesses on Google Maps via Apify ({int(time.time() - started)}s)")
    items = net.api_json(f"{APIFY}/datasets/{ds}/items?clean=true&format=json", timeout=60,
                         headers={"Authorization": f"Bearer {token}"}) if ds else []
    if status != "SUCCEEDED" and not items:
        raise ApifyError(f"The Apify lookup ended with status {status}. If your free credit is used up, it resets next month.")
    found = {}
    for it in items or []:
        pl = _place(it)
        found.setdefault(pl["search"], []).append(pl)
    out = {}
    for text, group in texts.items():
        cands = found.get(text) or [pl for pls in found.values() for pl in pls if compact(pl["search"]) == compact(text)]
        for L in group:
            out[L["id"]] = match_place(L, cands)
    if status != "SUCCEEDED":  # stopped part-way (e.g. out of credit): only trust leads that got a result
        out = {k: v for k, v in out.items() if v}
    return out
