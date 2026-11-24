# Publish Packaged Extension — a Tableau Studio skill

Publishes a workbook to Tableau Cloud so its packaged extensions (dashboard
extensions, viz extensions and data apps) still work after publishing.

Without this fix, Tableau Cloud can replace each packaged extension with the text
"Embedded extension removed when workbook was downgraded." Studio writes every
packaged-extension zone twice: the extension and a fallback text box. Sites that
don't support Studio's newer format pick the fallback. This skill makes a fixed
**copy** of the workbook that keeps only the extension, publishes that copy, then
downloads the server copy to confirm the extension survived. Your original file is
never changed.

**Example:** "Publish this workbook to the Finance project." The skill exports the
open workbook, makes a fixed copy, asks you to confirm the site, project and name,
checks whether a workbook with that name already exists, publishes, and confirms
the extension zones are intact on the server copy.

## Requirements

- **Tableau Studio**, signed in to your Tableau Cloud site.
- **Python 3**, standard library only (nothing to `pip install`). Check with
  `python3 --version` (on Windows, `py -3 --version` or `python --version`).
- **Packaged extensions:** Tableau 2026.3 or later, with **Site Settings > Packages >
  Allow Packages on this Site** turned on by a site admin.
- No token or password is needed. The skill uses Studio's own sign-in.

## What it does

1. Checks the sign-in and connection to your site.
2. Gets the workbook as a file: the open workbook, a `.twbx` you name, or an
   unzipped data-app folder.
3. Makes a fixed-for-publish copy and checks it (package files present, valid
   workbook, versions match).
4. Asks you to confirm the site, project and workbook name, every time.
5. Checks for an existing workbook with the same name and asks before replacing it.
6. Publishes the fixed copy, then downloads the server copy and verifies the
   extension zones and packages.
7. Gives you the link and offers to delete the local temporary copies.

## When to use it

- "Publish this workbook with its extension."
- "Publish my data app to Tableau Cloud."
- "Publish Sales.twbx to the Finance project as Sales Dashboard."
- "The extension disappears when I publish."

## When not to use it

- Plain publishes with no packaged extension (tableau-workbook-authoring
  handles those, though this skill can publish them too).
- Building or editing an extension or dashboard (use an authoring skill first,
  then publish with this one).
- Publishing to a different site than the one Studio is signed in to (switch
  sites in Studio first).
- Workbooks with packaged extensions on Tableau Server. Packaged extensions are
  a Tableau Cloud feature, so the skill won't publish the fixed copy to Server.

## Good to know

- Only the published copy is fixed. A workbook still open in Studio keeps the
  fallback, so republish through this skill after every edit.
- If the extension doesn't load after publishing, a site admin may need to check
  the Packages settings. The skill lists the settings to check, in order.
- The temporary copies can contain values the script flags as secret-looking.
  Delete them when you're done.

## Files

- `SKILL.md` — the agent's procedure
- `skill-expertise/fix_packages_for_publish.py` — makes and verifies the fixed copy
- `skill-expertise/why-extensions-are-removed.md` — background on why Cloud
  removes packaged extensions
- `skill-expertise/batches-and-large-workbooks.md` — rules for large files and
  several workbooks at once
