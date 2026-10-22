"""URL helpers shared by the grader and the database."""
import re
import urllib.parse


def normalize(url):
    """Turn whatever a listing has ('www.x.com', 'x.com/home; y.com') into a fetchable URL, or ''."""
    s = (url or "").strip().split(";")[0].split(" ")[0].strip()
    if not s:
        return ""
    if s.startswith("//"):
        s = "http:" + s
    if not re.match(r"^[a-z][a-z0-9+.-]*://", s, re.I):
        s = "http://" + s
    p = urllib.parse.urlsplit(s)
    if p.scheme.lower() not in ("http", "https"):
        return ""
    host = (p.hostname or "").lower().rstrip(".")
    if not host or "." not in host:
        return ""
    netloc = host + (f":{p.port}" if p.port else "")
    return urllib.parse.urlunsplit((p.scheme.lower(), netloc, p.path or "/", p.query, ""))


def host(url):
    return (urllib.parse.urlsplit(normalize(url)).hostname or "").lower()


def bare(h):
    return h[4:] if h.startswith("www.") else h


def match(h, suffix):
    return h == suffix or h.endswith("." + suffix)


def toggle_www(url):
    p = urllib.parse.urlsplit(url)
    h = p.hostname or ""
    nh = h[4:] if h.startswith("www.") else "www." + h
    return urllib.parse.urlunsplit((p.scheme, nh, p.path, p.query, ""))


def with_scheme(url, scheme):
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((scheme, p.hostname or "", p.path or "/", p.query, ""))
