---
name: LeadFinder
description: Bento board. A lead list laid out as tidy tiles, the reason to call first on top and everything else one click deeper.
colors:
  ground: "#F1F1EC"
  tile: "#FFFFFF"
  tile-well: "#F6F6F1"
  tile-deep: "#ECECE5"
  hairline: "#E3E3DB"
  hairline-strong: "#D3D3CA"
  ink: "#1A1B1D"
  ink-soft: "#3A3B3E"
  muted: "#6A6B66"
  lemon: "#EDE65A"
  lemon-hover: "#E4DC3E"
  lemon-wash: "#F8F4BE"
  lemon-ink: "#1F1E0A"
  selected: "#1F2023"
  selected-ink: "#F4F4EF"
  bar-charcoal: "#232322"
  bar-raised: "#31312F"
  bar-ink: "#F1F0EA"
  bar-muted: "#B3B2A9"
  dark-ground: "#161615"
  dark-tile: "#262624"
  dark-tile-well: "#2E2E2C"
  dark-tile-deep: "#383835"
  dark-hairline: "#353532"
  dark-hairline-strong: "#4A4A46"
  dark-ink: "#F1F0EA"
  dark-ink-soft: "#D9D8D1"
  dark-muted: "#A6A59C"
  dark-lemon-wash: "#48461F"
  dark-bar-charcoal: "#31312F"
  dark-bar-raised: "#3E3E3B"
  status-broken: "#B42318"
  status-broken-bg: "#FDECEA"
  status-social: "#6D28D9"
  status-social-bg: "#F1EAFE"
  status-no-website: "#8F5300"
  status-no-website-bg: "#FBEFD6"
  status-bad: "#B93C0B"
  status-bad-bg: "#FDECE2"
  status-weak: "#1D5FA8"
  status-weak-bg: "#E6EFFA"
  status-ok: "#157339"
  status-ok-bg: "#E3F4E8"
  status-unknown: "#57585A"
  status-unknown-bg: "#EBEBE5"
  dark-status-broken: "#FF9E94"
  dark-status-social: "#C9B0FF"
  dark-status-no-website: "#F2C76A"
  dark-status-bad: "#FFB287"
  dark-status-weak: "#97C3F5"
  dark-status-ok: "#8CDBA6"
  dark-status-unknown: "#BBBAB1"
typography:
  display:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(26px, 5cqi, 42px)"
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  figure:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  body:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Host Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  tile: "28px"
  card: "22px"
  compact-card: "18px"
  inset: "14px"
  pill: "999px"
  circle: "50%"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.lemon}"
    textColor: "{colors.lemon-ink}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 18px"
    typography: "{typography.body}"
  button-primary-hover:
    backgroundColor: "{colors.lemon-hover}"
  button-quiet:
    backgroundColor: "{colors.tile}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 18px"
  button-quiet-hover:
    backgroundColor: "{colors.tile-well}"
  button-dark:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.selected-ink}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 18px"
  button-small:
    height: "34px"
    padding: "0 14px"
    rounded: "{rounded.pill}"
  icon-button:
    backgroundColor: "{colors.tile}"
    textColor: "{colors.ink}"
    rounded: "{rounded.circle}"
    size: "40px"
  chip:
    backgroundColor: "{colors.tile}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "34px"
    padding: "0 14px"
  chip-selected:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.selected-ink}"
  status-pill:
    rounded: "{rounded.pill}"
    height: "26px"
    padding: "0 11px 0 9px"
    typography: "{typography.label}"
  input-field:
    backgroundColor: "{colors.tile-well}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    height: "42px"
    padding: "0 16px"
  lead-card:
    backgroundColor: "{colors.tile}"
    rounded: "{rounded.card}"
    padding: "18px 18px 14px 20px"
  bento-tile:
    backgroundColor: "{colors.tile}"
    rounded: "{rounded.tile}"
    padding: "22px 24px"
  stat-tile:
    backgroundColor: "{colors.tile}"
    rounded: "{rounded.card}"
    padding: "14px 16px"
  stat-tile-selected:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.selected-ink}"
  nav-link-active:
    backgroundColor: "{colors.lemon}"
    textColor: "{colors.lemon-ink}"
    rounded: "{rounded.pill}"
    height: "44px"
  top-bar:
    backgroundColor: "{colors.bar-charcoal}"
    textColor: "{colors.bar-ink}"
    rounded: "{rounded.pill}"
    height: "68px"
---

# Design System: LeadFinder

## Overview

**Creative North Star: "The Bento Board"**

