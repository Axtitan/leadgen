---
version: 1
slug: "web-index-html"
primary_target: "web/index.html"
related_targets: ["web/app.css","web/app.js"]
---

Scope: LeadFinder app shell and all views (Next up, All leads, Follow-ups, Searches, Import & check, Settings). Mode: Operate.

Audience and job: the owner and a Nigerian partner, at a laptop, deciding who to contact next and contacting them. Constraints: keep every existing feature; local Python server, vanilla HTML/CSS/JS, no build step.

## Direction contract

THESIS: The home screen answers "who next?" as a short ranked queue whose strength reads as indigo dye depth, the deeper the cloth, the stronger the lead. It refuses the CRM default: a full database table led by numeric scores.

OWN-WORLD: Adire eleko. Deep indigo rail (#0E1838) edged by a narrow starch-resist line band; pale undyed cloth ground (#EEF0F5) under white working panels; five dye steps (#AEBBE3, #6B7FBF, #344A8C, #1B2A5C, #0E1838) used only for lead strength and selection; rust (#C2410C) only for broken sites; Hanken Grotesk throughout; hairline rules, no floating cards; status as a shaped marker plus a word.

STORY: The seller opens the app, sees follow-ups due and today's ten deepest-dyed leads, reads why the top one is worth contacting, sends the drafted WhatsApp in one click, logs it, and the next lead moves up.

FIRST VIEWPORT: Left indigo rail (232px): brand, nav with counts, Find leads, live work status. Middle column (~520px): "Next up today", a guide line ("10 of 214 ready"), area chips, the dye key, follow-ups due, then ten rows each led by a dye swatch. Right panel: the selected lead's deep swatch and name, contact buttons (WhatsApp primary), Why them, What to say, Log it. Signature interaction: selecting a lead dips its swatch (dye rises in 220ms); logging a lead lifts it out of the queue and the next one moves up.

FORM: Adire Dye Depth, my first-ranked grounded candidate, chosen by the user as IMPECCABLE'S PICK over the assigned seventh (Danfo Call). seed:775a54a7758710e1

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
