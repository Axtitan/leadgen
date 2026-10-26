---
version: 1
slug: "web-index-html"
primary_target: "web/index.html"
related_targets: ["web/app.css","web/app.js"]
---

Scope: LeadFinder app shell and all views (Next up, All leads, Follow-ups, Searches, Import & check, Settings). Mode: Operate. Replaces the Adire Dye Depth world.

Audience and job: the owner and a Nigerian partner, at a laptop, deciding who to contact next and contacting them. Constraints: keep every existing feature; local Python server, vanilla HTML/CSS/JS, no build step; GSAP + Flip vendored locally (user asked for GSAP).

User-pinned references: Effix leads page (clean white, pipeline stat tiles, tabs with counts, card grid with status/source pills, filter bar) for light mode; Salesforce lead dashboard (charcoal bento panels, lemon pills, circular icon buttons) for dark mode; Salesforce's bento-style pills in both. Layout option: side nav (vertical) or top nav bar (horizontal). Light and dark themes.

## Direction contract

THESIS: A lead list should feel like a tidy board of bento tiles, not a database: few words per card, the reason to call first, everything else one click deeper. It refuses the dense CRM table and the always-open detail split.

OWN-WORLD: Bento board. Light: warm grey ground #F1F1EC, white tiles r=28, hairline #E3E3DC, charcoal ink #1A1B1D, charcoal selected pills. Dark: #161615 ground, charcoal tiles #262624 / #30302E, ink #F1F0EA. Lemon #EDE65A in both, only for the primary action, the active nav item and strong leads; selected pills are inverted ink in both themes. Host Grotesk throughout (light display weight, tabular numerals); pill buttons and fields, 40px circular icon buttons; website status as dot + word pills; unverified "no website" drawn with a diagonal hatch.

STORY: The seller opens Next up, sees follow-ups and the ten strongest leads as cards, opens one, reads why, checks the Google profile, sends the drafted WhatsApp, logs it, and the card folds away as the next one moves up.

FIRST VIEWPORT: Nav (side 256px, or charcoal top bar) carrying the lemon Find leads button; page head with title, count line and Export; a row of pipeline/strength stat tiles; status tabs with counts; a filter bar (search, Filters popover, active filter chips, density switch); then a 3-column card grid. Opening a card collapses the grid to one narrow column and the lead opens beside it as a bento of tiles: header with contact pills and a Google profile button, Why them, Where they're listed, What to say, Log it. Signature interaction: the card-to-profile Flip (GSAP Flip, ~450ms, expo out); logging folds the card out and the grid reflows.

FORM: User-pinned direction (Effix x Salesforce bento merge from the user's two reference images). The roll ran for the record, seed:4bf4fc975b00d09e, and the user-pinned direction overrides the world it dealt, as new-work allows.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
