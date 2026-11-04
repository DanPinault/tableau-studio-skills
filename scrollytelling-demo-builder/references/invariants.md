# Invariants (full wording)

The short list is in SKILL.md; this is the full text of each rule.

- **The live bind is always Tableau's, never baked data.** In both modes the read
  is RLS-aware and live-on-open.
  - **Packaged:** `queryAsync` against the published datasource, using the query
    JSON validated with `package_extension.py query`. Alias every field to the
    `MEAS` caption, and keep the window filter.
  - **Hosted:** a `feed_data` worksheet in the SAME workbook, read with
    `getSummaryDataAsync`. Match the feeder-sheet name and column contract
    exactly; see the style guide.
- **Publishing depends on the mode.**
  - **Packaged:** publish over REST with `package_extension.py publish`, but only
    after the user has confirmed the target project. Verify with `--image` and
    the user's own look at the view.
  - **Hosted:** Publish is a user step, and you must never claim a headless
    publish there. Save headlessly with an explicit `filePath`, trigger publish,
    then tell the user to complete the Publish dialog and wait for their
    confirmation.
- **PAT secrets never pass through you.** They live in Keychain (`store-secret`
  prompts in the user's terminal) or the user's own `TABLEAU_PAT_SECRET` env var.
  Never ask for a secret in chat or echo one, and never write site names, LUIDs or
  PAT details into this skill's folder. Scratch and config files only.
- **The goal is not a like-for-like reproduction of the vendored sample
  dashboards.** The vendored COO/CFO templates are a style and mechanics
  reference (animation, D3 patterns, Demo/Live toggle, prose-binding), not a
  fixed page structure to fill in. The signal actually found in the data, and
  who the story is for, should determine which acts/chapters exist, how many,
  and in what order — not the sample's chapter list. Drop a template chapter
  that has no honest analog in the real data (already required in step 4);
  also feel free to reorder, merge, split, or add a chapter if that's what the
  real story and audience call for, rather than defaulting to the template's
  shape.
- **The vendored templates are inspiration for mechanics only, never a source
  of numbers, fields, or story content.** Start from `assets/public/coo-brief.html`
  or `assets/public/cfo-brief.html` purely for their code plumbing —
  `readFromWorksheet`/`readPackagedTable`/`contractFromRows`/Demo-Live-toggle/D3 draw patterns.
  Keep the self-contained build discipline (0 external `<script src>`). Every
  axis domain, threshold, unit literal, KPI, chapter topic, and copy phrase in
  the template belongs to ITS original demo story (revenue-per-load, margin,
  warehouse utilization, etc.) — none of it transfers to a new datasource.
  Treat the templates the way you'd treat a coding reference, not a fill-in
  form: copy no story-specific number, field name, or narrative claim from
  them. See `references/build-procedure.md` step 4 for how to audit each
  chapter for leftover template-story content.
- **Style is chosen, not inherited.** The vendored templates' dark navy, serif,
  glow look is one style among several. Apply the chosen style from
  `references/output-styles.md` by overriding theme tokens and layout, keep the
  plumbing untouched, and never copy template titles or taglines.
- **Every number shown anywhere on the page — in Demo mode or Live mode, in a
  chart or in prose — must trace back to a real row you queried from the
  user's chosen datasource (`feed_data` or the packaged query).** Never fabricate a signal, KPI,
  threshold, or narrative number. `SEED` is not an exception: it must be set
  from the same real rows you queried (so Demo mode tells the true story and
  matches Live mode), never left as a template placeholder or invented for
  effect.
- **When the Live toggle is on, every number on the page must come from live
  data — prose AND charts, no exceptions.** `applyMode("live")` must drive both
  the chart-drawing functions (via `D`) and `paintProse()` (which rewrites every
  `[data-v="key"]` span) from the same live contract. A chart that updates but a
  headline/caption that still reads the SEED number (or vice versa) is a bug,
  not an acceptable partial state — verify both, not just one, when checking
  Live mode works.
- **The Explore view is live-only, and the story is never filtered.** All filters
  live in Explore, never in the scroll story — so no authored prose claim can go
  false under a filter. Explore slices `liveRecs`, which is populated ONLY when the
  live worksheet read passes `captureLive` to `contractFromRows`; the baked snapshot
  never does, so in Demo/snapshot mode the filter bar greys out with a note instead
  of showing fabricated rows. Preserve this greying when adapting — never invent
  row-level data to keep the filters active. See `references/style-guide.md`.
- **Never assume a CLI or runtime is installed/configured on the user's machine**
  (Python, wrangler, netlify-cli, any deploy tool they mention). Check it
  yourself (e.g. a version/whoami command) before relying on it; if missing or
  unauthenticated, stop and [needs you] with exactly what to install or run.
- **Scope:** v1 starts from an EXISTING published datasource. Generating the
  dataset/datasource/story from scratch is a deferred future enhancement — do not
  attempt it unless the user explicitly expands scope.
- **Scope — blended or dateless datasources:** if the chosen datasource is a
  blend (multiple published sources joined at the Studio layer) or has no
  usable date/day-offset field to window the story, say so plainly before
  building `feed_data` — a time-windowed trend story needs a date field, and
  a blend can complicate the RLS-aware live read. Ask the user for a
  single-datasource alternative, or (with an explicit non-time-series signal
  — see build-procedure step 2) proceed without a date window instead of
  forcing one.
- **Adjacent skill (`author-extension`):** placing an already-installed or
  Exchange extension, or building a single custom viz extension, belongs to
  `author-extension`, not this skill.
- **Adjacent skill:** this skill is mechanics/story-plumbing only — it does not
  set brand colors or a theme. If the user also wants the story's look to match
  a company brand, hand that off to `brand-theme-builder` for the color/theme
  choices and keep this skill's job to the story, data bind, and extension
  mechanics.
- **Naming conventions to avoid collision with other skills/sessions:** always
  name the feeder sheet `feed_data` (never a generic name like `Sheet 2` or
  `data`) and scope scratch files under this skill's own
  `.build/scrollytelling-demo-builder/` subdirectory (never the shared
  `.build/` root) — see Scratch files below. This keeps a re-run or a
  different skill's scratch work from colliding with or overwriting this
  skill's artifacts, and makes the feeder sheet unambiguously identifiable by
  the step-5 "check for an existing feed_data-shaped sheet" reuse check.
