---
name: LeadFinder
description: Adire Dye Depth. A ranked lead queue where indigo dye depth shows how strong each lead is.
colors:
  dye-1: "#C5CEEC"
  dye-2: "#8798D3"
  dye-3: "#4E66B4"
  dye-4: "#2A4396"
  dye-5: "#0B1430"
  primary: "#121A33"
  primary-ink: "#FFFFFF"
  undyed-cloth: "#EEF0F5"
  panel-white: "#FBFCFE"
  well: "#F4F6FA"
  ink: "#121A33"
  muted-ink: "#4E5977"
  faint-ink: "#6A7491"
  hairline: "#D5DAE8"
  hairline-soft: "#E4E8F1"
  focus-indigo: "#4A5FA0"
  selection-wash: "#DDE3F4"
  rail-indigo: "#0E1838"
  rail-ink: "#DCE3F7"
  rail-muted: "#9AA8D4"
  rail-active: "#2A3E7A"
  resist-ground: "#1B2A5C"
  status-broken-rust: "#B93A0B"
  status-no-website: "#7E3B8A"
  status-social: "#0E6F72"
  status-weak-site: "#A34D07"
  status-needs-work: "#876A0B"
  status-good: "#2F7A4B"
  status-unknown: "#6A7491"
  danger: "#B42318"
typography:
  display:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "27px"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "23px"
    fontWeight: 800
    letterSpacing: "-0.012em"
  title:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 750
    letterSpacing: "-0.012em"
  row-name:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
  body:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  guide:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
  label:
    fontFamily: "Hanken Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 650
rounded:
  swatch: "3px"
  sm: "6px"
  md: "10px"
  dialog: "14px"
  pill: "999px"
spacing:
  hairline-row: "12px 28px"
  pane-head: "26px 28px 12px"
  page: "30px 40px 48px"
  gap-sm: "8px"
  gap-md: "14px"
  section: "26px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.sm}"
    padding: "8px 15px"
  button-quiet:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 15px"
  button-cloth:
    backgroundColor: "{colors.undyed-cloth}"
    textColor: "{colors.rail-indigo}"
    rounded: "{rounded.sm}"
    padding: "8px 15px"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.sm}"
    padding: "8px 15px"
  chip:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.muted-ink}"
    rounded: "{rounded.pill}"
    padding: "5px 13px"
  chip-pressed:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.pill}"
  input:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 11px"
    height: "38px"
  lead-swatch:
    backgroundColor: "{colors.dye-3}"
    rounded: "{rounded.swatch}"
    width: "26px"
    height: "34px"
  nav-item-active:
    backgroundColor: "{colors.rail-active}"
    textColor: "{colors.primary-ink}"
    rounded: "8px"
    padding: "9px 10px"
  toast:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.md}"
    padding: "11px 16px"
---

# Design System: LeadFinder

## Overview

**Creative North Star: "Adire Dye Depth"**

LeadFinder is a working tool dressed in adire eleko, the Yoruba starch-resist indigo cloth. A deep indigo rail holds the navigation; a pale undyed-cloth ground carries the work; white panels hold the selected lead. The one idea the cloth carries is lead strength: the deeper a lead's swatch is dyed, the stronger the lead. Everything else stays quiet so that dye depth reads at a glance.

Density is that of a focused desk tool used for hours. Rows are separated by hairlines, not boxed into cards. Type is a single grotesk at modest sizes with tabular figures. Status never relies on colour: each one is a shaped marker plus a word. The cloth's pattern shows up in exactly one place, the starch-resist band along the rail's edge, so the motif stays special and never turns into wallpaper.

The system rejects the CRM default (a full database table led by numeric scores) as the home view. Tables exist for history pages, not for deciding who to contact next.

**Key Characteristics:**
- Five dye steps encode lead strength and selection only; thresholds are server-supplied quintiles.
- Ink, not dye, drives primary actions, pressed chips, badges and toasts.
- Status = shape + word; rust is reserved for broken sites.
- Hairline rows on an undyed ground; no cards, no floating containers in the flow.
- One family (Hanken Grotesk), heavy weights for names, tabular numerals everywhere.
- Light and dark themes share every rule; dark maps dye depth to chroma.

## Colors

An indigo-on-undyed-cloth palette: one blue family whose depth carries meaning, cool neutrals, and a small set of status hues that only ever appear beside a shape and a word.

### Primary
- **Ink** (`primary`): the action colour. Primary buttons (WhatsApp, Find leads in dialogs), pressed filter chips, count badges and toasts. Inverts to pale ink on navy in dark mode, so it always reads as the strongest contrast on the screen.

### Secondary: the dye steps
- **Dye 1, Faint Wash** (`dye-1`): weakest ready lead; also the text-selection wash and the pending-check marker.
- **Dye 2, Light Indigo** (`dye-2`): second quintile; hover hairline on quiet buttons, chips and icon buttons.
- **Dye 3, Mid Indigo** (`dye-3`): middle quintile; the indigo for links, caret, checkbox accent, running-job state and the checked-source border.
- **Dye 4, Deep Indigo** (`dye-4`): fourth quintile.
- **Dye 5, Night Indigo** (`dye-5`): strongest leads, the deepest dip.

