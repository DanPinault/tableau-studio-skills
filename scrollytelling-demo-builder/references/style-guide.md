# Style guide — the COO/CFO keynote-extension templates

The look, animations, interactivity, and live-bind plumbing all come from two
vendored templates shipped **inside this skill** (`assets/`), so no external repo
or login is needed. **Read the real files there rather than reconstructing
them** — this doc only orients you and names the anchors.

- **Templates:** `assets/public/coo-brief.html`, `assets/public/cfo-brief.html`
- **Build script:** `assets/build_standalone.py`
- **Vendor libs (inlined at build time):** `assets/vendor/d3.min.js`,
  `assets/vendor/tableau.extensions.1.latest.js`
- **Example `.trex` manifests:** `assets/example-coo.trex`, `assets/example-cfo.trex`
  — copy the closer one and edit for the new story.

## Two template patterns — pick the one that fits the signal

Both live in `assets/public/`. Copy the closer one, then adapt copy, fields, and marks.

- **`assets/public/coo-brief.html`** — "Running Hot." **Numbered-chapter** scrolly: a
  vertical sequence of chapters, each animating a chart into view on scroll
  (IntersectionObserver reveals + per-chapter `drawFor`). Good for a
  **linear narrative** (situation → tension → evidence → implication → action).
- **`assets/public/cfo-brief.html`** — "The Quiet Erosion." **Pinned/sticky** scrolly: a
  `position:sticky` graphic the reader scroll-drives through discrete states
  (`.scrolly` grid + `.step` elements → `setDivStep(n)` via IntersectionObserver),
  then waterfall / quadrant / rail / run-rate finale. Good for a **single evolving
  visual** that transforms as the reader scrolls (e.g. two diverging lines).

Both share: serif headlines on a dark theme, count-up KPIs, sticky dot-nav,
progress bar, modals on click, and a **Demo/Live topbar toggle**.

## Pattern and style are separate choices

The two patterns above are scroll mechanics. The visual style (palette, type,
layout density) is chosen separately from `references/output-styles.md`. Both
templates currently ship the dark keynote look; override their theme tokens
rather than reusing that look by default.

## The plumbing to reuse (same function names in both templates)

- **`const MEAS` + `const WS_NAMES`** — the field contract and the accepted feeder
  sheet names. Edit these to YOUR datasource's measures/dimensions and feeder name.
  `MEAS` entries carry `.cap` (the datasource caption), unit/format, and how each
  is aggregated. `WS_NAMES` must include your `feed_data` sheet name at the front.
- **`readFromWorksheet()`** — finds the feeder worksheet on
  `dashboard.worksheets` (exact match in `WS_NAMES`, else `/feed/i`), reads it with
  `getSummaryDataAsync` (fallback `getSummaryDataReaderAsync`). Runs in the
  viewer's session → **RLS-aware automatically**; the RLS field need not be on the
  sheet, and Full Data Access does not bypass RLS.
- **`contractFromRows(rows[,cols][,captureLive])`** — ports the story math to JS:
  builds every SEED-shaped array (KPIs with deltas, trends/sparklines with moving
  averages, per-dimension breakdowns) from the feeder rows. Uses `colIdx(sub)` =
  first column whose `fieldName.toLowerCase().includes(sub)` (matches bare or
  `AVG(...)`-wrapped captions). **This is the file you rewrite most** — reshape it
  to your fields. The optional `captureLive` flag stashes the parsed per-row
  records into `liveRecs` for the Explore view (see below); only the live
  worksheet read passes it true, so the baked snapshot never feeds Explore.
- **`boot()` fallback order** — worksheet-read (embedded) → baked `window.__LIVE__`
  snapshot → api/metrics → `SEED`. So the embedded tile is live-on-open; the
  standalone page shows a snapshot.
- **`watchLiveFilters()`** — called at the end of `boot()`. Attaches a
  `FilterChanged` listener to the feeder worksheet and re-runs `resolveLive()`
  whenever the workbook's own filters change (e.g. a relative-date window
  filter on `feed_data`), then redraws if Live mode is active. Without this,
  the tile only ever reflects the one-time snapshot taken at boot and goes
  stale the moment a viewer changes a filter without reopening the dashboard.
  Keep this listener when adapting — it is what makes the RLS-aware live bind
  also filter-aware.
- **`resolveLive()` + `applyMode(mode)`** — the Demo/Live toggle. `resolveLive()`
  caches the live contract once; `applyMode` swaps `D` between `normalize(SEED)`
  (demo) and the live data, clears `drawn={}`, and redraws every viz. Each draw fn
  clears its own host so re-render is idempotent. Buttons carry `data-mode`.
- **`const SEED`** — grounded demo data that also defines the shape every draw fn
  expects. Set it from the REAL signal you queried, so Demo mode tells the true
  story and Live mode matches it.

## The Explore view — a second, filterable surface (both templates)

