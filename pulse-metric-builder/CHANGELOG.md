# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

## 1.2.6 — 2026-11-02

- The update script is safer. It now installs the latest GitHub release when the
  repository has one (otherwise main), and `SKILL_UPDATE_REF` can force a tag,
  branch or commit.
- `apply` refuses a copy that is not newer than the installed one, is for a
  different skill, has links or unsafe paths, is larger than expected, or fails
  the optional `SHA256SUMS` check. A maintainer command, `sums`, writes that file.
- Tested with a local copy: same version, tampered file, wrong skill name and a
  good upgrade all behave as described.

## 1.2.5 — 2026-11-02

- Tested the full path on a real measure (Profit): plan, create, read-back,
  value check ($24.3K YTD) and one card on a dashboard. All passed.
- The time-field note now allows nothing after its fixed sentence (a run added
  its reasoning and a remark about another metric).
- A blank or covered card: screenshot once more, and if still unconfirmed say so
  and give the metric link as the fallback.

## 1.2.4 — 2026-11-02

- Tested 1.2.3 with two fresh chats on Profit: introduction, options, name,
  columns, currency code, date-field order, filter note, closing line and stop
  sentence all matched.
- Fixed the two remaining differences: the assumptions line in the plan is now
  fixed wording, and the plan never remarks on other definitions (only the
  "none yet" warning is allowed). The stop reply now adds nothing after the
  fixed sentence (a run had added a note about a temp file).

## 1.2.3 — 2026-11-02

- Found on a Profit run: the order of "Other date fields" varied, and the plan
  showed "Currency" without the code. Other date fields now follow the order the
  field list gives; CURRENCY always carries a currency code (USD by default) and
  the plan shows "Currency (USD)".
- The introduction is given on the first reply to a Pulse request even when the
  chat had earlier answers, and skipped only if already given in the same chat.

## 1.2.2 — 2026-11-02

- The reply to "stop" before a create and the filter-dimension note in the plan
  are now fixed wording (each was worded differently in every test run).
- Tested after 1.2.1: the metric name, time-field note, introduction and options
  matched on a fresh chat. A second run landed on a different data source with
  no Sales field and correctly declined to substitute one.

## 1.2.1 — 2026-11-02

- Found in a fresh-chat pair: the metric name differed (`Superstore_orders Sales`
  vs `Superstore Sales`) and the time-field note contradicted itself. The data
  source name is now used exactly as returned (the example was misleading), and
  the time-field note has fixed wording.
- The Short and Verbose option lines and the order of the last lines of the
  Step 0 message are now fixed wording.

## 1.2.0 — 2026-11-02

- The update check now runs last, after the final message or a clean stop, so it
  can no longer conflict with the introduction in Step 0 or delay the sign-in
  check.
- The Step 0 introduction is now fixed wording, so two runs open the same way.
- Keyword matching for sentiment and format is exact: a keyword matches a word
  that equals it or starts with it.
- Not yet retested after these edits.

## 1.1.1 — 2026-11-02

- Description now says that other dashboard extensions are not this skill.
- New pre-send check for plans and reports, and a "Common mistakes" item for it.
- Sentiment and format now come from a fixed keyword table, so two runs choose
  the same values.
- Measure suggestions are ordered by how many sheets chart each measure.
- Safer unpacking in the update script (`scripts/check_update.py`).

## 1.1.0 — 2026-11-02

Update check on launch: the skill now checks the DanPinault/tableau-studio-skills
repository for a newer version before doing anything else, and offers to
install it (old copy is backed up), skip it, or stop reminding for that
version. Works offline (silently skipped). Adds `scripts/check_update.py`.

## 1.0.0 — 2026-10-13

First release in Tableau Studio Skills. Passed a 24-row test matrix and was
graded 84.7 (B).

- Creates, lists, renames and deletes Tableau Pulse metric definitions and
  metrics on a published data source, through the Pulse REST API with a bundled
  script.
- Outputs the settings for Studio's Pulse Metric dashboard object.
- Reference files for setup, data source checks, measure suggestions, the metric
  spec, output formats, API notes and card placement.