LeadFinder is a board of soft, rounded tiles on a warm grey ground. Each lead is a small card that carries only its name, a website-status pill, an ink strength meter and a Google button. Everything else lives one click deeper, in a bento of tiles that opens beside a narrowed list. At rest the board is calm and low in contrast. Charcoal ink does the structural work, and a single lemon yellow marks where the seller should act next.

Both themes share one geometry. Light mode puts clean white tiles with hairline borders on warm grey. Dark mode puts charcoal tiles on a near-black ground with warm off-white ink. Lemon looks the same in both themes. Selection is always inverted ink: charcoal on light, off-white on charcoal. Navigation has two layouts that use the same tokens: a 256px side rail tile, or a charcoal top bar shaped like a pill.

Motion has one authored moment: a card opening into its profile. The grid collapses to a single column and the bento tiles stagger in. All other motion supports that moment: the reflow when a card is logged away, entrances, and the theme sweep. All of it turns off cleanly under reduced motion.

**Key Characteristics:**
- Warm grey ground with white (light) or charcoal (dark) tiles; hairline borders, no heavy chrome.
- Three nested radii: tiles 28px, cards 22px, and every control is a full pill or a circle.
- Lemon is a rare signal for what to do next; selection is inverted ink.
- Website status is a dot plus a word; an unverified status gets a diagonal hatch.
- Host Grotesk only, at medium weights, with tabular numbers wherever a count appears.
- GSAP Flip carries the card-to-profile opening; content stays visible without it.

## Colors

The palette is a near-neutral warm grey with charcoal ink, one lemon accent, and seven tinted status pairs that carry website health.

