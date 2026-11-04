# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

## 1.4.24 — 2026-11-04

- Datasource matching rule (datasource names only, never a project's ID) is also in
  SKILL.md; the 1.4.23 run still used a project ID for "use logistics".
- Scratch is kept until the user confirms the published view; later changes are made
  on the kept source and the whole gate re-runs.

## 1.4.23 — 2026-11-04

- `probe_signal.py` prints the proposal lines (measures, lead signal, move start, window,
  chapters, table rows) for the agent to copy; the 1.4.22 run miscounted the chapters line.
- Caveats: "no gaps and no nulls" and rise/fall restatements are banned.
- Declined shell prompt: ask for approval, never offer hosted mode as a workaround.

## 1.4.22 — 2026-11-04

- New `scripts/probe_signal.py` computes verdicts, lead signal, move start, window and
  divergent pairs from saved rows, so the maths no longer varies between runs.
- Pinned Step 0 and proposal wording moved to `references/messages.md`; SKILL.md
  is 280 lines instead of 451.

## 1.4.21 — 2026-11-04

- Datasource reply matches datasource names only, never a project name; the ID comes
  from the datasource's own entry (second-datasource run used a project ID and got a 403).
- Completion report shape is required for a Blocked build message too, with no cleanup promise.

## 1.4.20 — 2026-11-04

- Error playbook: expired sign-in, mid-run query failure and row-level security rows.

## 1.4.19 — 2026-11-04

- The datasource question starts from the open workbook: a connected published
  datasource is offered first ("Use it?"), several are listed alone, and the
  six-name list is asked only when none is connected.

## 1.4.18 — 2026-11-04

- Datasources with equal updated times list A to Z (two runs showed A to Z, most
  likely because every time was the same). The Lead signal line carries nothing
  after the figure. The page shows the proposal's move start date, not one
  recomputed in the window. The completion report omits scratch cleanup and an
  up-to-date update check.

## 1.4.17 — 2026-11-04

- The Lead signal figure must equal the first table row's change (a run showed
  +23.0% above a table that said +18.7%). The banned-caveat rule gets a concrete
  example. The datasource list must print in the newest-first order it was sorted
  into (a run fetched updatedAt and still listed A to Z).

## 1.4.16 — 2026-11-04

- Move start is now defined exactly (sample SD, 7-period trailing mean over periods
  i-6..i, move start at the end of the first qualifying span in the final unbroken
  run). The Logistics runs gave 2026-07-22 four times and 2026-07-25 once, so
  the earlier date may have used a different definition; recheck on a fresh run.
- The datasource question lists the six most recently updated (A to Z if the
  list has no updated time).
- SKILL.md shortened (494 to about 430 lines): the full Invariants text moved to
  references/invariants.md.

## 1.4.15 — 2026-11-04

- A fresh run clears the scratch folder and starts from the bundled template (a
  publish run reused a leftover template and kept the old top-bar title).
  The Lead signal line holds only the field and its change.

## 1.4.14 — 2026-11-04

- With a move start, the first-14 vs last-14 column is taken from the story
  window, so the page headline and the proposal agree (the Logistics page
  showed +18.7% against +23.0% in the proposal). Caveats hold no build plans.
  Long datasource names are shortened in the cover title.

## 1.4.13 — 2026-11-04

