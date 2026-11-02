---
name: publish-packaged-extension
description: Use when the user wants to publish a workbook to Tableau Cloud or Tableau Server, whether it is the workbook open in Studio, a .twbx file they name, or an unzipped data-app folder (a .twb next to a Packages/ folder). Phrases like "publish this workbook", "publish this workbook to Tableau", "publish this with the extension", "publish my data app", "publish Sales.twbx to Finance", "publish this workbook to project X as Y", "the extension disappears when I publish", or "Cloud says the embedded extension was removed when the workbook was downgraded". Checks the sign-in and connection to the connected site, always asks for the site, project and name before publishing, and publishes with publish-workbook. When the workbook carries a packaged extension it first runs a bundled fix-up script on a copy so the extension survives, then checks the published copy. Do NOT use to build or edit the extension itself (use author-extension or scrollytelling-demo-builder), to speed up or clean up a workbook before publishing (use workbook-optimizer), or to build charts and dashboards (use tableau-desktop-authoring); this skill only publishes and checks the published copy.
---

# Packaged extension publish

This is a Tableau Studio agent skill. It runs inside Studio's agent and
publishes through Studio's `tableau-web` MCP, which uses Studio's own sign-in
to the connected Tableau site (Tableau Cloud or Tableau Server).

It publishes any workbook that has a packaged extension (a dashboard extension
or a worksheet/viz extension, including data apps) so the extension still works
on the site. Without it, Cloud can replace each extension with the text
*"Embedded extension removed when workbook was downgraded."*

Studio writes every packaged-extension zone twice, behind a `_.fcp.Packages`
feature switch: the extension itself, and a fallback text box. Sites that don't
support the switch yet pick the fallback when the workbook arrives, whatever the
route: Studio's publish, the web **Upload Workbook**, or `publish-workbook` on an
unmodified file. The fix is to resolve the switch to the extension branch in a
**copy** before publishing. Workbooks built outside Studio usually have no
switch; the script then copies them unchanged, so always run it. Background is
in `references/why-extensions-are-removed.md`; read it only if the user asks why.

All file work goes through `scripts/fix_packages_for_publish.py` (Python 3, standard library
only, no sign-in). It prints JSON and exits non-zero on failure. Run it as:

```
python3 "<this skill folder>/scripts/fix_packages_for_publish.py" <command> ...
```

## Tools

Use only these:

- `tableau-web`: `list-projects`, `list-workbooks`, `publish-workbook`, `request-workbook-upload`, `download-workbook`
- `desktop`: `workbook-export-as` (or `save-workbook`), only to get the open workbook as a file
- Shell: `python3` for the script, `curl` only for the staged upload in step 5
- Only when the same message also asks to edit the extension (see Scope):
  the tools `author-extension` prescribes, such as `reload-extensions`. Do
  the edit before step 2, so the export includes it.

Never publish with Desktop's Publish dialog or any other UI route: it has no
headless path, and it applies the downgrade this skill exists to avoid. No
token, password or secret is involved at any point; never ask for one.

## Scope

In scope: fixing and publishing a workbook that already has a packaged
extension, and checking the server copy. This includes workbooks with several
extension zones or several packages: the script handles all of them, and the
step 6 comparison covers every zone and package ID.

Out of scope, and what to do instead:

- Tableau Server: the publish steps work on whichever site the connected
  `tableau-web` tools reach, so a workbook without a packaged extension is
  published the same way (step 3 branch, then the step 4 question). Packaged
  extensions are a Tableau Cloud beta. Decide Cloud or Server with this rule,
  using the host of any workbook, project or view link you have seen:
  1. The host is `online.tableau.com` or ends with `.online.tableau.com`
     (for example `us-east-1.online.tableau.com`): Tableau Cloud.
  2. Any other host: treat it as Tableau Server and say which host you saw. If
     the user says it is Tableau Cloud, believe them and go on as Cloud.
  3. No link seen yet: assume Cloud, and decide again as soon as a link
     appears (the step 5 publish result has one). Don't ask.
  If the workbook has a packaged extension and the site is Tableau Server, say
  the extension won't work there and ask whether to publish the original export
  as-is. Never publish the fixed-for-publish copy to Tableau Server. Publishing
  to Tableau Server hasn't been tested.