### Primary
- **Signal Lemon** (lemon): the primary action button (Find leads, and the lead's main contact button such as WhatsApp). It also marks the active navigation item in both layouts, the Google-profile row icon in "Where they're listed", the brandmark's first square, the live-search pulse dot, and text selection. On hover it deepens to Lemon Press (lemon-hover). Text on lemon is always Lemon Ink, never white.
- **Lemon Wash** (lemon-wash / dark-lemon-wash): a pale tint for gentle notices, for the file drop zone while a file is dragged over it, and for the "Very strong" strength pill in the open lead's header.

### Neutral
- **Warm Grey Ground** (ground / dark-ground): the page behind every tile.
- **Tile White** (tile) / **Charcoal Tile** (dark-tile): every card, tile, rail, popover and dialog surface.
- **Tile Well** (tile-well) and **Tile Deep** (tile-deep): fields, segmented tracks, icon wells, hover fills and nested panels inside a tile.
- **Hairline** (hairline) and **Hairline Strong** (hairline-strong): 1px tile borders and dividers. The stronger step is the hover border and the colour of an unlit strength bar.
- **Charcoal Ink** (ink), **Soft Ink** (ink-soft), **Muted** (muted): primary text, form labels, and secondary or meta text. Dark mode swaps these for the warm off-white family.
- **Inverted Ink** (selected / selected-ink): the fill of every selected state: filter chips, the selected stat tile, the current pipeline step, count badges and the dark button. In dark mode it flips to off-white with charcoal text.
- **Bar Charcoal** (bar-charcoal / dark-bar-charcoal): the top bar and the mobile header. It stays charcoal in both themes, with Bar Ink and Bar Muted for its text.

### Tertiary: status pairs
Seven text-and-fill pairs carry website health on pills, on tabs, and on the "Why them" dots: Broken (red), Social page only (violet), No website (amber), Bad (orange), Weak or could be better (blue), Good (green), and Unknown or pending (grey). Light mode uses deep text on a pale tint. Dark mode uses light text on a translucent tint of the same hue, for example rgb(255 110 95 / .14) behind dark-status-broken.

### Named Rules
**The Lemon Means Act Rule.** Full-strength lemon appears only where the seller acts next or where the app is live: the primary button, the active nav item, the Google-profile row and the live dot. Cards on the board never carry lemon; their strength shows as ink bars only.

**The Inverted Ink Rule.** A selected state always uses the ink colour as its fill and the ground colour as its text, in both themes. Never show selection with lemon or with a status colour.

## Typography

**Display Font:** Host Grotesk (with ui-sans-serif, system-ui, Segoe UI fallback), loaded from Google Fonts at weights 300–700.

**Character:** One grotesk at medium weights does every job. Large type gets lighter and tighter (400 at -0.03em). Small type gets heavier (600) so names stay legible on a busy board. Every count uses tabular numerals.

### Hierarchy
- **Display** (400, clamp(26px, 5cqi, 42px), 1.08, -0.03em): the open lead's name, sized to its tile by container width.
- **Headline** (500, 32px, 1.15, -0.025em; 26px under 860px): page titles. Dialog titles use the same voice at 22px.
- **Title** (600, 16px, -0.01em): tile headings ("Why them", "What to say"). Card names use 600 at 16.5px (15px in the compact list).
- **Figure** (500, 22px, -0.02em, tabular): stat-tile counts and audit gauges.
- **Body** (400, 14px, 1.5): default text. Guide copy is 13.5px, and page subtitles are capped at 70ch.
- **Label** (500, 12.5–13px): pills, chips, tabs, field labels and card meta. Count suffixes and badges are 11.5–12px at weight 600.

### Named Rules
**The Tabular Count Rule.** Any number that can change (tab counts, nav counts, stats, table numerals) uses tabular figures, so the board doesn't jitter as counts update.

**The No Shouting Rule.** No uppercase, no letter-spaced labels. Hierarchy comes from size and weight only.

## Layout

The shell is a CSS grid that switches on the root `data-layout` attribute.

- **Side:** a 256px column (228px under 1100px) holds a full-height, sticky rail tile inset 12px from the edges. The lemon Find leads button sits at the bottom of the rail.
- **Top:** a 68px charcoal pill bar, sticky at 12px, holds the nav links in a row. The work-status line hides under 1100px.
- **Mobile:** under 860px both layouts become one 60px charcoal header with a 22px bottom radius. A menu button opens the links as a floating tile.

Views stack with a 16px gap and are padded 24px 28px. The top padding drops to 14px in the top layout, and mobile uses 18px 16px. Stat tiles run six across, three under 1280px, and two under 860px. The card grid is auto-fill at minmax(290px, 1fr) with 12px gaps. Compact density stacks cards in a list with 6px gaps, and from 1100px up each compact card becomes a three-column row.

Opening a lead splits the board into a 340px list column (300px under 1280px) and a detail column. Both columns are sticky and scroll independently, and the stat row hides. On mobile the detail becomes a full-screen sheet on the ground colour. Inside the detail, tiles stack with 12px gaps and split into two columns once the container is 740px or wider. Pages like Settings use a bento grid of minmax(380px, 1fr) tiles, up to 1240px wide.

Spacing follows a rhythm based on 2px and 4px steps, mostly 6, 8, 12, 16, 24 and 28px. Tile padding is 22px 24px (18px under 480px).

## Elevation & Depth

The board is mostly flat. Depth comes from tone (a tile on the ground, a well inside a tile) and from 1px hairlines. Shadows appear only on hover and on anything floating above the board.

### Shadow Vocabulary
- **Lift** (`box-shadow: 0 1px 2px rgb(30 30 20 / .04), 0 10px 28px -14px rgb(30 30 20 / .16)`; dark: `0 1px 2px rgb(0 0 0 / .3), 0 12px 30px -14px rgb(0 0 0 / .6)`): a card on hover.
- **Pop** (`box-shadow: 0 2px 6px rgb(30 30 20 / .06), 0 24px 48px -16px rgb(30 30 20 / .28)`; dark: `0 2px 8px rgb(0 0 0 / .4), 0 28px 56px -18px rgb(0 0 0 / .75)`): popovers, dialogs, the mobile menu and toasts.
- **Ring** (`box-shadow: 0 0 0 1px` ink, with an ink border): the current card and a checked source option. It reads as a 2px ink outline, not as elevation.

### Named Rules
**The Flat Until Touched Rule.** Tiles and cards sit flat with a hairline at rest. A card lifts only on hover, and only floating layers carry Pop.

## Shapes

The shape language is nested roundness:

- **Large containers** (rail, bento tiles, empty states, dialogs): 28px.
- **Cards and stat tiles:** 22px, or 18px when compacted.
- **Inner panels and wells:** 14–20px.
- **Interactive controls:** always a full pill. This covers buttons, fields, chips, segmented controls, nav links and the top bar itself.
- **Icon buttons, icon wells and status dots:** perfect circles.

Textareas relax to 20px so multi-line text doesn't sit in a capsule. Drop zones and empty states have dashed 1.5px borders.

## Components

### Buttons
Soft, capsule-shaped and confident.
- **Shape:** full pill (999px), 40px tall (34px small), 18px side padding, weight 500.
- **Primary (lemon):** Signal Lemon fill with Lemon Ink text; hover goes to Lemon Press. Use one per region: Find leads in the nav, and the main contact action in the lead header.
- **Quiet:** tile fill, hairline border and ink text. Hover goes to Tile Well with the strong hairline. Used for Call, Find on Google, Export and Filters.
- **Dark:** Inverted Ink fill, for a strong secondary action.
- **Text / link:** a muted text button, or an underlined ink link (3px offset) whose underline thickens on hover.
- **Press:** every button scales to 0.97 on press (icon buttons to 0.94) with the expo-out ease.
- **Icon button:** a 40px circle (32px small, 30px on cards) with a hairline border and an 18px stroke icon. On the charcoal bar it turns transparent with a 14% white border.

### Chips
- **Style:** 34px pill, tile fill, hairline border, 13px label.
- **State:** a selected chip is Inverted Ink. Active-filter chips are 30px, on Tile Well, with a small × icon.

### Status pills (signature)
- **Style:** a 26px pill holding a 7px dot in the current colour followed by the word. Text and fill come from the status pair.
- **Unverified:** an unchecked "No website listed" pill keeps its fill and adds a 135° hatch: 1.5px stripes every 6px, in the status colour at 16%. Its dot becomes a hollow ring.
- **Pending:** the dot blinks while a check runs.
- Tabs reuse the same dot in front of the label, and the active tab gets a 2px ink underline.

### Strength meter (signature)
Five rising 3px bars, 5px to 13px tall. Lit bars are ink and unlit bars are the strong hairline. On cards the meter is bars only, inside a 26px pill with a hairline border. In the open lead's header it adds the word. At the top level ("Very strong") the header pill takes Lemon Wash, and in dark mode its bars turn lemon.

### Cards / Containers
- **Lead card:** 22px corners, tile fill, hairline border, padding 18px 18px 14px 20px. The whole card is one button, with links raised above it. Hover adds Lift, and the open lead's card gets an ink ring.
- **Bento tile:** 28px corners, tile fill, hairline border, 22px 24px padding and a 16px/600 heading.
- **Stat tile:** 22px corners, a 38px circular icon well, and a label above a 22px figure. It works as a filter and inverts to ink when pressed.

### Inputs / Fields
- **Style:** 42px pill, Tile Well fill, hairline border and 16px padding. Search and sort sit on tile fill with a 17px leading icon. Selects use a custom chevron.
- **Focus:** the border turns ink and the fill lifts to tile. Keyboard focus adds a 2px outline (ink in light, lemon in dark).
- **Segmented control:** a pill track on Tile Well. The chosen option is a raised tile pill with a soft 1px shadow.
- **Pipeline track:** a well with 22px corners holding pill-shaped steps. The current step is Inverted Ink.

### Navigation
- **Side rail:** a full-height tile with 28px corners. Links are 44px pills with an 18px icon, a label and a count. Hover is Tile Well, and the active link is Signal Lemon.
- **Top bar:** a 68px charcoal pill. Links drop their icons and hover to Bar Raised. The active link is Signal Lemon with Lemon Ink.
- **Mobile:** a charcoal header with a 22px bottom radius. The links open as a floating tile with 24px corners and Pop.

### Toast
A charcoal pill at the bottom centre with a lemon action link. It inverts to off-white in dark mode, and errors are deep red.

### Motion
Motion lives in one module that does nothing when GSAP is missing or reduced motion is on.

- **Opening and layout changes:** the card-to-profile opening and every layout change use GSAP Flip (0.45s, expo.out; 0.55s for the layout switch).
- **Reflow:** lists reflow with Flip (0.4s), and new cards fade up 8px with a 0.12s stagger.
- **Entrance:** tiles and cards rise 10–18px over 0.42s (power3.out), staggered 0.025–0.05s and capped at 0.24s in total.
- **Logging a lead:** its card folds away, fading and scaling to 0.96 over 0.2s.
- **Theme toggle:** a View Transition sweeps the new theme in as a circle from the button (0.55s).
- **CSS transitions:** 0.15s colour fades with `cubic-bezier(.16, 1, .3, 1)`.
- **First paint:** a `booting` class blocks all transitions until the first view has rendered.

## Do's and Don'ts

### Do:
- **Do** keep every control a full pill and every icon button a 40px circle; keep tiles at 28px and cards at 22px.
- **Do** show selection as Inverted Ink (selected / selected-ink) in both themes.
- **Do** write website status as dot + word, and hatch it when the status is unverified.
- **Do** keep cards sparse: name, one or two status pills, ink strength bars, the Google button.
- **Do** set every changing count in tabular figures.
- **Do** route new motion through the motion module so it respects reduced motion and the boot guard.

### Don't:
- **Don't** put lemon on board cards or use it for a selected state; it marks the next action, the active nav item and live state only.
- **Don't** set white text on lemon; use Lemon Ink.
- **Don't** convey status by colour alone; the word is always there.
- **Don't** give tiles or cards a resting shadow; Lift is for hover, Pop for floating layers.
- **Don't** add uppercase or letter-spaced labels above headings.
- **Don't** hide content behind animation; with no GSAP, changes just happen.
