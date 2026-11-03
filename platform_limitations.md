# Platform limitations (Tableau Studio agent)

Used by skill-grader-desktop to cross-check skills against known gaps. Each entry says where it was confirmed. Add entries only from live tests.

## Gaps listed by skill-grader-desktop (not re-verified here)

- No zone-move, view-fit or canvas-size commands for dashboards.
- No delete-field or delete-calc command.
- Sets are invisible to field-resolution tools.
- `author-parameter` is deterministically broken on Windows.
- `get-worksheet-xml` returns a 500 on dashboard-bound sheets.
- `build-and-apply-worksheet` can corrupt calcs on datasources that reference parameters.
- No mark-selection or parameter-value-set command, so behavior can't be tested.

## Gaps confirmed while testing publish-packaged-extension (2026-10-30)

- **Desktop's Publish dialog has no headless path** and applies the downgrade that removes packaged extensions. Workaround: export a copy, run the fix-up script, publish with `tableau-web` `publish-workbook`.
- **The `tableau-web` MCP uses Studio's own Tableau Cloud sign-in.** When it expires, the client shows "Dynamic Client Registration rejected (HTTP 404) Cannot POST /register". That is a sign-in expiry, not an OAuth problem. Workaround: sign in again in Studio and restart the agent.
- **Staged-upload and download links expire in about 60 seconds.** Use each in the very next call and never show it to the user.
- **Some `publish-workbook` versions require `projectId`**, so Personal Space is not always available.
- **Studio caches its copy of a skill.** After editing `SKILL.md`, reload skills before re-testing, or the old text runs.
- **The agent can't delete workbooks on Tableau Cloud.** Cleanup of published test workbooks is manual.
- **`list-projects` with a small `limit` returns the count but not all names.** Call it without `limit` when the names are needed.

## Gaps seen while testing scrollytelling-demo-builder hosted mode (2026-11-02)

- **Edits to a new feeder worksheet can start failing partway.** After the first field applied, further edits were rejected with a file-access error, and a fresh copy of the sheet did not help. The cause is unconfirmed (seen once). Workaround: stop after two rejections and give the user the manual recipe for the sheet.
- **The open workbook may be connected to a different datasource than the one the story uses.** The feeder sheet must come from the chosen datasource, so connect it first with the workbook CLI; do not substitute another source.
