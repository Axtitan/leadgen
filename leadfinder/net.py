"""HTTP helpers.

api() / api_json()  polite calls to data APIs (Nominatim, Overpass, Google)
get_page()          fetches a business website the way a visitor's browser would, and records what happened
"""
import gzip
import http.client
import json
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
TOOL_UA = "LeadFinder/1.0 (personal small-business lead research tool)"

# Minimum seconds between calls to the same host (Nominatim's usage policy asks for 1 request per second).
GAP = {"nominatim.openstreetmap.org": 1.1}
_last, _lock = {}, threading.Lock()


class ApiError(Exception):
    def __init__(self, code, url, body=""):
        super().__init__(f"HTTP {code} from {urllib.parse.urlparse(url).netloc}")
        self.code, self.body = code, body


def _polite(host):
    gap = GAP.get(host)
    if not gap:
        return
    with _lock:
        wait = _last.get(host, 0) + gap - time.time()
        _last[host] = max(time.time(), _last.get(host, 0) + gap)
    if wait > 0:
        time.sleep(wait)


def api(url, data=None, headers=None, timeout=60, retries=2, method=None):
    host = urllib.parse.urlparse(url).netloc
    h = {"User-Agent": TOOL_UA, "Accept": "application/json", "Accept-Language": "en"}
    h.update(headers or {})
    if data is not None and not isinstance(data, (bytes, str)):
        data = json.dumps(data)
        h.setdefault("Content-Type", "application/json")
    if isinstance(data, str):
        data = data.encode()
    for attempt in range(retries + 1):
        _polite(host)
        try:
            req = urllib.request.Request(url, data=data, headers=h, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:4000]
            except Exception:
                pass
            if e.code in (400, 401, 403, 404) or attempt == retries:
                raise ApiError(e.code, url, body)
            time.sleep(15 * (attempt + 1) if e.code in (429, 504) else 4 * (attempt + 1))
        except Exception:
            if attempt == retries:
                raise
            time.sleep(3 * (attempt + 1))


def api_json(url, **kw):
    return json.loads(api(url, **kw))


# ------------------------------------------------------------------ website fetching
def _ctx(verify):
    if not verify:
        return ssl._create_unverified_context()
    c = ssl.create_default_context()
    try:  # Windows only exposes the root certificates it has already needed; add the standard Mozilla list if available
        import certifi
        c.load_verify_locations(certifi.where())
    except Exception:
        pass
    # Python 3.13+ is stricter than browsers about some certificates; match browser behaviour.
    c.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
    return c


_OPENERS = {v: urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx(v))) for v in (True, False)}


def _kind(err):
    r = getattr(err, "reason", err)
    if isinstance(r, socket.gaierror):
        return "dns"
    if isinstance(r, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(r, ConnectionRefusedError):
        return "refused"
    if isinstance(r, (ConnectionResetError, ConnectionAbortedError, http.client.RemoteDisconnected)):
        return "reset"
    if isinstance(r, ssl.SSLError):
        return "ssl"
    s = str(r).lower()
    if "getaddrinfo" in s or "name or service" in s or "nodename" in s:
        return "dns"
    if "timed out" in s:
        return "timeout"
    return "other"


def _decode(raw, headers):
    enc = (headers.get("content-encoding") or "").lower()
    try:
        if "gzip" in enc:
            raw = gzip.decompress(raw)
        elif "deflate" in enc:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS) if raw[:1] != b"x" else zlib.decompress(raw)
    except Exception:
        pass  # truncated body; use what we have
    charset = "utf-8"
    ct = headers.get("content-type") or ""
    if "charset=" in ct:
        charset = ct.split("charset=")[-1].split(";")[0].strip().strip('"') or "utf-8"
    else:
        head = raw[:3000].decode("ascii", "ignore").lower()
        i = head.find("charset=")
        if i >= 0:
            charset = head[i + 8:i + 30].strip("\"' ").split('"')[0].split("'")[0].split(";")[0].split(">")[0].strip() or "utf-8"
    try:
        return raw.decode(charset, "replace")
    except LookupError:
        return raw.decode("utf-8", "replace")


def get_page(url, timeout=15, max_bytes=2_500_000):
    """Fetch a page like a browser. Never raises: problems are reported in the result."""
    res = {"url": url, "final_url": url, "status": None, "ms": None, "html": "", "headers": {},
           "error": None, "kind": None, "ssl_ok": True, "ssl_error": None}
    h = {"User-Agent": BROWSER_UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
         "Accept-Language": "en-GB,en;q=0.9", "Accept-Encoding": "gzip, deflate"}
    for verify in (True, False):
        t0 = time.monotonic()
        raw = b""
        try:
            with _OPENERS[verify].open(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                res.update(status=r.status, final_url=r.geturl(), headers={k.lower(): v for k, v in r.headers.items()})
                raw = r.read(max_bytes)
        except urllib.error.HTTPError as e:
            res.update(status=e.code, final_url=e.geturl() or url, headers={k.lower(): v for k, v in (e.headers or {}).items()})
            try:
                raw = e.read(max_bytes)
            except Exception:
                raw = b""
        except (urllib.error.URLError, ssl.SSLError, OSError, http.client.HTTPException) as e:
            kind = _kind(e)
            if kind == "ssl" and verify:
                res["ssl_ok"], res["ssl_error"] = False, str(getattr(e, "reason", e))[:200]
                continue  # retry without verification to see whether the site itself is there
            res.update(error=str(getattr(e, "reason", e))[:200], kind=kind)
            break
        except Exception as e:  # anything else: report, don't crash the grader
            res.update(error=str(e)[:200], kind="other")
            break
        res["ms"] = int((time.monotonic() - t0) * 1000)
        res["html"] = _decode(raw, res["headers"])
        break
    return res
