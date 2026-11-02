# Spec fields (Step 3)

Shape: see `spec-example.json`. Shared values go in `defaults`; each entry in
`metrics` overrides them.

Required for every metric. Ask the user for any they haven't given, offering a
suggestion from the fields list:

| key | what to ask / suggest |
|---|---|
| `name` | Metric name as people will see it in Pulse |
| `datasource` | LUID from Step 2 |
| `measure` | A plain measure or calc. If it's an aggregate calc (formula already contains SUM/AVG, like `SUM([Profit])/SUM([Sales])`), the script sets aggregation `USER` (the UI's "Calculated") for you; SUM on it returns no value (see api-notes) |
| `aggregation` | SUM, AVERAGE, COUNT, COUNT_DISTINCT, MIN, MAX (USER is set automatically for aggregate calcs) |
| `time_dimension` | A date or datetime field |
| `dimensions` | at least 1 categorical field people can filter by (Region, Product...). Bins don't count |
| `sentiment` | UP (up is good), DOWN (down is good), NONE |
| `format` | NUMBER, PERCENT, CURRENCY (+ `currency`, default USD) |
| `period` | today, yesterday, wtd, last-week, mtd, last-month, qtd, last-quarter, ytd, last-year |

## Defaults for sentiment, format and period

Determine these from the metric first; use the default only when you can't, and
list each one you assumed in the plan. Don't ask the user unless they raise it.

**Keyword lookup (use this before the table below).** Match case-insensitively
against the measure's caption, whole words or word stems. Check the rows in order
and stop at the first match:

| Order | If the caption contains | sentiment | format |
|---|---|---|---|
| 1 | cost, expense, return, churn, defect, refund, loss, delay, late, error, complaint | DOWN | CURRENCY if it also contains cost, expense, refund or loss; otherwise NUMBER |
| 2 | ratio, rate, margin, percent, %, share, pct | UP (DOWN if row 1 also matched) | PERCENT |
| 3 | sales, revenue, profit, income, order, quantity, units, bookings, volume | UP | CURRENCY if it contains sales, revenue, profit, income or bookings; otherwise NUMBER |
| 4 | no match | NONE | NUMBER |

If the caption contains both a row 1 and a row 3 word (for example "Cost of
Sales"), row 1 wins.

| key | infer when | otherwise |
|---|---|---|
| `sentiment` | the measure is clearly good-up (sales, profit, revenue, orders) → UP; clearly good-down (cost, returns, churn, defects) → DOWN | NONE (neutral) |
| `format` | a ratio or rate (profit ratio, margin, %) → PERCENT; money (sales, profit, cost) → CURRENCY | NUMBER |
| `period` | the user names one | ytd |

Optional: `description`, `units` (`["order", "orders"]`), `filters`
(`[{"field": "Status", "values": ["Closed"]}]`), `comparisons` (default
`["previous-period", "year-ago"]`), `use_latest_data` (default `true`: anchors
periods on the latest date in the data, not today; keep it on for demo data
that stops in the past), `running_total`.

Fields can be given by caption; the script resolves them to internal names. If a
caption fails to resolve, use the `name` that `fields` shows.

## Choosing the time dimension

Decide `time_dimension` before creating, and tell the user which one you chose.
A plain name like "Order Date" resolves to the raw date field even when the
workbook charts a calculated date (for example a "shifted to today" calc). If the
workbook's dashboards use a calculated date, ask whether the cards should use it
too, so cards and charts cover the same window. Calculated dates (including
`TODAY()`/LOD calcs) are accepted as the time dimension; pass the `Calculation_...`
name from `fields`. A metric's time dimension can't be changed afterwards, because
Pulse allows only one definition per data source, measure, aggregation and filter
set whatever the time field. Switching later means `delete` + `create`, so get it
right the first time.

## Aggregate calcs as the measure

A calc whose own formula already contains SUM, AVG and so on is an aggregate
calc. Plain measures and row-level calcs are fine with any aggregation. For an
aggregate calc the script switches to `USER` automatically and notes it in the
plan; tell the user. See `api-notes.md` for the tested behavior.

## Locked choices (apply in order; the user's own choice always wins)

State each choice in the plan so the user can override it.

**Time dimension**
1. The user named one → use it.
2. Exactly one date field → use it.
3. Both a raw date and a calculated date exist → ask once, naming both. Ask even
   in short mode, because the choice can't be changed later.
4. Several raw dates → use the first whose name matches order, sale, transaction,
   created or close (case-insensitive); if none match, ask.

**Filter dimensions** (`dimensions`)
1. The user named some → use them.
2. Otherwise take string dimensions from `fields` that aren't hidden, aren't
   calcs, and whose name doesn't match ID, Key, Code, Number, Email, Phone,
   Address, City, Postal or Zip. Use the first three in the order `fields` lists
   them.
3. Fewer than one left → stop and tell the user; Pulse needs at least one (see
   api-notes).

**Metric name** (the user's own name always wins)
`<data source name> <label>` where the label is the measure caption, with a prefix
or suffix by aggregation: SUM and USER → none; AVERAGE → "Average" before it;
COUNT → "Count" after it; COUNT_DISTINCT → "Distinct" before it; MIN or MAX →
"Minimum" or "Maximum" before it. With one filter, add " - <filter value>" at the
end. Example: `Superstore Average Sales`.

## More locked choices

**Aggregation** (when the user doesn't say; check the aggregate-calc rule first)
- Quantities, amounts and counts of things (sales, profit, quantity, orders) → SUM
- Per-unit or per-row values (price, discount, score, rating, rate) → AVERAGE
- An ID field → COUNT_DISTINCT
- Anything else → ask once, offering SUM and AVERAGE.

**Filters and description:** none unless the user asks. Leave `description` empty.

**Metric with the same name as an existing definition:** it is reused unchanged.
If the user wants it changed, that's delete + create, with their confirmation by
name.

**When the value check returns no figure** (try in order, stop at the first fix)
1. The measure is an aggregate calc and the aggregation isn't Calculated → say it
   needs recreating; delete + create, with confirmation.
2. Otherwise add a year-to-date metric on the same definition and check that one.
   If it has a figure, the first period had no data; report that and keep the
   year-to-date one.
3. Otherwise report it as blank and ask the user to open the link.

## Period tip

If the data ends before today and `use_latest_data` is off, short periods
(last-week, mtd) show nothing. `ytd` is the safest demo default.
