---
name: dashboard-builder
description: Use when the user wants to add a dashboard extension to a Tableau workbook but hasn't said which kind — phrases like "build a dashboard extension", "add an extension to my dashboard", "I want an extension for this viz", or "what extension should I use for this". Presents the four build paths (custom-built extension, scrollytelling data story, existing installed/Exchange extension, or something else) and routes to the right skill or workflow. Do NOT use when the user has already named a specific path — a scrollytelling/data-story/keynote ask routes straight to scrollytelling-demo-builder, and a named installed extension (e.g. "add the Horizon Chart extension") routes straight to native placement — this skill exists for the ambiguous entry point only, not as a wrapper around every extension-related request.
---

# Dashboard builder (router)

This skill is a **decision point, not a builder**. Its only job is to find out which
of four paths the user actually wants, then hand off — it does not itself write
HTML, author calcs, or place extension objects.

## Step 0 — Check existing state, then ask, don't guess

Before presenting the menu, call `get-workbook-inventory` (or `list-dashboards` if
inventory isn't available) to check whether the workbook already has a dashboard
with an Extension object placed. If one exists, name it and ask whether this
request is about that existing extension (e.g. reconfiguring it, or replacing it)
before offering the four-option menu — don't present the menu as if starting from
a blank workbook when it isn't one.

If the user's request already names a specific path (see negative triggers in the
description), skip straight to that path's handoff below — don't re-ask the menu.

Otherwise, present the four options with `ask-user` using this exact numbered
template — the bolded lead phrase of each option is locked verbatim, the
description after the em dash may be paraphrased for tone but must preserve
the same meaning and stay one line:

1. **Build a brand-new custom dashboard extension** — from scratch, based on your input
   (a bespoke visual/interaction not covered by anything installed or on the Exchange).
2. **Build a "scrollytelling" data story** — an animated, scroll-driven narrative
   extension built from a published datasource.
3. **Use a native Tableau element or an extension you already have installed (or one
   from the Exchange)** — reuse existing capability instead of building something new.
4. **Something else** — describe it in your own words if none of the above fit.

## Handoff by option

- **Option 1 (brand-new custom extension):** this skill does not build custom
  extensions from scratch today. Say so plainly, and ask the user to describe
  the desired visual/interaction in enough detail that a decision can be made
  about whether it's actually closer to option 2 (a data story) or option 3
  (something an installed/Exchange extension already does) — most "build me
  something custom" asks turn out to be one of those two once the actual need
  is named. If neither fits after asking, this is a genuine gap: say so and stop.
  **Worked example:** user says "I want a custom extension that walks through
  our quarterly numbers with some animation as you scroll." The word "scroll"
  plus "walks through" numbers over time is a narrative/animated ask — that's
  option 2, hand off to `scrollytelling-demo-builder`. Contrast: user says "I
  want a custom extension that lets people type in a what-if number and see
  the chart update" — no narrative/scroll framing, just an interactive
  input-driven visual — check the Extensions folder first (option 3) for a
  what-if/scenario tool before concluding it's a genuine gap.
- **Option 2 (scrollytelling data story):** hand off entirely to
  `scrollytelling-demo-builder`. Do not re-implement any part of its Step 0
  orientation or build procedure here — invoke that skill and let it run.
- **Option 3 (native element or existing/Exchange extension):** see "Inventory
  the installed Extensions folder" below. This is this skill's own job, not a
  handoff — walk the user through picking and placing the right one.
- **Option 4 (something else):** ask what they have in mind, in their own
  words, then match it to the closest of options 1-3 (or a different skill
  entirely, e.g. `tableau-desktop-authoring` for a plain chart/dashboard ask
  with no extension involved) rather than forcing it into this skill's scope.

## Inventory the installed Extensions folder (option 3)

- Read the local Extensions folder. **Mac:**
  `/Users/<user>/Documents/My Tableau Repository (Beta)/Extensions/*.trex`.
  **Windows:** `C:\Users\<user>\Documents\My Tableau Repository\Extensions\*.trex`
  (no "(Beta)" segment on most Windows installs — confirm the exact folder name
  if the default path returns nothing). For each `.trex`, extract the
  `<description>` text (human-readable name) and, if present, the `<encoding>`
  blocks (what data types/roles it expects — e.g. temporal/string/numeric) so
  you can match extensions to the user's actual fields, not just list filenames.
- **Never guess an extension's capability from its filename alone** — read the
  actual `.trex` content. A name like `smm-horizon.viz.trex` doesn't tell you
  it needs a temporal dimension + a string category + a numeric measure; the
  `<encoding>` blocks do.
- **Locked matching rule** (replaces any "seems relevant" judgment call): if the
  user has named specific fields or a chart shape, compare their field types
  (dimension/measure, temporal/string/numeric) against each `.trex`'s
  `<encoding>` `<data-type>` values and surface only extensions whose encodings
  are satisfiable by the named fields. If the user hasn't named fields yet, show
  the full list. This makes the shortlist deterministic — same fields, same
  shortlist, every session.
- **If the folder has more than ~15-20 `.trex` files,** don't dump the full list
  unprompted — ask what kind of visual/interaction they're after first (e.g.
  "a chart type, a table enhancement, a what-if/scenario tool?") and use that to
  pre-filter by `<description>` before applying the field-type matching rule
  above, rather than presenting an unfiltered wall of options.
