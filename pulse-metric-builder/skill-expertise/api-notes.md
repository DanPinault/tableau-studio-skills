# Pulse REST API notes

The script already handles most of these; they're here so you can explain
errors and steer the spec.

- **Base URL** `https://<pod>/api/-/pulse`, header `X-Tableau-Auth` from a REST
  sign-in. Sign in with a **PAT**. Connected App JWTs have returned 403 on
  `POST /definitions` even with the Pulse scopes.
- **First definition on a data source:** not always blocked. Some data sources
  return 400 until a metric is saved in the Pulse UI; others accept it. So try
  it; only if it returns 400,
  have the user save one metric in the Pulse UI, then retry. The dry run notes
  when a data source has no definitions.
- **Send the full body** the Pulse UI sends (insights settings, comparisons,
  representation options). Trimmed bodies return 400 on many data sources. The
  script's `definition_body()` is that full shape.
- **At least one categorical filter dimension** (`allowed_dimensions`) is
  required, or 400. Bins don't count. If the data source has none, the user can
  add a simple string calc in the data source and republish.
- **Calculated fields by internal name.** A calc referenced by caption returns
  404. Use the `Calculation_…` name from `fields` (the script resolves captions).
- **409** = duplicate name, or a second definition with the same data source,
  measure, aggregation and filters. The dry run catches the second case.
- **What counts as an aggregate calc.** Plain measures (Sales, Profit) and
  row-level calcs (`[Profit]/[Sales]` per row, a 1/0 flag) are fine: Pulse applies
  the SUM or AVERAGE you choose. An aggregate calc has an aggregate function
  inside its own formula (`SUM([Profit])/SUM([Sales])`), so Pulse would aggregate
  an already-aggregated value. A FIXED, INCLUDE or EXCLUDE LOD
  (`{FIXED [Order ID]: SUM([Sales])}`) is row-level to Pulse, so the script
  ignores aggregates inside LOD braces. Pulse rejects table calcs (`WINDOW_…`,
  `RUNNING_…`) as the measure. The restriction applies to the *measure* only: a
  date calc flagged `aggregate_calc` (e.g. one using `{ MAX(...) }`) still works
  as the time dimension.
- **Aggregate calcs as the measure use aggregation `USER`.** A calc like
  `SUM([A])/SUM([B])` sent as SUM is accepted (no error) but the metric returns
  no value for any date range. The Pulse UI's "Calculated" option is the API
  aggregation `USER`. The script switches to `USER` automatically for any measure `fields` marks
  `aggregate_calc: true`, and rejects `USER` on any other measure. The sparkline
  is non-cumulated (the script's `running_total` defaults to false). A metric
  already created with SUM on an aggregate calc is broken; the user can fix it in
  the UI, or delete it (with their confirmation by name) and recreate it.
- **Shared-calc captions can come back as the internal name.** A published data
  source can report a calc's caption as `Calculation_…`, so a plain caption may
  not resolve. Run `fields` and use whatever `name` it shows.
- **Distinct counts:** `COUNT_DISTINCT` on an ID field.
- **`GET /definitions` has no data source filter** (400). The script pages
  through all definitions and filters locally.
- **Metrics:** `POST /metrics:getOrCreate` with the definition ID, a
  `measurement_period` (granularity + `RANGE_CURRENT_PARTIAL` for to-date or
  `RANGE_LAST_COMPLETE` for last full period), and a comparison. It returns the
  existing metric if one matches.
- **Data that stops in the past:** with `use_dynamic_offset: true` (spec
  `use_latest_data`, default on) periods anchor on the latest date in the data.
  Without it, last-week/mtd metrics on old data are empty. YTD is the safest
  card default.
- **PAT sessions:** signing in with a PAT ends any other session using the same
  PAT, so run script commands one at a time; a parallel call ends the other's
  session (401, exit 2). Unused PATs expire after 15 days.
