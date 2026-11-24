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
- A Tableau **published datasource** to build from. (It starts from an existing
  published datasource; it doesn't generate one.)
- **Python 3** — the scripts use the standard library only, so there is
  **nothing to `pip install`**. Check with `python3 --version` (on Windows,
  `py -3 --version` or `python --version`).
- **Packaged mode:** a Tableau Cloud site with **Settings > Packages > Allow
  Packages on this Site** enabled (site admin), a published datasource with
  VizQL Data Service enabled, and a **Personal Access Token**. Run
  `python3 skill-expertise/package_extension.py configure` once, then save the
  secret with `store-secret`: it goes to Keychain on Mac, or Windows Credential
  Manager on Windows (run it in PowerShell; an environment-variable fallback is
  in `skill-expertise/packaged-extension.md`, Prerequisites). The secret never goes in chat or files. Note: neither Tableau
  Studio nor Tableau Desktop can open a packaged workbook (error D2E8DA72), so the packaged story is viewed and edited only through
  Tableau Cloud and the skill's scripts. Don't download it to edit in Desktop;
  re-run the build instead.
- **Hosted mode:** a **public, framable static host** for the finished HTML (e.g. Cloudflare
  Pages, Netlify, S3 + CDN). A dashboard extension is fetched client-side by the
  viewer's browser, so the host must be public (no login), send no framing
  headers (`X-Frame-Options` / CSP), and be reachable from the presenter's
  laptop. A gated/internal host will not work as the iframe source.

## Install and update

1. **Unzip** `scrollytelling-demo-builder.zip`.
2. **Move the `scrollytelling-demo-builder/` folder** into your Tableau Agent
   skills directory:

   ```
   ~/Documents/My Tableau Repository/Tableau Agent/skills/scrollytelling-demo-builder
   ```

   If you're on the beta build, the repository folder is named
   "My Tableau Repository (Beta)", so the path is
   `~/Documents/My Tableau Repository (Beta)/Tableau Agent/skills/`. Create the
   `skills/` folder if it doesn't exist. The final layout should be:

   ```
   Tableau Agent/skills/scrollytelling-demo-builder/
     ├─ SKILL.md
     ├─ README.md            (this file)
     └─ skill-expertise/     (procedure and style references, Python scripts,
                              story templates, vendored libraries,
                              example .trex manifests, license notices)
   ```

   Templates, vendored libraries and example manifests are stored as `.txt`
   files (for example `coo-brief.html.txt`); the scripts read them as-is.

3. **Reload skills** — run `/reload-skills` in Tableau Studio, or restart Studio.
4. Confirm the skill appears in the available-skills list.

After you update or edit any file in this skill, run `/reload-skills` in Tableau
Studio (or restart Studio) so the change takes effect.

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

- The vendored COO/CFO templates in `skill-expertise/` are a **mechanics and style
  reference** (animation, D3 patterns, Demo/Live toggle, live-bind plumbing) —
  not a page to fill in. Every number, field, threshold, and chapter is adapted
  to your datasource; nothing from the sample story transfers.
- The **Explore filter bar is live-only**: it greys out in Demo mode and on the
  standalone page, and lights up in Live mode when the extension is embedded
  (packaged, or hosted with the floated `feed_data` sheet). That's by design — it never fabricates
  row-level data.
- Read `skill-expertise/build-procedure.md` and `skill-expertise/style-guide.md` for the
  full procedure and the function-level anchors; the skill reads them too.

## Third-party code

- `skill-expertise/d3.min.js.txt` — D3, ISC license.
- `skill-expertise/tableau.extensions.1.latest.js.txt` and
  `skill-expertise/tableau.extensions.data-apps.min.js.txt` — the Tableau Extensions
  API (the latter is the Data Apps build from the `tableau/tableau-mcp`
  templates), Apache License 2.0, © Tableau Software / Salesforce.
- Full license texts are in `skill-expertise/THIRD-PARTY-NOTICES.md` and
  `skill-expertise/apache-2.0-license.txt`.

## Support

Report issues through Tableau Exchange.
