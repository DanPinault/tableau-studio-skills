# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

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
