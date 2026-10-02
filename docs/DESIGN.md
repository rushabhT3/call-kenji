# Design

The visual and interaction spec for the Call Kenji page: the landing area (role card, phone number, browser call) and the live X-ray (transcript, Turn, Strategist, Compliance, Latency, post-call records). Build only from the tokens in this file; a hard-coded colour, size or duration in a component is a bug.

Measured on 2026-10-02. Reference captures live locally in `docs/design-refs/` (git-ignored, see its README).

---

## 1. Intent

Minato Servicer is a fictional debt servicer, and the visitor plays someone who owes money. That situation is tense, so the page has to feel the opposite of a collections letter.

- **Warm.** Cream paper, warm brown ink, an editorial serif. Nothing cold, blue-black or neon.
- **Trustworthy.** Every safeguard is visible and spelled out in words, never only in colour. Numbers are tabular and they don't animate, because a figure that counts up looks like marketing.
- **Human.** The conversation is the main surface. Kenji's latest line is the largest text in the live view.
- **Calm.** One accent colour, no glow, no shadows on cards, and the shortest motion that still explains a change (300 ms or less on the live page).

**The 10-second test.** A non-engineer opening the live page mid-call must be able to answer three questions without scrolling:

1. *Is the call live?* The header shows a dot, the word LIVE and a running timer.
2. *What is happening right now?* The "Now" strip has one plain-English sentence above the transcript.
3. *Is Kenji behaving?* Each card opens with a one-sentence summary, and the Compliance card's summary counts the safeguards that are holding.

Everything else (scores, milliseconds, flow nodes) is supporting detail beneath those sentences.

---

## 2. References: what we took and why

All values below were read from `getComputedStyle` and `document.fonts` on the live sites. The tool was Playwright 1.61.1 driving Chrome 149 at 1440×900 and 390×844 (device pixel ratio 1), after fonts were ready, the network was idle and cookie notices were dismissed. Colour frequencies are weighted by character count for text and by area for backgrounds. The Awwwards pages list palettes but not fonts. Their listings were:

| Site | Awwwards | Listed palette |
|---|---|---|
| microsoft.ai | Site of the Day 30 Nov 2025, score 7.16 | #FEF9ED, #5D524B |
| cerebrium.ai | Site of the Day 10 Sep 2026, score 7.39 | #172B76, #902177 |
| L.I.S.A. (lisa.locomotive.ca/en) | Site of the Day 16 Sep 2026, score 7.48 | #000000, #FFFFFF |

### 2.1 Microsoft AI (primary): palette, type and calm

**Measured**

| Property | 1440 | 390 |
|---|---|---|
| Faces loaded | Bradford LL 450 roman + italic (Lineto, self-hosted; 600 declared but unused on the home page). Red Hat Mono 400 and 500. | same |
| Root font size | 10px. Sizes come from a fluid unit (1440 values ≈ design × 0.833). | 10px |
| Text colour | #5D524B on 99% of all characters | same |
| Backgrounds by area | #FEF9ED page; #F7F1E3 cards; #FBF0DC menu items; #F7ECD9 buttons; #FBD3BE hero tint | adds the tiles #E3EFDD, #F6EBC6, #E6EFEE, #D7E6D6 |
| Hero h1 | 125px / 1.0, −5px (−0.04em), 450. "Humanist" set in italic over a roman line. | 48.5px / 1.15, −0.03em |
| Editorial sizes | 56.89 / 1.0; 42.67 / 48 (−0.02em); 37.33 / 1.0 (−0.02em); 28.44 / 34.13 (−0.0225em); 21.33 / 26.67 (−0.01em) | 31.0, 29.1, 26.2, 23.3; body 17.46 / 23.2 |
| Mono roles | Nav 13.33px +0.1em; caption 14.22 / 19.9 +0.05em; description 11.56 / 18.49; button 14.22px 500 | 12px throughout |
| Container | 1383px, 28px side gutters | 16px gutters |
| Header | Floating cream bar, radius 5px, 59px tall, inset 28px, 33px from the top | 67px tall, inset 15px |
| Section rhythm | 120px margins and padding, up to 266px | 58–194px |
| Button | Red Hat Mono 14.22px / 500, padding 14.22 × 42.67 (1em × 3em), radius 28.44 (pill), bg #F7ECD9, ink text | 12px, padding 12 × 36, 36px tall, radius 24 |
| Radii | 2, 2.5, 3.33, 4.17, 5px (crisp editorial corners); 28.44 and 50px pills | 3.9, 4.85, 24, 50px |
| Shadows | Exactly one: `0 4px 40px rgba(93,82,75,0.30)`, on the floating accessibility toggle | none |
| Motion | Reveals use opacity + transform at 1.3s and 1.8s with `cubic-bezier(0.43,0.195,0.02,1)` (54 elements). Colour and background use 0.6s `cubic-bezier(0.215,0.61,0.355,1)`. | same |

**Taken**

