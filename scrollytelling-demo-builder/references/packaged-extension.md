# Packaged extension (Tableau Data App) — the default delivery

The story HTML ships **inside the workbook**. `package_extension.py` wraps it into a
`.twbx` as a worksheet (viz) extension and publishes it over REST. When a viewer
opens the view, **Tableau Cloud hosts and runs the HTML**, and the page reads the
published datasource live with the Extensions API's `queryAsync`. Compared with
hosted mode, packaged mode drops:
- the external host,
- the `.trex` placed by hand,
- the `feed_data` sheet,
- the dashboard steps,
- and the Publish dialog.

Use hosted mode (build-procedure steps 5–7) only when:
- the user asks for it,
- the site can't enable Packages, or
- the story must run on a Desktop dashboard.

## Prerequisites (check before building)

1. **Packages are enabled on the site.** A site admin must check
   Settings > Packages > **Allow Packages on this Site**. Until then the view loads
   but the extension never runs. `package_extension.py check` reports
   `"packages": "enabled"` or `"unavailable"`. If it's unavailable, [needs you]:
   ask a site admin to enable it, or switch to hosted mode.
2. **The datasource is published and VDS-queryable.** It must be a published
   datasource on the same site, with VizQL Data Service enabled. This is the same
   query path as the probing step. Embedded and file-only datasources won't work.
3. **A PAT for REST publish.** Publish is headless in this mode, so you need a PAT:
   - Run `configure` with the server, site content URL and PAT name.
   - Then `store-secret`. On macOS it prompts and stores the secret in Keychain.
     Elsewhere, have the user `export TABLEAU_PAT_SECRET` in their own shell.
   - The secret never goes in chat, argv or files.
   - An existing `pulse-metric-builder` profile and its Keychain item are reused
     automatically.
4. `python3` is available. Check `python3 --version` and never assume it.

**Studio and Desktop limitation:** neither Studio (build 26.1026) nor Tableau
Desktop can open a packaged workbook. Both fail with error D2E8DA72, because their
schema rejects `VizExtension`, `<add-in>` and `<referenced-extensions>`. So:
- There is no in-Studio or in-Desktop preview. Tableau Cloud is the first place
  the packaged story appears.
- Author and probe in Studio as usual, and check the HTML as a local page
  (`build_standalone.py` without flags, from SEED). Then package and verify on Cloud.
- To change a published story, edit the HTML or query and re-run `build` and
  `publish`. Downloading the `.twbx` to edit in Desktop won't work, so tell the
  user this up front.
- Retest Studio and Desktop on new builds.

## How the live read works

`build_standalone.py --packaged --query q.json` injects the query as
`window.__PKG_QUERY__` and inlines the Data Apps build of the Extensions API
(`assets/vendor/tableau.extensions.data-apps.min.js`). The older
`tableau.extensions.1.latest.js` lacks `queryAsync`.

In the template:
- `readFromWorksheet()` sees `PKG_QUERY` and calls `readPackagedTable()`.
- That function finds the datasource with `workbook.getAllDataSourcesAsync()`,
  matching it by `PKG_QUERY.datasource`, and runs
  `ds.queryAsync({fields, filters})`.
- It returns the rows as a summary-DataTable-shaped `{columns, data}`.
- `contractFromRows` then parses them unchanged, so the Demo/Live toggle,
  `paintProse()`, `captureLive` and the Explore view all work as in hosted mode.

When `PKG_QUERY` is null (hosted mode), the `feed_data` read runs instead.

### The query JSON = the feeder sheet, as VDS

Write the query that returns the rows `feed_data` would have held, and validate it
**before** building: `package_extension.py query --query q.json`.

```json
{
  "datasource": "<exact published datasource name>",
  "fields": [
    {"fieldCaption": "Date", "function": "TRUNC_DAY", "fieldAlias": "Date"},
    {"fieldCaption": "<Dimension A>"},
    {"fieldCaption": "<Measure 1>", "function": "AVG", "fieldAlias": "<Measure 1>"},
    {"fieldCaption": "<Measure 2>", "function": "SUM", "fieldAlias": "<Measure 2>"}
  ],
  "filters": [
    {"field": {"fieldCaption": "Day_Offset"}, "filterType": "QUANTITATIVE_NUMERICAL",
     "quantitativeFilterType": "RANGE", "min": -89, "max": 0}
  ]
}
```

