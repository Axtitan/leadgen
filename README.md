# LeadFinder

Finds local businesses, checks their websites, and sorts them into:

| Bucket | Meaning | Pitch |
|---|---|---|
| **No website** | Nothing on their listing, and LeadFinder couldn't find one either (see below) | "People searching for you find competitors first" |
| **Social / listing only** | "Website" is a Facebook, Instagram, Linktree, WhatsApp, Yell, Checkatrade, Fresha… page | "A real site gets you found on Google" |
| **Broken website** | Domain expired, parked, suspended, server error, "coming soon", dead Google `business.site` page | "Your site is down and you're losing customers right now" |
| **Bad website** (score < 50) | Several serious problems | List the top 3 problems |
| **Needs work** (50–74) | A few fixable problems | List the top problems |
| **Decent website** (75+) | Fine site | Pitch automations instead |
| **Couldn't check** | Site blocked the automated check | Look at it yourself |

Each lead gets an **opportunity score** (0–100): how weak their web presence is × how busy they look (Google reviews) × whether you can reach them. Sort by it and work from the top.

## Run it

LeadFinder runs on your own computer. It is not a website you host: it needs a program that stays running and a database file on disk, so services like Vercel or Netlify won't work.

### 1. Install Python (once)

You need **Python 3.10 or newer**. Check with `python --version` in a terminal.

