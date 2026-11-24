# Large workbooks and batches

Rules for SKILL.md when a file is large or the user publishes several workbooks.
Step numbers refer to SKILL.md.

- **Size.** Before step 5, note the size of the `out` file. If the tool or the
  staged upload reports a size limit (`maxSizeBytes`) and the file is over it,
  stop. Tell the user the file size and the limit, and offer to publish
  without the packaged extract if they can refresh it on the site, or to
  publish the data source separately. Don't strip data from the copy yourself.
- **Very large files.** The script streams the archive: it reads only the
  `.twb` and the package files into memory and copies `Data/` files across
  unchanged, so a large extract doesn't slow it much. Expect the upload and
  the step 6 download to be the slow parts.
- **Slow uploads.** The staged upload link expires within about a minute. For
  a large file, request the upload and run `curl` back to back with no other
  step in between. If it expires, request a new one once, then stop and report.
- **Many packages or zones.** The script reports them all. Step 6 compares every
  zone count and package ID, so a missing one is a failed check. List the
  missing IDs in plain words.
- **Batches.** For several workbooks, do the sign-in check once and ask one
  step 4 question that lists each workbook on its own line with its name and
  overwrite status: "<name>: new", "<name>: already exists, replace?" or
  "<name>: checked once you pick a project". Run the step 4 overwrite check
  for each workbook, not just the first. Then fix, publish and verify one workbook at a time, and
  report a status line for each ("Published and verified" or "Published, not
  verified"). A failure in one workbook doesn't stop the rest. Never re-send a
  publish that returned an unclear result: check the site with `list-workbooks`
  first.
