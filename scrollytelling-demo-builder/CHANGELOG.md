# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

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