Both templates ship a second top-level mode alongside the scroll story. The story
stays the **pristine authored narrative with no filter bar**; an **"Explore
data ↗"** button in the topbar switches to it via
`body.classList.toggle("exploring")` (`#story` hides, `#explore` shows), and
"Back to story" returns. Explore is a condensed **chart grid + a live filter bar
+ a cosmetic Save button** — no prose, so filtering can never make an authored
claim go false. Keep this separation when adapting: **filters live only in
Explore, never in the story.**

Anchors to adapt (same names in both files): `#explore` panel markup, `#fbar`
filter bar, `enterExplore()`/`exitExplore()`, `bindFilterBar()`/`syncFilterBar()`
+ `buildDropdown()`, `sliceRecs()`, `buildExplore(recs, days)` (computes the
Explore KPIs/trend/rail — a dedicated fn, NOT `contractFromRows`), `computeDX()`,
`redrawExplore()`, and `toastSave()` (the fake Save = a "View saved ✓" toast that
fades; no persistence, no network).

Two rules that must survive adaptation:

- **Explore is LIVE-ONLY.** Its rows come from `liveRecs`, which is populated
  **only** by `readFromWorksheet()` → `contractFromRows(rows, cols, /*captureLive*/ true)`
  (the 3rd arg stashes the parsed per-row records). The baked `window.__LIVE__`
  snapshot path calls `contractFromRows` **without** `captureLive`, so `liveRecs`
  stays null in Demo/snapshot mode and the filter bar **greys out** (`.fbar.off`
  + a "switch to Live to slice" note). Never fabricate row-level data to fill it.
  Because the rows are read live via the Extensions API, Explore is **RLS-aware**
  automatically — filter dropdown values are built from the entitled rows only.
- **Adapt the filter set to your datasource's dimensions.** COO ships Window
  (30/60/90/180) + Region + Facility; CFO adds a **Client Segment** dropdown
  (`#ddSegments`). Rebuild these from the real dimensions you queried (drop
  Segment or add your own), and recompute any Explore-specific domains/thresholds
  from real rows just like every other chapter (step 4 of the build procedure).
- **Filter widget types matter, and they aren't interchangeable.** The Window
  filter is single-select — a `.seg` button group (`#fWindow`, `data-days`
  buttons). Region/Facility/Segment (or whatever dimension filters you add) are
  **multi-select dropdowns** — the `.fdd`/`.fdd-btn`/`.fdd-panel`/`.fopt`
  pattern (`buildDropdown(ddSel, values, key)`, keyed into a `Set` on
  `FILTER[key]`, button label summarized via `ddSummary(key)`). Do not
  reuse the topbar `.toggle` button-group pattern for dimension filters — it
  only supports single-select and has caused a real bug (an "All" option plus
  a mismatched preset array producing `undefinedD` on a button with no
  matching index). Copy the `.seg`/`.fdd` CSS and the `buildDropdown`/
  `bindFilterBar`/`syncFilterBar` functions verbatim from a vendored template
  and only rename the FILTER keys and value lists.
- **`#exTrend`'s `viewBox` alone does not size it — copy its CSS rule too.**
  An SVG with only a `viewBox` attribute and no explicit `width`/`height` CSS
  collapses to the browser default (~300×150, sometimes 0 in a flex/grid
  parent) and renders nothing visible even though the path drew correctly.
  Copy the `#exTrend{width:100%; height:...; display:block}` rule from the
  vendored template alongside the markup — it's easy to port the SVG element
  and the draw function but drop this one CSS line.
- **Explore's KPI cards have no info-icon popover.** `drawKpis(hostSel, kpis, withInfo)`
  takes an optional third argument (default `true`); call it with `false` for
  `#exKpis` — `drawKpis("#exKpis", DX.kpis, false)`. The "i" info icon opens a
  popover keyed off `KPI_META`/`openPop`, which is wired for the story's
  narrative chapters, not the Explore grid; showing it there is a dead click.
- **Explore layout: metrics on top, charts side by side below.** The KPI
  scorecard (`drawKpis` into a host carrying both `.ex-card wide` and `.kpis`
  — the `.kpis` class is what gives the 3-per-row grid) goes in its own full-width
  row at the top of `.ex-grid`. The trend chart and the rail/bar chart go in two
  plain (non-`wide`) `.ex-card`s directly below it, side by side via `.ex-grid`'s
  2-column layout. Do not stack the trend and rail as two more full-width rows.

## Self-contained build