- **If a `.trex` fails to parse as valid XML,** skip it and note by filename
  which one failed rather than silently omitting it from the list or letting a
  parse error abort the whole inventory step.
- Present the shortlist as a numbered list, one extension per line, in this
  exact format: `N. **<description text from .trex>** — needs: <data types
  from <encoding> blocks, or "no field requirements" if none declared>`. Sort
  by filename ascending for a stable, reproducible order across sessions. End
  with a single line: "Which one do you want?" Do not add extra commentary
  between list items — one line per extension, nothing more.
- **If the user wants something not in the local Extensions folder,** it must
  come from the Tableau Exchange — this skill does not download or install
  Exchange extensions (no supported tool for that). Tell the user plainly to
  browse the Exchange in Desktop (**Dashboard pane → Extensions object → More
  Extensions...**) and install it there; once installed, it will appear in the
  same local Extensions folder and this skill can pick it up on a re-run.
- Once an extension is chosen, placement follows the same manual pattern as
  scrollytelling-demo-builder's dashboard-placement step (drag the Extension
  object onto the dashboard, browse to the `.trex`, approve the data-access
  prompt) — **never attempt automated `apply-dashboard` placement for this
  either**; the same corruption risk documented in
  `scrollytelling-demo-builder/references/build-procedure.md` (Known failure
  modes §A) applies to any Extension object, not just the scrollytelling one.
- **After the user confirms placement is done, verify before declaring success:**
  ask them to confirm the tile actually renders (not a blank/error tile) and that
  the fields they mapped show real values, not placeholder/demo content. Don't
  treat "I dragged it on" as confirmation that it's working — the render and the
  placement are two different things that can each fail independently.
- For a **native Tableau element** (no extension needed — e.g. the user's ask
  is actually just a chart type Tableau already supports), don't force an
  extension: say so and hand off to `tableau-desktop-authoring` instead.

## Common mistakes

- **Guessing an extension's capability from its filename.** Always read the
  actual `.trex` `<encoding>` blocks before shortlisting or recommending it.
- **Presenting the four-option menu when a dashboard/Extension object already
  exists.** Always run the Step 0 inventory check first and ask about the
  existing object instead of assuming a blank workbook.
- **Attempting automated `apply-dashboard` placement for any Extension
  object.** This is off-limits regardless of which extension — hand off to
  manual placement every time, per the Invariants below.
- **Treating "I dragged it on" as done.** Placement and rendering are separate
  failure points — always confirm the tile renders with real (not
  placeholder) data before declaring success.
- **Forcing an ambiguous "custom extension" ask into option 1** without first
  checking whether it's actually a data-story ask (option 2) or something an
  installed/Exchange extension already covers (option 3) — see the worked
  example above.

## Error handling

| Failure | Recovery |
|---|---|
| Extensions folder doesn't exist or is empty | Verify by reading the folder yourself before reporting this — never take the user's claim about folder state at face value. If it's genuinely empty, say so plainly and offer the Exchange path (Dashboard pane → Extensions object → More Extensions...). If it isn't empty, correct the premise and proceed with the real contents. |
| A `.trex` file fails to parse | Skip it, name the specific filename that failed, and continue with the rest of the folder — don't abort the whole inventory step over one bad file. |
| User names an extension not found locally or on Exchange after browsing | Confirm the exact name/spelling with the user before concluding it doesn't exist; typos in extension names are common. |
| `get-workbook-inventory`/`list-dashboards` call fails or times out | Proceed to the menu anyway, noting you couldn't check for an existing dashboard first — don't block the whole flow on this check. |
| User picks an extension whose `<encoding>` requirements don't match any fields they've named | Say plainly which data types it needs (per its `<encoding>` blocks) and ask which fields to map, rather than placing it and hoping it resolves. |

## Tools and sequencing

| Order | Tool | Purpose |
|---|---|---|
| 1 | `get-workbook-inventory` (or `list-dashboards`) | Check for an existing dashboard/Extension object before presenting the menu (Step 0). |
| 2 | `Read` / `Glob` on the Extensions folder | Batch-read all `.trex` files in one pass — don't read them one-by-one across multiple turns; the folder is small enough to read in full each time. |
| 3 | `ask-user` | Present the menu (Step 0) or the extension shortlist (option 3), only after steps 1-2 are done so the choice reflects real state. |
| 4 | Manual placement (user-driven) | Never `apply-dashboard` for extension placement — hand off per the Invariants below. |
| 5 | `get-workbook-inventory` / visual confirmation from the user | Post-placement verification — confirm the tile renders before declaring the task done. |

## Invariants

- **This is a router, not a builder.** Never duplicate scrollytelling-demo-builder's
  orientation/build steps here — invoke that skill instead of re-explaining its flow.
- **Never fabricate an extension's data requirements.** Read the real `.trex`
  encoding blocks; don't infer from the name.
- **Automated dashboard/zone placement is off-limits for any Extension object**,
  not just scrollytelling's — the corruption risk is a Tableau-engine-level gap,
  not specific to one skill's extension.
- **Installing new Exchange extensions is a Desktop UI action, not something this
  skill can do headlessly.** Point the user to the Exchange picker in Desktop.

After creating or editing this skill, tell the user to run `/reload-skills`.
