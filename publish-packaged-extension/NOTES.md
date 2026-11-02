# publish-packaged-extension: improvement notes (2026-10-30)

## Current state (read this first)

Everything below this section is the history of the first build. The current rules live in SKILL.md.
The skill was tested with a 22-prompt matrix (21 pass, 0 open fail), then re-tested after later changes
(regression runs: extension workbook, plain workbook, full publish, ask-first check; all pass).
Current behavior:
- The skill fires on any "publish this workbook" request, to Tableau Cloud or Tableau Server, not only workbooks
  with an extension. A workbook with no packaged extension is offered as-is, after the same ask-first question.
- Step 0 is one or two plain sentences before the first tool call. The sign-in check comes before the export.
- Step 4 always asks for site, project and name, and lists every publishable project (alphabetical as well as the
  agent can; completeness and correct "(in Parent)" marks are required). With no project default it says "Reply
  with a project", not "Reply yes".
- The fixed copy is `<name>.fixed-for-publish.twbx`. The cleanup rule only ever offers that file and
  `server-copy.twbx`, never the original export.
- A combined "publish and edit the extension" request edits first, then publishes.
- A declined permission prompt stops the run with a short explanation; nothing is published.
- The script is `fix_packages_for_publish.py`.
Known gaps: Tableau Server publishing is untested (the Server check is a link-domain heuristic); the plan
sentence is sometimes missing; the project order can slip. Reload skills after editing SKILL.md.

## Status (2026-10-30, later the same day)

Implemented:
- SKILL.md: step 0 tells the user the plan; step 1 checks the Tableau Cloud sign-in and MCP connection
  (`list-projects` with `capability: "Write"`; a 401 or `/register` 404 means the sign-in expired);
  a Studio-only line and tool list; `workbook-export-as` to get the open workbook; `problems`/`warnings`;
  the staged-upload fallback and publish status; the step 7 troubleshooting order; the Cloud-only beta note.
- fix_packages_for_publish.py: the §3 checks (root layout, .trex, requestedOrigins string, Data/ files, origins,
  secrets, version match), `Resources/.agents/` kept for folder input, `_.fcp.VizExtensions` zones counted.

Tested end to end on danfy27 / `.Dan` with Sales-Extension-Test (published as "Sales-Extension-Test (skill test)").
Export, then fix (15 markers resolved), staged upload, `status: "published"`, then download and verify: 2 zones, no fallback text.
Found during the test, and now in SKILL.md:
- Some `publish-workbook` versions require `projectId`, so Personal Space isn't always available.
- Staged-upload and download links expire in about 60 seconds. Use each one in the very next call, and never show it.

Not done: the optional REST/Keychain fallback (§1), `summarize_publish_access.py` (§2),
the `fetch()`-of-relative-path warning (§3), and a rerun inside Studio's own agent.


Sources:
- The first real run in Tableau Studio (agent logs from 2026-10-29).
- The official Data Apps docs (tableau.github.io/extensions-api/docs/dataapps/: overview, details, getting started, manage, security, samples).
- The Tableau plugin's `tableau-data-app-authoring` skill (github.com/tableau/tableau-plugin).

***

## 1. What went wrong in the Studio run

What the user saw: `tableau-web` "failed to connect", a 404 on `/register`, and "the Desktop MCP has no publish command".

The actual cause:
- Studio's web MCP (tableau-mcp 5.0.2, `localhost:<port>/tableau-mcp`) uses **passthrough auth**. It reuses Studio's own Tableau Cloud sign-in token.
- That token had expired. `web-mcp.log` shows `Passthrough auth validation failed ... 401002 Invalid authentication credentials`.
- After the 401, the agent's MCP client fell back to OAuth discovery: `/.well-known/oauth-*` returned 404, and then `POST /register` (dynamic client registration) also returned 404.
- **The `/register` 404 is a side effect, not the problem.** The local server doesn't do OAuth at all.
- Earlier `publish-workbook` calls in the same Studio install had succeeded, so the skill's path does work once auth is valid.

