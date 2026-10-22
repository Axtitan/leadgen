# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The owner, a Nigerian founder based in Abuja selling websites and automations to small businesses, plus a Nigerian partner who works leads alongside him. A UK partner in Portsmouth may use it later (unlikely). They work on a laptop at a desk, in focused sessions. They are sellers, not engineers: they need to know who to contact and what to say, not how the website check works.

## Product Purpose

LeadFinder finds local businesses in Nigeria, the UK and the US, checks each one's web presence, and tells the seller who to contact next and what to say. Success is a session that ends with conversations started: the user opens it, sees the best leads to contact today, reaches out, and logs it.

## Positioning

The mechanism is the website check turned into a sales argument. Every lead arrives with the specific, verifiable problems in plain English ("your domain has expired", "your footer still says © 2015") and a ready-to-send message built from them. Lead lists from scrapers give names and numbers; LeadFinder gives a reason to call.

## Operating Context

- Runs locally on the owner's Windows laptop (Python server at http://127.0.0.1:8790), opened in a browser. Internet in Nigeria can be slow or intermittent.
- Leads come from OpenStreetMap (free, patchy), TomTom (free key), Google Places (optional, paid) and CSV imports (Outscraper/Apify).
- Outreach happens outside the app: phone calls, WhatsApp (via wa.me links), email and in-person visits. The app drafts the message; the human sends it.
- Target cities right now: Abuja (owner) and Portsmouth (UK partner).

## Capabilities and Constraints

- Website status buckets: no website, social/listing page only, broken, bad, needs work, decent, couldn't check. Score 0–100 with point deductions; opportunity score combines site weakness, review count and contactability.
- "No website" from OpenStreetMap is unverified and must never be presented as fact.
- Pipeline statuses: new, shortlisted, contacted, demo sent, replied, won, lost, not a fit; free-text notes.
- Background searches and website checks run continuously; results arrive while the user works.
- Stack: Python standard library server, SQLite, vanilla HTML/CSS/JS, no build step, no external JS. Web fonts from Google Fonts are acceptable.
- Must not lose existing features: filters, search history, CSV import/export, manual check, PageSpeed, outreach drafts, settings.

## Evidence on Hand

Real data only: ~1,250 real businesses in Leeds, Portsmouth, Abuja and Ikeja with real website findings. No testimonials, customer logos or results exist yet; none may be invented.

## Product Principles

1. Answer "who next?" before showing anything else.
2. Evidence before opinion: every claim about a business is something the user can verify in a click.
3. Plain words over scores; numbers only where they help a decision.
4. Calm under background work: new data never moves what the user is looking at.
5. The human sends the message; the tool makes it effortless and honest.

## Accessibility & Inclusion

Long desk sessions: comfortable contrast and type size, full keyboard use, no reliance on colour alone for status. Works on a modest laptop and a slow connection.
