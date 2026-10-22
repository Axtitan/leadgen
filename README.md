# LeadFinder

Finds local businesses, checks their websites, and sorts them into:

| Bucket | Meaning | Pitch |
|---|---|---|
| **No website** | Nothing on their listing | "People searching for you find competitors first" |
| **Social / listing only** | "Website" is a Facebook, Instagram, Linktree, WhatsApp, Yell, Checkatrade, Fresha… page | "A real site gets you found on Google" |
| **Broken website** | Domain expired, parked, suspended, server error, "coming soon", dead Google `business.site` page | "Your site is down and you're losing customers right now" |
| **Bad website** (score < 50) | Several serious problems | List the top 3 problems |
| **Needs work** (50–74) | A few fixable problems | List the top problems |
| **Decent website** (75+) | Fine site | Pitch automations instead |
| **Couldn't check** | Site blocked the automated check | Look at it yourself |

Each lead gets an **opportunity score** (0–100): how weak their web presence is × how busy they look (Google reviews) × whether you can reach them. Sort by it and work from the top.

## Run it

Double-click **start.bat**, or:

```
python -X utf8 app.py
```

Then open http://127.0.0.1:8790. Needs Python 3.10+ and nothing else (it uses `certifi` for certificate checks if installed).

## Finding leads

1. Click **Find leads**, tick one or more business types (filter by Nigeria / UK / USA), or type your own.
2. Enter places, one per line. Neighbourhoods work best in big cities (Ikeja, Yaba, Peckham, Katy).
3. Pick a source:
   - **OpenStreetMap**: free, no key. Good in UK/US cities, thin in Nigeria. Each search takes ~40s+ because the free public servers queue requests. A missing website on OSM is less certain, so use the "Search Google for a site" button before pitching "you have no website".
   - **TomTom** (recommended free option): free key from developer.tomtom.com, no card. About 2,500 requests a month on the free plan (each up to 100 businesses), with phone numbers and websites but no ratings. When the allowance runs out, searches stop until next month; nothing is charged. TomTom calls it a "free evaluation" plan, so check their terms if you scale up.
   - **Google Maps**: needs a Google Maps Platform API key (Settings tab has the steps). Much more complete, with ratings and review counts, and the "no website" flag is reliable. Google has a monthly free allowance; check its pricing page before running very deep searches.
4. Leads appear as they're found, and every website is checked automatically in the background.

You can also **import a CSV** (Outscraper, Apify Google Maps scraper, any sheet with a name column) or **check one website** by hand, both on the "Import & check" tab.

## What the website check looks at

Down / expired / parked / suspended / placeholder pages; padlock and certificate; mobile-friendly; load time; copyright year (abandoned sites); outdated tech (Flash, frames, old WordPress/Joomla/Drupal, 2000s builders); free builder address (`name.wixsite.com`); tap-to-call button; contact form or online booking (also checks the contact page); Google title and description; thin content; link previews for WhatsApp/Facebook; insecure content. It also picks up emails and social links from the site.

Optional: **Google speed test** (PageSpeed Insights, mobile) per lead, with a phone screenshot of their site, handy for a "before" shot in a demo video.

## Working the leads

- **Next up** (the home screen) shows follow-ups that are due, then the ten strongest leads you haven't contacted, for all areas or one area. The deeper a lead's indigo swatch, the stronger the lead.
- Pick a lead to see why they're worth contacting, contact them (WhatsApp, call, email), and log it. Marking a lead Contacted or Demo sent sets a follow-up 3 days later, and the next lead moves up. "Skip for today" hides a lead until tomorrow. Every log, skip and delete can be undone from the message at the bottom.
- **Follow-ups** lists everyone you need to chase, grouped Overdue, Today, This week and Later.
- **All leads** is the full database with filters, website status, sorting and CSV export. New results are announced instead of reshuffling the list under you.

## Writing to leads

The "What to say" box drafts a WhatsApp message, an email and a call script from that lead's actual problems. Add your name and business in Settings so they're signed. WhatsApp opens your own WhatsApp with the message ready; you press send.

## Files

- `data/leadfinder.db`: all leads, notes and searches (SQLite). Back this up.
- `data/settings.json`: your details and Google key (stays on this computer).
- `python app.py --grade example.com`: check one site in the terminal.
