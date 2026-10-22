# LeadFinder UX evaluation (Intent /evaluate, 2026-10-22)

Evaluated against the job the owner named as most important: **open the app and pick who to contact next**. Users are the owner and a Nigerian partner (possibly the UK partner later), working on a laptop at a desk. They named "too busy, too techy, too ugly" as what would make it feel wrong.

## Anti-pattern verdict

**Clean.** No deceptive or manipulative patterns in the tool itself. The outreach it writes includes an opt-out line and shows UK/US cold-contact rules. One honesty risk is handled but under-weighted: "No website" leads from OpenStreetMap are uncertain, and a pitch built on them ("you don't have a website") could be false. The warning exists only inside the detail pane.

## Priority issues

### P1 (significant friction on the core task)

1. **There is no "who next" answer, only a list to interpret.** The home view is seven colour-coded counts, an eight-control filter rail and a long list. To decide who to contact, the user must understand buckets, scores, opportunity bars and sources. Violates H8 and H6. Route: /organize (make a ranked "next up" queue the home view).
2. **The list reorders under the cursor.** Live refreshes while websites are checked re-render and re-sort the list every few seconds. A click can land on a different lead than the one aimed at (reproduced during testing). Violates H1 and H3. Route: /fortify (stable list; announce new results instead of reshuffling).
3. **Contact actions are buried.** In the detail pane, the order is verdict → problems → pipeline → outreach → contact → facts. Calling or WhatsApping the lead, the action this job ends in, sits below two screens of content. Route: /organize.
4. **Uncertain and confirmed leads look the same.** The queue mixes OpenStreetMap "no website" leads (unverified) with confirmed broken sites. The strongest leads (confirmed broken, social-only) don't stand out. Route: /articulate + /organize.

### P2 (friction users recover from)

5. **Jargon.** "Opportunity", "bucket", "Unchecked", "Needs work 62", "−25" are system terms. A new partner would need them explained. Violates H2 and H10. Route: /articulate.
6. **No follow-ups.** The pipeline records "Contacted" but never says when to chase. Leads contacted 3 days ago don't come back. Violates H6. Route: /journey.
7. **Confusing delete dialog.** Deleting a search asks a question where OK means "delete the leads too" and Cancel means "keep the leads", but Cancel still deletes the search. Violates H4 and H5. Route: /fortify.
8. **Delete has no undo**, and uses the browser's native confirm box. Violates H3.

### P3 (polish)

9. Status tiles truncate labels at mid widths. The theme toggle is unlabeled. Country shows as a two-letter code.

## Heuristic verdicts

| | Verdict | Deciding finding |
|---|---|---|
| H1 Visibility of status | Strained | Background work is visible, but the list reshuffles silently (#2) |
| H2 Real-world language | Strained | Score and bucket jargon (#5) |
| H3 User control | Broken | Clicks land on the wrong lead during refresh (#2) |
| H4 Consistency | Strained | Delete-search dialog semantics (#7) |
| H5 Error prevention | Strained | Same (#7) |
| H6 Recognition over recall | Strained | No next-lead or follow-up surfacing (#1, #6) |
| H7 Efficiency | Holds | Keyboard navigation, batch searches, CSV export |
| H8 Minimalism | Broken | Home view shows everything at once (#1) |
| H9 Error recovery | Holds | Plain-language errors with a fix suggested |
| H10 Help | Strained | No explanation of scores in context (#5) |

## Cognitive walkthrough: "pick who to contact next"

1. **Open app.** Will they know what to do? Partly: the list is sorted best-first, but nothing says so, and seven tiles compete for attention.
2. **Choose a lead.** Will they see the right action? The top rows show a score, a bar and a bucket chip. Telling "confirmed broken" from "unverified no website" requires reading the small grey headline.
3. **Decide whether it's worth it.** Will they understand the feedback? The problems are clear and in plain English. Strong.
4. **Contact them.** The phone, WhatsApp button and message are below the fold. The partner would likely scroll past the outreach tool before finding the number.
5. **Log it.** The status buttons work, but nothing schedules a follow-up.

## Positive findings

- The plain-English pitch lines are the product's strongest asset. They turn a technical audit into a sales argument.
- The generated email, WhatsApp message and call script remove a hard task.
- Honest handling of uncertainty (the OSM warning, the "couldn't check" bucket) and the legal notes.

## Recommended actions (in order)

1. /organize: make **"Next up"** the home view, a short ranked queue of the best leads to contact today. Put follow-ups due first, then confirmed problems, then the rest, with the full database one step away.
2. /organize: reorder the lead view as **who → why them → reach them → what to say → log it**.
3. /fortify: a stable list during background work, with a "12 new leads, show" notice instead of reshuffling. Fix the delete dialog and add undo.
4. /articulate: rename scores in plain words and explain them where they appear.
5. /journey: follow-up dates on "Contacted" and "Demo sent".
6. Visual (Impeccable): a calmer, better-looking world that serves the queue, not the database.
