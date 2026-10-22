"""TomTom Search API. Free key, no card: about 2,500 requests a month (TomTom pricing page, Oct 2026).

Each request returns up to 100 businesses with name, phone, website and address (no ratings or reviews).
We try Category Search first (matches TomTom's own business categories), and fall back to POI Search
(matches names and categories as free text) when a term isn't one of TomTom's categories.
Once the monthly allowance is used up, TomTom refuses further requests until next month; it never charges.
"""
import json
import urllib.parse

from .. import net

BASE = "https://api.tomtom.com/search/2"
FREE_PER_MONTH = 2500
PAGE = 100
MAX_PER_TERM = 500  # at most 5 requests per search term


def _error(e):
    msg = ""
    try:
        body = json.loads(e.body)
        msg = body.get("errorText") or (body.get("detailedError") or {}).get("message") or body.get("error") or ""
    except Exception:
        msg = (e.body or "")[:200]
    if e.code == 403:
        return ("TomTom refused the request: " + (msg or "check your key") +
                ". If this says over the limit, your free monthly allowance is used up and resets next month.")
    if e.code in (401, 400) and "key" in msg.lower():
        return "TomTom says the API key isn't valid. Copy it again from your TomTom dashboard into Settings."
    return f"TomTom error {e.code}: {msg or e}"


def search(key, terms, geo, log=None, on_call=None):
    s, w, n, e = geo["bbox"]
    seen, calls = {}, 0
    for term in terms:
        for mode in ("categorySearch", "poiSearch"):
            got = 0
            ofs = 0
            while ofs < MAX_PER_TERM:
                params = {"key": key, "limit": PAGE, "ofs": ofs, "topLeft": f"{n},{w}", "btmRight": f"{s},{e}", "language": "en-GB"}
                if geo.get("country"):
                    params["countrySet"] = geo["country"]
                url = f"{BASE}/{mode}/{urllib.parse.quote(term)}.json?" + urllib.parse.urlencode(params)
                try:
                    data = net.api_json(url, timeout=30, retries=1)
                except net.ApiError as err:
                    calls += 1  # count it: TomTom may still bill rejected requests against the allowance
                    if on_call:
                        on_call()
                    if err.code == 400 and mode == "categorySearch":
                        break  # not a TomTom category word; try the name search instead
                    raise RuntimeError(_error(err))
                calls += 1
                if on_call:
                    on_call()
                results = [r for r in data.get("results", []) if r.get("type") == "POI"]
                for r in results:
                    seen[r["id"]] = r
                got += len(results)
                if log:
                    log(f"TomTom: {len(seen)} businesses so far ({calls} requests)")
                total = (data.get("summary") or {}).get("totalResults", 0)
                ofs += PAGE
                if not results or ofs >= total:
                    break
            if got:
                break  # the category search worked; no need for the name search
    leads = [lead for lead in map(_lead, seen.values()) if lead]
    return leads, calls


def _lead(r):
    poi = r.get("poi") or {}
    if poi.get("brands"):
        return None  # chains (Costa, Shoprite branches) aren't prospects
    name = (poi.get("name") or "").strip()
    if not name:
        return None
    a = r.get("address") or {}
    pos = r.get("position") or {}
    addr = a.get("freeformAddress") or ""
    city = a.get("municipality") or a.get("municipalitySubdivision") or ""
    cc = (a.get("countryCode") or "").upper()
    q = urllib.parse.quote_plus(f"{name} {addr or city}".strip())
    return {
        "key": f"t:{r['id']}", "source": "tomtom", "name": name, "address": addr, "city": city,
        "country": "GB" if cc == "UK" else cc, "lat": pos.get("lat"), "lon": pos.get("lon"),
        "phone": poi.get("phone") or "", "email": "", "website": poi.get("url") or "", "socials": {},
        "gmaps_url": f"https://www.google.com/maps/search/?api=1&query={q}", "osm_url": "",
        "rating": None, "reviews": None, "closed": 0,
    }
