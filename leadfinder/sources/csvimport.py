"""Import a CSV from anywhere (Outscraper, Apify Google Maps scraper, a spreadsheet your partner made...).

Column names are matched loosely, so most exports work without editing.
"""
import csv
import hashlib
import io
import re

COLS = {
    "name": ["name", "business", "title", "business name", "business_name", "company", "company name", "place name", "place_name"],
    "website": ["website", "site", "url", "domain", "web", "website url", "website_url", "homepage"],
    "phone": ["phone", "phone number", "phone_number", "telephone", "tel", "mobile", "phone_1", "international phone", "phoneunformatted"],
    "email": ["email", "emails", "email_1", "e-mail", "email address"],
    "address": ["address", "full address", "full_address", "formatted address", "formatted_address", "street"],
    "city": ["city", "town", "locality"],
    "country": ["country", "country code", "country_code", "countrycode"],
    "category": ["category", "main category", "main_category", "categoryname", "type", "categories", "subtypes"],
    "rating": ["rating", "stars", "totalscore", "total score", "average rating"],
    "reviews": ["reviews", "review count", "review_count", "reviews_count", "reviewscount", "user ratings total", "user_ratings_total", "rating count", "number of reviews"],
    "gmaps_url": ["google maps", "google maps url", "google_maps_url", "maps url", "location link", "location_link", "place url", "place_url", "google maps link"],
}
COUNTRY_NAMES = {"united kingdom": "GB", "uk": "GB", "england": "GB", "scotland": "GB", "wales": "GB", "nigeria": "NG",
                 "united states": "US", "usa": "US", "united states of america": "US"}


def _norm(h):
    return re.sub(r"[\s_]+", " ", (h or "").strip().lower().lstrip("﻿"))


def parse(text, default_category="Imported", default_country=""):
    text = text.lstrip("﻿")
    try:
        dialect = csv.Sniffer().sniff(text[:4000], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if not rows:
        return [], "The file has no rows."
    headers = {_norm(h): h for h in rows[0].keys() if h}
    pick = {}
    for field, names in COLS.items():
        for n in names:
            if _norm(n) in headers:
                pick[field] = headers[_norm(n)]
                break
    if "name" not in pick:
        return [], "Couldn't find a business name column (looked for: name, title, business name, company)."
    leads = []
    for r in rows:
        g = {f: (r.get(col) or "").strip() for f, col in pick.items()}
        if not g.get("name"):
            continue
        site = g.get("website", "")
        gm = g.get("gmaps_url", "")
        if not gm and "google." in site and "/maps" in site:  # Apify puts the Maps link in "url"
            gm, site = site, ""
        c = g.get("country", "")
        c = COUNTRY_NAMES.get(c.lower(), c.upper() if len(c) == 2 else default_country)
        try:
            rating = float(g["rating"]) if g.get("rating") else None
        except ValueError:
            rating = None
        try:
            reviews = int(float(re.sub(r"[^\d.]", "", g["reviews"]))) if g.get("reviews") else None
        except ValueError:
            reviews = None
        ident = "|".join([g["name"].lower(), re.sub(r"\D", "", g.get("phone", ""))[-9:], site.lower(), g.get("address", "").lower()])
        leads.append({
            "key": "c:" + hashlib.sha1(ident.encode()).hexdigest()[:16], "source": "csv", "name": g["name"],
            "address": g.get("address", ""), "city": g.get("city", ""), "country": c, "lat": None, "lon": None,
            "phone": g.get("phone", ""), "email": (g.get("email", "").split(",")[0]).strip(), "website": site, "socials": {},
            "gmaps_url": gm, "osm_url": "", "rating": rating, "reviews": reviews, "closed": 0,
            "category": (g.get("category", "").split(",")[0]).strip() or default_category,
        })
    return leads, None