- Another site than the one Studio is signed in to: tell the user to switch
  sites in Studio, then ask again.
- Building or editing the extension: hand off to author-extension or
  scrollytelling-demo-builder. If the same message also asks to publish, make
  the edit first by following `author-extension`, tell the user what changed
  and that you haven't seen it render, then continue with the publish steps so
  the published copy includes the edit.
- A workbook with no packaged extension: call `publish-workbook` directly.
- Repairing a workbook that exists only on the site: ask for the original file.
- Changing site settings, package permissions or data source access: these need
  a site admin. Only point the user to them (step 7).

## Steps

### 0. Order of work

Start with the steps below; no opening sentence is required. Carry on without
waiting; the only stop is step 4. The order is fixed: finish step 1 (sign-in
check) before step 2 (export), and never export or run the script until the
check has passed.

### 1. Check the Tableau Cloud sign-in and MCP connection

Do this before any file work, so a sign-in problem doesn't surface only at
publish time.

1. Check that the `tableau-web` tools listed above are available. If they
   aren't, stop: the Tableau MCP connection isn't loaded.
2. Call `list-projects` with `capability: "Write"` and no `limit`, so the
   result holds every project name, not just the count. Keep the full result
   for step 4. Step 4 shows every name, so a count alone is not enough.
   If the user named a project that isn't in the result, say so in the same
   message and show the full alphabetical project list with the total
   (step 4 rules). Never end with only an offer to list them or to create
   the project.

| Result | What it means and what to tell the user |
|---|---|
| A list of projects (even an empty one) | Signed in and connected. Tell the user which site you're connected to, if the result or a project link shows it, then go on. An empty list means they can't publish to any project; only Personal Space is left, and only where `publish-workbook` lets you omit `projectId`. |
| 401, "Unauthorized", "Invalid authentication credentials", or code 401002 | Studio's Tableau Cloud sign-in has expired. |
| 404 on `/register`, `/.well-known/oauth-*`, or any OAuth discovery or registration error | **The same thing: the sign-in has expired.** Studio's MCP doesn't use OAuth, so the client's OAuth fallback 404s. Don't troubleshoot OAuth or MCP configuration. |
| Connection refused, "failed to connect", or tools missing | The Tableau MCP connection isn't running. |
| 403, or an error about site role or permissions | Signed in, but the account can't publish. Publishing needs the Creator or Explorer (can publish) site role. |