- **The whole base palette.** Cream #FEF9ED, warm brown #5D524B and the three cream surfaces. #5D524B on #FEF9ED measures 7.21:1, so kanji strokes and small subtitles stay crisp.
- **The faces.** A book serif at weight 450 does all the talking, with Red Hat Mono for labels and buttons. Red Hat Mono is used as-is. Bradford LL is commercial, so it is replaced with Newsreader (see 3.2).
- **The editorial hero.** A very large serif display with negative tracking (−0.04em), one italic accent line, a quiet mono eyebrow, and lots of air (120px section rhythm).
- **The floating inset header bar** (radius 5px), the **pill buttons** in #F7ECD9, and the **single soft shadow**, used only for floating elements.
- **The state tints** (#E3EFDD, #F6EBC6, #E6EFEE). These became the backgrounds for the pass, warning and info pills.
- **The slow editorial reveal curve**, on the landing hero only, once.

**Left behind**

- The photographic gradient hero.
- 1.3–1.8s motion anywhere on the live page.
- Hairline-thin mono at 11.56px. Our minimum is 12px.

### 2.2 Cerebrium (secondary): metric and observability anatomy

**Measured**

| Property | 1440 | 390 |
|---|---|---|
| Faces loaded | Suisse Int'l 400, Suisse Int'l Mono 400/500, ABC Favorit Trial 300 (display). All three are commercial. | same |
| Colours | Navy text #172B76, muted #586490, pink #FF488B; light surfaces #FFFFFF / #EEF2F5 / #DBE5ED; dark hero #101421 | same |
| Display | Favorit 86.09 / 1.0, −0.025em, weight 300; 72.6 / 76.2 | — |
| Metric value | 26.52px / 35.8 (1.35), −0.025em | 20 / 27 |
| Body | 18 / 27 (1.5), +0.01em | 17 / 25.5 |
| Labels | Mono 13px / 13.91, uppercase, −0.025em | same |
| Range chart (the latency comparison) | Outer card radius 15px, padding 24px. Inner panel radius 10px, padding 24px, row gap 16px, `backdrop-filter: blur(50px)`. Each row is a mono label above a [5px bar, radius 10px] + [value, basis 56px] pair with an 8px gap. | same |
| Segmented control | Track #EEF2F5, padding 4px, radius 7px. Tabs 44px tall, padding 8 × 20, 17px. Active indicator #586490 slides in 0.2s `cubic-bezier(0,0,0.2,1)`. | — |
| Chips | Mono 13px uppercase, padding 8px, radius 7px. Navy fill with white text, or white fill with navy text. | same |
| Section label | 6×6px square + mono uppercase label | same |
| Buttons | 54px tall, padding 0 20px, radius 7px | 42px tall, padding 0 14px |
| Container | max-width 2000px, padding 40px; two 670px columns with a 20px gap | padding 15px |
| Radii (count) | 7px (237), 10px (34), 15px (4), 32px (section corners) | 7, 10, 15, 32 |
| Shadows | None on the whole page | none |
| Motion | 0.2s `cubic-bezier(0.4,0,0.2,1)` on 97 of about 125 transitions; 0.35–0.4s `cubic-bezier(0.645,0.045,0.355,1)` for larger moves; scramble-text labels; WebGL hero and globe | same |

**Taken**

- **The metric anatomy.** A mono uppercase label sits above a row with a thin bar (5–6px, fully rounded) and a right-aligned value of fixed width. This is exactly how a latency stage reads at a glance. It becomes the Latency card's stage rows and the Turn card's score bar.
- **The working rhythm for data cards.** 24px padding, 16px gaps between rows, and radii in the 7–15px range for data containers.
- **No shadows on cards.** Separation comes from surface tint and a hairline instead.
- **The 200ms standard curve** for hover, press and state changes.
- **The small square marker + mono label** pattern for card headers.

**Left behind**

- The dark theme, WebGL, the pink accent and scramble-text.
- The frosted inner panel (`backdrop-filter: blur(50px)`). Frosted glass is on the avoid list, so data sits on solid #F7F1E3.

### 2.3 L.I.S.A. by Locomotive: the conversation is the interface

**Measured**

| Property | 1440 | 390 |
|---|---|---|
| Faces loaded | Helvetica Now Display 400 (commercial) for everything; PP Locomotive New Light for the cookie heading | same |
| Message | One message at a time at x = 40px, about 440px wide, 26px / 28.6 (1.1), black | 22px / 24.2, on a white bottom sheet with rounded top corners |
| Reveal | Characters appear one by one (one span each), with a block cursor while "speaking" (`-show-cursor`) | same |
| History | The previous message stays above, with `filter: blur(4px)` and `transform: scale(0.8) translateY(-97px)` | same |
| Transition | `transform 0.3s, filter 0.3s cubic-bezier(0.215,0.61,0.355,1)` | same |
| Reply chips | 12px, padding 6 × 18, 26px tall, radius 999px. White fill with black text (inverted on the mobile sheet). The outline chip uses a 0.8px border at 20% black. | same |
| Spacing tokens exposed in CSS | 14 / 20 / 30 / 40 / 80 / 150 / 200 / 250 | 8 / 20 / 30 / 40 / 52 / 80 / 100 / 140; 4-column grid, 10px gutter |

**Taken**

- **The transcript as the primary surface,** with no chat bubbles and no avatar circles: text set large on the page itself.
- **One "current" line that is clearly bigger and darker,** with the history quieter above it (LISA's 26 → 22px sizes are reused for our current line).
- **The block cursor** as the "speaking now / listening" signal.
- **Pill chips** as the shape for status pills.
- **The 300ms ease-out curve** for line changes. microsoft.ai uses the same curve for colour, so it becomes our main live-page curve.

**Left behind**

- **The blur on past lines.** Blurred kanji are unreadable, and the visitor needs the history. Past lines recede through size and colour only.
- Character-by-character reveal of final text. We show words as speech recognition returns them.
- The 3D head and its WebGL.

---

## 3. Tokens

### 3.1 Colour

The base palette is microsoft.ai's. #574C45 is one step darker than the brand brown #5D524B, so body text reaches AAA on every surface; the two look identical side by side. The accent is a terracotta taken from the hue of microsoft.ai's peach hero tint (#FBD3BE) and darkened until it passes AA as text.

| Token | Hex | Use |
|---|---|---|
| `--color-bg` | #FEF9ED | Page background (microsoft.ai page bg) |
| `--color-surface` | #F7F1E3 | Cards (microsoft.ai cards) |
| `--color-surface-sunken` | #FBF0DC | Header bar, quiet wells (microsoft.ai menu items) |
| `--color-surface-action` | #F7ECD9 | Secondary buttons, pending pills (microsoft.ai buttons) |
| `--color-surface-action-hover` | #F1E3CB | Secondary button hover |
| `--color-surface-code` | #F3EAD8 | JSON / code blocks |
| `--color-tint-peach` | #FBD3BE | Outcome card, call panel, text selection (microsoft.ai hero tint) |
| `--color-ink` | #5D524B | Brand ink: primary button fill, icons, budget marker |
| `--color-text` | #574C45 | Body text |
| `--color-text-strong` | #3B322C | Headlines, Kenji's current line, metric values |
| `--color-text-muted` | #6F6259 | Labels, timestamps, subtitles, interim speech |
| `--color-text-on-ink` | #FEF9ED | Text on ink fills |
| `--color-border-subtle` | #E9E0CE | Card outlines and dividers (decorative, no contrast duty) |
| `--color-border-strong` | #958779 | Input and code-cell outlines (UI boundary, ≥ 3:1) |
| `--color-accent` | #A8461F | Live dot, "You" speaker label and rule, links on hover |
| `--color-focus` | #A8461F | Focus ring |
| `--color-success-text` / `-bg` / `-fill` | #2E5A34 / #E3EFDD / #46704A | Pass |
| `--color-warning-text` / `-bg` / `-fill` | #6E4D0C / #F6EBC6 / #94650C | Caution (near limit, lagging subtitle) |
| `--color-danger-text` / `-bg` / `-fill` | #922F1E / #FBE1D3 / #B3432C | Blocked, over budget, connection lost |
| `--color-info-text` / `-bg` | #2F5558 / #E6EFEE | Neutral facts ("Not sent", "Demo replay") |
| `--color-track` | #EDE3D0 | Empty part of bars |

**Contrast, text pairs** (WCAG 2.x relative luminance; AA needs 4.5:1, AAA needs 7:1)

| Text | Background | Ratio | Grade |
|---|---|---|---|
| `text` #574C45 | `bg` #FEF9ED | 7.92:1 | AAA |
| `text` #574C45 | `surface` #F7F1E3 | 7.38:1 | AAA |
| `text` #574C45 | `surface-sunken` #FBF0DC | 7.37:1 | AAA |
| `text` #574C45 | `surface-action` #F7ECD9 | 7.11:1 | AAA |
| `text` #574C45 | `surface-action-hover` #F1E3CB | 6.57:1 | AA |
| `text` #574C45 | `surface-code` #F3EAD8 | 6.96:1 | AA |
| `text` #574C45 | `tint-peach` #FBD3BE | 6.01:1 | AA |
| `text-strong` #3B322C | `bg` #FEF9ED | 11.91:1 | AAA |
| `text-strong` #3B322C | `surface` #F7F1E3 | 11.11:1 | AAA |
| `text-strong` #3B322C | `surface-code` #F3EAD8 | 10.47:1 | AAA |
| `text-strong` #3B322C | `tint-peach` #FBD3BE | 9.03:1 | AAA |
| `ink` #5D524B | `bg` #FEF9ED | 7.21:1 | AAA |
| `ink` #5D524B | `surface` #F7F1E3 | 6.72:1 | AA |
| `text-muted` #6F6259 | `bg` #FEF9ED | 5.60:1 | AA |
| `text-muted` #6F6259 | `surface` #F7F1E3 | 5.23:1 | AA |
| `text-muted` #6F6259 | `surface-sunken` #FBF0DC | 5.21:1 | AA |
| `text-muted` #6F6259 | `surface-action` #F7ECD9 | 5.03:1 | AA |
| `text-muted` #6F6259 | `surface-code` #F3EAD8 | 4.93:1 | AA |
| `text-on-ink` #FEF9ED | `ink` #5D524B | 7.21:1 | AAA |
| `text-on-ink` #FEF9ED | `text-strong` #3B322C | 11.91:1 | AAA |
| `accent` #A8461F | `bg` #FEF9ED | 5.61:1 | AA |
| `accent` #A8461F | `surface` #F7F1E3 | 5.24:1 | AA |
| `success-text` #2E5A34 | `success-bg` #E3EFDD | 6.72:1 | AA |
| `success-text` #2E5A34 | `surface` #F7F1E3 | 7.09:1 | AAA |
| `warning-text` #6E4D0C | `warning-bg` #F6EBC6 | 6.45:1 | AA |
| `danger-text` #922F1E | `danger-bg` #FBE1D3 | 6.35:1 | AA |
| `danger-text` #922F1E | `surface` #F7F1E3 | 7.04:1 | AAA |
| `info-text` #2F5558 | `info-bg` #E6EFEE | 7.01:1 | AAA |
| `text-on-ink` #FEF9ED | `danger-fill` #B3432C | 5.32:1 | AA |
| `text-strong` #3B322C | `success-bg` #E3EFDD | 10.52:1 | AAA |
| `text-strong` #3B322C | `surface-sunken` #FBF0DC | 11.08:1 | AAA |
| `accent` #A8461F | `surface-sunken` #FBF0DC | 5.22:1 | AA |

Rules that follow from the table:

- Running text (transcript, card body, SMS preview) uses `text` or `text-strong`, which is AAA on every surface except code (6.96, AA) and peach (6.01, AA).
- `text-muted` is never used on `tint-peach` (4.25:1, fails). On the peach call panel and outcome card, captions and secondary lines use `text`.

**Contrast, non-text pairs** (WCAG 1.4.11 requires ≥ 3:1)

| Element | Against | Ratio |
|---|---|---|
| `border-strong` #958779 | `bg` / `surface` | 3.32:1 / 3.10:1 |
| `focus` #A8461F | `bg` / `surface` | 5.61:1 / 5.24:1 |
| `success-fill` #46704A | `track` / `surface` | 4.49:1 / 5.07:1 |
| `warning-fill` #94650C | `track` / `surface` | 4.00:1 / 4.52:1 |
| `danger-fill` #B3432C | `track` / `surface` | 4.39:1 / 4.96:1 |
| `ink` #5D524B (budget marker) | `track` | 5.95:1 |

The focus ring sits 3px outside the element, so it is always measured against the page or card behind it, never against an ink-filled button.

### 3.2 Typography

**Faces.** All four are SIL Open Font License, variable, and on Google Fonts (axes confirmed against the CSS2 API on 2026-10-02).

| Role | Face | Axes requested | Why |
|---|---|---|---|
| Latin text and display | **Newsreader** | wght 400–600, opsz 6–72, ital | microsoft.ai's Bradford LL is a commercial Lineto face. Newsreader is the closest free match: a contemporary book serif with moderate contrast and an editorial texture. Its optical-size axis mimics how Bradford tightens at display sizes and opens up at text sizes, and it takes the measured weight of 450 directly. Its default figures are already tabular (measured: "111111" and "000000" are both 136.9px wide at 40px). |
| Labels, numbers, code | **Red Hat Mono** | wght 400–500 | The exact face microsoft.ai uses. Monospaced digits keep every timer and millisecond value from jittering. |
| Japanese text | **Noto Serif JP** | wght 400–600 | Mincho pairs with a Latin book serif, so a mixed line such as 「¥35,000のお支払い」 reads as one voice. Weight 500 is used for the current line, where thin Mincho strokes would otherwise fade at 22px. |
| Japanese in small UI | **Noto Sans JP** | wght 400–500 | Reached through the mono stack: Red Hat Mono has no kana or kanji, so 本人確認 in a 12–13px label falls back to Gothic, which survives small sizes where Mincho does not. |

**Loading.** Prefer self-hosting through the Fontsource variable packages, so visitors make no third-party request. These are `@fontsource-variable/newsreader` (import `opsz.css` and `opsz-italic.css`), `@fontsource-variable/red-hat-mono`, `@fontsource-variable/noto-serif-jp` and `@fontsource-variable/noto-sans-jp`, all OFL-1.1. Pin versions in `docs/VERSIONS.md`. If self-hosting is not used, this Google Fonts URL returns 200:

```
https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=Red+Hat+Mono:wght@400..500&family=Noto+Serif+JP:wght@400..600&family=Noto+Sans+JP:wght@400..500&display=swap
```

Both routes slice the Japanese faces by `unicode-range`, so only the glyph ranges actually used are downloaded. Use `font-display: swap`. Preload only the Newsreader roman file, because it carries the landing headline.

**Scale.** The scale is modular with ratio 1.2 from an 18px body at 1440. The steps land on microsoft.ai's measured sizes: 21.6 (measured 21.33), 37.3 (37.33) and 53.7 (56.89). Sizes are fluid between 390 and 1440 using `clamp()`. Root font size is 16px.

| Token | 390 → 1440 | Line height | Tracking | Weight | Face | Use |
|---|---|---|---|---|---|---|
| `--text-display` | 44 → 92px | 1.0 | −0.04em | 450 | serif | Landing headline |
| `--text-h1` | 34 → 54px | 1.15 | −0.02em | 450 | serif | Page titles |
| `--text-h2` | 28 → 37px | 1.15 | −0.02em | 450 | serif | Section titles, outcome, phone number |
| `--text-h3` | 22 → 26px | 1.3 | −0.01em | 450 | serif | Card titles in prose, role name |
| `--text-lead` | 19 → 22px | 1.3 (Latin) | −0.01em | 400 | serif | Landing lead, "Now" strip |
| `--text-body` | 17 → 18px | 1.6 | 0 | 400 | serif | Paragraphs, card summaries |
| `--text-small` | 15px | 1.6 | 0 | 400 | serif | Notes, help text |
| `--text-caption` | 12 → 13px | 1.4 | +0.06em, uppercase for English | 500 | mono | Labels, pills, timestamps |
| `--text-line-current` | 22 → 26px | 1.7 | +0.02em | 500 | serif (JA) | Kenji's latest final line |
| `--text-line` | 17 → 19px | 1.8 | +0.02em | 400 | serif (JA) | Every other transcript line |
| `--text-subtitle` | 15 → 16px | 1.5 | 0 | 400 | serif | English subtitle under each line |
| `--text-metric` | 32 → 40px | 1.0 | −0.02em | 450 | serif, tabular | Headline numbers (latency, amount) |
| `--text-metric-sm` | 15 → 16px | 1.4 | 0 | 500 | mono | Stage values, p50/p95 |
| `--text-code` | 13px | 1.6 | 0 | 400 | mono | JSON |
| `--text-digit` | 40px | 1.0 | 0 | 500 | mono | Link-code digits |

**Japanese rules.** These apply to everything marked `lang="ja"`:

- **Line height is 1.7 or more for all Japanese, with no exception:** 1.8 for running text and 1.7 for 22px and above.
- `letter-spacing: 0.02em`.
- `line-break: strict` and `word-break: normal` give correct kinsoku.
- `font-feature-settings: "palt"` only at 22px and above, to tighten kana in headings and the current line.
- Never set Japanese in italic.
- Mark every Japanese span with `lang="ja"` and every English subtitle with `lang="en"`, so fonts, line breaking and screen-reader voices switch correctly.

**Numbers.** Every number uses `font-variant-numeric: tabular-nums lining-nums`. That covers timers, milliseconds, amounts, dates, scores, the phone number and the link code. Format with `Intl.NumberFormat("en-US")` (1,180 ms; ¥35,000). Values change in place; they never count up or tick.

### 3.3 Spacing

The base unit is 4px. Cerebrium's 24px card padding and 16px gaps, LISA's 20/40/80 steps and microsoft.ai's 120px section rhythm all sit on this grid.

| Token | px | Typical use |
|---|---|---|
| `--space-1` | 4 | JA line to its English subtitle |
| `--space-2` | 8 | Bar to value; icon to label; between code cells |
| `--space-3` | 12 | Pill padding; visitor-line rule offset |
| `--space-4` | 16 | Card row gap; mobile gutter; mobile rail gap |
| `--space-5` | 20 | Mobile card padding |
| `--space-6` | 24 | Desktop card padding; gap between transcript turns |
| `--space-7` | 32 | 1024 gutter; gap before Kenji's current line |
| `--space-8` | 40 | 1440 gutter; landing panel padding |
| `--space-9` | 48 | Card-group separation |
| `--space-10` | 64 | Mobile section gap |
| `--space-11` | 80 | 768 section gap |
| `--space-12` | 96 | Hero headline to role card (≥ 1024) |
| `--space-13` | 120 | Section gap at ≥ 1024 (microsoft.ai rhythm) |
| `--space-14` | 160 | Landing hero top padding at 1440 |

### 3.4 Radius

| Token | px | Source | Use |
|---|---|---|---|
| `--radius-xs` | 3 | microsoft.ai 2–3.33px | Bar ends on non-pill bars, kbd |
| `--radius-sm` | 5 | microsoft.ai header bar | Header bar, inputs, code cells, JSON block |
| `--radius-md` | 10 | Cerebrium inner panel | Cards |
| `--radius-lg` | 15 | Cerebrium outer card | Outcome card, landing role card and call panel |
| `--radius-pill` | 999 | microsoft.ai buttons, LISA chips | Buttons, status pills, bars |

### 3.5 Elevation

Cards have no shadow: they separate from the page through `surface` plus a hairline, which matches Cerebrium (no shadows at all) and microsoft.ai (one shadow on the whole page).

| Token | Value | Use |
|---|---|---|
| `--shadow-float` | `0 4px 40px rgba(93, 82, 75, 0.30)` (microsoft.ai, measured) | Only elements that float over content: the mobile call bar, the "Jump to latest" pill, the "Copied" confirmation |

### 3.6 Motion

| Token | Value | Source | Use |
|---|---|---|---|
| `--ease-out` | `cubic-bezier(0.215, 0.61, 0.355, 1)` | LISA line shift; microsoft.ai colour | Default on the live page |
| `--ease-standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | Cerebrium (97 transitions) | Hover, press, pill state |
| `--ease-editorial` | `cubic-bezier(0.43, 0.195, 0.02, 1)` | microsoft.ai reveals | Landing hero entrance only |
| `--duration-fast` | 200ms | Cerebrium | Hover, press, focus |
| `--duration-base` | 300ms | LISA | New transcript line, final colour, pill change, Now strip cross-fade |
| `--duration-slow` | 600ms | microsoft.ai | Landing button background changes |
| `--duration-reveal` | 1300ms | microsoft.ai | Landing hero entrance, once per load |
| `--duration-pulse` | 2000ms | — | Live dot opacity pulse (1 → 0.35), ease-in-out, infinite |
| `--distance-enter` | 8px | — | New transcript line rises 8px while fading in |

**Allowed animations:**

- opacity;
- `transform: translateY()` up to 8px;
- colour and background-colour;
- the indicator slide inside the budget bar;
- the live-dot pulse;
- the block-cursor blink (1s, `steps(2)`).

Nothing animates font size, layout, blur or numbers.

**Reduced motion.** Under `@media (prefers-reduced-motion: reduce)`:

- every duration token becomes 0ms and `--distance-enter` becomes 0px;
- a global rule sets `animation-duration` and `transition-duration` to `0.01ms` with one iteration;
- the live dot and cursor are static;
- auto-scroll uses `behavior: "auto"`;
- the landing hero renders in its final state.

State still changes instantly, so no information depends on motion.

### 3.7 Breakpoints and layout grid

Layouts are mobile-first and widen at each breakpoint with `min-width` media queries. 390 is the base, with no query. Custom properties cannot be used inside media queries, so 768, 1024 and 1440 are written as literal values.

| Viewport | Query | Gutter | Content width | Column gap | Live page | Landing |
|---|---|---|---|---|---|---|
| 390 | base | 16px | 358px | — | One column. Transcript bounded to 56svh. Cards stacked. Sticky call bar at the bottom. | Stacked |
| 768 | `min-width: 768px` | 24px | 720px | 16px | One column. Transcript 60svh. Cards in a 2-up grid. | Stacked; explainer 2-up |
| 1024 | `min-width: 1024px` | 32px | 960px | 32px | Two columns: `minmax(0,1fr)` + rail 340px | Role card / call panel 6 + 6 of 12 |
| 1440 | `min-width: 1440px` | 40px | 1360px (max) | 40px | Two columns: transcript ≈ 845px + rail ≈ 475px | Role card / call panel 7 + 5 of 12 |

- **Rail width:** `clamp(340px, 33vw, 480px)`.
- **Container:** `max-width: 1360px; margin-inline: auto; padding-inline: var(--gutter)`. Above 1440 the container centres.
- **Header height:** 56px below 1024, 64px from 1024.
- **Japanese measure:** transcript text is capped at `36em`, which is 36 characters per line at any size. At 1440 that gives about 32 characters for the current line and 36 for past lines.

---

## 4. Layout

### 4.1 Landing area

**At 1440**

1. **Header bar.** Inset floating bar (the microsoft.ai pattern):
   - `position: sticky; top: 16px`, inset 40px, 64px tall;
   - `surface-sunken` with a hairline, `radius-sm`;
   - left: the wordmark "Minato Servicer · みなと債権回収" in serif 18px, plus a mono caption "DEMO · FICTIONAL COMPANY";
   - right: anchor links "How to read the X-ray" and "Source", in mono caption.
2. **Hero.**
   - 160px top padding; a 12-column grid.
   - Eyebrow: mono caption in `text-muted`, such as "A JAPANESE VOICE AGENT · 音声エージェント".
   - Headline: `--text-display` spanning columns 1–10, two lines, the second in italic for one accent phrase (example copy: "Call Kenji. / *Watch him think.*").
   - Japanese sub-headline: `--text-h3` in Noto Serif JP, line height 1.7.
   - Lead paragraph: `--text-lead`, max-width 34em, `text`.
   - The entrance uses `--duration-reveal` with `--ease-editorial`: opacity plus a 16px rise, staggered by 120ms across eyebrow, headline and lead. It runs once.
3. **Play area.** Starts 96px below the lead, as two panels on the 12-column grid with a 40px gap.
   - **Role card** (columns 1–7). Uses `surface`, `radius-lg`, padding 40. Contents:
     - mono caption "YOUR ROLE · あなたの役";
     - the name `佐藤ゆうき` at `--text-h2` with "Yuki Sato" beneath in `text-muted`;
     - a definition list with Date of birth 1990-07-14, Account ending 7731 and Overdue ¥35,000. Each row has an English label and a Japanese label (mono caption) on the left and the value on the right at `--text-h3`, tabular, with hairline separators;
     - a "Things to try" list in English help text (agree to pay, ask for instalments, say you are someone else, ask for a person), at `--text-body`. Each item shows the Japanese phrase to say, with its English meaning in `text-muted`.
   - **Call panel** (columns 8–12). Uses `tint-peach`, `radius-lg`, padding 40. Contents:
     - mono caption "CALL KENJI · ケンジに電話" in `text` (every caption and note on peach uses `text`, never `text-muted`);
     - the phone number as a `tel:` link at `--text-h2`, `text-strong`, tabular, grouped with spaces so it can wrap between groups;
     - a note at `--text-small`: Japan number, calls are kept as a text transcript for 30 days, audio is never stored;
     - an "or" divider (hairline + mono caption);
     - a primary large "Call from browser" button at full panel width, with a phone icon;
     - the 4-digit link code (see 5.6) once the page has one, labelled "Calling by phone? Type this code when Kenji asks."
4. **How to read the X-ray.** A row of four plain items (Turn, Strategist, Compliance, Latency) separated by hairline rules. Each item has a mono caption title and a one-sentence explanation at `--text-body`. Four columns at 1440 and 1024, two at 768, one at 390. This is a list, not a bento grid: no tiles, no fills.

**At 390**

- The header bar is inset 16px, 56px tall, `top: 12px`. The wordmark shortens to "Minato · みなと", and the links collapse into one "Menu" button (44 × 44 target).
- The hero has 64px top padding. The headline is 44px over two lines, the Japanese sub-headline 22px, the lead 19px.
- The role card and call panel stack at full width with padding 20 and a 16px gap.
- The phone number sits at 28px. The primary button is full width and 56px tall. Code cells are 56 × 72 (4 × 56 + 3 × 8 = 248px, which fits inside 358px).
- The explainer is a single column.
- Section gaps are 64px.

### 4.2 Live X-ray page

**At 1440**

- **Header** (sticky, 64px, `surface-sunken`, hairline bottom border):
  - left: the short wordmark;
  - centre: call status. While live, an accent dot, "LIVE" in a mono caption and the timer `02:14` (`--text-metric-sm`, tabular), then the channel: "Browser call", or "Phone ··· 5678" with the last four digits. A demo replay adds an info pill "Demo replay · 再生". After the call: "Call ended · 04:32".
  - right: "Mute" and "End call" (secondary buttons, browser calls only).
- **Main grid.** Columns `minmax(0, 1fr) var(--rail-width)` with a 40px gap and 32px top padding.
  - **Transcript column** (left, about 845px). This column is the hero. It sticks (`top: header + 16px`) at `height: calc(100svh - 64px - 48px)` and scrolls inside, newest at the bottom. From top to bottom:
    1. **Now strip.** No card chrome: mono caption "NOW · いま", one sentence in `--text-lead` / `text-strong` saying in plain English what Kenji is doing (for example "Checking that you are Yuki Sato before discussing the account."), and the Japanese line beneath at `--text-small`. A hairline rule sits below it, with 24px of space either side. The sentence cross-fades in 300ms when the flow node changes.
    2. **Transcript log.** See 5.4. Lines sit directly on `bg`, so the conversation is the interface. Kenji's latest final line is the largest text on the page.
    3. **Listening row.** Interim speech from the caller with a block cursor, always last.
    4. **"Jump to latest" pill.** Floats 16px above the panel bottom and appears only when the reader has scrolled up more than 48px.
  - **Rail** (right, about 475px). Four cards stacked with 16px gaps in this order: **Turn, Strategist, Compliance, Latency.** The rail scrolls with the page while the transcript stays pinned, so at 1440×900 the first two cards and the top of Compliance are visible without scrolling.
- **Post-call section.** Inserted below the grid when the call ends. Focus moves to its heading, and the page scrolls to it (smooth unless reduced motion).
  - Uses the full container width with 120px top margin.
  - h2 `--text-h2` "What happened · 通話の結果".
  - Row 1: the **Outcome card** across all 12 columns.
  - Row 2: **SMS preview** (columns 1–7) and **Handoff record** (columns 8–12).
  - Row 3: **Audit record** across 12 columns.
  - 24px gaps.
- **At 1024:** same structure, with a 32px gutter and gap and a 340px rail.

**At 390**

- **Header:** 56px. Live dot, LIVE, timer and channel on the left. On the right, a "Menu" button holding Mute and the demo badge.
- **Now strip:** sticky under the header with `surface-sunken` background and a hairline below. Caption plus one sentence at `--text-body`, with the Japanese hidden behind a "日本語" toggle so the strip stays two lines at most.
- **Transcript:** a bounded region (`height: 56svh; min-height: 320px`) with internal scroll, newest at the bottom, and the meta row above each line instead of beside it (see 5.4).
- **Summary chips:** one wrapping row of pills linking to each card, such as "Compliance 4 pass · 1 pending", "Latency 1,180 ms" and "Identity verified". These keep the 10-second test on a small screen. Each chip is an anchor link with a 44px tall hit area.
- **Cards:** stacked at full width with padding 20 and 16px gaps, in the same order as desktop.
- **Call bar:** a sticky bottom bar for browser calls only, with Mute and End call, each half-width and 52px tall. It uses `surface-sunken` and `--shadow-float`, with `padding-bottom: max(12px, env(safe-area-inset-bottom))`. The page adds matching bottom padding so the bar never covers content.
- **Post-call:** every card is full width. The SMS preview stacks Japanese above English.
- **At 768:** the transcript region is 60svh, cards sit in a 2-up grid (Turn | Strategist, Compliance | Latency) with a 16px gap, and the SMS preview shows Japanese and English side by side.

---

## 5. Components

Every component is built from tokens only. All interactive targets are at least 44 × 44px, except the small Copy button, which is 32px tall with a 44px hit area through padding.

### 5.1 Button

| Variant | Background | Text | Border | Hover | Active |
|---|---|---|---|---|---|
| Primary | `ink` | `text-on-ink` (7.21:1) | none | bg `text-strong` | bg `text-strong`, `translateY(1px)` |
| Secondary | `surface-action` | `text` (7.11:1) | none | bg `surface-action-hover` | same as hover, `translateY(1px)` |
| Quiet | transparent | `ink` | none | underline, 1px, offset 3px | `text-strong` |
| Danger (End call) | `danger-bg` | `danger-text` (6.35:1) | none | bg `danger-fill`, text `text-on-ink` | same as hover |

| Size | Height | Padding | Type |
|---|---|---|---|
| Large | 56px | 0 32px | mono 15px / 500, +0.02em, sentence case |
| Medium | 44px | 0 24px | mono 14px / 500 (microsoft.ai: 14.22px / 500) |
| Small | 32px | 0 16px | mono `--text-caption` / 500 |

**Common to all buttons**

- Shape: `radius-pill`.
- Layout: inline-flex, centred, 8px gap between a 20px icon and the label.
- Transitions: `background-color` and `color` at `--duration-fast` with `--ease-standard`.
- **Focus-visible:** `outline: 2px solid var(--color-focus); outline-offset: 3px`. Never `outline: none` without this replacement. Mouse focus shows no ring; keyboard focus always does.
- **Disabled:** set `aria-disabled="true"` (keeps it focusable and announced), use `surface-action` with `text-muted` and `cursor: not-allowed`, and ignore activation.
- **Loading:** the label changes (for example "Connecting…") with `aria-busy="true"`. No spinner. The width is locked to its idle size to avoid layout shift.
- **Copy rules:** labels are verbs ("Call from browser", "End call", "Copy JSON") and never all caps in English. Icons are inline SVG, 20px, 1.5px stroke, round caps, `currentColor`.

### 5.2 Card

- Container: `surface` background, `1px solid var(--color-border-subtle)`, `radius-md`, padding 24 (≥ 1024) or 20 (< 1024), internal row gap 16, no shadow.
- **Header row:** a 6 × 6px `ink` square (the Cerebrium marker), then a mono caption title in English, a middle dot, and the Japanese, such as "COMPLIANCE · コンプライアンス". An optional status pill sits right-aligned. The title is an `h2` inside a `section` with `aria-labelledby`.
- **Summary sentence:** `--text-body` in `text-strong`, always first under the header and always present. This sentence is what the 10-second reader takes in.
- **Detail rows:** a `dl` grid of `minmax(0, 1fr) auto`:
  - labels in mono caption, `text-muted`;
  - values at `--text-body`, or `--text-metric-sm` for numbers, in `text`;
  - hairline separators between rows, with 12px padding above and below each row.
- **Changes:** when a value changes, its background flashes `surface-action` for 300ms and fades back. This is skipped under reduced motion.
- **Empty state:** before data exists, show the summary sentence "Waiting for the first turn." in `text-muted`. Never show blank cards or skeleton shimmer.

**Card contents**

| Card | Summary sentence (example) | Detail rows |
|---|---|---|
| **Turn** | "You said はい while Kenji was talking. He kept going, because that was a backchannel." | Last overlap (ms, or "None"); Characters (integer); Score (0.00–1.00 with a score bar against its threshold, see 5.5); Decision (pill: "Backchannel" in info, "Interruption" in warning); Flow node (plain label plus the node id in mono caption, such as "Checking identity · `identity_check`") |
| **Strategist** | "Identity confirmed. You can pay part now; Kenji is offering a plan inside the terms." | Identity (pill: Verified / Unverified / Locked); Situation (sentence); Ability to pay (sentence or ¥ amount, tabular); Offers (list, one row each: amount and schedule, tabular, with a pill "Inside terms" or "Outside terms"); Next move (sentence in `text-strong`) |
| **Compliance** | "4 of 5 safeguards holding. Recording notice not given yet." | Five rows: Calling hours 通話時間帯; Identity gate 本人確認; Offer inside terms 条件内の提案; AI disclosure AIであることの告知; Recording notice 記録の告知. Each row has the English label (`--text-body`), the Japanese label (mono caption, so it falls back to Noto Sans JP), and a status pill right-aligned. A blocked row adds its reason beneath in `danger-text` at `--text-small`. |
| **Latency** | "Last reply in 1,180 ms, within the 1,500 ms budget." | See 5.5 |

### 5.3 Chip / status pill

- Shape: height 24px, padding `0 var(--space-3)`, `radius-pill`.
- Text: mono `--text-caption`, 500, uppercase English, +0.06em.
- Icon: a 12px stroke icon before the label with a 6px gap. The icon and the word carry the meaning together, so it is never colour alone.

| Status | Domain value | Background | Text | Icon | Label |
|---|---|---|---|---|---|
| Pass | `pass` | `success-bg` | `success-text` | check | PASS |
| Blocked (fail) | `blocked` | `danger-bg` | `danger-text` | cross | BLOCKED |
| Pending | `pending` | `surface-action` | `text` | clock | PENDING |
| Info | — | `info-bg` | `info-text` | none | e.g. NOT SENT, DEMO REPLAY |
| Caution | — | `warning-bg` | `warning-text` | clock | e.g. SUBTITLE LAGGING |

**Behaviour**

- A status change cross-fades background and colour in `--duration-base` with `--ease-out`.
- Pills are not interactive. The exception is the mobile summary chips, which are links: same look, a 44px hit area through padding, an underline on hover, and the focus ring.
- Each pill carries visually hidden context for screen readers, such as "Identity gate: pass".

### 5.4 Transcript line

**Anatomy**

- At 768 and above, each line is a grid of `7.5rem` (meta) + `minmax(0, 1fr)` (text) with a 24px column gap.
- At 390 the meta sits on one row above the text.

| Part | Spec |
|---|---|
| Speaker | Mono caption, uppercase. Kenji's lines read "KENJI ケンジ" in `text-muted`. The visitor's read "YOU あなた" in `accent`. The word always names the speaker; colour only reinforces it. |
| Timestamp | `<time datetime="PT2M14S">02:14</time>`, call-relative mm:ss, mono caption, tabular, `text-muted`, under the speaker (beside it at 390) |
| Japanese text | `lang="ja"`, serif stack, `--text-line`, line height 1.8, +0.02em, `text`, max-width `36em` |
| English subtitle | `lang="en"`, Newsreader `--text-subtitle`, line height 1.5, `text-muted`, 4px below the Japanese. It reserves one line (`min-height: 1.5em`) so a late subtitle doesn't shift the layout. A subtitle that hasn't arrived shows "Translating…" in `text-muted` with no spinner; if it lags more than 3s, show the "Subtitle lagging" caution pill. |
| Visitor marker | Visitor lines add `border-left: 2px solid var(--color-accent)` and `padding-left: var(--space-3)` on the text block, so "you vs Kenji" scans instantly. |
| Spacing | 24px between turns; 32px above Kenji's current line |

**States**

| State | Spec |
|---|---|
| Interim | Lives only in the listening row. Text in `text-muted`, followed by a block cursor: `0.5em × 1em`, `accent`, blinking 1s `steps(2)` (static under reduced motion). Updated in place without animation; `aria-hidden="true"`. |
| Final | Appended to the log. It enters with opacity 0 → 1 and `translateY(var(--distance-enter))` → 0 over `--duration-base` / `--ease-out`. Colour settles to `text`. |
| Current | Kenji's most recent final line: `--text-line-current`, Noto Serif JP 500, line height 1.7, `palt`, `text-strong`. When a newer Kenji line arrives, it drops to the Final style instantly with a 300ms colour fade; size changes are not animated. |
| Speaking | While Kenji's audio is playing, the block cursor sits at the end of the current line. |
| Empty | Before the call connects: centred in the column, mono caption "WAITING FOR YOUR CALL", a sentence at `--text-lead`, the link code (5.6) and the phone number. |
| Connection lost | A banner at the top of the column: `danger-bg` / `danger-text`, `radius-sm`, padding 16, reading "Connection lost. The call may still be running — reconnecting…", with a secondary "Retry" button. |

**Scrolling and accessibility**

- The log is `role="log"` with `aria-live="polite"` and `aria-relevant="additions"`, so only final lines are announced.
- Auto-scroll keeps the newest line in view while the reader is within 48px of the bottom. Otherwise it stops and shows "Jump to latest".
- The scroll region has `tabindex="0"` and an accessible name, "Call transcript", so keyboard users can scroll it.

### 5.5 Metric

This is the Cerebrium range-chart anatomy, re-set on the cream palette.

| Part | Spec |
|---|---|
| Label | Mono caption, uppercase, `text-muted`, such as "LAST REPLY · 直近の応答" |
| Value | `--text-metric`, serif 450, `text-strong`, tabular, formatted with a thousands separator (1,180) |
| Unit | "ms", mono `--text-caption`, `text-muted`, 4px after the value, baseline-aligned |
| Budget bar | Height 6px, `radius-pill`, `track` background, full card width. The scale runs 0–2,000 ms, or up to the largest value if that is higher. Fill is `success-fill` at or under 1,500 ms and `danger-fill` above. A budget marker (2 × 14px, `ink`) sits at 1,500 ms with "1,500 ms budget" beneath it, right-aligned, in mono caption `text-muted`. Fill width transitions in `--duration-base`. |
| Verdict | Text under the bar, never colour alone: "Within budget" (success pill) or "Over budget by 220 ms" (blocked pill) |
| Stage rows | One row per stage: End of turn, LLM first token, TTS first audio. Each row has a mono caption label above a flex row of [6px bar, `flex: 1`, scaled to the budget] + [value in `--text-metric-sm`, right-aligned, `min-width: 5.5em`] with an 8px gap. Stage bars use `ink` fill on `track`; only the total gets the success or danger colour. |
| Percentiles | Footer row separated by a hairline: "P50 1,120 ms · P95 1,460 ms · 9 turns", in `--text-metric-sm`, tabular |
| Turn history | A strip of up to 12 bars (one per turn): 6px wide, 4px gap, 40px tall, heights scaled to 2,000 ms, with a dashed 1px `ink` line at the budget. Bars over budget use `danger-fill`; the rest use `ink`. A visually hidden table lists turn number and total ms for screen readers. |

The Turn card's score bar reuses the budget bar, with a 0–1 scale, `ink` fill and the classifier threshold as the marker.

Values update in place. They never count up or tween, and a new turn replaces the numbers instantly.

### 5.6 Four-digit link code

- **Container:** caption "YOUR CODE · 認証コード", then four digit cells, then help text.
- **Cells:** each 56 × 72px with `surface` background, `1px solid var(--color-border-strong)` (3.10:1 on surface) and `radius-sm`, 8px apart. Digits are `--text-digit` (40px), Red Hat Mono 500, `text-strong`, tabular, centred.
- **Help text:** `--text-small`: "When Kenji asks, type these four digits on your phone keypad." with the Japanese beneath. An expiry line reads "Expires in 9:42" in mono caption, tabular. The code expires after 10 minutes (decision 11).
- **Accessibility:** the group has `role="group"` and `aria-label="Your code: 4 8 1 2"`, and the individual cells are `aria-hidden`. A "Copy code" quiet button follows.
- **States:**

| State | Spec |
|---|---|
| Linked | Cells change to `success-bg` and a pass pill reads "Linked to your call". |
| Expired | Cells use `surface-action` with `text-muted` digits, and a "New code" secondary button appears. |
| Locked after 3 wrong attempts | A blocked pill and the sentence "Linking is disabled for this call." |

### 5.7 Copy-JSON block (audit record)

- **Header row:** mono caption "AUDIT RECORD · 監査記録" on the left. On the right, a pass pill "HASH CHAIN VERIFIED" (or blocked "CHAIN BROKEN") and a small secondary "Copy JSON" button with a copy icon.
- **Body:** `<pre><code>` on `surface-code`, `radius-sm`, padding 16, `--text-code` / 1.6, `text-strong` (10.47:1). Indent 2 spaces, no syntax colours. `max-height: 320px` with `overflow: auto`, plus `tabindex="0"` and `aria-label="Audit record JSON"` so it can be scrolled by keyboard. A quiet "Show all" button removes the height cap.
- **Copy behaviour:**
  - Uses `navigator.clipboard.writeText` on the exact JSON shown.
  - On success, the button label becomes "Copied" with a check icon for 2s, and a visually hidden `aria-live="polite"` region says "Audit record copied."
  - On failure, the label becomes "Copy failed", with a note in `danger-text`: "Select the text and copy it manually."
  - The button width stays fixed across states.

### 5.8 Post-call cards

- **Outcome card.**
  - Uses `tint-peach`, `radius-lg`, padding 40 (24 at 390) and no border.
  - Mono caption "OUTCOME · 結果" in `text`, not `text-muted`, because it sits on peach.
  - The outcome at `--text-h2` in `text-strong`, with the Japanese beneath at `--text-h3` (Noto Serif JP, 1.7).
  - Key facts in a row: amount (`--text-metric`, tabular), first payment date and schedule.
  - Supports every domain outcome: promise to pay, human handoff, stop contact, callback requested, identity not verified, outside calling hours, no agreement.
  - No celebratory colour or confetti: a promise to pay is stated, not cheered.
- **SMS preview.** A standard card.
  - Header pill "NOT SENT · 未送信" (info).
  - Japanese body (`--text-line`, line height 1.8) and English body (`--text-body`), separated by a hairline: side by side at 768 and above, stacked below.
  - Footer: "68 characters" in mono caption, tabular. No phone-frame mock-up.
- **Handoff record.** A standard card with a `dl` of Reason, Summary, Identity status (pill) and Requested at (tabular timestamp). When there is no handoff, the summary reads "No handoff on this call."

---

## 6. Avoid

These must not appear anywhere on the page.

- Purple or indigo gradients, or any gradient used as decoration.
- Inter, Roboto or Geist as the main face. They are not in any font stack.
- Sparkle or star icons standing for "AI", or any decorative AI iconography.
- Glow orbs, gradient blobs or light leaks on near-black, and dark hero sections in general.
- Bento grids: mosaics of tiles in mixed sizes. Cards here stack in one rail.
- Frosted glass (`backdrop-filter: blur()`), including Cerebrium's 50px panel blur.
- 1px glowing or gradient borders. Borders are solid hairlines.
- A chat-input hero. The landing invites a phone call, not typing.
- Emoji anywhere: copy, pills, buttons or the JSON preview. Use stroke icons.
- Also excluded by this spec:
  - blur on past transcript lines (taken from LISA, rejected for legibility);
  - count-up or ticking numbers;
  - skeleton shimmer;
  - chat bubbles with avatars;
  - box shadows on cards;
  - WebGL and 3D;
  - scroll-jacking;
  - italic Japanese.

---

## 7. Accessibility rules

- **Contrast.** All text meets WCAG 2.2 AA at minimum. Body and transcript text is AAA on `bg`, `surface`, `surface-sunken` and `surface-action` (see 3.1). Non-text UI (control borders, focus ring, bars, markers) is 3:1 or more.
- **Focus.** Every interactive element shows `outline: 2px solid var(--color-focus); outline-offset: 3px` on `:focus-visible`. Focus order follows the visual order:
  - header;
  - Now strip;
  - transcript;
  - rail cards;
  - post-call section.

  When the call ends, focus moves to the post-call heading (`tabindex="-1"`).
- **Reduced motion.** Honour `prefers-reduced-motion: reduce` exactly as in 3.6. No information is conveyed only through motion.
- **No horizontal scroll** at 1440, 1024, 768 or 390. To guarantee it:
  - every grid track uses `minmax(0, 1fr)`;
  - long tokens (flow-node ids, hashes, JSON) wrap or scroll inside their own box;
  - the phone number wraps between digit groups.

  Playwright asserts `document.documentElement.scrollWidth <= innerWidth` at all four widths.
- **Tabular numbers.** Every numeric value uses `font-variant-numeric: tabular-nums lining-nums` (3.2).
- **Not colour alone.** Every status pairs colour with a word and an icon. Speakers are named in text. The over-budget state is spelled out ("Over budget by 220 ms").
- **Languages.** Japanese is marked `lang="ja"` and English `lang="en"`. The document is `lang="en"`.
- **Live regions.** The transcript is `role="log"` / `aria-live="polite"` with final lines only. Copy confirmations go through their own polite region. Nothing uses `aria-live="assertive"` except the connection-lost banner (`role="alert"`).
- **Targets.** At least 44 × 44px for every control. The minimum type size is 12px (mono captions); body copy is never below 15px.
- **Semantics.** The header is a `header`, the transcript and cards are `main` content, and each card is a `section` with a heading. Definition lists hold label/value pairs, buttons are real `<button>`s and links are real `<a href>`s.

---

## 8. Tokens: CSS custom properties

Paste this into `web/src/styles/tokens.css` and import it once at the root.

```css
:root {
  color-scheme: light;

  /* Colour: base (microsoft.ai palette) */
  --color-bg: #FEF9ED;
  --color-surface: #F7F1E3;
  --color-surface-sunken: #FBF0DC;
  --color-surface-action: #F7ECD9;
  --color-surface-action-hover: #F1E3CB;
  --color-surface-code: #F3EAD8;
  --color-tint-peach: #FBD3BE;

  --color-ink: #5D524B;
  --color-text: #574C45;
  --color-text-strong: #3B322C;
  --color-text-muted: #6F6259;
  --color-text-on-ink: #FEF9ED;

  --color-border-subtle: #E9E0CE;
  --color-border-strong: #958779;

  --color-accent: #A8461F;
  --color-focus: #A8461F;

  /* Colour: states */
  --color-success-text: #2E5A34;
  --color-success-bg: #E3EFDD;
  --color-success-fill: #46704A;
  --color-warning-text: #6E4D0C;
  --color-warning-bg: #F6EBC6;
  --color-warning-fill: #94650C;
  --color-danger-text: #922F1E;
  --color-danger-bg: #FBE1D3;
  --color-danger-fill: #B3432C;
  --color-info-text: #2F5558;
  --color-info-bg: #E6EFEE;
  --color-track: #EDE3D0;
  --color-selection: #FBD3BE;

  /* Typography: faces */
  --font-serif: "Newsreader Variable", "Newsreader", "Noto Serif JP Variable", "Noto Serif JP",
    "Hiragino Mincho ProN", "Yu Mincho", serif;
  --font-mono: "Red Hat Mono Variable", "Red Hat Mono", "Noto Sans JP Variable", "Noto Sans JP",
    ui-monospace, "SF Mono", Menlo, Consolas, monospace;

  /* Typography: weights */
  --weight-regular: 400;
  --weight-book: 450;
  --weight-medium: 500;
  --weight-semibold: 600;

  /* Typography: sizes, fluid from 390px to 1440px */
  --text-display: clamp(2.75rem, 1.6357rem + 4.5714vw, 5.75rem);        /* 44 -> 92 */
  --text-h1: clamp(2.125rem, 1.6607rem + 1.9048vw, 3.375rem);           /* 34 -> 54 */
  --text-h2: clamp(1.75rem, 1.5411rem + 0.8571vw, 2.3125rem);           /* 28 -> 37 */
  --text-h3: clamp(1.375rem, 1.2821rem + 0.381vw, 1.625rem);            /* 22 -> 26 */
  --text-lead: clamp(1.1875rem, 1.1179rem + 0.2857vw, 1.375rem);        /* 19 -> 22 */
  --text-body: clamp(1.0625rem, 1.0393rem + 0.0952vw, 1.125rem);        /* 17 -> 18 */
  --text-small: 0.9375rem;                                               /* 15 */
  --text-caption: clamp(0.75rem, 0.7268rem + 0.0952vw, 0.8125rem);      /* 12 -> 13 */
  --text-line-current: clamp(1.375rem, 1.2821rem + 0.381vw, 1.625rem);  /* 22 -> 26 */
  --text-line: clamp(1.0625rem, 1.0161rem + 0.1905vw, 1.1875rem);       /* 17 -> 19 */
  --text-subtitle: clamp(0.9375rem, 0.9143rem + 0.0952vw, 1rem);        /* 15 -> 16 */
  --text-metric: clamp(2rem, 1.8143rem + 0.7619vw, 2.5rem);             /* 32 -> 40 */
  --text-metric-sm: clamp(0.9375rem, 0.9143rem + 0.0952vw, 1rem);       /* 15 -> 16 */
  --text-code: 0.8125rem;                                                /* 13 */
  --text-digit: 2.5rem;                                                  /* 40 */

  /* Typography: line height */
  --leading-display: 1;
  --leading-heading: 1.15;
  --leading-snug: 1.3;
  --leading-subtitle: 1.5;
  --leading-body: 1.6;
  --leading-label: 1.4;
  --leading-ja: 1.8;
  --leading-ja-large: 1.7;

  /* Typography: tracking */
  --tracking-display: -0.04em;
  --tracking-heading: -0.02em;
  --tracking-tight: -0.01em;
  --tracking-label: 0.06em;
  --tracking-button: 0.02em;
  --tracking-ja: 0.02em;

  /* Spacing: 4px base */
  --space-1: 0.25rem;   /* 4 */
  --space-2: 0.5rem;    /* 8 */
  --space-3: 0.75rem;   /* 12 */
  --space-4: 1rem;      /* 16 */
  --space-5: 1.25rem;   /* 20 */
  --space-6: 1.5rem;    /* 24 */
  --space-7: 2rem;      /* 32 */
  --space-8: 2.5rem;    /* 40 */
  --space-9: 3rem;      /* 48 */
  --space-10: 4rem;     /* 64 */
  --space-11: 5rem;     /* 80 */
  --space-12: 6rem;     /* 96 */
  --space-13: 7.5rem;   /* 120 */
  --space-14: 10rem;    /* 160 */

  /* Layout */
  --container-max: 85rem;                   /* 1360 */
  --gutter: var(--space-4);                 /* 16 at 390 */
  --column-gap: var(--space-4);
  --section-gap: var(--space-10);           /* 64 at 390 */
  --header-height: 3.5rem;                  /* 56 */
  --rail-width: clamp(21.25rem, 33vw, 30rem); /* 340 -> 480 */
  --measure-ja: 36em;
  --measure-en: 34em;
  --tap-target: 2.75rem;                    /* 44 */
  --button-height-lg: 3.5rem;               /* 56 */
  --button-height-md: 2.75rem;              /* 44 */
  --button-height-sm: 2rem;                 /* 32 */
  --pill-height: 1.5rem;                    /* 24 */
  --bar-height: 0.375rem;                   /* 6 */
  --marker-size: 0.375rem;                  /* 6, card-header square */
  --code-cell-width: 3.5rem;                /* 56 */
  --code-cell-height: 4.5rem;               /* 72 */
  --cursor-width: 0.5em;
  --rule-width: 2px;

  /* Radius */
  --radius-xs: 3px;
  --radius-sm: 5px;
  --radius-md: 10px;
  --radius-lg: 15px;
  --radius-pill: 999px;

  /* Borders and focus */
  --border-hairline: 1px solid var(--color-border-subtle);
  --border-control: 1px solid var(--color-border-strong);
  --focus-ring: 2px solid var(--color-focus);
  --focus-offset: 3px;

  /* Elevation */
  --shadow-float: 0 4px 40px rgba(93, 82, 75, 0.3);

  /* Motion */
  --ease-out: cubic-bezier(0.215, 0.61, 0.355, 1);
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-editorial: cubic-bezier(0.43, 0.195, 0.02, 1);
  --duration-fast: 200ms;
  --duration-base: 300ms;
  --duration-slow: 600ms;
  --duration-reveal: 1300ms;
  --duration-pulse: 2000ms;
  --duration-blink: 1000ms;
  --distance-enter: 8px;
  --distance-reveal: 16px;
  --stagger-reveal: 120ms;

  /* Budgets shown in the UI */
  --latency-budget-ms: 1500;
  --latency-scale-ms: 2000;
}

@media (min-width: 768px) {
  :root {
    --gutter: var(--space-6);        /* 24 */
    --section-gap: var(--space-11);  /* 80 */
  }
}

@media (min-width: 1024px) {
  :root {
    --gutter: var(--space-7);        /* 32 */
    --column-gap: var(--space-7);
    --section-gap: var(--space-13);  /* 120 */
    --header-height: 4rem;           /* 64 */
  }
}

@media (min-width: 1440px) {
  :root {
    --gutter: var(--space-8);        /* 40 */
    --column-gap: var(--space-8);
  }
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast: 0ms;
    --duration-base: 0ms;
    --duration-slow: 0ms;
    --duration-reveal: 0ms;
    --duration-pulse: 0ms;
    --duration-blink: 0ms;
    --distance-enter: 0px;
    --distance-reveal: 0px;
    --stagger-reveal: 0ms;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Base rules that go with the tokens:

```css
html { background: var(--color-bg); color: var(--color-text); font-family: var(--font-serif); }
body { font-size: var(--text-body); line-height: var(--leading-body); }
:lang(ja) { line-height: var(--leading-ja); letter-spacing: var(--tracking-ja); line-break: strict; word-break: normal; font-style: normal; }
::selection { background: var(--color-selection); color: var(--color-text-strong); }
:focus-visible { outline: var(--focus-ring); outline-offset: var(--focus-offset); }
.numeric, time, data { font-variant-numeric: tabular-nums lining-nums; }
```

---

## 9. Reference captures

Captured on 2026-10-02 at 1440×900 and 390×844 (the first three viewports, or successive viewports on scroll-driven pages). They are stored in `docs/design-refs/` and not committed.

| File | Source |
|---|---|
| `microsoft-ai-1440.png`, `microsoft-ai-390.png` | https://microsoft.ai |
| `cerebrium-1440.png`, `cerebrium-390.png` | https://cerebrium.ai |
| `lisa-1440.png`, `lisa-1440-v2.png`, `lisa-1440-v3.png`, `lisa-390.png`, `lisa-390-v2.png`, `lisa-390-v3.png` | https://lisa.locomotive.ca/en (intro, after scroll, after the "Start a project" chip) |
| `awwwards-microsoft-ai-*.png`, `awwwards-cerebrium-*.png`, `awwwards-lisa-*.png` | https://www.awwwards.com/sites/microsoft-ai, `/sites/cerebrium`, `/sites/l-i-s-a` |

**Not measured.**

- LISA's per-character reveal timing (each character is its own element, revealed by script).
- Cerebrium's WebGL scenes.
- Any hover-only states that need a pointer over a specific element.
- The video highlights on the Awwwards pages, which render as black frames in a headless capture.
- The LISA mobile capture after a chip tap (`lisa-390-v3.png`), which caught the sheet mid-transition.
