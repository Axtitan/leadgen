"""Turns 'Lekki, Lagos' or 'Leeds' into a search area using OpenStreetMap's free Nominatim service (cached)."""
import json
import time
import urllib.parse

from . import db, net


def geocode(q):
    key = " ".join(q.lower().split())
    conn = db.connect()
    try:
        hit = conn.execute("SELECT data FROM geocache WHERE q=?", (key,)).fetchone()
        if hit:
            return json.loads(hit[0])
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {"q": q, "format": "jsonv2", "limit": 5, "addressdetails": 1})
        arr = net.api_json(url, timeout=30)
        if not arr:
            return None
        # Prefer an actual boundary (city, district, neighbourhood) over a single point such as a city-centre marker.
        places = ("city", "town", "village", "suburb", "city_district", "borough", "quarter", "neighbourhood", "municipality",
                  "county", "state", "state_district", "district", "hamlet", "region", "province")
        g = (next((x for x in arr[:3] if x.get("osm_type") == "relation" and x.get("addresstype") in places), None)
             or next((x for x in arr if x.get("addresstype") in places), None) or arr[0])
        s, n, w, e = map(float, g["boundingbox"])
        # A street or a single point gives a tiny box; widen it to roughly 5 km so there is something to search.
        if n - s < 0.045:
            m = (n + s) / 2
            s, n = m - 0.0225, m + 0.0225
        if e - w < 0.07:
            m = (e + w) / 2
            w, e = m - 0.035, m + 0.035
        area_id = None
        if g.get("osm_type") == "relation":
            area_id = 3600000000 + int(g["osm_id"])
        addr = g.get("address") or {}
        city = (addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or addr.get("municipality")
                or addr.get("county") or addr.get("state") or q.split(",")[0].strip())
        cc = (addr.get("country_code") or "").upper()
        out = {"display": g.get("display_name", q), "lat": float(g["lat"]), "lon": float(g["lon"]), "bbox": [s, w, n, e],
               "country": "GB" if cc == "UK" else cc, "city": city, "area_id": area_id, "type": g.get("addresstype")}
        with db.lock:
            conn.execute("INSERT OR REPLACE INTO geocache VALUES(?,?,?)", (key, json.dumps(out), time.time()))
            conn.commit()
        return out
    finally:
        conn.close()
