"""Google Places API (New) text search. Needs your own API key (Settings tab).

This is the most accurate source for "no website", because owners manage their own Google listing.
Each request returns up to 20 businesses. Deeper searches split the area into a grid to get past Google's
60-results-per-search limit. Google's pricing has a monthly free allowance; check
https://developers.google.com/maps/billing-and-pricing/pricing for the current numbers.
"""
import json
import time

from .. import net

URL = "https://places.googleapis.com/v1/places:searchText"
FREE_PER_MONTH = 1000  # Text Search Enterprise free cap (Google pricing page, checked Oct 2026)
MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.websiteUri", "places.nationalPhoneNumber",
    "places.internationalPhoneNumber", "places.rating", "places.userRatingCount", "places.googleMapsUri",
    "places.businessStatus", "places.location", "places.addressComponents", "nextPageToken",
])


def tiles(bbox, n):
    s, w, nn, e = bbox
    dlat, dlon = (nn - s) / n, (e - w) / n
    for i in range(n):
        for j in range(n):
            yield s + i * dlat, w + j * dlon, s + (i + 1) * dlat, w + (j + 1) * dlon


def requests_estimate(depth):
    return depth * depth * 3  # worst case: every tile has 3 full pages


def _error(e):
    try:
        msg = json.loads(e.body)["error"]["message"]
    except Exception:
        msg = e.body[:300] or str(e)
    if e.code == 403:
        msg += " (Check that the Places API (New) is enabled for this key and billing is set up in Google Cloud.)"
    return f"Google said: {msg}"


def search(key, text, geo, depth=1, log=None, on_call=None):
    seen = {}
    calls = 0
    for (s, w, n, e) in tiles(geo["bbox"], max(1, int(depth))):
        token = None
        for _ in range(3):
            body = {"textQuery": text, "pageSize": 20,
                    "locationRestriction": {"rectangle": {"low": {"latitude": s, "longitude": w}, "high": {"latitude": n, "longitude": e}}}}
            if token:
                body["pageToken"] = token
            try:
                data = net.api_json(URL, data=body, method="POST", timeout=40,
                                    headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": MASK})
            except net.ApiError as err:
                raise RuntimeError(_error(err))
            calls += 1
            if on_call:
                on_call()
            for p in data.get("places", []):
                seen[p["id"]] = p
            if log:
                log(f"Google: {len(seen)} businesses so far ({calls} requests)")
            token = data.get("nextPageToken")
            if not token:
                break
            time.sleep(1.2)
    return [_lead(p) for p in seen.values()], calls


def _lead(p):
    comps = {}
    for c in p.get("addressComponents") or []:
        for ty in c.get("types", []):
            comps.setdefault(ty, c)
    city = (comps.get("locality") or comps.get("postal_town") or comps.get("sublocality") or comps.get("administrative_area_level_2") or {}).get("longText", "")
    country = (comps.get("country") or {}).get("shortText", "")
    loc = p.get("location") or {}
    return {
        "key": f"g:{p['id']}", "source": "google", "name": (p.get("displayName") or {}).get("text", "").strip(),
        "address": p.get("formattedAddress", ""), "city": city, "country": "GB" if country == "UK" else country,
        "lat": loc.get("latitude"), "lon": loc.get("longitude"),
        "phone": p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber") or "",
        "email": "", "website": p.get("websiteUri") or "", "socials": {},
        "gmaps_url": p.get("googleMapsUri") or "", "osm_url": "",
        "rating": p.get("rating"), "reviews": p.get("userRatingCount", 0),
        "closed": 1 if p.get("businessStatus") == "CLOSED_PERMANENTLY" else 0,
    }
