# Changelog

The current version is in the `VERSION` file. To update, replace your copy of
this folder with the newer one and run `/reload-skills`.

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
- The plan sentence is sometimes missing, and the project order can slip.
