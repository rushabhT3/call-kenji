# Design review — live page, 2 October 2026

An independent review compared the built page with `DESIGN.md` and the reference captures at
1440, 1024, 768 and 390 px. Every finding is listed with what was done.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | Live header wrapped to 90 px at 390 and overprinted "Call ended" | Below 768 px the live header drops the wordmark: status left, demo pill right; 56 px tall |
| 2 | High | Label column collapsed in detail rows ("FLOW/STEP") | Rows are `auto` label + `minmax(0, 1fr)` value |
| 3 | High | With data, the Turn card pushed Compliance below the fold at 1440×900 | Turn measures moved into one three-column row and the verdict into the card header; Strategist lost its duplicate "Caller" row; Compliance is visible at 1440×900 |
| 4 | Med | Content 1280 px wide at 1440 instead of 1360 | Container max width includes both gutters |
| 5 | Med | Live grid offsets and a dead band under the transcript | Transcript column is sticky with a viewport-height flex column; transcript fills it |
| 6 | Med | Now strip at 390 not sticky, no 日本語 toggle | Sticky on `surface-sunken` with a 日本語 toggle below 768 px; 24 px around the hairline |
| 7 | Med | Tap targets under 44 px | Header link and medium buttons are 44 px; small buttons keep a 32 px look with a 44 px hit area |
| 8 | Med | Mobile summary chips looked like 44 px buttons | 24 px pills with an invisible 44 px hit area |
| 9 | Med | Latency turn-history strip missing | Up to 12 bars against a dashed budget line, with a hidden table for screen readers |
| 10 | Med | Outcome facts had no hierarchy | Amount at metric size; payments and first payment at h3 |
| 11 | Med | Cursor blinked through 50% opacity | `step-end` timing |
| — | Low | Pills and "Show all" stretched; units uppercased; 13 px medium buttons; 44 px mobile call bar; missing heading tracking; status not centred; faint pill icons; spacing above play area and post-call; subtitle-driven scroll; mobile transcript edge; strategist summary; idle space beside the call panel | All fixed as suggested; the call panel is sticky beside the role card from 1024 px |

Not changed: the Strategist offers carry no "inside terms" pill, because the page cannot verify
an offer string on its own; offers Kenji makes are checked by `check_terms` on the server and the
Compliance card shows the result.