The Studio agent was right not to drive Desktop's Publish dialog. That dialog has no headless path, and it also runs the downgrade.

### Changes to make
- **Add a preflight step before step 1.** Call `list-projects` (or any cheap `tableau-web` tool) before doing anything else.
  - If it returns 401, or `tableau-web` tools are missing, stop and tell the user: *"Studio's Tableau sign-in has expired. Sign in to the site again in Studio (or restart the agent), then rerun."*
  - Tell the agent explicitly that a `/register` or OAuth 404 means the same thing, so it doesn't go chasing OAuth config.
- **Name the exact tools the skill needs**, so a low-effort agent (Studio runs Sonnet at effort=low) doesn't improvise:
  - `tableau-web`: `list-projects`, `publish-workbook`, `request-workbook-upload`, `download-workbook`
  - `desktop`: `save-workbook`
  - Say plainly: *never* use Desktop's Publish dialog or `workbook-export-as` to publish.
- **Add one line at the top of SKILL.md:** "This is a Tableau Studio agent skill; it runs inside Studio's agent and publishes through Studio's `tableau-web` MCP."
- **Optional fallback if `tableau-web` stays down:** publish over REST with a PAT kept in the macOS Keychain, the same way scrollytelling's `package_extension.py` does (`~/Code-Projects/studio-pkg-publish/` already does this).
  - Only offer this; don't do it automatically. Keep the secret out of chat, argv and files.

## 2. The official publish path (from the docs and plugin)

The official flow is: scaffold → wire datasource → author → `package_twbx.py` → `publish-workbook` through Tableau MCP.
- It's the same MCP tool we use, so our approach matches the sanctioned path.
- The plugin's packager has **no** `_.fcp.Packages` handling. It only ever sees scaffolded or hand-built `.twb`s. The official Superstore sample `.twb` has 0 `_.fcp.Packages` markers, and its `<add-in>` is plain.
- So **our fix-up step is still needed for Studio-saved workbooks.** The docs say nothing about the downgrade, either as a known issue or as a fix.

### Changes to make
- **Staged-upload fallback.** If `publish-workbook` errors that `workbookFilePath` isn't supported (some MCP configs require staged uploads):
  1. Call `request-workbook-upload({fileName})`. It returns `workbookUploadId`, `uploadUrl`, `requiredHeaders`, `maxSizeBytes` and `expiresAt`.
  2. Run `curl -fsS -X PUT` with every header in `requiredHeaders` and `--data-binary @file` to `uploadUrl`.
  3. Call `publish-workbook({workbookUploadId, name, overwrite})`.
  - Add `projectId` to the calls when publishing to a project.
- **Destination default.** The plugin's convention is to omit `projectId`, which means Personal Space. When a project is needed, it calls `list-projects({capability: "Write"})`. Use the `capability: "Write"` filter so the list only shows projects the user can publish to.
- **Read the publish result.**
  - `status: "published"` means it worked.
  - `status: "invalid"`, or an error, means show the `errors` and `warnings` exactly as returned. Per the plugin, these usually come from `.twb`/`.trex` wiring, not packaging.
- **Optionally borrow `summarize_publish_access.py`** from the plugin. It turns the publish result JSON into a plain-English "who can view this" summary. Relay its output word for word.
- **Overwrite rule.** Set `overwrite: true` only when the user wants to replace a workbook with the same name. The skill already says this; keep it.

## 3. Preflight checks to borrow from `package_twbx.py`

Add these to `fix_packages_for_publish.py fix` (and `verify` where it makes sense). Each one catches a failure that otherwise only shows up at publish time or when the dashboard opens:

