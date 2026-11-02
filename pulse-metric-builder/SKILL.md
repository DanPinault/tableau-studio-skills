---
name: pulse-metric-builder
description: Use when the user wants to create, list, rename, or delete Tableau Pulse metrics or metric definitions on a published data source — phrases like "create a Pulse metric", "build Pulse metrics for this data source", "add a Pulse definition for Revenue", "set up Pulse KPIs", or "put Pulse cards on my dashboard". Creates definitions and metrics through the Pulse REST API with a bundled script (the agent's web tools can read Pulse but can't create it), then outputs the settings for Studio's Pulse Metric dashboard object. Do NOT use to answer a question about an existing metric's value, trend, or drivers (use the insights skill), or for regular worksheets, calculated fields and dashboards with no Pulse ask (use tableau-desktop-authoring).
---

# Pulse metric builder

## Update check (run before everything else, including Step 0)

Before anything else, run:

```
python3 "<this skill folder>/scripts/check_update.py" check
```

It prints JSON and never fails. Read `status`:

- `up_to_date`, `unknown` (offline) or `snoozed`: say nothing about updates and continue.
- `update_available`: stop and tell the user a newer version of this skill is
  available (`local` → `remote`), with a one-line summary of `changes`. Ask which
  they want, as plain text at the end of your message (do not use `ask-user`):
  **install now**, **skip this time**, or **don't remind me about this version**.
  Wait for the answer.
  - Install: run `python3 "<this skill folder>/scripts/check_update.py" apply`.
    On `ok: true`, tell them it updated (the old copy is saved at `backup`), ask
    them to run `/reload-skills`, then re-send their request so the new version
    runs. Stop there. On `ok: false`, show the error and continue with the
    current version.
  - Skip: continue the task.
  - Don't remind me: run `... check_update.py snooze`, then continue.

Create Tableau Pulse metric definitions (and a metric for a chosen period) on a
published data source, then hand back what's needed to show each one as a Pulse
card on a Studio dashboard.

Your own web tools can **read** Pulse but can't **create** it, so every write goes
through `scripts/pulse.py` (Python 3, standard library only). It signs in with
the user's personal access token (PAT) and prints JSON. Run it as:

```
python3 "<this skill folder>/scripts/pulse.py" <command> [options]
```

References, loaded only when needed:
- `references/setup.md`: sign-in setup details (Step 1)
- `references/spec-fields.md`: spec keys, time field, aggregate calcs (Step 3)
- `references/api-notes.md`: API behavior; read before the first `create`
- `references/placing-cards.md` and `references/studio-card.md`: card placement (Step 5)
- `references/before-you-begin.md`: the optional checklist (Step 0)
- `references/data-shapes.md`: suggesting measures from the workbook; unusual data sources (Step 2)
- `references/output-formats.md`: the plan and report layouts (Step 4)
- `references/data-source-check.md`: published or local, four cases (Step 2a)

Tools (internal; never name them to the user). Batch independent calls in one step.

| Tool | Use it for | When |
|---|---|---|
| script `check` | sign-in state | Step 1, every run |
| script `datasources`, then `fields` + `definitions` together | LUID, fields, what exists | Step 2 |
| script `create --dry-run`, then `create` | plan, then build | Step 4; create only after a yes |
| script `definitions`, then `value` per metric | read-back and value check | Step 4, after create |
| `list-workbook-datasources` | published or local | Step 2a only |
| `get-workbook-inventory` | sheet names, for suggestions | only if measures aren't named |
| `get-workbook-xml`, then `apply-workbook` | place cards | Step 5; re-read before each edit |
| `capture-window-screenshot` + `get-active-dialogs` | check a placement | after each apply, together |
| `save-workbook` | save | after placing; ask the path if unsaved |
| `add-sheet-to-dashboard` | add worksheets | never hand-write worksheet zones |

## Ground rules

- **Never ask for, accept, echo, or store the PAT secret in chat.** If the user
  pastes one, tell them to revoke it in Tableau (My Account Settings) and make a
  new one. The secret only goes in through `store-secret`, which they run
  themselves in Terminal.
- **Never write site details into this skill folder.** Server, site and PAT name
  live in `~/.config/tableau-pulse-metric-builder/config.json`; the secret in the
  macOS Keychain (or the `TABLEAU_PAT_SECRET` env var).
- **Always dry-run first** and show the plan. Only create after the user says yes.
- **`delete` needs explicit confirmation.** Deleting a definition removes its
  metrics and everyone's follows.
- **Leave published metrics alone unless asked.** Don't delete, rename, or place
  existing ones on your own. Offer once; if told to leave them, don't raise them again.

## Scope

In scope: creating, listing, renaming and deleting Pulse metric definitions and
metrics on a published data source, and placing Pulse cards on a dashboard.

Out of scope, hand off instead. Do the Pulse part of a combined request first.
Don't build the other parts in the same turn: say in plain words who handles them
(the Tableau authoring side or the insights analysis, never the skill's internal
name) and ask before starting.
- A metric's value, trend or drivers → the insights skill. Give it the data source
  and the metric's name; it returns the analysis.