- Change cells show only the signed percentage (a run showed "3.3% -> 4.0%
  (+23.0%)"), and the Move start line keeps its "Move start date:" label.

## 1.4.12 — 2026-11-04

- Logistics repeat runs matched on every number; wording pins from them: Rule
  column is only the aggregation, nothing (including divergent pairs) between
  the table and Caveats, and no "not checked" or "none found" caveats.

## 1.4.11 — 2026-11-04

- When more than 4 measures qualify, the Chapters line shows the real qualifying
  count and says the 4 strongest get chapters; the cap is not a caveat (the
  Logistics proposal said "4 qualifying" with 6 qualifying and added a cap caveat).

## 1.4.10 — 2026-11-04

- Both bundled templates now draw and label dates in UTC (utcFormat, scaleUtc and a
  UTC "as of" date), because the live read gives midnight-UTC dates and local
  formatting showed them a day early in time zones west of UTC. The hosted run
  fixed this in its own page; this puts the fix in the templates.

## 1.4.9 — 2026-11-04

- Hosted end-to-end run: no figures in caveats, a pending user check keeps the
  turn Blocked (not Done), and a percent field on the page must equal the
  proposal's figure (Discount read 15.4% on the page, +1.4% in the proposal).

## 1.4.8 — 2026-11-04

- The page check now fails a sticky header that has no short-frame rule, and
  gate item 8 points to it, so the Cloud nav clipping found by eye is caught
  before publishing.

## 1.4.7 — 2026-11-04

- The yearly comparison uses each year's per-period average, not the raw year
  total (the packaged run reported Profit +85.6% from totals where the locked
  per-day method gives +75.3%, because 2023 starts on January 3).
- A third caveat is only for a real data-quality issue; no calculation notes.

## 1.4.6 — 2026-11-04

- Proposal wording pins from the 1.4.5 run: the Audience line keeps its label,
  the Move start line carries no baseline numbers, and caveats carry no yearly
  values or verdict explanations.

## 1.4.5 — 2026-11-04

- Profit Ratio is always probed when a datasource has both Profit and Sales, so
  the measure count no longer varies between runs (the hosted test counted 4 of
  4 where an earlier run counted 5 of 5).

## 1.4.4 — 2026-11-04

- The description now sends a plain queryAsync worksheet app to author-data-app
  and a single custom viz or story-less dashboard extension to author-extension,
  because Studio now ships both and this skill's packaged mode looks like the
  first one.

## 1.4.3 — 2026-11-02

From a full packaged run (it published; the user's check on Cloud found defects the
local checks missed).

- Only four of six chapter links showed in Cloud's frame: a wrapped, sticky header
  filled the visible area. Both templates now un-stick the header in short frames,
  and the style guide requires a one-row scrolling chapter nav.
- The monthly chart clipped negative values and its year labels ran together; the
  caption claimed "January dips repeat every year" without a test. The style guide
  now covers axes and captions, and the pre-delivery gate has item 8 for both.
- The story title pin carries the full datasource name ("Superstore Datasource
  Profit brief"); the run used "Superstore Profit Brief".

## 1.4.2 — 2026-11-02

- A run ended by offering a seventh chapter on its own (the locked maximum is 6).
  The limit now holds after the build: no unrequested extra chapters, and a
  requested one replaces the weakest signal chapter.

## 1.4.1 — 2026-11-02

From the first hosted-mode run (it got as far as the feeder sheet; hosting,
placement steps and the Publish dialog are still untested).

- A "full" year is judged from the data, never from today's date. The hosted run
  dropped 2026 and reported Profit +52.9% where the packaged runs gave +75.3%.
- The hosted feeder sheet needs the chosen datasource connected first. The skill
  now connects it through the workbook CLI instead of asking the user to choose
  between connecting it and using another source.
- The stop reply is different when a feed_data sheet was already added (the old
  wording said the workbook was unchanged, which was false).
- The hosted outline's audience line now matches the packaged one.
- The proposal carries no ranking line or anomaly caveat between the table and
  the caveats.
- Two rejected feeder edits now end in a hand-over of the manual recipe.
- A packaged run on 1.4.0 text-with-fixes reproduced the earlier numbers exactly
  (Profit +75.3%, Quantity +54.0%, Sales +42.5%, Profit Ratio +23.0%, Discount
  +1.3%). Two small pins from it: the datasource list order for names that differ
  only by a hyphen or underscore, and the Chapters line always carries the count of
  qualifying measures.

## 1.4.0 — 2026-11-02

From a re-grade (79.1; weakest areas were efficiency, autonomy and scalability).

- The prompting-level and style questions now arrive together in one message,
  with a "defaults" reply (Medium prompting, recommended style, executive reader).
  One fewer round trip before any work starts. Retest in a fresh chat.
- Probe scaling is now locked by size: narrow, typical, wide (capped at 20 measures
  with the cap stated), very wide (ask for a subset), and tiny (under 28 periods).
- From the first 1.4.0 run: both questions and "defaults" worked. Fixed three
  drifts: a lower-case datasource name now matches the full name instead of
  asking which of three, a disambiguation list carries no recommendation, and the
  stop reply is followed by nothing (a run added "I'm not reporting anything
  further"). The "defaults" acknowledgement is one pinned line.
- A second 1.4.0 run reached the proposal with the same numbers as before. Fixed:
  the render check's secrets scan flagged three event names in the bundled
  Extensions library (a real credential-style value is still caught; tested), and
  percentages in the proposal table are always signed with one decimal.

## 1.3.9 — 2026-11-02

- The update script is safer. It now installs the latest GitHub release when the
  repository has one (otherwise main), and `SKILL_UPDATE_REF` can force a tag,
  branch or commit.
- `apply` refuses a copy that is not newer than the installed one, is for a
  different skill, has links or unsafe paths, is larger than expected, or fails
  the optional `SHA256SUMS` check. A maintainer command, `sums`, writes that file.
- Tested with a local copy: same version, tampered file, wrong skill name and a
  good upgrade all behave as described.

## 1.3.8 — 2026-11-02

From a 1.3.7 run (outline, datasource question, proposal and verdicts all matched
the pinned wording and the earlier run's numbers).

- The stop reply is the final message: nothing after it when the update check has
  nothing to report, and never twice (it printed twice in two runs).

## 1.3.7 — 2026-11-02

From a 1.3.6 run (yearly verdicts, 4 qualifying measures, 6 chapters, pinned
stop all worked; four details drifted).

- The datasource question moved into Step 0 (item 7): the agent asked it before
  reading the procedure, so the 1.3.6 wording in the procedure was never used.
- The outline is now word for word, including its lead-in.
- Proposal: "Checklist" and "Caveats" headings, a one-line Grain, and the window
  question pinned word for word.
- Percent and rate fields (Discount) use the plain mean of per-period AVG values,
  never weighted by row counts (runs gave -34% and -25%).

## 1.3.6 — 2026-11-02

From a 1.3.5 run (proposal shape matched; three details differed).

- With no move start, the yearly comparison now decides every verdict (first-14 is
  reference only), so a measure like Profit Ratio (+23% a year, -2.5% first-14) is
  no longer shown as "noise" next to a qualifying yearly change. Measures are
  ranked by absolute yearly change; that order sets the lead signal, table rows
  and chapters. Superstore now gives 4 qualifying measures and 6 chapters.
- Datasource question: exactly six names, A to Z, numbered, with no suggestions or
  remarks (the old "first six as returned" order changed between runs and made "1"
  pick a different datasource).

## 1.3.5 — 2026-11-02

Re-graded 81.1 (B-, stricter pass than the earlier 85.1; not comparable).

- Proposal shape pinned: opening sentence, checklist (fixed lines), measures
  table, at most three caveats in a fixed order, window question last.
- Chapter titles and order pinned for the build (question opening, result
  sentences with real numbers, largest change first, fixed closing titles).
- Not yet retested in fresh chats.

## 1.3.4 — 2026-11-02

From two fresh-chat runs of 1.3.3 (both clean on Step 0, window fallback,
seasonality check and stop; they differed on three details).

- Profit Ratio is a ratio of block sums, never an average of per-period ratios.
- Proposal table columns pinned; the yearly comparison covers every measure,
  ratios included; measures are named by field name with "N of N (names)".
- Chapter count is mechanical: qualifying measures + 2, clamped to 3 to 6; the
  audience no longer changes it (one run gave 4, the other 5).

## 1.3.3 — 2026-11-02

- New `scripts/check_story.py`: pre-delivery check on the built page. Static checks
  (no external scripts, no secrets, chapters, prose spans, query window filter and
  aliases) plus a headless Chrome/Edge render that checks every chapter for
  placeholder text, empty spans, thin chapters and missing charts. Now gate item 0.

## 1.3.2 — 2026-11-02

From a full 1.3.1 run through publish (worked end to end; live numbers verified).

- Seasonality check when there is no move start: a measure that qualifies on
  first-14 vs last-14 but not on first vs last full calendar year is "noise
  (seasonal)" and can't be the lead signal, so the proposal matches the build.
- Outline only after the delivery answer, for the chosen mode; verdict cells are
  exactly "qualifies" or "noise"; a final message is sent once.
- Completion report: Blocked whenever a manual check is left; no package id.
- No update remark when the local version is newer than the remote.

## 1.3.1 — 2026-11-02

Fixes from two fresh-chat runs of 1.3.0 (same answers; the pinned Step 0 text
matched in both, but later steps differed).

- Window rule is now numeric: baseline = mean and SD of the first 14 periods; move
  start = first period from which the 7-period trailing average stays more than
  3 SD from the baseline mean through the latest period. If none qualifies, the
  window is the full history, with a note, and is still confirmed with the user.
- Measures probed: count every numeric measure the datasource lists, including
  calculated ratios, as "N of N"; no extra measures such as row counts. Divergence
  is tested on every pair.
- Datasource question pinned; the audience is asked once (in the style question).
- Style question: nothing after the two Optional lines.
- Pinned clean-stop reply; scratch files are deleted silently. Messages never say
  "the build procedure".

## 1.3.0 — 2026-11-02

Re-graded 85.1 (B); this release addresses the three biggest gaps. Not yet
retested in fresh chats.

- The update check now runs last, after the final message or a clean stop, so it
  can't delay the orientation in Step 0.
- The orientation paragraph and the delivery-mode, prompting-level and style
  questions are now fixed wording, one question at a time. New "Check before
  sending" for Step 0 and the proposal.
- New gate item: before the first publish, check the project for a different
  workbook with the same name (the publish command overwrites without asking).
- Removed two duplicated rules from "Common mistakes", and the scratch folder is
  now described relative to the skills folder instead of a personal path.

## 1.2.1 — 2026-11-02

- Safer unpacking in the update script (`scripts/check_update.py`). No change in
  behavior.

## 1.2.0 — 2026-11-02

Update check on launch: the skill now checks the DanPinault/tableau-studio-skills
repository for a newer version before doing anything else, and offers to
install it (old copy is backed up), skip it, or stop reminding for that
version. Works offline (silently skipped). Adds `scripts/check_update.py`.

## 1.1.0 — 2026-11-02

Results of a 24-prompt test matrix (24/24 pass, six rows only after fixes) and a
re-grade (88.4, B+).

### Added
- Locked window rule as a numbered procedure: finest native grain, probe every
  numeric measure, lead signal with a tie order, move start at 3 SD, window
  starts 14 periods before the move, ends at the latest complete period, max 3x
  the move length.
- Mechanical qualification: each measure qualifies by its first-14 vs last-14
  period change against the locked thresholds, never by judgment. The proposal
  lists every measure with its change, aggregation rule and verdict.
- Aggregation by measure type: totals SUM; percentages, hours and indexes AVG;
  per-unit ratios as a ratio of sums when both parts exist, otherwise AVG
  labeled "average".
- Locked chapter count (one per qualifying signal plus opening and closing, 3 to 6).
- "Never skip" list and a restate checklist in the Build section.
- Two opt-in offers at the style question: Tableau Public Viz of the Day and
  the Exchange extension lookup. Nothing is fetched until the user says yes.
- New references: `output-styles.md`, `sample-gallery.md`.

### Changed
- A user-named change below the locked thresholds (for example "a 2% change")
  is declined with the numbers in the first reply.
- A user's claim that Packages is not enabled is checked with the setup check
  before acting on it.
- Hosted dashboard placement always gives all 5 manual steps in full, with
  Automatic sizing.

### Known limits
- Packaged stories cannot be previewed in Tableau Desktop or Studio; view them
  in Tableau Cloud.
- Hosted mode cannot publish headlessly; the Publish dialog is the user's step.
- Reproducibility across fresh chats is good but rests on two agreeing test
  pairs.

## 1.0.0

Packaged-extension (Tableau Data App) delivery mode as the default, hosted mode
as an option, and the original build procedure and style guide.
