"""Grades a business's web presence the way a customer would experience it.

Every problem found becomes an "issue" with points (deducted from 100) and a plain-English
pitch line you can paste straight into outreach.

Buckets:
  none     no website at all
  social   the "website" is a Facebook / Instagram / Linktree / directory / booking page
  broken   the site is down, expired, parked, suspended or a placeholder
  bad      score under 50
  weak     score 50-74 ("needs work")
  ok       score 75+
  unknown  the site blocked our automated check (bot protection) - look at it yourself
"""
import datetime
import html as htmllib
import math
import re
import urllib.parse

from . import net, urls

YEAR = datetime.date.today().year

# A "website" that is really a profile, link page, directory listing or booking page.
LINK_PAGES = [
    ("facebook.com", "Facebook page"), ("fb.com", "Facebook page"), ("fb.me", "Facebook page"), ("instagram.com", "Instagram page"),
    ("instagr.am", "Instagram page"), ("tiktok.com", "TikTok page"), ("twitter.com", "X/Twitter page"), ("x.com", "X/Twitter page"),
    ("linkedin.com", "LinkedIn page"), ("youtube.com", "YouTube channel"), ("pinterest.com", "Pinterest page"), ("snapchat.com", "Snapchat page"),
    ("linktr.ee", "Linktree page"), ("beacons.ai", "Beacons link page"), ("bio.link", "link-in-bio page"), ("taplink.cc", "Taplink page"),
    ("lnk.bio", "link-in-bio page"), ("campsite.bio", "link-in-bio page"), ("msha.ke", "Mainstack page"), ("solo.to", "link-in-bio page"),
    ("hoo.be", "link-in-bio page"), ("wa.me", "WhatsApp link"), ("api.whatsapp.com", "WhatsApp link"), ("chat.whatsapp.com", "WhatsApp group"),
    ("wa.link", "WhatsApp link"), ("t.me", "Telegram link"), ("selar.co", "Selar store page"), ("selar.com", "Selar store page"),
    ("paystack.shop", "Paystack store page"), ("paystack.com", "Paystack page"), ("flutterwave.com", "Flutterwave store page"),
    ("yell.com", "Yell directory listing"), ("checkatrade.com", "Checkatrade profile"), ("bark.com", "Bark profile"),
    ("mybuilder.com", "MyBuilder profile"), ("ratedpeople.com", "Rated People profile"), ("trustatrader.com", "TrustATrader profile"),
    ("freeindex.co.uk", "FreeIndex listing"), ("yelp.com", "Yelp listing"), ("yelp.co.uk", "Yelp listing"), ("angi.com", "Angi listing"),
    ("homeadvisor.com", "HomeAdvisor listing"), ("thumbtack.com", "Thumbtack profile"), ("nextdoor.com", "Nextdoor page"), ("nextdoor.co.uk", "Nextdoor page"),
    ("bbb.org", "BBB listing"), ("yellowpages.com", "Yellow Pages listing"), ("vconnect.com", "VConnect listing"),
    ("businesslist.com.ng", "BusinessList listing"), ("jiji.ng", "Jiji listing"), ("nigeriagalleria.com", "directory listing"),
    ("booksy.com", "Booksy booking page"), ("fresha.com", "Fresha booking page"), ("treatwell.co.uk", "Treatwell page"),
    ("vagaro.com", "Vagaro booking page"), ("styleseat.com", "StyleSeat booking page"), ("setmore.com", "Setmore booking page"),
    ("calendly.com", "Calendly link"), ("airbnb.com", "Airbnb listing"), ("airbnb.co.uk", "Airbnb listing"), ("booking.com", "Booking.com listing"),
    ("tripadvisor.com", "Tripadvisor listing"), ("tripadvisor.co.uk", "Tripadvisor listing"), ("just-eat.co.uk", "Just Eat page"),
    ("deliveroo.co.uk", "Deliveroo page"), ("ubereats.com", "Uber Eats page"), ("doordash.com", "DoorDash page"), ("grubhub.com", "Grubhub page"),
    ("chowdeck.com", "Chowdeck page"), ("glovoapp.com", "Glovo page"), ("linkinbio.com", "link-in-bio page"),
]
# Free website hosts that no longer exist.
GONE_HOSTS = {"business.site": "free Google site (Google shut these down in 2024)"}
# Free builder sub-domains: the site exists but on someone else's address.
FREE_HOSTS = [
    ("wixsite.com", "Wix"), ("wixstudio.io", "Wix"), ("editorx.io", "Wix"), ("weebly.com", "Weebly"), ("weeblysite.com", "Weebly"),
    ("wordpress.com", "WordPress.com"), ("blogspot.com", "Blogger"), ("blogspot.co.uk", "Blogger"), ("godaddysites.com", "GoDaddy"),
    ("square.site", "Square"), ("squarespace.com", "Squarespace"), ("sites.google.com", "Google Sites"), ("mystrikingly.com", "Strikingly"),
    ("strikingly.com", "Strikingly"), ("webnode.page", "Webnode"), ("webnode.com", "Webnode"), ("webnode.co.uk", "Webnode"),
    ("jimdosite.com", "Jimdo"), ("jimdofree.com", "Jimdo"), ("yolasite.com", "Yola"), ("site123.me", "SITE123"), ("carrd.co", "Carrd"),
    ("ueniweb.com", "UENI"), ("webflow.io", "Webflow"), ("framer.website", "Framer"), ("framer.ai", "Framer"), ("framer.app", "Framer"),
    ("vercel.app", "Vercel"), ("netlify.app", "Netlify"), ("github.io", "GitHub Pages"), ("000webhostapp.com", "000webhost"),
    ("bumpa.shop", "Bumpa"), ("myshopify.com", "Shopify"), ("zyrosite.com", "Hostinger"), ("canva.site", "Canva"), ("my.canva.site", "Canva"),
    ("webs.com", "Webs"), ("tripod.com", "Tripod"), ("angelfire.com", "Angelfire"), ("simdif.com", "SimDif"), ("mozello.com", "Mozello"),
]

