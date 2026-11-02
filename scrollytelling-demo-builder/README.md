# Scrollytelling Demo Builder — a Tableau Studio skill

Turn a Tableau **published datasource** into an animated, interactive
**scrollytelling data-story dashboard extension** — a "keynote"-style page that
scrolls through a narrative (situation → tension → evidence → implication →
action) with D3 charts that reveal and count up as you scroll, plus a second
**Explore view** with a live filter bar for hands-on slicing.

The skill runs **inside Tableau Studio**. You point it at a datasource you
choose; it examines the data, finds the signal that makes a good story, drafts
the narrative, and builds a self-contained HTML extension that reads **live**
from your data (RLS-aware) with a Demo/Live toggle. It's a guided, prompt-driven
build — it flags every point where it needs you.

## Two delivery modes (you choose at the start)

- **Packaged extension (default, recommended).** The HTML ships *inside* the
  `.twbx` as a worksheet extension (a Tableau Data App). Tableau Cloud hosts and
  runs it, and it reads the published datasource live with `queryAsync`. There's
  no external host, no `feed_data` sheet, no dashboard to place by hand, and no
  Publish dialog: the skill packages and publishes over REST to a project you
  confirm. Needs **Settings > Packages** enabled on the site and a PAT.
- **Hosted extension.** The original flow. The HTML lives on a public static
  host, a dashboard extension (`.trex`) frames it, and it reads a hidden
  `feed_data` worksheet. You place objects in Desktop and complete the Publish
  dialog. Use this when Packages can't be enabled or the story must run on a
  Desktop dashboard.

## What you get

- A single self-contained HTML file — D3 and the Tableau Extensions API are
  **inlined**, so there are **0 external `<script src>`** and any public static
  host can serve it.
- **Two surfaces in one bundle:** the scroll story (the authored narrative) and
  an **Explore view** (chart grid + live filter bar) toggled from the topbar.
- **Live-on-open** when embedded: reads the datasource (packaged) or the
  `feed_data` worksheet (hosted) via the Extensions API, honoring row-level
  security automatically.
- A **Demo/Live toggle**. Packaged mode produces a published `.twbx`; hosted
  mode produces a `.trex` manifest to add to a dashboard.

## Requirements

- **Tableau Studio** (the in-Desktop agent) — this is where you invoke the skill.
- A Tableau **published datasource** to build from. (v1 starts from an existing
  datasource; it does not generate one from scratch.)
- **Python 3** on your PATH — the bundler uses the standard library only, so
  there is **nothing to `pip install`**. Check with `python3 --version`.
- **Packaged mode:** a Tableau Cloud site with **Settings > Packages > Allow
  Packages on this Site** enabled (site admin), a published datasource with
  VizQL Data Service enabled, and a **Personal Access Token**. Run
  `python3 assets/package_extension.py configure` then `store-secret` once; on
  macOS the secret goes in Keychain, elsewhere `export TABLEAU_PAT_SECRET` in
  your shell. The secret never goes in chat or files. Note: neither Tableau
  Studio (build 26.1026) nor Tableau Desktop can open a packaged workbook yet
  (error D2E8DA72), so the packaged story is viewed and edited only through
  Tableau Cloud and the skill's scripts. Don't download it to edit in Desktop;
  re-run the build instead.
- **Hosted mode:** a **public, framable static host** for the finished HTML (e.g. Cloudflare
  Pages, Netlify, S3 + CDN). A dashboard extension is fetched client-side by the
  viewer's browser, so the host must be public (no login), send no framing
  headers (`X-Frame-Options` / CSP), and be reachable from the presenter's
  laptop. A gated/internal host will not work as the iframe source.

## Install

1. **Unzip** `scrollytelling-demo-builder.zip`.
2. **Move the `scrollytelling-demo-builder/` folder** into your Tableau Agent
   skills directory:

   ```
   ~/Documents/My Tableau Repository/Tableau Agent/skills/scrollytelling-demo-builder
   ```

   If you're on the beta build, the path is
   `~/Documents/My Tableau Repository (Beta)/Tableau Agent/skills/`. Create the
   `skills/` folder if it doesn't exist. The final layout should be:

   ```
   Tableau Agent/skills/scrollytelling-demo-builder/
     ├─ SKILL.md
     ├─ README.md            (this file)
     ├─ VERSION, CHANGELOG.md
     ├─ assets/              (templates, vendor libs, .trex examples,
     │                        build_standalone.py, package_extension.py)
     └─ references/          (style-guide.md, build-procedure.md,
                              packaged-extension.md, output-styles.md,
                              sample-gallery.md)
   ```

3. **Reload skills** — run `/reload-skills` in Tableau Studio, or restart Studio.
4. Confirm the skill appears in the available-skills list.

## Start using it

In Tableau Studio, just ask — for example:

- "Build a scrollytelling demo from my published datasource."
- "Find the story in my data and make a keynote dashboard."
- "Turn this datasource into a data story."

The skill orients you first (what it will do, which delivery mode you want,
the outline for that mode, and how much prompting you want — Minimal / Medium /
Maximum), then walks the build end to end.

**Packaged mode:**

1. **Pick & connect** the published datasource — *you choose it and sign in.*
2. Examine the data and **find the signal** — automatic VizQL probes.
3. Draft the story and pick the scrolly design.
4. Build the self-contained HTML (story + Explore view), with the live query.
5. **Package and publish** the `.twbx` to a project — *you confirm the project.*
6. **Verify** on Tableau Cloud — the skill checks a server render; *you open
   the view and check scrolling, the toggle, and Explore.*

**Hosted mode:**

1. **Pick & connect** the published datasource — *you choose it and sign in.*
2. Examine the data and **find the signal** — automatic VizQL probes.
3. Draft the story and pick the scrolly design (linear chapters vs. pinned/
   sticky) for your audience.
4. Build the self-contained HTML (story + Explore view).
5. Build the `feed_data` feeder worksheet.
6. **In Tableau Desktop:** add a dashboard, float `feed_data` off-canvas, and
   drop the Extension object — *this part is done by hand* (automated dashboard
   placement has been unreliable).
7. **Host** the HTML at a public framable URL and point the `.trex` at it.
8. **Publish** the workbook — *you complete the Publish dialog.*

## Tips

- The vendored COO/CFO templates in `assets/public/` are a **mechanics and style
  reference** (animation, D3 patterns, Demo/Live toggle, live-bind plumbing) —
  not a page to fill in. Every number, field, threshold, and chapter is adapted
  to your datasource; nothing from the sample story transfers.
- The **Explore filter bar is live-only**: it greys out in Demo mode and on the
  standalone page, and lights up in Live mode when the extension is embedded
  (packaged, or hosted with the floated `feed_data` sheet). That's by design — it never fabricates
  row-level data.
- Read `references/build-procedure.md` and `references/style-guide.md` for the
  full procedure and the function-level anchors; the skill reads them too.

## Third-party code

- `assets/vendor/d3.min.js` — D3, ISC license.
- `assets/vendor/tableau.extensions.1.latest.js` and
  `assets/vendor/tableau.extensions.data-apps.min.js` — the Tableau Extensions
  API (the latter is the Data Apps build from the `tableau/tableau-mcp`
  templates), Apache License 2.0, © Tableau Software / Salesforce.

## Support

Questions or issues, ping the author who shared this zip.