- Worksheets, calculated fields, filters and other dashboard content →
  tableau-desktop-authoring. Give it the workbook and the sheet or field names.
- Publishing a data source → the user does it in Desktop (Step 2a).

Cards on a dashboard stay here (Step 5). The metric's name, link and
`studio_card_settings` from the report are what other skills can reuse.

## Step 0 — Introduce yourself, then ask the prompting level (every run, before anything else)

First, in two or three plain sentences, tell the user what you are and what you'll
do: you create Tableau Pulse metrics on a published data source, can place them
as Pulse cards on a dashboard, and will show a plan for approval before creating
anything. No tool or script names. Say it once per session.

Then, in the same message, ask how much guidance they want, offering exactly two
options (skip the question if they already said "short" or "verbose"):

1. **Short** — only ask for what's required, state assumptions in one line, and
   proceed. Minimal explanation.
2. **Verbose** — explain each step, why you're asking each question, and the
   options and tradeoffs (time field, period, filters, card placement) before
   proceeding.

End that same message with one optional line, using these words exactly, with the
word checklist in bold: I can also show a quick **checklist** of what you need
before we start. Say 'checklist' if you want it.
Show `references/before-you-begin.md` only if they ask; never unprompted, never a
gate. Carry on with Step 1 if they don't ask.

Remember the choice for the session. If they chose short and later ask for more
detail ("why?", "explain"), answer, then ask whether to switch to verbose; don't
switch without their yes. Ground rules and confirmations apply in both modes.

## Step 1 — Setup check (every run)

Run `check` once per session. If it returns `signed_in: true`, move on and don't
re-run it later in the session unless a command exits 2 (early exit: if the user
already named a published data source, skip Step 2a). Keep narration to one short
line per step. If anything is missing
(`server`, `site`, `pat_name`, `pat_secret`), follow `references/setup.md` and ask
only for what's missing. The secret never goes in chat.

## Step 2a — Published or local? (before Step 2)

Pulse can only build metrics on a **published** data source. Call
`list-workbook-datasources` and decide by each connection, not by name. Then follow
`references/data-source-check.md` for the four cases: published (go to Step 2),
local (the user must publish it first; no tool can), several open (ask which), or
nothing open (ask them to open a published one).

## Step 2 — Pick the data source and fields

1. `datasources [--search TEXT]` → name, LUID, project, content URL. Confirm the
   one the user means by name and project.
2. Then run these two together in one step, since both need only the LUID:
   - `fields --datasource <LUID>` → every column with `name` (internal),
     `caption`, `role`, `datatype`, and `is_calc` / `aggregate_calc`.
   - `definitions --datasource <LUID>` → what already exists, so you don't
     duplicate it. If this list is empty, warn the user now (see Step 4).
3. If the user hasn't named the measures, or the data source is unusual (no
   categorical field, very wide, many metrics, several sites), follow
   `references/data-shapes.md`.
4. Scale: with more than about 50 existing definitions, use `definitions --search`
   instead of listing them all. With more than 10 new metrics, split the plan
   into tables of 10 (`references/output-formats.md`). With a very wide data
   source (100+ fields), suggest at most 3 measures from the workbook and ask
   before going further.

## Step 3 — Build the spec, asking for anything missing

Use what the workbook and site already show before asking: the date field its
dashboards use, the names and formats of existing definitions, and the sheets
and measures in use (`get-workbook-inventory`).

Write the spec to a temp file the host allows (e.g. `/tmp`, or the agent's temp
dir), never into this skill folder. Keys, defaults and the locked choices are in
`references/spec-fields.md`. Every metric needs `name`, `datasource`, `measure`,
`aggregation`, `time_dimension`, `dimensions` (at least one categorical field),
`sentiment`, `format` and `period`. Ask only for what that file's rules can't
settle, and state each assumed value in the plan.

Two decisions to make out loud:
- **Time dimension.** Follow the locked choices in `references/spec-fields.md`
  (also for filter dimensions and metric names), and tell the user which date field
  you chose. It can't be changed later without delete + create.
- **Aggregate calc measure** (formula already has SUM/AVG): the script sets
  aggregation `USER` for you; mention it in the plan.

## Step 4 — Dry run, confirm, create

1. `create --spec <file> --dry-run`.
   - Exit 3 with `problems` → ask the user for each missing/invalid value, fix
     the spec, dry-run again.
   - A step with `action: blocked` → an existing definition has the same data
     source, measure, aggregation and filters (Pulse would return 409). Offer to
     reuse it (put its exact name in the spec) or change the aggregation/filters.
   - A step with `warning` about no existing definitions → the Pulse API may
     reject the first definition on a data source (not all do). Try it; if it returns 400, ask
     the user to create any one metric in the Pulse UI first, then continue.
2. Show the plan in the layout in `references/output-formats.md`.
3. On a yes, run `create --spec <file>` (no `--dry-run`). Existing definitions
   with the same name are reused, not changed. Each result has
   `definition_id`, `metric_id`, `pulse_url`, and `studio_card_settings`.