BUILDERS = [
    ("Wix", r"static\.wixstatic\.com|x-wix-|wix\.com website builder"), ("Squarespace", r"static1\.squarespace\.com|squarespace-cdn"),
    ("Shopify", r"cdn\.shopify\.com"), ("Webflow", r"data-wf-page|website-files\.com"), ("Framer", r"framerusercontent\.com"),
    ("GoDaddy Website Builder", r"img1\.wsimg\.com|go ?daddy website builder|starfield technologies"), ("Weebly", r"editmysite\.com|weebly\.com"),
    ("Duda", r"cdn-website\.com|multiscreensite|dudamobile"), ("Jimdo", r"jimcdn\.com|jimdo(free|site)?\.com"), ("SITE123", r"site123\.(me|com)"),
    ("Strikingly", r"strikingly(-cdn)?\.com|mystrikingly"), ("Yola", r"yolacdn|yola\.com"), ("Mr Site", r"mrsite\.(com|co\.uk)"),
    ("IONOS MyWebsite", r"mywebsite-editor\.com|ionos\.(com|co\.uk)"), ("Hostinger", r"zyrosite\.com|zyro\.com|hostinger"),
    ("WordPress", r"/wp-content/|/wp-includes/"), ("Joomla", r"/media/jui/|joomla"), ("Drupal", r"drupal|/sites/default/files/"),
    ("Next.js", r"__next_data__|/_next/static"), ("Nuxt", r"__nuxt"),
]

BOOKING = re.compile(
    r"calendly\.com|acuityscheduling|squareup\.com/appointments|square\.site/book|booksy\.com|fresha\.com|treatwell|vagaro\.com|setmore\.com"
    r"|simplybook|mindbodyonline|janeapp|opentable|resy\.com|sevenrooms|quandoo|bookingbug|housecallpro|getjobber|servicetitan|wa\.me/|api\.whatsapp\.com"
    r"|book (now|online|an appointment|a table|your|a call|a consultation)|request a (quote|callback|call back)|get a (free )?(quote|estimate)"
    r"|schedule (an? )?(appointment|service|estimate|consultation|call)|online booking|make a reservation", re.I)

PARKED = ["domain is for sale", "buy this domain", "this domain may be for sale", "domain for sale", "is for sale!", "parkingcrew", "sedoparking",
          "domain parking", "this domain is parked", "this web page is parked", "hugedomains", "future home of something quite cool",
          "domain has expired", "this domain has expired", "domain name has expired", "renew this domain", "this domain name is registered"]