For the sign-in and connection rows, stop and tell the user: *"Studio isn't
signed in to Tableau Cloud (or its Tableau connection isn't running). Sign in to
your site again in Studio, or restart the agent, then ask me to publish again."*
Don't retry in a loop, and don't fall back to another publish route.

### 2. Get the workbook as a file

Work out which workbook the user means, then get a path for step 3:

| The user means | What to do |
|---|---|
| The workbook open in Studio (the default when they don't name one) | Call `workbook-export-as` with `format: "packaged-workbook"` and an absolute `filePath` ending in `.twbx`: `~/Documents/My Tableau Repository (Beta)/Workbooks/<Workbook Name>.twbx` (expand `~`). This writes a copy and leaves the open workbook pointing where it was. If `workbook-export-as` isn't available, call `save-workbook` with the same `filePath`. |
| A `.twbx` file they name | Use that path as-is. Don't open or re-save it. |
| A folder with a `.twb` and a `Packages/` folder (an unzipped workbook or data-app workspace) | Use the folder path; the script zips it into a `.twbx`, keeping `Data/` and `Resources/.agents/`. |
| A `.twb` file on its own | Look for a `Packages/` folder next to it and use the folder that holds both. If there isn't one, the extension files are missing: ask the user where they are. |
| A workbook that's only on the site | Tell the user that the published copy can't be repaired, because the server already swapped the extension for text when it arrived. Ask for the original file instead. |

### 3. Make the fixed-for-publish copy

```
python3 "<this skill folder>/scripts/fix_packages_for_publish.py" fix --in "<path from step 2>"
```

When you tell the user about it, call it the "fixed-for-publish copy".
It writes `<name>.fixed-for-publish.twbx` next to the input (`--out` to choose another path)
and never changes the original. It also runs the checks Tableau applies when the
workbook is published. Read the JSON:

| Field | Meaning |
|---|---|
| `ok` | The copy has extension zones, no switch markers, no fallback text, and no `problems` |
| `out` | Absolute path of the copy to publish (`null` when `ok` is false; no copy is left behind) |
| `switch_markers_resolved` | How many switch markers were removed |
| `already_clean` | `true` when the input had no switch, so the copy is unchanged |
| `packages` | Package IDs found under `Packages/` |
| `extension_zones` | Extension zones in the copy |
| `problems` | Things that would make publishing fail or leave the app without data. Any entry means `ok` is false |
| `warnings` | Runtime risks that don't block publishing: undeclared origins, secret-looking values, version mismatches |

If the workbook has no `Packages/` folder and no extension zones, it has no
packaged extension, so there is nothing to fix. Say so in one sentence, offer
to publish it as-is with `publish-workbook` (the original export, no fixed-for-publish
copy, never Desktop's Publish dialog), and ask the step 4 question first.
Publish only after they reply. Then skip step 6's extension comparison and
end with "Published" and the link. Don't offer to delete a `.fixed-for-publish.twbx`,
because none was made.

If `ok` is false for any other reason, stop and tell the user what the `error`, `problems` or counts
say, in plain words. Usual causes: the workbook has no `Packages/` folder, the
extension was never placed on a dashboard or worksheet (`extension_zones` is 0),
or the file was already downgraded (`fallback_text` is true with no switch), in
which case the original Studio file is needed.

If there are `warnings`, tell the user each one briefly and carry on. A secret
warning matters most: anyone who can download the workbook can read that value.

Start the step 4 message with exactly one of these sentences, filling only the
angle-bracket parts, with nothing before it:

> I made a fixed-for-publish copy of <workbook name>: <n> extension zones, package <package IDs, comma-separated>, <no problems or warnings | each warning in a few words>. Nothing is published yet.

> <workbook name> has no packaged extension, so there's nothing to fix. I can publish the plain export as it is. Nothing is published yet.

### 4. Ask for the site, project and workbook name

Publishing is visible to others on the site, so always ask the user for all
three in one message before publishing, and wait for the answer. If they
already gave any of them in this conversation, show those as the defaults
instead of skipping the question. A request that already names the site,
project and workbook name is not an answer to this question: end your turn
with the question, and call no publish tool until the user replies. Defaults
are fixed, so two runs give the same question:

- **Project default:** the project the user named in this conversation. If
  they named none, suggest nothing and list every publishable project from
  the step 1 result, never a subset. Sort them with this exact rule: compare
  names case-insensitively after removing one leading dot; break ties by the
  original name. Write the sorted names out one by one and check each against
  the previous one before sending. A missing project or a wrong parent is a
  failed answer.
  Show a nested project as "<name> (in <parent name>)", using each project's
  parent from the step 1 result. Say how many projects there are in total, and
  print every name in the message: a count without the names is wrong. With
  no project default, don't offer "Reply yes": ask them to reply with a
  project (and any name change).
- **Workbook name default:** the input file's name without `.twbx` and
  without `.fixed-for-publish` (for the open workbook, its name in Studio).

Use this template exactly, filling only the angle-bracket parts. Put the
project names on separate lines, in sorted order:

> Where should I publish it?
> - **Site:** <the site Studio is signed in to>
> - **Workbook name:** <workbook name>
> - **Project:** <suggested project, or "choose one of the <total> below">
>
> <one project per line, "<name>" or "<name> (in <parent>)", only when there is no project default>
>
> <With a project default: Reply "yes" to use these, or tell me what to change. Without one: Reply with a project, plus a different name if you want one.>
> Before publishing, I'll check whether a workbook with that name already exists there.

- **Site.** `tableau-web` publishes only to the site Studio is signed in to,
  so a site can't be picked here. Show that site if you can tell which it is
  (for example, from a link in an earlier result). If the user names a
  different site, stop and tell them to switch to it in Studio, then ask
  again; don't publish to the current site instead.
- **Project.** List the project names from step 1's `list-projects` result.
  They're only the projects the user can publish to. Never show the IDs. Use
  the chosen project's ID in step 5. If they name a project that isn't in the
  list, tell them they can't publish there, and ask again. Match names
  case-insensitively and ignore one leading dot (`Dan` matches `.Dan`). Match
  the whole name, never part of it (`Sales` doesn't match `Sales Demo`).
  - Exactly one match: use it as the project default, and show "(in <parent>)"
    if it is nested. Don't ask which one.
  - Two or more matches: list them, one per line, as "<name> (in <parent>)" or
    "<name> (top level)", and ask which one. Never pick for them. If they
    already named a parent ("Samples in Demos"), use it to choose.
  - Offer **Personal Space** only if `publish-workbook` lets you omit
    `projectId`. Some versions require it.
- **Workbook name.** Suggest the workbook's name without `.fixed-for-publish`. This is
  the name it gets on the site, so any name the user gives is fine. The local
  file name doesn't change.
- **Overwrite.** Before step 5, check whether a workbook with that exact name
  exists in that project: call `list-workbooks` with
  `filter: "name:eq:<name>"` and look for a result in the chosen project. If
  the tool isn't available, treat it as "may exist" and ask. If one exists,
  ask whether to replace it. Only set `overwrite: true` if they say yes. If
  none exists, leave `overwrite` false.

### 5. Publish the fixed-for-publish copy

Call `publish-workbook` with:

- `workbookFilePath`: the `out` path from step 3 (never the original)
- `name`: the workbook name from step 4
- `projectId`: from step 4, or omit it for Personal Space (where the tool allows that)
- `overwrite`: `true` only if the user agreed to replace an existing workbook

If it errors that `workbookFilePath` isn't supported or uploads must be staged,
use the staged upload instead:

1. Call `request-workbook-upload` with `fileName` (the file name of `out`). It
   returns `workbookUploadId`, `uploadUrl`, `requiredHeaders`, `maxSizeBytes`
   and `expiresAt`. Check the file is smaller than `maxSizeBytes`.
2. Upload the file **in your very next call**: the URL can expire within a
   minute (check `expiresAt`). Pass every header in `requiredHeaders`:
   `curl -fsS -X PUT -H "<name>: <value>" ... --data-binary @"<out>" "<uploadUrl>"`
   If it fails with 403 or "expired", request a new upload and try once more.
   Never show `uploadUrl` to the user; it's a signed link.
3. Call `publish-workbook` with `workbookUploadId` instead of
   `workbookFilePath`, plus the same `name`, `projectId` and `overwrite`.

Read the result:

- `status: "published"`: it worked. Keep the workbook link and ID for steps 6–7.
- `status: "invalid"`, or an error: stop and show the `errors` and `warnings`
  exactly as returned. These usually come from the `.twb` or `.trex` wiring,
  not from the fix-up.
- A 401 here means the sign-in expired mid-run: give the step 1 sign-in message.

### 6. Check the server copy

Call `download-workbook` with the published workbook's ID. It returns either a
local file or a short-lived signed link (a resource link). For a link, fetch it
**in your very next call**, as with the upload URL, and don't show it to the user:
`curl -fsS -o "<folder of out>/server-copy.twbx" "<link>"`. Then run:

```
python3 "<this skill folder>/scripts/fix_packages_for_publish.py" verify --in "<downloaded>.twbx"
```

`ok: true` means the server kept the extension zones and has no fallback text.
Also compare it to the step 3 result: `extension_zones` must be equal and
`packages` must list the same IDs. A mismatch is a failed check even when `ok`
is true. Report both counts and end with "Published, not verified". If
`fallback_text` is `true`, the site still downgraded the workbook: tell the
user, and mention the site may need **Allow Packages on this Site** turned on
(Site Settings > Packages, site admin only).

If you can't download it, skip the check and say so.

### 7. Hand back

Give the user the workbook's link from the publish result and ask them to open
it to confirm the extension renders. A view image or thumbnail won't show it,
because extensions only render in an interactive browser session.

End with a one-line result using these exact words:

- **Published and verified:** the publish returned `status: "published"` and
  `verify` returned `ok: true`.
- **Published, not verified:** the publish worked but the download or `verify`
  didn't run or failed. Say which.

Use this shape for the final message, one block per workbook:

> **<Published and verified | Published, not verified>:** <workbook name> in <project>
> Link: <workbook link>
> Extension zones: <n> (same as the fixed-for-publish copy) | Packages: <package IDs>
> Please open the link and confirm the extension renders.

Then offer the cleanup from **Clean up** below in the same message.

Overflow rules:
- With more than 3 workbooks, put one summary line first: "<n> published and
  verified, <m> published but not verified, <k> not published." Then the blocks,
  in the order the user gave the workbooks.
- A workbook that was not published still gets a block, with "Not published:"
  in place of the status words and the reason on the next line.
- Put the cleanup offer once, after all blocks.

If the extension doesn't load, or loads but shows nothing, go through these in
order. All but the last are in **Site Settings > Packages** and need a site admin:

1. **Allow Packages on this Site** is on.
2. This package is **Enabled** in the site's Packages list. A package can be
   disabled on its own even when the site switch is on.
3. **Extension Package Allowed Origins** includes every outside origin the
   extension calls (HTTPS only), matching the package's `requestedOrigins`.
4. **Tableau REST API Access** allows the calls the extension makes, but only if
   it uses `fetch()` against the Tableau REST API.
5. The viewer has **View**, full data query and **API access** on the workbook,
   and View, Connect and **API access** on each published data source. API access
   is the one most often missed.

Packaged extensions are a Tableau Cloud beta; Tableau Server doesn't support
them yet. Packaged extensions need Tableau version 2026.3 or higher. If the
extension won't load, ask which version the site and Studio are on, and treat
anything older than 2026.3 as the likely cause.

## When something fails

| Symptom | What it means and what to do |
|---|---|
| `workbook-export-as` fails or the workbook has no file yet | Ask the user to save the workbook in Studio, then retry the export once. |
| `publish-workbook` says the name already exists | Ask whether to replace it. Retry with `overwrite: true` only on a yes. |
| `publish-workbook` says you lack Overwrite or Publish rights | Tell the user they need those on the project. Offer a different name or project. |
| Upload `curl` returns 403 or "expired" | Request a new upload and retry once. A second failure: stop and report. |
| `download-workbook` link expired or fails | Call `download-workbook` once more. If it still fails, skip the check and say so. |
| `verify` returns `ok: false` | Report the counts. Don't call it published-and-working. |
| The permission prompt for the script or the export was declined | Stop and don't retry. Say in one or two sentences what the script does (reads the export, writes a separate copy, no sign-in, original untouched) and that nothing was published. Ask them to say "go" to run it again and approve the prompt. Offer to publish the plain export only if they ask, and say a packaged extension would likely be removed. |
| The project the user named isn't in the step 1 list | Say they can't publish there, show the full alphabetical project list from step 1 in the same message and ask again. Don't pick another project. |

## Common mistakes

- Publishing the original file instead of the `out` path from step 3.
- Using Desktop's Publish dialog, which applies the downgrade.
- Showing an upload or download link to the user.
- Treating `status: "published"` as proof the extension works. Only `verify`
  and the user's browser check prove that.
- Picking a project when the name matches more than one.
- Skipping the step 4 question because the request already named the site,
  project and name. Show them as defaults and wait for a reply, even for a
  batch (Step 4).
- Ending a batch with prose and links instead of one status line per
  workbook. Each workbook gets "Published and verified" or "Published, not
  verified" on its own line, followed by its link (Step 7).
- Publishing before a requested extension edit is made. Edit first, then
  export and fix, so the published copy includes the edit (Scope).
- Offering to delete the original export (`<name>.twbx`) when the user stops
  or finishes. Only the `.fixed-for-publish.twbx` and `server-copy.twbx` may be offered
  for deletion (Clean up).

## Check before sending

Run this on the step 4 question and on the final message, silently, before you
send either:
1. The step 4 message starts with one of the two step 3 sentences, then the
   question follows the step 4 template: site, name, project, then
   (with no project default) every project from step 1 on its own line, sorted
   by the rule above, with the total and "(in <parent>)" on nested ones. With
   no project default it says "Reply with a project", not "Reply yes".
2. The final message uses exactly "Published and verified" or "Published, not
   verified" (or "Not published:" for a skipped one), one block per workbook,
   with its link on the next line, plus the summary line for more than 3.
3. No upload or download link, project ID or script name appears in the text.
Fix any miss before sending; don't mention the check.

## Clean up

If the user stops before publishing (for example, replies "stop" at the step 4
question), end with exactly this, and ask about deleting only once:

> Stopped. Nothing was published. Say "delete" to remove <name>.fixed-for-publish.twbx.

If no fixed-for-publish copy was made, end with "Stopped. Nothing was
published." and nothing more. Don't list the original export as deletable.

After step 6, offer to delete the local `.fixed-for-publish.twbx` and `server-copy.twbx`.
Both can contain secret-looking values the script warned about. Delete them
only if the user says yes, and never delete the original export.

## Large workbooks and batches

- **Size.** Before step 5, note the size of the `out` file. If the tool or the
  staged upload reports a size limit (`maxSizeBytes`) and the file is over it,
  stop. Tell the user the file size and the limit, and offer to publish
  without the packaged extract if they can refresh it on the site, or to
  publish the data source separately. Don't strip data from the copy yourself.
- **Slow uploads.** The staged upload link expires within about a minute. For
  a large file, request the upload and run `curl` back to back with no other
  step in between. If it expires, request a new one once, then stop and report.
- **Many packages or zones.** The script reports them all. Step 6 compares every
  zone count and package ID, so a missing one is a failed check. List the
  missing IDs in plain words.
- **Batches.** For several workbooks, do the sign-in check and the project
  question once. Then fix, publish and verify one workbook at a time, and
  report a status line for each ("Published and verified" or "Published, not
  verified"). A failure in one workbook doesn't stop the rest. Never re-send a
  publish that returned an unclear result: check the site with `list-workbooks`
  first.

## Update check (last step)

Run this once, after the step 7 hand-back message or after a clean stop (for
example the user replies "stop" at the step 4 question). Never run it before or
during the publish steps, and never delay the step 4 question for it.

```
python3 "<this skill folder>/scripts/check_update.py" check
```

It prints JSON and never fails. Read `status`:

- `up_to_date`, `unknown` (offline) or `snoozed`: say nothing about updates.
- `update_available`: add a short note after your result: a newer version of this
  skill is available (`local` → `remote`), with a one-line summary of `changes`.
  Ask which they want, as plain text at the end of your message (do not use
  `ask-user`): **install now**, **skip this time**, or **don't remind me about
  this version**. Wait for the answer.
  - Install: run `python3 "<this skill folder>/scripts/check_update.py" apply`.
    On `ok: true`, tell them it updated (the old copy is saved at `backup`) and
    ask them to run `/reload-skills`. On `ok: false`, show the error and keep the
    current version.
  - Skip: do nothing more.
  - Don't remind me: run `... check_update.py snooze`.

## Notes

- Only the published copy is fixed. A Studio workbook still carries the switch,
  so republish through this skill after every edit.