- **Windows:** download it from [python.org/downloads](https://www.python.org/downloads/). On the first installer screen, tick **"Add python.exe to PATH"**.
- **Mac:** download it from python.org too, or run `brew install python`. On a Mac the command is `python3`, not `python`.

### 2. Get the code (once)

With git:

```
git clone https://github.com/Axtitan/leadgen.git
cd leadgen
```

Or, on the GitHub page, click **Code → Download ZIP** and unzip it.

### 3. Optional: better certificate checks (once)

```
pip install certifi
```

Without it, some Windows computers wrongly report a "certificate problem" on sites that are fine. Everything else uses only Python's built-in parts, so there's nothing else to install.

### 4. Start it

- **Windows:** double-click **start.bat**. It opens the app in your browser.
- **Mac / Linux / terminal:** run `python3 -X utf8 app.py` (Windows: `python -X utf8 app.py`), then open http://127.0.0.1:8790.

Keep that window open while you use the app; closing it stops LeadFinder. Searches that were running pick up again the next time you start it.

### 5. First-time setup in the app

Open **Settings** and:

1. Add your name, business name, website and phone, so the drafted messages are signed.
2. Paste a **TomTom key**, the recommended free source. Get one at [developer.tomtom.com](https://developer.tomtom.com): sign up (no card needed), open your dashboard, and copy the key it creates for you. Each person should use their own key, since the free allowance is per account.
3. Optional but recommended: paste a free **Apify token** under *Find missing websites* ([apify.com](https://apify.com), no card; in the Apify Console it's under Settings → API & Integrations). LeadFinder uses it to check "No website" leads against their Google profile.
4. A Google key is optional and needs a card on file with Google. OpenStreetMap needs no key at all.

### Updating

If you used git, get the latest version with:

```
git pull
```

Your leads and settings are not touched; they live in `data/`, which git ignores.

### Working as a team

Each copy of LeadFinder keeps its **own** leads, and copies don't sync with each other. When two people use it:

- Split the work by area or business type so you don't message the same business twice.
- To share a list, use **Export CSV** on the All leads page in one copy, then **Import** it on the Import & check page in the other. Imports skip businesses the other copy already has. Contact status and notes don't carry over, so mark the ones you've already contacted in your own copy.

### Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Python isn't on PATH. Reinstall it with "Add python.exe to PATH" ticked, or try `py -X utf8 app.py`. On Mac use `python3`. |
| "Address already in use" | LeadFinder is already running in another window. Use that one, or start a second copy on another port: `python app.py --port 8791`. |
| Page won't load | Check the terminal window is still open and shows "LeadFinder running at…". |
| OpenStreetMap searches are slow or fail | The free public servers are busy. It retries automatically; TomTom is faster. |
| Lots of "certificate problem" findings | Run `pip install certifi` and restart. |
| Strange characters or crashes on Windows | Start it with `-X utf8` as shown above (start.bat already does). |

### Command-line options

```
python app.py                    start the app (http://127.0.0.1:8790)
python app.py --port 9000        use another port
python app.py --grade URL        check one website in the terminal and exit
```

`--host` changes the address the app listens on. Leave it at the default: the app has no login, so making it reachable from other computers would expose your leads and keys.

## Finding leads

1. Click **Find leads**, tick one or more business types (filter by Nigeria / UK / USA), or type your own.
2. Enter places, one per line. Neighbourhoods work best in big cities (Ikeja, Yaba, Peckham, Katy).
3. Pick a source:
   - **OpenStreetMap**: free, no key. Good in UK/US cities, thin in Nigeria. Each search takes ~40s+ because the free public servers queue requests. A missing website on OSM is less certain, so use the "Search Google for a site" button before pitching "you have no website".
   - **TomTom** (recommended free option): free key from developer.tomtom.com, no card. About 2,500 requests a month on the free plan (each up to 100 businesses), with phone numbers and websites but no ratings. When the allowance runs out, searches stop until next month; nothing is charged. TomTom calls it a "free evaluation" plan, so check their terms if you scale up.
   - **Google Maps**: needs a Google Maps Platform API key (Settings tab has the steps). Much more complete, with ratings and review counts, and the "no website" flag is reliable. Google has a monthly free allowance; check its pricing page before running very deep searches.
4. Leads appear as they're found, and every website is checked automatically in the background.

You can also **import a CSV** (Outscraper, Apify Google Maps scraper, any sheet with a name column) or **check one website** by hand, both on the "Import & check" tab.

## Finding websites the listing left out

OpenStreetMap and TomTom often have no website for a business that does have one. So before a lead counts as **No website**, LeadFinder looks for it in the background:

1. **By name (free, automatic).** It tries the obvious web addresses (for *CBW Plumbing and Heating* in the UK: cbwplumbingandheating.co.uk, cbwplumbing.co.uk and so on) and only keeps a site that shows the business's phone number, or its name together with its town or postcode.
2. **On their Google profile (with an Apify token).** It looks the business up on Google Maps with Apify's Google Maps Scraper and takes the website from their Google Business Profile, plus their rating, review count and an exact link to the profile. Apify gives $5 of free credit a month with no card, which covers roughly 1,000 businesses (one Google listing each, checked 40 at a time, strongest leads first). When the credit runs out, checks pause until next month and nothing is charged. Each person on the team should use their own Apify account.

What you'll see:

- **No website listed**: not checked yet.
- **No website found**: not on the listing and not found by name, but not confirmed on Google. The lead shows a warning and a **Look again** button. Check their Google profile before saying they have none.
- **No website**: confirmed, since their Google profile has no website either (or the lead came from Google).
- A website LeadFinder found itself says where it came from on the lead ("Found on their Google profile" or "found under their name").

Settings → *Find missing websites* shows the progress, and **Look for missing websites** runs it again for any leads not yet checked.

## What the website check looks at

Down / expired / parked / suspended / placeholder pages; padlock and certificate; mobile-friendly; load time; copyright year (abandoned sites); outdated tech (Flash, frames, old WordPress/Joomla/Drupal, 2000s builders); free builder address (`name.wixsite.com`); tap-to-call button; contact form or online booking (also checks the contact page); Google title and description; thin content; link previews for WhatsApp/Facebook; insecure content. It also picks up emails and social links from the site.

Optional: **Google speed test** (PageSpeed Insights, mobile) per lead, with a phone screenshot of their site, handy for a "before" shot in a demo video.

## Working the leads

- **Next up** (the home screen) shows follow-ups that are due, then the ten strongest leads you haven't contacted, as cards, for all areas or one area. The bars on each card show lead strength.
- Click a card and the list folds into a narrow column with the lead beside it: why they're worth contacting, contact buttons (WhatsApp, call, email), what to say, and a place to log it. Marking a lead Contacted or Demo sent sets a follow-up 3 days later, and the next lead opens. The clock button skips a lead until tomorrow. Every log, skip and delete can be undone from the message at the bottom.
- **Where they're listed** links to the business's Google Business Profile (or a Google Maps search by name and address when LeadFinder didn't find them on Google), wherever it found them (OpenStreetMap listing, or the TomTom map pin), their website and social pages. "Show Google map here" loads a map inside the app. Every card also has a **Google** button.
- **Follow-ups** lists everyone you need to chase, grouped Overdue, Today, This week and Later.
- **All leads** has every lead, with pipeline tiles (click one to filter), website-status tabs with counts, search, sort, CSV export and a card or compact-list view. **Filters** adds area, country, type, where it was found, search, reviews, phone and email, plus **Cut the clutter**: hide leads you've already contacted and hide whole website statuses (for example Good website, or Couldn't check). Active filters show as chips you can remove one by one. New results are announced instead of reshuffling the list under you.
- **Look and layout:** the sun/moon button switches light and dark mode, and the layout button moves the menu between the side and the top. Both are also in Settings, where the theme can follow your computer.
- Links: `?lead=ID` opens a lead directly, and `?theme=dark` or `?layout=top` open the app that way without changing your saved choice.

## Writing to leads

The "What to say" box drafts a WhatsApp message, an email and a call script from that lead's actual problems. Add your name and business in Settings so they're signed. WhatsApp opens your own WhatsApp with the message ready; you press send.

## Files

- `data/leadfinder.db`: all leads, notes and searches (SQLite). Back this up; it is not on GitHub. Copy it while the app is stopped.
- `data/settings.json`: your details and API keys. They stay on this computer and are never uploaded.
- `data/` is created on first start. Deleting it gives you a fresh, empty app.