SUSPENDED = ["account suspended", "account has been suspended", "site suspended", "website is suspended", "bandwidth limit exceeded",
             "website expired", "site has expired", "hosting has expired", "hosting account has expired", "subscription has expired",
             "this website is currently unavailable", "this site is temporarily unavailable", "there isn't a github pages site here",
             "no such app", "site not found", "this site is no longer available", "website is no longer available"]
DEFAULT_PAGES = ["welcome to nginx", "apache2 ubuntu default page", "apache2 debian default page", "test page for the apache",
                 "iis windows server", "default web site page", "there is no website configured at this address", "web server's default page",
                 "index of /", "this is the default welcome page", "plesk obsidian", "default page for", "congratulations! your website is up"]
PLACEHOLDER = ["coming soon", "under construction", "launching soon", "under maintenance", "we'll be back soon", "be right back",
               "website is under construction", "stay tuned", "something awesome is coming", "new website coming"]
CHALLENGE = ["just a moment...", "cf-chl", "challenge-platform", "attention required! | cloudflare", "sucuri website firewall",
             "ddos protection by", "checking your browser", "verify you are human", "captcha", "access denied | ", "request unsuccessful. incapsula"]

GENERIC_TITLES = {"home", "homepage", "home page", "welcome", "untitled", "index", "my site", "my website", "new page", "page", "website",
                  "untitled document", "default", "main", "start", "index.html", "document"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
BAD_EMAIL_DOMAINS = ("example.", "sentry", "wixpress.com", "domain.com", "yourdomain", "godaddy.com", "squarespace.com", "schema.org",
                     "email.com", "website.com", "company.com", "yoursite", "mysite.com", "test.com", "sentry.io", "w3.org")
BAD_EMAIL_LOCAL = {"you", "your", "name", "user", "email", "example", "someone", "yourname", "info@example", "username"}


def a(word):
    """'a Facebook page' / 'an Instagram page'"""
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def issue(id_, sev, pts, title, pitch):
    return {"id": id_, "sev": sev, "pts": pts, "title": title, "pitch": pitch}


def classify(url):
    """-> (kind, label, normalized_url); kind is none | link | gone | free | site."""
    u = urls.normalize(url)
    if not u:
        return "none", None, ""
    h = urls.host(u)
    for suf, why in GONE_HOSTS.items():
        if urls.match(h, suf):
            return "gone", why, u
    if re.match(r"^(www\.|maps\.)?google\.[a-z.]+$", h) or h in ("g.page", "maps.app.goo.gl", "goo.gl", "g.co"):
        return "link", "Google Maps listing", u
    for suf, label in LINK_PAGES:
        if urls.match(h, suf):
            return "link", label, u
    for suf, b in FREE_HOSTS:
        if urls.match(h, suf):
            return "free", b, u
    return "site", None, u


def _fixed(bucket, headline, issues=None, site=None):
    return {"kind": "fixed", "bucket": bucket, "headline": headline, "base_issues": issues or [], "site": site or {}}


def visible_text(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg|template)\b[^>]*>.*?</\1\s*>", " ", h)
    h = re.sub(r"(?s)<!--.*?-->", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", htmllib.unescape(h)).strip()


def _title(h):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", h)
    return re.sub(r"\s+", " ", htmllib.unescape(m.group(1))).strip()[:200] if m else ""


def _meta(h, name):
    for m in re.finditer(r"(?is)<meta\b[^>]*>", h):
        tag = m.group(0)
        if re.search(rf"""(name|property)\s*=\s*["']?{re.escape(name)}["'\s/>]""", tag, re.I):
            c = re.search(r"""content\s*=\s*(["'])(.*?)\1""", tag, re.I | re.S)
            return htmllib.unescape(c.group(2)).strip() if c else ""
    return None


def _cf_decode(hexstr):
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def find_emails(h, text):
    found = [urllib.parse.unquote(m) for m in re.findall(r"""mailto:([^"'?>\s]+)""", h, re.I)]
    found += [_cf_decode(m) for m in re.findall(r"""data-cfemail=["']([0-9a-f]+)["']""", h, re.I)]
    found += [_cf_decode(m) for m in re.findall(r"/cdn-cgi/l/email-protection#([0-9a-f]+)", h, re.I)]
    found += EMAIL.findall(text)
    out = []
    for e in found:
        e = e.strip().strip(".").lower()
        if not EMAIL.fullmatch(e) or e in out:
            continue
        local, _, dom = e.partition("@")
        if local in BAD_EMAIL_LOCAL or any(b in dom for b in BAD_EMAIL_DOMAINS) or re.search(r"\.(png|jpe?g|gif|webp|svg|js|css)$", e):
            continue
        out.append(e)
    return out[:5]


SOCIAL_RX = {
    "facebook": r"https?://(?:www\.|m\.|web\.)?facebook\.com/(?!sharer|share|dialog|plugins|tr\?|wix|groups/?$)[^\s\"'<>?#]+",
    "instagram": r"https?://(?:www\.)?instagram\.com/(?!p/|explore|wix)[A-Za-z0-9_.]+",
    "tiktok": r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+",
    "linkedin": r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|in)/[^\s\"'<>?#]+",
    "x": r"https?://(?:www\.)?(?:twitter|x)\.com/(?!share|intent|home|wix)[A-Za-z0-9_]{2,}",
    "youtube": r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/|user/)[^\s\"'<>?#]+",
    "whatsapp": r"https?://(?:wa\.me/|api\.whatsapp\.com/send\?phone=)\+?\d{7,15}",
}


def find_socials(h):
    out = {}
    for k, rx in SOCIAL_RX.items():
        m = re.search(rx, h, re.I)
        if m:
            out[k] = htmllib.unescape(m.group(0)).rstrip("/\\")
    return out


def copyright_year(text):
    years = []
    rx = r"(?:©|\(c\)|copyright)\s*[^\d<>]{0,60}?((?:19|20)\d{2})(?:\s*(?:-|–|—|to)\s*((?:19|20)\d{2}))?"
    for m in re.finditer(rx, text, re.I):
        y = max(int(m.group(1)), int(m.group(2) or 0))
        if 1995 <= y <= YEAR + 1:
            years.append(y)
    return max(years) if years else None


def builder_of(low, generator):
    g = (generator or "").lower()
    for name, rx in BUILDERS:
        if re.search(rx, low) or name.lower().split()[0] in g:
            return name
    return generator.split()[0] if generator else None


def outdated(low, generator, has_viewport):
    """-> list of (reason, weight)"""
    out, g = [], (generator or "").lower()
    if re.search(r"\.swf\b|shockwave-flash", low):
        out.append(("Flash (no browser runs it any more)", 15))
    if "<frameset" in low or re.search(r"<frame\s", low):
        out.append(("old-style frames", 15))
    if "<marquee" in low or "<blink" in low:
        out.append(("scrolling marquee text", 8))
    if low.count("<font") >= 3:
        out.append(("1990s-style font tags", 8))
    if not has_viewport and low.count("<table") >= 3 and re.search(r"<td[^>]+width\s*=", low):
        out.append(("a table-based layout", 8))
    m = re.search(r"wordpress (\d+)\.(\d+)", g)
    if m and int(m.group(1)) < 5:
        out.append((f"WordPress {m.group(1)}.{m.group(2)}, which is years out of date", 10))
    if re.search(r"joomla!? ?(1|2)\.", g):
        out.append(("an old, unsupported version of Joomla", 10))
    m = re.search(r"drupal (\d+)", g)
    if m and int(m.group(1)) <= 7:
        out.append((f"Drupal {m.group(1)}, which is no longer supported", 10))
    for old in ("frontpage", "dreamweaver", "iweb", "microsoft word", "publisher", "netobjects", "homestead", "webplus", "web easy", "web page maker"):
        if old in g:
            out.append((f"{generator.strip()} (a 2000s-era tool)", 12))
            break
    m = re.search(r"jquery(?:/|[.-])1\.(\d+)", low)
    if m and int(m.group(1)) < 9:
        out.append(("jQuery 1." + m.group(1) + " (from around 2012)", 4))
    return out


def _challenge(page, low_head, words):
    if words > 200:  # a real page that happens to use reCAPTCHA on a form
        return False
    return any(c in low_head for c in CHALLENGE) or ("cloudflare" in (page["headers"].get("server") or "").lower() and page["status"] in (403, 503))


def _dead_reason(title, text, words):
    hay = (title + " " + text[:1500]).lower()
    if any(p in hay for p in PARKED) and words < 500:
        return "Domain is parked, for sale or expired"
    if any(p in hay for p in SUSPENDED) and words < 400:
        return "Hosting account suspended or expired"
    if any(p in hay for p in DEFAULT_PAGES) and words < 250:
        return "Server shows a blank default page, not a website"
    if any(p in hay for p in PLACEHOLDER) and words < 150:
        return "Just a 'coming soon' / under construction page"
    return None


CONNECT_REASONS = {
    "dns": ("Domain doesn't work (no DNS record, may have expired)", "When people click your website link they get \"This site can't be reached\". The domain may have expired."),
    "timeout": ("Website doesn't respond", "Your website didn't load at all when we tried it, so anyone clicking through from Google gives up."),
    "refused": ("Server refuses connections", "Your website's server isn't accepting visitors, so the site is effectively offline."),
    "reset": ("Connection drops", "Your website's server cuts the connection, so the site won't load for visitors."),
    "ssl": ("Secure connection fails", "Browsers can't open a secure connection to your website, so most visitors see an error page."),
    "other": ("Website won't load", "Your website wouldn't load when we tried it."),
}


def _fetch_best(u):
    """Try the listed address, then common variants (www / https), the way a patient visitor might."""
    p = net.get_page(u)
    if p["error"] and p["kind"] == "timeout":
        p = net.get_page(u, timeout=25)
    if not p["error"]:
        return p, None
    for alt in (urls.toggle_www(u), urls.with_scheme(u, "https" if u.startswith("http:") else "http")):
        p2 = net.get_page(alt, timeout=12)
        if not p2["error"]:
            return p2, alt
    return p, None


def grade(url):
    kind, label, u = classify(url)
    if kind == "none":
        return _fixed("none", "No website on their listing")
    if kind == "link":
        return _fixed("social", f"Only has {a(label)}", [issue(
            "link_only", "high", 0, f"\"Website\" is just {a(label)}",
            f"Your website link goes to {a(label)}. A proper site shows up on Google, looks more established and lets people enquire or book any time.")],
            {"input_url": u, "link_page": label})
    if kind == "gone":
        return _fixed("broken", f"Website link is an old {label}", [issue(
            "gone", "high", 0, "Website link points to a site that no longer exists",
            "Your website link is a free Google site, and Google switched those off in 2024. Anyone who clicks it from your listing lands on nothing.")],
            {"input_url": u})

    page, alt = _fetch_best(u)
    site = {"input_url": u, "final_url": page["final_url"], "status": page["status"], "ms": page["ms"], "ssl_ok": page["ssl_ok"]}
    if page["error"]:
        title, pitch = CONNECT_REASONS.get(page["kind"], CONNECT_REASONS["other"])
        site["error"] = page["error"]
        return _fixed("broken", title, [issue("down", "high", 0, title, pitch)], site)

    fk, flabel, _ = classify(page["final_url"])
    if fk == "link":
        return _fixed("social", f"Domain just forwards to {a(flabel)}", [issue(
            "forwards", "high", 0, f"Domain just forwards to {a(flabel)}",
            f"Your web address redirects to {a(flabel)} instead of a real website, so you get none of the benefits of having your own site.")], site)

    h = page["html"]
    low = h.lower()
    text = visible_text(h)
    words = len(text.split())
    title = _title(h)
    site.update(title=title, words=words)

    if _challenge(page, low[:20000], words):
        return _fixed("unknown", "Site blocked our automated check (bot protection). Open it to judge it yourself.", [], site)
    dead = _dead_reason(title, text, words)
    if dead:
        return _fixed("broken", dead, [issue("dead", "high", 0, dead,
                      "Your web address doesn't show your business. Visitors see a holding or error page instead, which looks like you've closed.")], site)
    status = page["status"] or 0
    if status in (401, 403, 429):
        return _fixed("unknown", f"Site refused our automated check (HTTP {status}). Open it to judge it yourself.", [], site)
    if status >= 400:
        t = "Homepage shows 'page not found'" if status in (404, 410) else f"Homepage shows a server error ({status})"
        return _fixed("broken", t, [issue("http_error", "high", 0, t, "Your homepage shows an error message instead of your business.")], site)

    return {"kind": "site", "bucket": None, "headline": None, "base_issues": _analyze(page, h, low, text, words, title, kind, label, alt, site), "site": site}


def _analyze(page, h, low, text, words, title, kind, label, alt, site):
    issues = []
    final = page["final_url"]
    host = urls.host(final)
    https = final.lower().startswith("https://")
    site["https"] = https

    if alt:
        issues.append(issue("alt_address", "med", 10, "Listed web address doesn't work",
                            f"The address on your listing ({urls.host(site['input_url'])}) doesn't load. Only {urls.host(alt)} works, so some customers hit a dead end."))
    cert_err = (page["ssl_error"] or "").lower()
    # "unable to get local issuer" usually means a missing intermediate certificate, which browsers fetch for
    # themselves, so visitors don't see a warning. Only flag errors a browser would show too.
    real_cert_problem = not page["ssl_ok"] and "local issuer" not in cert_err
    if real_cert_problem:
        why = "has expired" if "expired" in cert_err else "is for a different web address" if ("hostname" in cert_err or "match" in cert_err)             else "is self-signed" if "self" in cert_err else "isn't trusted"
        site["cert_error"] = page["ssl_error"]
        issues.append(issue("ssl", "high", 20, f"Security certificate {why}",
                            "Browsers warn visitors that your site is \"not private\" before they can see it, which scares most people off."))
    elif not https:
        a = net.get_page(urls.with_scheme(final, "https"), timeout=8)
        if not a["error"] and a["ssl_ok"] and (a["status"] or 0) < 400:
            issues.append(issue("no_https_redirect", "low", 5, "Doesn't force the secure version",
                                "Your site opens without the padlock unless people type https:// themselves, so Chrome labels it \"Not secure\"."))
        else:
            issues.append(issue("no_https", "high", 15, "No padlock (\"Not secure\")",
                                "Chrome shows \"Not secure\" next to your web address. Customers notice, and Google ranks secure sites higher."))

    has_viewport = bool(re.search(r"""<meta[^>]+name\s*=\s*["']?viewport""", low))
    if not has_viewport:
        issues.append(issue("no_mobile", "high", 25, "Not mobile-friendly",
                            "Your site doesn't resize for phones, so visitors have to pinch and zoom. Most people looking for a local business are on their phone."))

    ms = page["ms"] or 0
    if ms > 7000:
        issues.append(issue("slow", "med", 12, f"Slow to load ({ms / 1000:.1f}s)",
                            f"Your homepage took {ms / 1000:.1f} seconds to load in our test. Half of visitors leave after about 3 seconds."))
    elif ms > 4000:
        issues.append(issue("slow", "low", 6, f"A bit slow ({ms / 1000:.1f}s)", f"Your homepage took {ms / 1000:.1f} seconds to load in our test."))

    yr = copyright_year(text)
    site["copyright_year"] = yr
    if yr and yr <= YEAR - 6:
        issues.append(issue("stale", "med", 15, f"Looks abandoned (© {yr})",
                            f"Your footer still says © {yr}, which makes visitors wonder whether you're still trading."))
    elif yr and yr <= YEAR - 3:
        issues.append(issue("stale", "low", 8, f"Footer says © {yr}", f"Your footer says © {yr}, so the site looks like it hasn't been touched in years."))

    generator = _meta(h, "generator") or ""
    site["generator"] = generator[:80] or None
    site["builder"] = builder_of(low, generator)
    old = outdated(low, generator, has_viewport)
    if old:
        pts = min(25, sum(w for _, w in old))
        issues.append(issue("outdated", "high" if pts >= 15 else "med" if pts >= 8 else "low", pts, "Built with outdated technology",
                            "Your site uses " + ", ".join(r for r, _ in old) + ", which modern browsers and phones handle badly."))

    if kind == "free":
        issues.append(issue("free_host", "high", 20, f"On a free {label} address",
                            f"Your site lives on a free {label} address ({host}) instead of your own name. Your own domain looks more professional and is easier to remember."))

    # Calls to action. Many sites keep the form on a contact page, so look there too before calling it missing.
    tel = bool(re.search(r"""href\s*=\s*["']?tel:""", low))
    form = bool(re.search(r"<form", low) and re.search(r"""<textarea|type\s*=\s*["']?email""", low))
    booking = bool(BOOKING.search(low))
    emails = find_emails(h, text)
    socials = find_socials(h)
    contact_url = None
    if not (form or booking) or not emails:
        m = re.search(r"""href\s*=\s*["']([^"'#]*(contact|get-in-touch|enquir|book|quote)[^"'#]*)["']""", h, re.I)
        if m:
            contact_url = urllib.parse.urljoin(final, htmllib.unescape(m.group(1)))
            if urls.bare(urls.host(contact_url)) == urls.bare(host) and contact_url.rstrip("/") != final.rstrip("/"):
                cp = net.get_page(contact_url, timeout=10)
                if not cp["error"] and (cp["status"] or 0) < 400:
                    cl = cp["html"].lower()
                    form = form or bool(re.search(r"<form", cl) and re.search(r"""<textarea|type\s*=\s*["']?email""", cl))
                    booking = booking or bool(BOOKING.search(cl))
                    tel = tel or bool(re.search(r"""href\s*=\s*["']?tel:""", cl))
                    for e in find_emails(cp["html"], visible_text(cp["html"])):
                        if e not in emails:
                            emails.append(e)
                    for k, v in find_socials(cp["html"]).items():
                        socials.setdefault(k, v)
    site.update(tel=tel, form=form, booking=booking, emails=emails[:5], socials=socials, contact_url=contact_url)

    if not tel:
        issues.append(issue("no_call", "med", 8, "No tap-to-call button",
                            "People on phones can't tap to call you, and calling is how most customers contact a local business."))
    if not (form or booking):
        issues.append(issue("no_enquiry", "med", 8, "No way to enquire or book online",
                            "There's no contact form or online booking, so people who visit outside working hours just leave."))

    site["description"] = _meta(h, "description")
    if not title or title.lower() in GENERIC_TITLES or len(title) < 4 or title.lower() == urls.bare(host):
        issues.append(issue("bad_title", "low", 6, "Weak Google title",
                            f"Your page title is \"{title or 'missing'}\", so Google doesn't know what you do or where you are."))
    if not site["description"]:
        issues.append(issue("no_desc", "low", 4, "No Google description",
                            "There's no description for Google to show under your name, so it picks random text from the page."))

    spa = bool(re.search(r"""<div id=["'](root|app|__next|__nuxt)["'][^>]*>\s*</div>""", low) or "__next_data__" in low or "ng-version" in low)
    if words < 120 and not spa:
        issues.append(issue("thin", "med", 10, "Very little content",
                            f"Your homepage has only about {words} words. Google needs more to rank you, and customers need more to trust you."))

    if not re.search(r"""property\s*=\s*["']?og:(image|title)""", low):
        issues.append(issue("no_preview", "low", 3, "No link preview",
                            "When someone shares your site on WhatsApp or Facebook, it shows no picture or summary."))
    if https and re.search(r"""<(img|script|iframe)\b[^>]+src\s*=\s*["']http://""", low):
        issues.append(issue("mixed", "low", 4, "Some parts load insecurely",
                            "Some images or scripts load over an insecure connection, which can trigger browser warnings."))
    return issues


def psi_issues(psi):
    if not psi or psi.get("error"):
        return []
    out = []
    p, seo, a11y = psi.get("performance"), psi.get("seo"), psi.get("accessibility")
    if p is not None and p < 30:
        out.append(issue("psi_perf", "high", 20, f"Very slow on phones (Google score {p}/100)",
                         f"Google's own speed test scores your site {p}/100 on mobile. Slow sites lose visitors and rank lower."))
    elif p is not None and p < 50:
        out.append(issue("psi_perf", "med", 12, f"Slow on phones (Google score {p}/100)",
                         f"Google's own speed test scores your site {p}/100 on mobile. Slow sites lose visitors and rank lower."))
    if seo is not None and seo < 80:
        out.append(issue("psi_seo", "low", 5, f"Google SEO check: {seo}/100", f"Google's checker scores your homepage {seo}/100 for search basics."))
    if a11y is not None and a11y < 70:
        out.append(issue("psi_a11y", "low", 3, f"Hard to read or use (accessibility {a11y}/100)",
                         "Google flags your site as hard to read or use: small text, low contrast or buttons that are hard to tap."))
    return out


def finalize(res, psi=None):
    """-> bucket, score, issues, headline"""
    if res["kind"] != "site":
        return res["bucket"], None, res["base_issues"], res["headline"]
    issues = sorted(list(res["base_issues"]) + psi_issues(psi), key=lambda i: -i["pts"])
    score = max(0, 100 - sum(i["pts"] for i in issues))
    bucket = "bad" if score < 50 else "weak" if score < 75 else "ok"
    big = [i for i in issues if i["pts"] >= 5]
    if not big:
        headline = "No major problems found"
    else:
        headline = f"{len(big)} problem{'s' if len(big) != 1 else ''}: " + ", ".join(i["title"] for i in big[:3])
    return bucket, score, issues, headline


NEED = {"none": 100, "broken": 97, "social": 92, "unknown": 35}


def need_for(res, bucket):
    """How certain and how pitchable the web-presence problem is. Only real differences in the evidence."""
    head = ((res or {}).get("headline") or "").lower()
    if bucket == "broken":
        if "domain doesn't work" in head:
            return 97  # the domain is gone: certain, and an urgent pitch
        if "parked" in head or "expired" in head or "suspended" in head or "old free google" in head:
            return 95
        if "default page" in head or "coming soon" in head or "page not found" in head:
            return 93
        return 89  # didn't respond or server error: real today, but could be temporary
    if bucket == "social":
        if any(w in head for w in ("facebook", "instagram", "tiktok", "whatsapp", "x/twitter")):
            return 92  # running the business from social media
        if any(w in head for w in ("linktree", "link page", "link-in-bio", "beacons", "mainstack")):
            return 90
        if any(w in head for w in ("booking", "fresha", "booksy", "treatwell", "calendly")):
            return 82  # has a booking tool already
        return 86  # a directory or marketplace listing
    return NEED.get(bucket)


def opportunity(bucket, score, reviews, rating, has_contact, closed, uncertain_none=False, res=None, contact=None):
    """0-100: how good a prospect this is. Bad web presence x signs of a busy business x a way to reach them.
    uncertain_none: "no website" came from OpenStreetMap, which often just lacks the website tag.
    contact: 'both' (phone and email), 'phone', 'email' or None; phone wins because calls and WhatsApp convert."""
    if closed:
        return 0
    if bucket in NEED:
        need = 70 if (bucket == "none" and uncertain_none) else (need_for(res, bucket) or NEED[bucket])
    elif score is None:
        need = 40
    else:
        need = max(100 - score, 55 if score < 50 else 0)
    demand = 0.45 if reviews is None else min(1.0, math.log10(reviews + 1) / 2.4)
    if rating is not None and rating < 3.5:
        demand *= 0.8
    reach = {"both": 1.0, "phone": 0.96, "email": 0.86}.get(contact, 1.0 if has_contact and contact is None else 0.7)
    return round(need * (0.5 + 0.5 * demand) * reach)


def pagespeed(url, key=None):
    q = [("url", url), ("strategy", "mobile")] + [("category", c) for c in ("performance", "seo", "accessibility", "best-practices")]
    if key:
        q.append(("key", key))
    try:
        data = net.api_json("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(q), timeout=150, retries=1)
    except net.ApiError as e:
        msg = e.body
        try:
            import json
            msg = json.loads(e.body)["error"]["message"]
        except Exception:
            pass
        return {"error": f"PageSpeed failed: {msg or e}"[:300]}, None
    except Exception as e:
        return {"error": f"PageSpeed failed: {e}"[:300]}, None
    lh = data.get("lighthouseResult", {})
    cats, audits = lh.get("categories", {}), lh.get("audits", {})
    out = {}
    for k, name in (("performance", "performance"), ("seo", "seo"), ("accessibility", "accessibility"), ("best-practices", "best_practices")):
        s = (cats.get(k) or {}).get("score")
        out[name] = None if s is None else round(s * 100)
    for k, name in (("largest-contentful-paint", "lcp"), ("total-byte-weight", "weight"), ("speed-index", "speed_index")):
        out[name] = (audits.get(k) or {}).get("displayValue")
    shot = ((audits.get("final-screenshot") or {}).get("details") or {}).get("data")
    return out, shot
