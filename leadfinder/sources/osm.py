"""OpenStreetMap via the free Overpass API. No key needed.

Good coverage in UK/US cities, patchier in Nigeria. A missing website tag on OSM doesn't always mean the business
has no website, so "No website" leads from here are worth a quick Google check before you pitch.
"""
import re
import time
import urllib.parse

from .. import net

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def build_query(filters, geo):
    if geo.get("area_id"):
        head, scope = f'area(id:{geo["area_id"]})->.a;', "(area.a)"
    else:
        head, scope = "", "({},{},{},{})".format(*geo["bbox"])
    body = "".join(f"nwr{f}{scope};" for f in filters)
    return f"[out:json][timeout:150];{head}({body});out center tags 4000;"


def _first(t, *keys):
    for k in keys:
        if t.get(k):
            return t[k].split(";")[0].strip()
    return ""


def _address(t):
    street = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street")) if x)
    parts = [t.get("addr:unit"), street, t.get("addr:suburb") or t.get("addr:district"), t.get("addr:city") or t.get("addr:town"), t.get("addr:postcode")]
    return ", ".join(p for p in parts if p)


NOMINATIM = "https://nominatim.openstreetmap.org/search?"
TAG_RX = re.compile(r'^\["([^"]+)"="([^"]+)"\]$')
_health = {}  # endpoint -> (alive, checked_at)


def _alive(ep):
    ok, at = _health.get(ep, (None, 0))
    if ok is not None and time.time() - at < 300:
        return ok
    try:
        net.api(ep.replace("/interpreter", "/status"), timeout=8, retries=0)
        ok = True
    except net.ApiError:
        ok = True  # it answered, just not with 200; the server is up
    except Exception:
        ok = False
    _health[ep] = (ok, time.time())
    return ok


def _overpass(filters, geo, log):
    q = build_query(filters, geo)
    live = [ep for ep in ENDPOINTS if _alive(ep)]
    if not live:
        raise ConnectionError("no Overpass server is answering")
    last = None
    for attempt, ep in enumerate(live * 2):
        log(f"Searching OpenStreetMap ({ep.split('/')[2]}). Busy servers can take a minute or two")
        try:
            data = net.api_json(ep, data=urllib.parse.urlencode({"data": q}), timeout=150, retries=0,
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
        except net.ApiError as e:
            last = e
            if e.code == 400:
                raise RuntimeError("OpenStreetMap rejected the search. Try a simpler business type.")
            if e.code in (429, 502, 503, 504):  # rate limited or overloaded: wait for a free slot
                log("OpenStreetMap server is busy, waiting for a free slot")
                time.sleep(15)
            continue
        except Exception as e:
            last = e
            _health[ep] = (False, time.time())
            continue
        remark = (data.get("remark") or "").lower()
        if "timed out" in remark or "out of memory" in remark:
            raise RuntimeError("That area is too big for one OpenStreetMap search. Try a smaller city or a neighbourhood.")
        return data.get("elements", [])
    raise ConnectionError(f"Overpass servers busy ({last})")


def _nominatim(filters, geo, log):
    """Fallback when Overpass is down: ask Nominatim for each map tag inside the area, 40 at a time.
    Only works for plain tag filters like ["craft"="plumber"], not name patterns."""
    tags = [m.groups() for m in (TAG_RX.match(f) for f in filters) if m]
    if not tags:
        raise RuntimeError("OpenStreetMap's main search servers are busy, and this business type can only be found by name, "
                           "which needs them. Try again later, pick a standard type (e.g. Plumbers, Dentists), or use Google.")
    s, w, n, e = geo["bbox"]
    found = {}
    for k, v in tags:
        seen = []
        for page in range(12):
            log(f"Searching OpenStreetMap via Nominatim: {k}={v}, {len(found)} found")
            p = {"q": f"[{k}={v}]", "format": "jsonv2", "limit": 40, "extratags": 1, "addressdetails": 1,
                 "viewbox": f"{w},{n},{e},{s}", "bounded": 1}
            if seen:
                p["exclude_place_ids"] = ",".join(map(str, seen))
            arr = net.api_json(NOMINATIM + urllib.parse.urlencode(p), timeout=40)
            new = [x for x in arr if x["place_id"] not in seen]
            for x in new:
                seen.append(x["place_id"])
                found[(x["osm_type"], x["osm_id"])] = x
            if len(arr) < 40 or not new:
                break
    elements = []
    for (otype, oid), x in found.items():
        a = x.get("address") or {}
        tags = dict(x.get("extratags") or {})
        tags["name"] = x.get("name") or ""
        for src, dst in (("house_number", "addr:housenumber"), ("road", "addr:street"), ("suburb", "addr:suburb"),
                         ("postcode", "addr:postcode")):
            if a.get(src):
                tags.setdefault(dst, a[src])
        city = a.get("city") or a.get("town") or a.get("village")
        if city:
            tags.setdefault("addr:city", city)
        elements.append({"type": otype, "id": oid, "lat": float(x["lat"]), "lon": float(x["lon"]), "tags": tags})
    return elements


def search(filters, geo, log=lambda m: None):
    try:
        elements = _overpass(filters, geo, log)
    except ConnectionError:
        elements = _nominatim(filters, geo, log)
    return [lead for lead in map(_to_lead, elements) if lead]


def _to_lead(el):
    t = el.get("tags") or {}
    nm = t.get("name") or t.get("name:en")
    if not nm:
        return None
    if t.get("brand") or t.get("brand:wikidata") or t.get("operator:wikidata"):
        return None  # chains (Tesco, KFC, Shoprite branches) aren't prospects
    if any(k.startswith(("disused:", "abandoned:", "was:")) for k in t) or t.get("disused") == "yes":
        return None
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lon = el.get("lon") or (el.get("center") or {}).get("lon")
    addr = _address(t)
    city = t.get("addr:city") or t.get("addr:town") or t.get("addr:suburb") or ""
    socials = {k: v for k, v in (("facebook", _first(t, "contact:facebook", "facebook")),
                                 ("instagram", _first(t, "contact:instagram", "instagram")),
                                 ("tiktok", _first(t, "contact:tiktok"))) if v}
    for k, v in list(socials.items()):  # OSM sometimes stores just a handle
        if not v.startswith("http"):
            socials[k] = {"facebook": "https://facebook.com/", "instagram": "https://instagram.com/", "tiktok": "https://tiktok.com/@"}[k] + v.lstrip("@")
    gq = urllib.parse.quote_plus(" ".join(x for x in (nm, addr, city) if x))
    return {
        "key": f"o:{el['type']}/{el['id']}", "source": "osm", "name": nm.strip(), "address": addr, "city": city,
        "lat": lat, "lon": lon,
        "phone": _first(t, "phone", "contact:phone", "contact:mobile", "mobile"),
        "email": _first(t, "email", "contact:email"),
        "website": _first(t, "website", "contact:website", "url"),
        "socials": socials,
        "gmaps_url": f"https://www.google.com/maps/search/?api=1&query={gq}",
        "osm_url": f"https://www.openstreetmap.org/{el['type']}/{el['id']}",
        "rating": None, "reviews": None, "closed": 0,
    }
