# Why Cloud removes Studio's packaged extensions

Root-caused Oct 29 2026 on a Tableau Cloud site running 2026.3.1, with Studio
build `main.26.1026.0859`.

## What Studio writes

Studio stamps the workbook as version 18.1, the same as Cloud, so the version
number is not the problem. The problem is a feature-control (FCP) switch named
`Packages`. Each extension zone is written twice:

- `_.fcp.Packages.true...` attributes and elements: the real zone,
  `type-v2='dashboard-object'`, a `param` that points at
  `tableauunpackedext:///<packageId>/...`, and an `<add-in>` element.
- `_.fcp.Packages.false...` attributes and elements: a `type-v2='text'` zone
  whose `<formatted-text>` reads "Embedded extension removed when workbook was
  downgraded."

The document header also lists `<_.fcp.Packages.true...Packages />` in the
`document-format-change-manifest`.

## What Cloud does

When the switch isn't enabled for the site, Cloud keeps the `false` branch on
ingest. That happens whatever the upload route: Studio's publish, the web
**Upload Workbook**, or the MCP `publish-workbook` tool. The `Packages/` folder
inside the `.twbx` survives, so the site still registers the package (you'll see
it under Site Settings > Packages), but no dashboard zone points to it.

## The fix

`fix_packages_for_publish.py fix` edits only the `.twb` inside a copy of the `.twbx`:

1. Deletes every `_.fcp.Packages.false...` element and attribute.
2. Deletes the `Packages` entry from the format-change manifest.
3. Strips the `_.fcp.Packages.true...` prefix from the remaining attributes and
   elements, so the extension zone is written plainly.

Every other file in the package is copied unchanged. A workbook fixed this way
and published to the 2026.3.1 site kept both extension zones, had no fallback
text, registered its package as enabled, and rendered in the browser. The
`tableauunpackedext://` address that Studio writes works on Cloud as-is.
