# Output formats (Step 4)

Use these two layouts exactly, so every run reads the same. Plain language only:
no script, command or tool names, and no raw IDs except the link.

## 1. Plan (before create)

One table, one row per metric:

| Name | Measure | Time field | Filter dimensions | Period | Sentiment, format | Action |
|---|---|---|---|---|---|---|

- **Measure:** aggregation and field, for example `Average of Sales`. For an
  aggregate calc write `Calculated (Profit Ratio)`.
- **Action:** exactly one of `Create`, `Reuse` (a definition with that name
  exists), or `Blocked` (same data source, measure, aggregation and filters as
  another definition; say which one below the table).
- **Over 10 metrics:** split into tables of 10 under the heading `Metrics 1–10`,
  `Metrics 11–20`, and so on.

Under the table, a `Notes` list. Include each item that applies, one line each,
and omit the heading if none apply:
- Assumed defaults: which of sentiment, format and period you inferred or
  defaulted, and why.
- The time field chosen and the alternative you didn't pick.
- Aggregate calc measures set to Calculated.
- Fields resolved from caption to internal name.
- Warnings, such as no existing definitions on this data source.
- Other work in the request (a worksheet, calculated field, or a question about a
  metric's value, trend or drivers): one line saying it isn't part of this plan,
  who handles it in plain words, and that you'll ask before starting. For
  example: `The line chart and calculated field aren't part of this plan. I'll
  ask you before starting them, through the Tableau authoring side.` Use "the
  insights analysis" for value, trend or drivers questions.

End with this line, using these words exactly, on its own final line:
`Say yes to create these, or tell me what to change.`

## 2. Report (after create, read-back and value check)

One table, one row per metric:

| Name | Measure | Time field | Period | Value | Link | Status |
|---|---|---|---|---|---|---|

- **Value:** the figure and period from the value check, for example
  `$217.33 (2026 YTD, -4.1% vs 2025)`. If there was no figure, write
  `No value`.
- **Link:** the metric's Pulse link.
- **Status:** exactly one of `Created`, `Reused`, or `Failed` (put the reason and
  the fix in Notes, not in the cell).

Under the table, a `Notes` list, one line each, omitted if empty:
- Each `No value` or `Failed` metric: what happened and what you suggest.
- Any metric the read-back didn't list as intended.
- Anything that differs from the plan the user approved.

End with exactly one next step: place the metrics as cards on a dashboard (Step 5),
fix the failed ones, or nothing further.