- **`fieldAlias` every aggregated field** with the caption that `MEAS[...].cap`
  substring-matches. Without an alias the key becomes e.g. `AVG(Measure 1)`. That
  still matches by substring, but aliasing removes any ambiguity.
- **The window filter is required**, just like the feeder sheet's: the exact
  window confirmed in step 2. Without it the story reads the whole history.
- Dates arrive as ISO strings (`"2026-09-16T00:00:00"`). Percent fields arrive in
  their stored scale, and the template's `contractFromRows` handles the ×100.
- Check in the `query` output that the row count, keys and magnitudes match what
  you probed. Fix the query there, not in the page.

## Commands (all JSON on stdout; exit 2 = setup incomplete)

```bash
python3 assets/package_extension.py check
python3 assets/package_extension.py datasources --search "<word>"
python3 assets/package_extension.py query --query <scratch>/q.json
python3 assets/build_standalone.py --template <scratch>/story.html --packaged --query <scratch>/q.json --out <scratch>/story-pkg.html
python3 assets/package_extension.py build --html <scratch>/story-pkg.html --name "<Story Name>" --datasource "<exact DS name>" --out-dir <scratch>
python3 assets/package_extension.py publish --twbx "<scratch>/<Story Name>.twbx" --project "<project>" --image <scratch>/check.png
```

- Use `--persona cfo|coo` instead of `--template` only to rebuild a vendored
  template as a smoke test.
- `build` resolves the datasource's `contentUrl` over REST and writes a workspace:
  - `<name>.twb`, holding the sqlproxy datasource, a `VizExtension` mark,
    `<add-in>`, and `<referenced-extensions>`;
  - `Packages/com.tableau.mcp.<slug>/{manifest.json, extensions/data-app.trex, content/index.html}`.

  It then zips them into `<name>.twbx` from inside the workspace.
- `publish` takes the project name, or a path such as `"/Parent/Child"` for a nested project. A bare name that matches more than one project is rejected with the candidate paths. It overwrites a workbook with the same
  name, lists the connections (expect one `sqlproxy` to your datasource), and saves
  a server-side render of the view with `--image`.
- Publishing to a project is outward-facing. Confirm the project with the user
  before the first publish, then re-publish freely while iterating.

## Verify (both are required)

1. **Look at `--image`.** The render must show the story itself, not a blank or
   error tile. The **prose spans** must show the live numbers, not the SEED ones:
   compute one headline number from the `query` rows and compare.
   - If SEED shows, the live read failed. The usual causes are a missing
     `fieldAlias`, the wrong datasource name, or Packages being disabled.
   - The image shows only the first viewport. Have the user scroll the view
     to check the later chapters and Explore.
2. **[needs you]: open the view URL** that `publish` printed, and confirm:
   - it scrolls,
   - the Demo/Live toggle switches,
   - Explore filters work.
   Ask once whether the extension is sized to fill the view, since the worksheet
   extension fills the sheet.

## Known failure modes

- **Extension tile blank on Cloud, workbook published fine.** Packages are disabled
  on the site, or the workbook is missing `source-build`. Run `check`, and keep
  `SOURCE_BUILD` in the script.
- **Connection missing or broken after publish.** The `dbname` must be the
  datasource's **contentUrl**, not the name or LUID. `build` resolves it for you,
  so never hand-edit it.
- **`queryAsync is not a function`.** The page inlined the old Extensions API.
  Rebuild with `--packaged`.
- **View image 406.** The image endpoint rejects `Accept: image/png`. The script
  sends `*/*`.
- **Zip contains a parent folder.** Tableau can't find the `.twb`. `build` zips
  relative to the workspace, so keep it that way.