`assets/build_standalone.py` produces ONE self-contained HTML with D3 + the
Tableau Extensions API **inlined** — **0 external `<script src>`**, so any
static host can frame it. `--extension` builds the framed (`dist-ext/`)
variant; `--persona cfo` selects the CFO template. `--packaged --query q.json`
builds the packaged (Data App) variant instead: it inlines
`vendor/tableau.extensions.data-apps.min.js` (which has `queryAsync`) and injects
the query as `window.__PKG_QUERY__`. In the template, `readFromWorksheet()`
branches on `PKG_QUERY` to `readPackagedTable()`, which returns the same
`{columns, data}` shape as the feeder read, so keep that adapter when you adapt
a template. See `references/packaged-extension.md`. Vendor libs live under
`assets/vendor/`; the build needs no network. Read `assets/build_standalone.py`
before running it — copy it into the scratch dir alongside the template you're
adapting rather than editing it in place.

## `.trex` manifest (dashboard-extension descriptor)

Each brief has an example `.trex` (`assets/example-coo.trex`,
`assets/example-cfo.trex`). Rules that bite: element order is strict
(default-locale, name, description, author, min-api-version, source-location,
**then `<icon>` — REQUIRED, no `?`**, then optionals); a missing `<icon>` is a
parse error. `<source-location><url>` = the public host URL.

## Hosting requirement (hosted mode only)

Packaged mode needs no host: Tableau Cloud serves the HTML from the `.twbx`.
In hosted mode, the extension iframe is fetched **client-side by the viewer's browser**, so the
host must be **public (no auth) + send no framing-blocking headers**
(`x-frame-options` / `content-security-policy`). This skill does not assume any
particular host — use whatever public static host the user has (or wants to
set up). A gated/internal host (SSO-behind, VPN-only) will NOT work as the
iframe host. See `references/build-procedure.md` for how to host a new story.

## Feeder sheet recipe (the `feed_data` bind)

A crosstab worksheet in the same workbook: **Date × the story dimensions on rows
+ the measures**, filtered to the story window (step 2 of the build procedure).
Build it with the authoring tools (`add-field` + `apply-worksheet`), then confirm
the real shape with `get-summary-data` — not just a clean apply receipt. This is
the single reference for the feeder's shape; the build procedure points here.

- **Date pill:** discrete Day-Trunc (`[tdy:Date:ok]`). A raw `[none:Date:ok]` pill
  triggers a `date-field-bound-as-string` validation error.
- **Match each measure's aggregation (`derivation`) to what it is, not a blanket
  `Sum`.** Rate/percentage/average measures (a per-unit cost, an on-time %, any
  "rate," an average duration) must use **`Avg`** at the Date × dimension grain —
  `Sum`-ing a rate across the underlying rows produces a nonsensical inflated
  number (e.g. a 95% rate summed across 30 rows/day reads as 2850%). Only genuine
  volume/count measures (units shipped, transactions, counts completed) use `Sum`.
  This must match the JS contract's own `MEAS` aggregation (`agg:"avg"` vs
  `agg:"sum"`) — if they disagree the live numbers are wrong even though everything
  "applies cleanly." Sanity-check sample rows in `get-summary-data` against
  plausible magnitudes (a percentage reads 0–100%, not >100%).
- **Multi-measure crosstab — the only pattern that works:** put all dimensions on
  rows (nest with `/`), leave `cols` for a discrete dimension only (or empty), set
  `mark class='Text'`, and add every measure as its own `<text>` encoding (repeated
  `add-field target=encoding encodingType=text`). Do **not** join continuous
  measures on `cols` with `+` (creates one pane per measure → fails `mark_type
  requires exactly one pane`) or with `/` (silently dropped on continuous pills).
- Do **not** pre-aggregate or add derived columns the JS parses itself (e.g. a
  Region parsed from a facility name). Percentages are 0–1 in the datasource; the
  JS multiplies by 100.
- Place the sheet **floating and parked off-canvas** (x/y ≈ −3000) so it feeds the
  extension but isn't visible. (Placement is a manual user step — see
  build-procedure step 5.)
- **Sentinel test** to prove the tile reads the sheet (not a baked snapshot): swap
  one measure for a constant calc whose name still contains the caption substring,
  and confirm the tile shows the constant.

## Rules from published runs (keep in every style)

- **Header and chapter links:** pin only a compact bar (title, Demo/Live toggle
  and Explore button, one row, no wrapping, about 56px tall) with `position:sticky`.
  The chapter links sit in a second row that scrolls away with the page, on one
  row that scrolls sideways. Give chapter anchors a `scroll-margin-top` equal to
  the bar height. The bar is not sticky when the frame is short (height under
  600px: `@media (max-height:600px)` sets `position:static`). A wrapped sticky
  header filled a short Cloud frame so a reader saw only four of six chapters, and
  a full banner of about 120px was reported as scrolling away when left unpinned.
- **Axes:** a value axis spans the data's real minimum and maximum, and goes below
  zero when any value is negative. A multi-year monthly axis labels one tick per
  year so labels never run together.
- **Captions state only what the rows show.** Words like "every year", "always",
  "repeats" or a cause are allowed only after you tested them on the queried rows.
  Otherwise describe the range or the size of the move.
