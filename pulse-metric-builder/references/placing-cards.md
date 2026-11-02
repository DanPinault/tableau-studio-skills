# Placing Pulse cards (Step 5)

Before placing, run `value --metric <metric_id>` for each metric and confirm it
returns a summary with a figure (an accepted definition can still be blank,
especially with a calculated time dimension). If it can't confirm, have the user
open one `pulse_url` instead.

Placing the cards yourself by editing the workbook document (Option B in
`studio-card.md`) is verified to work: it renders, saves cleanly, and works after
publishing. Don't tell the user it must be done by hand.

## Procedure

1. Test on one dashboard first (one card): `get-workbook-xml`, edit the cached
   file, `apply-workbook`. Then `capture-window-screenshot` and
   `get-active-dialogs`. Then do the rest.
2. Re-read the workbook with `get-workbook-xml` before each further edit; a stale
   cache file is rejected.
3. After placing, screenshot, then save the workbook (`save-workbook`); a clean
   save is the final proof the zones are valid. Use `undo-workbook` if a "no
   visual representation" error appears.
   - If the workbook has never been saved (untitled, like "Book2"), **ask the user
     where to save it and what to name it** before saving. Suggest their
     `~/Documents` folder (e.g. `~/Documents/Book2.twb`) as the default, since most
     users don't keep workbooks in the Tableau Repository's Workbooks folder. Never
     pick a location for them.
   - Prompt in this shape: "Where should I save the workbook, and what should I
     name it? My suggestion is `/Users/<user>/Documents/<WorkbookName>.twb`. Say
     'ok' to use that, or give me a different folder or name. If a file already
     exists at the path you choose, I'll ask before overwriting it." Wait for the
     reply before saving.
   - Pass the confirmed absolute path as `filePath`. Check that the target file
     doesn't already exist; if it does, ask before overwriting.
   - The save writes a copy at that path; tell the user the open workbook may still
     show as untitled and they can use File > Save As to point it at the saved file.
4. Add worksheets to the same dashboard afterwards with `add-sheet-to-dashboard`
   (Tableau's own command), not hand-written zones. Hand-written zones are only for
   the Pulse card objects.

## Data source name

The workbook needs the metric's published data source connected. Use the content
URL (the script's default) for `DATASOURCE_NAME`, even though the workbook's own
data source name may be a `sqlproxy.xxx` id.

## Deleting or replacing metrics

`delete` needs the user's explicit confirmation by name, and any card already
pointing at a deleted metric must be re-pointed.

## If something fails

| Symptom | Fix |
|---|---|
| Apply is rejected as stale or out of date | Re-read with `get-workbook-xml`, redo the edit on the fresh file, apply once. Don't re-send the same file. |
| Apply or validate rejects the add-in | Check the manifest edits in `studio-card.md` (`Extensions` entry, `referenced-extensions` block) before anything else. |
| A dialog is open and blocks the edit | Run `get-active-dialogs`, tell the user what it is, and wait for them to close it or answer it. |
| The published data source isn't in the workbook | Stop. The user connects it (Data > New Data Source > Tableau Server / Tableau Cloud), then re-read the workbook and continue. |
| Save fails with "no visual representation" | Undo with `undo-workbook`. A hand-written worksheet zone is the usual cause; use `add-sheet-to-dashboard` instead. |
| Dashboard image export returns an error | Expected with Pulse zones present. Check the result with `capture-window-screenshot` instead. |
| Card is blank right after a change, or the agent pane covers the dashboard | Usually reloading or hidden. Screenshot once more after a few seconds. If it is still blank or covered, don't say it worked: say you couldn't confirm it, ask the user to close the agent pane or switch to presentation mode and check for the value, and give the metric's `pulse_url` as the fallback. |
| Last card is pushed off-screen on a wide dashboard | Shrink the card widths so they split the strip evenly, then re-apply. |