In dark mode the steps become chroma, not darkness: `#2C3350`, `#313F7E`, `#3549AE`, `#3F58DA`, `#5C77FF`. The strongest lead is the most saturated, brightest blue. An unscored lead has an empty swatch with a dashed hairline border.

### Tertiary: status hues
- **Broken Rust** (`status-broken-rust`): broken sites (expired domain, doesn't load, page not found) and overdue follow-ups. Nothing else is rust.
- **Plum** (`status-no-website`): no website listed.
- **Teal** (`status-social`): social or listing page only.
- **Burnt Amber** (`status-weak-site`) and **Ochre** (`status-needs-work`): weak website and needs work.
- **Leaf** (`status-good`): decent site; also "Saved" confirmations.
- **Slate** (`status-unknown`): couldn't check.
- **Danger Red** (`danger`): destructive buttons and error toasts only, never a website status.

### Neutral
- **Undyed Cloth** (`undyed-cloth`): the app ground and the queue column.
- **Panel White** (`panel-white`): the detail panel, inputs, quiet buttons, the current row.
- **Well** (`well`): row hover, segmented-control track, caution and rule notes, dialog footers.
- **Ink / Muted Ink / Faint Ink** (`ink`, `muted-ink`, `faint-ink`): text, guide lines and metadata, placeholders and counts.
- **Hairline / Soft Hairline** (`hairline`, `hairline-soft`): row rules, input strokes, table rules.
- **Selection Wash** (`selection-wash`): notices and a checked source card.
- **Rail Indigo, Rail Ink, Rail Muted, Rail Active** (`rail-*`): the rail is dark in both themes; its active nav item sits on `rail-active`.

### Named Rules
**The Dye Means Strength Rule.** A filled dye block (row swatch, detail swatch, dye key) means lead strength and nothing else. The selected row is shown by a focus outline around its swatch. Dye 2 and 3 may appear as a hairline or text accent (hover borders, links), never as a filled block for anything other than strength.

**The Ink Acts Rule.** Primary buttons, pressed chips, badges and toasts use ink (`primary`), never a dye value, so an action can never be mistaken for a strong lead.

**The Rust Is Broken Rule.** Rust appears only for broken sites and overdue follow-ups. Destructive actions use `danger`, a different red.

## Typography

**Display Font:** Hanken Grotesk (with Segoe UI, system-ui, sans-serif)
**Body Font:** Hanken Grotesk
**Label/Mono Font:** none; labels use the same family at weight 650

**Character:** A single warm grotesk used throughout. Hierarchy comes from weight (400 to 800) more than size, with tight negative tracking on headings and tabular figures in the body, so counts and dates line up in columns.

### Hierarchy
- **Display** (800, 27px, 1.12, -0.02em): the selected lead's name in the detail panel; 23px on mobile.
- **Headline** (800, 23px): view titles ("Next up today", "All leads").
- **Title** (750, 17px): section headings; 15px for in-panel sections ("Why them", "What to say"); 20px dialog titles.
- **Row Name** (700, 15px): the business name in each queue row, truncated with an ellipsis.
- **Body** (400, 15px, 1.5): running text and form values.
- **Guide** (400, 13.5px, muted ink): one-line guides under titles ("10 of 182 ready... Strongest first."). Body measure on pages is capped at 62 to 70ch.
- **Label** (650, 13px, muted ink): form labels, chips, status markers, section labels in the queue. Sentence case, never uppercase-tracked.

### Named Rules
**The One Family Rule.** Hanken Grotesk everywhere, with no second display face and no monospace. Emphasis comes from weight.

## Layout

The app is a fixed-height three-zone shell. A 232px indigo rail on the left; a queue column from 380 to 520px on undyed cloth; a white detail panel filling the rest (content capped at 860px). Each zone scrolls on its own; the page itself never scrolls.

Rhythm: rows pad 12px vertically and 28px horizontally; pane heads 26px 28px 12px; full pages 30px 40px 48px; detail sections are 26px apart. Settings and import pages use auto-fit columns (min 420px, 40px gutter, max 1100px) of hairline-topped blocks.

Responsive:
- **1180px and below:** the split collapses to the queue alone; the detail panel becomes a fixed right sheet (up to 640px) that slides in over 220ms.
- **820px and below:** the rail becomes a top bar (brand, Find leads, menu button); nav drops down as an overlay; the resist band moves to the bar's bottom edge as a horizontal strip; horizontal padding tightens to 16px.

## Elevation & Depth

Flat by default. Depth comes from tone (rail, cloth, panel), not shadows. One shadow token exists and is used only for things that truly float above the page: dialogs, toasts, the slide-in detail sheet, and the mobile nav dropdown. The segmented control's selected tab has a tiny 1px lift to read as pressed-out.

### Shadow Vocabulary
- **Float** (`box-shadow: 0 1px 2px rgba(0,0,0,.08), 0 12px 32px rgba(0,0,0,.12)`; dark: `.4` / `.45`): dialogs, toasts, the overlaid detail sheet, the mobile menu.
- **Tab Lift** (`box-shadow: 0 1px 2px rgba(0,0,0,.1)`): selected segment only.

### Named Rules
**The Only Floaters Rule.** Shadow belongs to overlays. Nothing in the reading flow (rows, filters, sections) gets a shadow.

## Shapes

Small, quiet radii. Controls use 6px; containers that group controls (filters panel, segmented track, source cards, drop zone) use 10px; dialogs 14px; chips and badges are full pills. Swatches keep near-square corners (3px rows, 4px detail) so they read as cut cloth. Borders are 1px hairlines; dashed 1.5px borders mean "empty or waiting" (unscored swatch, file drop zone).

Status markers are 10px geometric shapes: square, circle, diamond, triangle, short bar, ring, or thin ring.

**The Starch-Resist Band.** The 10px band down the rail's right edge (an authored, repeating SVG of curved resist lines and dots on `resist-ground`) is the only place the cloth's pattern appears. It becomes a 6px strip along the bottom of the mobile top bar.

## Components

### Buttons
- **Shape:** gently rounded (6px), 8px 15px padding, weight 650 at 14px, icon gap 7px; small variant 5px 11px at 13px.
- **Primary:** ink fill, white text. Hover blends 14% toward the cloth.
- **Quiet:** white panel, hairline border; hover turns the border to dye 2.
- **Cloth:** undyed-cloth fill with rail-indigo text; the one button that sits on the rail (Find leads).
- **Text:** no fill, muted ink, darkens on hover (Skip for today).
- **Danger:** danger red, only for destructive confirmations.
- **Focus:** 2px focus-indigo outline, 2px offset, on every interactive element.

### Chips
- **Style:** pill, white panel, hairline border, muted 13px/650 text, optional count in `<small>` at 75% opacity.
- **State:** pressed = ink fill and ink border with white text. Hover = dye-2 border. In the status bar, chips lose their border and lead with a status marker.

### Cards / Containers
- No cards in the reading flow. Grouping is done with hairline rules and the well tone. Bordered containers (filters panel, source options, category list, gauges) appear only around form controls. A checked source card takes the selection wash and a dye-3 border.

### Inputs / Fields
- **Style:** white panel, 1px hairline, 6px radius, 38px min height, 8px 11px padding; labels stack above at 13px/650 muted.
- **Focus:** border becomes focus indigo with a 3px 25% focus-indigo halo.
- **Placeholder:** faint ink. Checkboxes and radios use the dye-3 accent.

### Navigation
- Rail nav: 14.5px/600 rail ink, 9px 10px padding, 8px radius, muted icon, count right-aligned in rail muted. Hover is a 60% rail-active wash; the current page has a solid rail-active background with white text and icon. The follow-ups count becomes a cloth-coloured pill when items are due. A live-work line at the bottom of the rail shows a status dot that pulses between two indigos while work runs.

### Lead Row (signature)
- A three-column grid (26px swatch, name and meta, right-side status) on a hairline top border. Hover = well; current row = panel white plus a focus-indigo outline around its swatch. Logging a lead slides its row out (fades and shifts 16px right over 200ms) and the next one moves up.

### Dye Swatch (signature)
- 26 by 34px in rows, 52 by 68px in the detail head. On selection the detail swatch "dips": the dye scales up from the bottom over 220ms `cubic-bezier(.16,1,.3,1)`. The dye key ("Lead strength: weak to strong") shows all five steps as 15 by 11px chips.

### Status Marker
- 10px shape plus a 13px/650 word: square = broken, circle = no website, diamond = social only, triangle = weak site, short bar = could be better, ring = good, thin slate ring = couldn't check, pulsing dye-1 dot = checking. The word is always present.

## Do's and Don'ts

### Do:
- **Do** fill a lead swatch with exactly one of the five dye steps, chosen by the server's `dye_cuts` quintiles; leave unscored leads as a dashed empty swatch.
- **Do** use ink (`primary`) for primary buttons, pressed chips, badges and toasts.
- **Do** pair every status colour with its shape and a plain-word label.
- **Do** separate list items with 1px hairlines on the undyed-cloth ground.
- **Do** show selection as a 2px focus-indigo outline offset around the swatch.
- **Do** keep the starch-resist band on the rail edge (bottom of the top bar on mobile) and nowhere else.
- **Do** keep Hanken Grotesk for every role, with tabular figures.

### Don't:
- **Don't** use a dye step as a fill for buttons, chips, badges, toasts or any non-strength meaning.
- **Don't** use rust for anything but broken sites and overdue follow-ups.
- **Don't** show status by colour alone.
- **Don't** wrap rows or sections in floating cards or give in-flow elements a shadow.
- **Don't** mark selection with a coloured side stripe.
- **Don't** repeat the cloth pattern on backgrounds, headers or empty states.
- **Don't** lead the home view with a full table or numeric scores.