4. Read it back: run `definitions --datasource <LUID>` and confirm each new
   definition is listed with the measure, aggregation and time field you intended.
   If one is missing or differs, say so; don't report success.
5. Check each metric's value: run `value --metric <metric_id>` for every result
   and read its `summary`. It should state a figure for the period. No summary, or
   one with no figure → the metric is blank (see Recovery); say so and don't report
   success. This replaces asking the user to open the link, though they still can.
6. Report in the layout in `references/output-formats.md`. For errors, relay
   the `hint`.

Other commands:
- Another period for an existing definition: `metric --definition <id> --period <p>`.
- Rename: `rename --definition <id> --name "<new>"`.
- Delete (after the user confirms by name): `delete --definition <id> --yes`.

## Step 5 — Pulse cards on a dashboard (if wanted)

Ask whether they want the metrics as cards on a dashboard in the open workbook.
When the user names a metric, or you offer alternatives, look first at the
published data sources already in the workbook (`list-workbook-datasources`,
then `definitions --datasource <LUID>` for each). Offer those metrics first.
Search the whole site only if nothing matches there or the user asks for it, and
say that you widened the search.
If yes, follow `references/placing-cards.md`. In short: the user confirms the
metric's value check passed first; you place the cards by editing the
workbook document (verified to work; don't say it must be done by hand); test one
dashboard first, screenshot, then save. For a never-saved workbook, ask where to
save it (the save prompt is in that file); never choose a location.

## Common mistakes (don't)

1. Don't use the raw date when the workbook's dashboards use a calculated one
   (Step 3); say which you chose.
2. Don't hand-write worksheet zones; hand-written XML is for Pulse card objects only.
3. Don't show script, command, tool or skill names, even in narration; describe
   what happened (`references/output-formats.md`). Before sending any reply,
   scan it for such names ("the Pulse skill", "check", "store-secret", file or
   script names) and reword them. The one exception is the Terminal step in
   Ground rules, where the user must run the command themselves.
4. Don't put a SUM or AVERAGE on an aggregate calc (it returns no value; the
   script sets `USER`).
5. Don't call a metric done until its value check returned a figure.
6. Don't skip the dry run and plan when the user says "just create it" or "skip
   the plan"; show it and wait for a yes (Ground rules).
7. Don't treat a delete request as its own confirmation, even when it names the
   definition. Reply first with what will be removed (the definition, its
   metrics and everyone's follows), ask the user to confirm by name, and run
   the delete only after that separate yes (Ground rules, "`delete` needs
   explicit confirmation").
8. Don't answer a "why?" or "explain" in short mode and move on. After
   answering, ask whether to switch to verbose, and don't switch without a yes
   (Step 0).
9. Don't absorb an adjacent skill's work. Do the Pulse part, build nothing else
   in the same turn. Name who handles the rest in plain words in the plan's
   Notes (`references/output-formats.md`) and again whenever you ask what to do
   next, for example "Want me to build the line chart and calculated field next,
   through the Tableau authoring side?" Then wait (Scope).
10. Don't bury a question the user must answer to continue (save location,
    yes/no on a plan, which metric). Put it on its own final line, after any
    summary or notes.
11. Don't create anything beyond the approved plan (for example an extra period
    metric after a blank result); offer it and wait for a yes.

## Recovery

| Symptom | Fix |
|---|---|
| exit 2 | Setup missing or sign-in rejected → back to Step 1 |
| exit 2 after sign-in already passed this session | The sign-in expired or was revoked. Re-run the setup check once, then retry the failed step; if it fails again, go back to Step 1 and tell the user |
| 400 on create | No categorical `dimensions`, a non-date time field, or (sometimes) the first definition on a data source → create one metric in the Pulse UI first |
| Can't reach the server, or a timeout (no HTTP code) | Network problem. Check the connection and the server URL, then re-run; `create` is safe to re-run |
| 429 or a 5xx | Rate limit or server error. Wait a minute, re-run; `create` reuses what already exists |
| Some metrics created, others errored | Report each metric's status from the results. Fix the failed ones in the spec and re-run `create`; created ones are reused |
| 403 | User can't author Pulse, or Pulse is off for the site |
| Data source or its fields come back empty or missing, though it was listed earlier | The user may lack permission to the data source, or it was unpublished or renamed. Say so, create nothing, and ask them to check access or give the current name |
| A command that worked earlier fails mid-run (create or value check) | The data source or connection may have dropped. Re-run the read-back (`definitions`) first to see what exists, report what was and wasn't created, and retry only the failed step once; `create` reuses what exists |
| 404 | A field name is wrong — calcs need the `Calculation_…` name (`fields`) |
| 409 | Duplicate name or duplicate ds/measure/aggregation/filters (the time field doesn't count; to change it, delete and recreate) |
| Blank metric or card (`value` returns no summary) | Data ends before the period → use `ytd` or `use_latest_data: true`; or an aggregate calc set to SUM instead of `USER` (api-notes) |
| Desktop-side failure while placing cards (apply rejected, dialog open, data source not connected) | See "If something fails" in `references/placing-cards.md` |