| Check | Why | Severity |
|---|---|---|
| At least one `.trex` under `Packages/*/extensions/` | Without one, publish fails with `PackageValidationException: Package directory contains no extension .trex files under extensions/` | fail |
| `.twb` and `Packages/` at the archive **root**, not nested under `<App Name>/` | Nesting causes the same PackageValidationException | fail (we already write the twb at the root, but add an explicit check) |
| `manifest.json` `requestedOrigins` is **one space-separated string** | An array, or an `allowedOrigins` key, is silently ignored, and then every external origin is blocked | fail |
| Every `Data/` file the `.twb` references (`connection` `filename`/`dbname`, plus `directory`) is in the archive | Otherwise there's no data at runtime | fail |
| `Resources/.agents/` kept when repackaging | The plugin's convention: agent docs travel with the `.twbx`. Ours keeps all entries, but confirm for folder input | keep |
| External origins in `content/` code that aren't in `requestedOrigins` | The CSP blocks them | warn |
| `fetch()` of a package-relative path | Fails in the null-origin sandbox. Load data or config as a `.js` file with `<script src>` instead | warn |
| Secret-looking keys in packaged files | Anyone who can download the workbook can read them | warn |

Also report `add-in-id` and `extension-version` against the `.trex` `id` and `extension-version`. They must match. Instance IDs must be unique.

## 4. Site and permission requirements (for step 6)

Today, step 6 only mentions "Allow Packages on this Site" and allowed origins. The docs list more:

**Site Settings → Packages tab, set per site:**
- **Allow Packages on this Site.** The site-wide on/off switch.
- **Allow Packaged Extensions to trigger popups.**
- **Extension Package Allowed Origins.** HTTPS only. Packages that declare an origin outside this list won't run.
- **Tableau REST API Access.** Either "Allow all", or an allowlist of method + path entries using `{api-version}` and `{site-id}` placeholders. This governs the Extensions API's `fetch()`.
- **Packages view.** A table of every package on the site. A package can be **disabled on its own**, so check its Enabled column when an app won't load even though the site switch is on.

**To view a data app, the viewer needs:**
- On the workbook: View, full data query, and **API access**.
- On each published data source: View, Connect, and **API access**.

**To publish, the user needs:**
- A Creator or Explorer (can publish) site role.
- Publish and Overwrite on the project.
- View, Connect and API access on each data source.

### Changes to make
- Rework step 6's troubleshooting list in this order:
  1. Site Packages switch.
  2. This package's Enabled flag.
  3. Allowed origins.
  4. REST API allowlist (only if the app calls `fetch()`).
  5. Viewer permissions, including the easy-to-miss **API access** capability on both the workbook and the data source.
- Mention that the beta is **Tableau Cloud only**.
- Mention that the official sample requires **2026.3.1+**. That matches danfy27.

## 5. Smaller items

- **Folder input.** The docs' "unpacked app" layout (`<App>.twb` + `Packages/<id>/{manifest.json, extensions/*.trex, content/}`) is exactly the folder case our script already handles. Optionally also zip `Data/` and `Resources/.agents/` when they're present. The script already zips every non-hidden file, so this is mainly about checking that it behaves that way.
- **Workbooks from the plugin.** They won't have the FCP switch. Our `fix` already treats that as `already_clean`, so the skill doubles as a safe publisher for them. Say so in the description.
- **Version bumps.** The docs say a new distributed version needs consistent updated metadata: `manifest.json` `version`, `.trex` `extension-version`, and the `.twb` `add-in` `extension-version`. Consider a check that warns when these three disagree.
- **Hosted MCP alternative.** Outside Studio, `https://mcp.tableau.com` exposes the same `publish-workbook` and `request-workbook-upload` tools with real OAuth. That's useful for a Claude Code or desktop variant of this flow, but not for the Studio skill.
- **Memory.** Save the "passthrough 401 → OAuth `/register` 404 red herring" finding to memory.

## Suggested order when picking this back up

1. Add the preflight auth check, the tool list and the Studio-only line (§1). Biggest win, smallest change.
2. Add the staged-upload fallback and `capability: "Write"` (§2).
3. Add the `fix_packages_for_publish.py` checks: `.trex`, root layout, `requestedOrigins`, `Data/`, version match (§3).
4. Rewrite the step-6 troubleshooting list (§4).
5. Test again in Studio with a fresh sign-in.
