# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

## 1.2.4 — 2026-11-02

- The update script is safer. It now installs the latest GitHub release when the
  repository has one (otherwise main), and `SKILL_UPDATE_REF` can force a tag,
  branch or commit.
- `apply` refuses a copy that is not newer than the installed one, is for a
  different skill, has links or unsafe paths, is larger than expected, or fails
  the optional `SHA256SUMS` check. A maintainer command, `sums`, writes that file.
- Tested with a local copy: same version, tampered file, wrong skill name and a
  good upgrade all behave as described.

## 1.2.3 — 2026-11-02

- The sentence that opens the project question (after the fix step) and the
  reply to "stop" are now fixed wording, so two runs read the same: the fix
  result always names the extension zones and package IDs, and the stop reply
  asks about deleting the fixed-for-publish copy once.

## 1.2.2 — 2026-11-02

- Fixed rule for telling Tableau Cloud from Tableau Server: a host that is or
  ends with `.online.tableau.com` is Cloud, any other host is treated as Server
  (the user can say it is Cloud), and with no link seen yet it assumes Cloud
  and decides again when a link appears.
- Fixed project matching: whole name only, one leading dot ignored. One match
  becomes the default (with its parent shown); two or more are listed with
  their parents and the user chooses.

## 1.2.1 — 2026-11-02

- Safer unpacking in the update script (`scripts/check_update.py`).
- Tidied two formatting nits in `SKILL.md`. No change in behavior.

## 1.2.0 — 2026-11-02

- The update check now runs last, after the final message or a clean stop, so
  it can never delay the sign-in check or the project question.
- Dropped the required opening plan sentence. It was skipped in every test run
  however it was worded, so the project question now carries that job.
- Step 4 project list: exact sort rule (case-insensitive, one leading dot
  ignored, ties by original name), with the total and parents on nested ones.
- New pre-send check on the project question and the final message.
- The step 4 question is now a fixed template (site, name, project, one project
  per line), the description names what the skill does not do (workbook-optimizer,
  tableau-desktop-authoring), and batches of more than 3 get a summary line.
- Tested: a plain workbook with `stop` at the project question, a project that
  doesn't exist, and a request that names project and name up front. All pass,
  nothing published. A workbook with a packaged extension and a real publish
  were not retested in this round.

## 1.1.0 — 2026-11-02

Update check on launch: the skill now checks the DanPinault/tableau-studio-skills
repository for a newer version before doing anything else, and offers to
install it (old copy is backed up), skip it, or stop reminding for that
version. Works offline (silently skipped). Adds `scripts/check_update.py`.

## 1.0.0 — 2026-10-30

First release. Tested with a 22-prompt matrix (21 pass, 0 open fail) and
regression runs on an extension workbook, a plain workbook, a full publish and
the ask-first check.

- Fires on any "publish this workbook" request to Tableau Cloud or Tableau
  Server, not only workbooks with an extension.
- Checks the sign-in and connection first, then always asks for site, project
  and name before publishing, and lists every publishable project.
- When the workbook carries a packaged extension, runs the bundled
  `fix_packages_for_publish.py` on a copy (`<name>.fixed-for-publish.twbx`) so
  the extension survives, then checks the published copy.
- A combined "publish and edit the extension" request edits first, then
  publishes. A declined permission prompt stops the run with nothing published.

### Known limits
- Tableau Server publishing is untested; the Server check is a link-domain
  heuristic.
- (1.0.0) The plan sentence is sometimes missing, and the project order can
  slip. Fixed in 1.2.0: no plan sentence is required, and the sort rule is exact.
