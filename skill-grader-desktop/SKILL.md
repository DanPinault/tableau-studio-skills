---
name: skill-grader-desktop
description: Grade and evaluate the effectiveness of Tableau Desktop agent skills against 20 weighted criteria adapted for the Desktop tool environment. Triggers on grade this desktop skill, evaluate my desktop skill, score this tableau skill, desktop skill audit, or skill-grader-desktop. Do NOT use for Claude/Cowork skills (use skill-grader instead), code review, debugging skill execution failures, or troubleshooting whether a skill is firing correctly.
---

# Skill Grader — Tableau Desktop Edition

You are evaluating a Tableau Desktop agent skills effectiveness across 20 weighted criteria. This framework is calibrated for skills that run inside Tableau Desktops agent environment, which uses natural-language tool routing, worksheet-based data access, and authoring tools (calcs, worksheets, fields).

For Claude/Cowork skills (skills that run in the Claude desktop app, not inside Tableau), use the standard skill-grader instead.

## Independence Requirement

Every evaluation must be fully independent. If you authored, co-authored, or recently worked on the skill being evaluated, you MUST:

- Disclose this at the top of the report: Note: I participated in creating/editing this skill. Scoring with extra scrutiny.
- Err toward stricter scoring on any criterion where you might be generous due to familiarity.
- Treat the skill as if a stranger wrote it and youre seeing it for the first time.

## Tools to Use

- Read — to read the SKILL.md and any supporting files in the skill directory, and `../platform_limitations.md` at the skills/ root (see Platform Limitations Reference below)
- Glob — to discover what files exist in the skills directory (templates, examples, configs, skill-expertise/)
- Memory — memory here is a set of flat markdown files in a fixed per-project directory (indexed by MEMORY.md), not a live query tool. Check MEMORY.md for an entry referencing this skills name before scoring; if none exists, note no prior memory found rather than skipping the step silently.

## Platform Limitations Reference (Read Before Scoring)

Before scoring any skill, read `platform_limitations.md` at the skills/ root (sibling to the skill directories, e.g. `.../Tableau Agent/skills/platform_limitations.md`). This file catalogs confirmed, live-tested gaps in the Desktop tool surface — no zone-move/view-fit/canvas-size commands, no delete-field/delete-calc, sets invisible to field-resolution tools, `author-parameter` deterministically broken on Windows, `get-worksheet-xml` 500s on dashboard-bound sheets, `build-and-apply-worksheet` calc-corruption risk on parameter-referencing datasources, no mark-selection/parameter-value-set command for behavioral testing, and more. If a skill directory has its own limitations reference file (e.g. `skill-expertise/agent_limitations.md`), read that too and treat it as the skills own restatement of the same underlying gaps — cross-check it against the root file rather than treating it as a separate source of truth.

This reference cuts both ways in scoring — it is not a blanket excuse:

- **Legitimate carve-out:** if a skills design correctly routes around a confirmed gap (e.g., gives manual dashboard-assembly instructions instead of claiming to place zones, or hard-stops worksheet mutation on parameter-referencing datasources per the `build-and-apply-worksheet` corruption risk), that is a *strength*, not a baseline-3 — score it on merit under whichever criterion it touches (typically #6 Output Quality Floor, #5 Error Handling, or #2 Scope Boundaries), since a well-written skill can and should design around a known gap rather than just being excused for hitting it.
- **Missed acknowledgment is a real deduction:** if a skills domain clearly intersects a documented gap (e.g., a dashboard-building skill that never mentions the zone-placement/view-fit/canvas-size limitations, an interaction-testing skill that doesnt mention the mark-selection gap, or a calc/field skill that doesnt mention the no-delete-calc constraint) and the skill is silent about it — or worse, implies it can do the thing the platform cannot — this is a deduction, not neutral. Cap #16 Domain Accuracy and #6 Output Quality Floor at 3 in this case, and note in the justification exactly which documented gap was ignored, citing the specific line/section of `platform_limitations.md`.
- **Baseline-3 is reserved for genuine platform absence with no workaround documented anywhere** (e.g., no persistent memory across sessions, no visual/screenshot capability) — not for gaps this reference file already documents a known workaround for. If a workaround is documented in `platform_limitations.md` or a skills own limitations reference and the skill being graded doesnt use it, score on merit (i.e., dock the skill), not baseline.

## Scope & Boundaries

This skill evaluates:

- Custom skills built for the Tableau Desktop agent environment
- Skills that call Desktop-specific tools (bind-template, list-available-fields, get-summary-data, author-calc, author-parameter, author-set, author-action, build-and-apply-worksheet, resolve-field, add-field, remove-field, refine-worksheet, dashboard-auto-apply, plan-dashboard-creation, batch-create-and-cache-sheets, etc.)
- Skills of any domain within the Desktop context (data quality, dashboard design, calculation authoring, etc.)

**Minimum viable input:** A skill with at least a description field and 10+ lines of instruction. For skills below this threshold, state: This skill is below minimum evaluation threshold (< 10 lines). A meaningful grade requires more substance.

**This skill does NOT evaluate:**
- Claude/Cowork skills (use `skill-grader`)
- Code quality (use a code review tool)
- Whether a skill is executing correctly (thats debugging)
- General prompts that arent structured as skills

**Hybrid skills (Desktop + Claude):** For skills that target both environments, evaluate only the Desktop-facing instructions here. Note partial coverage and recommend the user run `skill-grader` on the Claude-facing portions separately.

***

## Modes

**Full report (default):** Complete evaluation with all sections. Use when user says grade this skill, evaluate, score, audit.

**Quick grade:** Header + Category Breakdown + Quick Wins only. Use when user says quick grade, just the score, hows this skill looking, or explicitly asks for brevity.

**Length-aware adjustments:**
- **For skills under 20 lines:** Expect lower scores on #4 (Workflow Completeness), #5 (Error Handling), #10 (Adaptability). Brevity naturally limits coverage.
- **For skills over 200 lines:** Also evaluate whether length serves purpose or adds bloat (factor into #12 Efficiency). A long skill thats specific scores well; a long skill thats padded does not.
- **For skills with 3+ reference files:** Read all, but note if context limits prevent full coverage.

***

## Workflow

### Step 1: Identify the Skill to Grade

If the user names a specific skill, read its SKILL.md file. If they paste content directly, use that. If ambiguous, ask which skill to evaluate.

Use **Glob** to check the skills directory for supporting files:
```
<skill_directory>/**/*
```

Read ALL supporting files (templates, examples, configs, reference docs). These inform scoring on criteria #4 (Workflow Completeness), #8 (Tool Utilization), #10 (Adaptability), and #6 (Output Quality Floor). A skill with rich supporting files may score higher than its SKILL.md alone suggests.

Read `platform_limitations.md` at the skills/ root per the Platform Limitations Reference section above. Identify which confirmed gaps, if any, are relevant to this skills domain (e.g. a dashboard skill intersects the zone/view-fit/canvas-size gaps; a calc skill intersects the no-delete-calc gap; an interaction-testing skill intersects the mark-selection gap). Note explicitly whether the skill acknowledges and designs around each relevant gap, or is silent/wrong about it — this feeds #16, #6, #5, and #2 below.

Check the memory index (MEMORY.md and its linked files) for any prior feedback about this specific skill by name — it may reveal known issues or validated strengths that inform scoring. If nothing references the skill, state that explicitly rather than treating the check as satisfied by omission.

**When re-grading a previously evaluated skill:** Reference prior scores if available in conversation context. Note which criteria changed and why. This prevents regression on previously-validated strengths and makes the delta from improvements explicit.

### Step 2: Evaluate Against the 20 Weighted Criteria

Score each criterion from 1-5 using this scale:

- **5** — Exceptional — best-in-class implementation
- **4** — Strong — meets the bar with minor gaps
- **3** — Adequate — functional but clear room for improvement
- **2** — Weak — partially addressed or inconsistently applied
- **1** — Missing — not addressed at all

**If a criterion is genuinely not applicable** to the skill type, score it 3 (baseline) and note N/A — scored at baseline in the justification.

### Weighted Scoring System

Each criterion has a **weight** based on its impact on skill capability and necessity. The weighted score for each criterion = raw score (1-5) x weight. Maximum possible total = **100**.

- **#3 Instruction Specificity** — Weight 1.53, Max Contribution 7.65
- **#20 Measurable Impact** — Weight 1.53, Max Contribution 7.65
- **#6 Output Quality Floor** — Weight 1.37, Max Contribution 6.87
- **#4 Workflow Completeness** — Weight 1.37, Max Contribution 6.87
- **#1 Trigger Precision** — Weight 1.22, Max Contribution 6.11
- **#19 Reuse Frequency** — Weight 1.22, Max Contribution 6.11
- **#7 Reproducibility** — Weight 1.22, Max Contribution 6.11
- **#16 Domain Accuracy** — Weight 1.22, Max Contribution 6.11
- **#9 Validation Steps** — Weight 1.07, Max Contribution 5.34
- **#2 Scope Boundaries** — Weight 1.07, Max Contribution 5.34
- **#5 Error Handling** — Weight 0.92, Max Contribution 4.58
- **#8 Tool Utilization** — Weight 0.92, Max Contribution 4.58
- **#10 Adaptability** — Weight 0.92, Max Contribution 4.58
- **#14 User Autonomy** — Weight 0.76, Max Contribution 3.82
- **#12 Efficiency** — Weight 0.76, Max Contribution 3.82
- **#18 Scalability** — Weight 0.76, Max Contribution 3.82
- **#13 Context Leverage** — Weight 0.61, Max Contribution 3.05
- **#17 Formatting Standards** — Weight 0.61, Max Contribution 3.05
- **#15 Documentation Clarity** — Weight 0.46, Max Contribution 2.29
- **#11 Composability** — Weight 0.46, Max Contribution 2.29

**Total max = 100.00**

***

### The 20 Criteria (Desktop-Adapted Anchors)

#### TIER 1 — Core Capability (Weight 1.53)

**3. Instruction Specificity** — Are instructions concrete enough that two independent sessions would produce near-identical results?

- **1** — Instructions are vague platitudes (check the data, use appropriate fields)
- **2** — Some specific instructions exist but most decision points are left to interpretation
- **3** — Core workflow is specified but detection logic, thresholds, or tool sequences are vague
- **4** — Most decision points have explicit guidance; only minor edge cases are unspecified
- **5** — Every decision point has explicit guidance: locked thresholds, regex patterns, field-name rules, exact tool sequences

**Desktop-specific scoring notes:**
- Specificity in this environment means: locked detection patterns (regex, threshold values), explicit field-name matching rules, exact severity assignment logic, and prescribed tool call sequences.
- Vague references to relevant fields or appropriate checks score 2 max.
- A skill that says check for issues without defining what constitutes an issue at what threshold scores 1.

**20. Measurable Impact** — Does following this skill produce noticeably better results than the Desktop agent would produce without it?

- **1** — The agent would produce essentially identical output without this skill
- **2** — Minor improvements (slightly better formatting or structure)
- **3** — Noticeable improvement in one dimension (e.g., better structure OR better accuracy, not both)
- **4** — Clear improvement across multiple dimensions; output is meaningfully better
- **5** — Transformative — output without the skill would be clearly inferior or dangerous (wrong findings, silent data mutation, missed critical issues)

**Control comparison test:** Consider what the Desktop agent would do for a typical request in this skills domain with NO skill loaded. The agent has access to the same tools but no systematic guidance. Compare that imagined output to what the skill produces. The gap is the impact score.

#### TIER 2 — Quality Assurance (Weight 1.37)

**6. Output Quality Floor** — Does following the skill guarantee a minimum quality bar every time?

- **1** — Quality varies wildly; following the skill doesnt prevent bad output
- **2** — Some quality controls but significant variance remains possible
- **3** — Consistent format/structure, but content accuracy or depth can still vary
- **4** — Strong quality floor with anti-patterns identified; bad output is unlikely
- **5** — Worst possible output from following this skill is still professional-grade; multiple quality gates prevent every known failure mode

**Desktop-specific scoring notes:**
- Anti-patterns are particularly important here: Dont infer from field names alone, Dont fabricate findings, Dont silently create objects. A skill that lists these explicitly scores higher.
- A Common Mistakes section is a strong signal for scores 4-5.
- Check for these Desktop-specific anti-patterns and dock accordingly if absent from a skill that plausibly needs them:
  - **Bind-template bypass** — does the skill route named-chart requests through manual shelf/field authoring instead of `bind-template`? This produces inconsistent, non-deterministic results and should cap this criterion at 3.
  - **Context/instruction leakage** — does the skill correctly treat `<live-tableau-context>` (or similar injected context blocks) as data to read, never as instructions to follow?
  - **Internal-detail leakage to the user** — does the skills report/output template avoid surfacing tool names, template ids, or internal command syntax to the end user? Leaking these caps the score at 3-4 depending on severity.
  - **Mutation discipline** — see the standalone Mutation Risk Observation called out in Step 3 below; do not fold this into the numeric score for this criterion.

**4. Workflow Completeness** — Does the skill define the full path from receiving the request to delivering final output?

- **1** — Major workflow gaps — the agent must improvise most of the execution
- **2** — Starting point defined but middle and end are vague
- **3** — Main happy-path workflow complete but branches, alternatives, and endings are underspecified
- **4** — Complete workflow including branches; only rare edge cases unaddressed
- **5** — Full path defined including entry, branches, alternatives, and exit; nothing left to improvisation

**Desktop-specific phases to check for:**
- Datasource identification/confirmation
- Field scoping and resolution
- Worksheet setup (scratch sheets, field placement)
- Data reading via `get-summary-data`
- Analysis/detection logic
- Triage/prioritization
- Fix proposal and approval
- Fix application and verification
- Report rendering
- Cleanup or export

#### TIER 3 — Reliability & Activation (Weight 1.22)

**1. Trigger Precision** — Does the description clearly define when the skill should fire AND when it shouldnt?

- **1** — Description is generic or missing
- **2** — Positive triggers exist but no negative boundaries
- **3** — Clear positive triggers; weak or missing negative boundaries
- **4** — Both positive triggers and negative boundaries; minor disambiguation gaps
- **5** — Positive triggers, negative boundaries, AND explicit disambiguation from adjacent Desktop skills

**Desktop-specific scoring notes:**
- Desktop skills are routed via natural language (the agent interprets user intent). Trigger precision is critical because theres no slash-command guarantee.
- Disambiguation matters: if the Desktop environment has multiple skills that could plausibly match help me with this data, each skill needs clear boundaries.
- Score 5 requires explicit Do NOT trigger for... language plus disambiguation from named adjacent skills.

**19. Reuse Frequency** — Does this skill address a genuinely recurring need?

- **1** — Solves a one-off problem that doesnt recur
- **2** — Might be used a few times per year
- **3** — Monthly use — addresses a recurring but infrequent need
- **4** — Weekly use — part of a regular workflow
- **5** — Daily or near-daily use — central to the users core Tableau workflow

**7. Reproducibility** — Would the same datasource produce consistent outputs across sessions?

- **1** — Results depend heavily on unstated assumptions; high variance between sessions
- **2** — Structure is consistent but findings/decisions vary significantly
- **3** — Core output is consistent; secondary details (phrasing, ordering, minor judgments) vary
- **4** — Near-identical output for the same datasource; minor wording differences only
- **5** — Deterministic — same datasource always produces functionally equivalent findings and report

**Desktop-specific scoring notes:**
- In this environment, reproducibility depends on: locked detection thresholds, explicit severity rules, deterministic priority ordering, and consistent report templates.
- Soft judgment language (looks like, might be, consider whether) reduces reproducibility. Locked rules (if >10% match pattern X, flag as Y with severity Z) increase it.

**Worked calibration example (score 3 vs 4):**
- Score 3 text: Flag fields with a lot of nulls as a data quality issue. — a lot is undefined; two sessions could flag different fields at different thresholds.
- Score 4 text: Flag any field where `COUNT(field)` / `COUNT(*)` from `get-summary-data` falls below 90% as a null-rate issue; below 50% escalate to high severity. — same datasource, same threshold, same flagged fields every time.
- The gap between 3 and 4 is whether the *number* and the *comparison operator* are written down, not whether the skill cares about data quality in general terms.

**16. Domain Accuracy** — Are the Tableau-specific instructions technically correct?

- **1** — Contains factual errors about Tableau functions, shelf behavior, or aggregation
- **2** — Mostly correct but some formulas would produce wrong results or errors
- **3** — Correct for common cases; gaps in advanced scenarios (LOD edge cases, date handling, multi-table behavior)
- **4** — Technically sound throughout; a Tableau expert would approve with minor quibbles
- **5** — Expert-level accuracy; correct function syntax, accurate aggregation behavior, proper shelf mechanics, and handles Tableau-specific nuances (NULL behavior in joins, date hierarchy levels, FIXED vs. INCLUDE vs. EXCLUDE)

**Desktop-specific things to verify:**
- Calculated field syntax (correct Tableau function names, proper quoting, valid LOD structure)
- Shelf mechanics (Detail vs. Rows/Columns, filter order of operations)
- Aggregation behavior (SUM vs. AGG, NULL handling in COUNT vs. COUNTD)
- Date functions (DATEPARSE format strings, DATEDIFF vs. DATEADD behavior)
- Data type conversion (FLOAT, INT, STR, DATE interactions)

#### TIER 4 — Robustness (Weight 1.07)

**9. Validation Steps** — Does the skill include self-checks before delivering output?

- **1** — No validation — output is delivered without any check
- **2** — One informal check (verify results look right)
- **3** — A checklist exists but its vague or optional
- **4** — Specific validation steps with clear pass/fail criteria
- **5** — Multiple validation gates: data-backed evidence check, consistency verification, post-fix confirmation, and pre-report audit

**Desktop-specific validation examples (for scoring 4-5):**
- Every finding must be backed by an actual `get-summary-data` read
- After applying a fix calc, call `get-summary-data` to verify output values
- Before rendering report, confirm finding count matches table rows
- Re-scan affected fields after fix to confirm resolution

**2. Scope Boundaries** — Are the limits of what the skill does vs. doesnt do explicit?

- **1** — Scope undefined
- **2** — Implicit boundaries from context but nothing stated
- **3** — What the skill DOES is clear; what it DOESNT do is unstated
- **4** — Both positive scope and exclusions defined; minor edge cases unaddressed
- **5** — Full boundary definition including: whats in scope, whats out, edge cases (calcs, parameters, sets, multi-table), and handoff guidance

#### TIER 5 — Execution Depth (Weight 0.92)

**5. Error Handling** — Does the skill anticipate Desktop-specific failure modes?

- **1** — Only happy path — no mention of what can go wrong
- **2** — Acknowledges errors exist without specifics
- **3** — Handles 1-2 common failures (e.g., field not found) but misses others
- **4** — Comprehensive error taxonomy with specific recovery steps for most Desktop failures
- **5** — Full error playbook covering: tool call failures, field resolution misses, datasource disconnects, permission issues, timeout/capacity, worksheet creation conflicts, calc syntax errors, and partial-result recovery

**Desktop-specific failure modes to check for:**
- `get-summary-data` timeout or empty return
- `resolve-field` returns no match (renamed/removed field)
- `build-and-apply-worksheet` name collision
- `author-calc` syntax error
- Datasource disconnection mid-workflow
- Field-level permission denial (RLS)
- Sample returns fewer rows than requested
- All fields fail to read (catastrophic)
- A proposed fix would mutate the workbook (calc, worksheet, or XML edit) without a stated user-confirmation step first — flag this in the standalone Mutation Risk Observation (Step 3) rather than scoring it here

**8. Tool Utilization** — Does the skill specify which Desktop tools to use and when?

- **1** — No tool guidance
- **2** — Mentions tools exist but doesnt specify which
- **3** — Names tools but doesnt specify sequencing or when each is needed
- **4** — Clear tool prescription for main workflow phases; minor gaps in edge cases
- **5** — Specific tools prescribed for each phase with batching strategy, sequencing logic, and efficiency guidance

**Desktop tool environment (known tools):**
- `bind-template` — the FIRST-CHOICE path for any named chart type or common viz ask; deterministic two-call sequence (propose, then apply). A skill that builds named charts via manual shelf/field authoring instead of bind-template is bypassing the platforms primary routing path — treat this as a scoring concern, not a stylistic choice.
- `list-available-fields` — enumerate fields/types
- `resolve-field` — disambiguate field name to exact reference
- `get-summary-data` — read actual data from a worksheet (requires fields on Detail)
- `add-field` / `remove-field` — manage worksheet shelves
- `build-and-apply-worksheet` — create worksheets
- `refine-worksheet` — top-N, sort, by-field refinements on an existing sheet
- `dashboard-auto-apply` — build a dashboard from 2-6 asks in one call
- `list-worksheets` / `get-workbook-inventory` — discover existing content
- `author-calc` — create calculated fields
- `author-parameter` / `author-set` / `author-action` — parameters, sets, and worksheet actions; should precede chart authoring when the ask needs them
- `plan-dashboard-creation` / `batch-create-and-cache-sheets` — multi-sheet dashboard planning and bulk sheet caching
- `resolve-field` before shelf placement when a field name is ambiguous across datasources

**Score 5 requires:** Tool table with purpose, sequencing guidance (what order to call them), batching strategy (how to minimize calls), and awareness of dependencies (cant call get-summary-data before fields are on Detail; cant call manual shelf-authoring tools between bind-templates Call 1 and Call 2).

**10. Adaptability** — Can the skill handle meaningful variation in datasource shape?

- **1** — Handles only one narrow datasource type or field count
- **2** — Works for 2-3 variants but breaks on others
- **3** — Covers common cases (moderate field count, single datasource); unusual cases require improvisation
- **4** — Branches intelligently for most variations; few gaps
- **5** — Handles the full range: narrow vs. wide datasources, single vs. multi-table, live vs. extract, small vs. large row counts, all field types

#### TIER 6 — User Experience (Weight 0.76)

**14. User Autonomy** — Does the skill make smart defaults while preserving user control?

- **1** — Asks too many questions or makes no decisions on its own
- **2** — Some defaults but still interrupts for decisions that should be automatic
- **3** — Reasonable defaults for common cases; asks when truly ambiguous
- **4** — Smart defaults across the board; only pauses for genuinely ambiguous choices
- **5** — Proceeds confidently with excellent defaults AND explicitly offers override points (sample size, field scope, output detail level)

**12. Efficiency** — Does the skill minimize tool calls and user wait time?

- **1** — Bloated with redundant tool calls or unnecessary steps
- **2** — Some redundancy but core workflow is functional
- **3** — Lean main path; some unnecessary steps in edge case handling
- **4** — Purposeful at every step; includes batching guidance to minimize calls
- **5** — Every step serves a clear purpose; explicit batching, early-exit options, and no redundant data reads

**Desktop-specific efficiency concerns:**
- Each `get-summary-data` call has latency (especially on live connections). Batching fields together is critical.
- Unnecessary field resolution calls (resolving fields that wont be used).
- Creating scratch worksheets when an existing empty one could be reused.
- Running all checks when early checks return clean (opportunity for early exit).

**18. Scalability** — Does the skill work across the range of datasource sizes?

- **1** — Only works for one datasource size/complexity
- **2** — Works for typical cases; struggles at extremes
- **3** — Handles simple and moderate inputs; very wide or very small datasets require workarounds
- **4** — Scales well across the spectrum with minor gaps at extremes
- **5** — Explicit handling for: narrow (<10 fields), typical (10-50), wide (50-100), very wide (100+), tiny (<sample_size rows), and large datasets

#### TIER 7 — Polish (Weight 0.61)

**13. Context Leverage** — Does the skill use available workbook context rather than re-asking?

- **1** — Ignores available context entirely
- **2** — Uses direct user input only; doesnt query workbook state
- **3** — Uses immediate workbook context (fields, worksheets) but not broader state
- **4** — Leverages workbook inventory, existing calcs, and datasource metadata
- **5** — Intelligently incorporates workbook state, prior scan results (if available), existing calculated fields, and conversation history to avoid redundant work

**Desktop-specific context sources:**
- `get-workbook-inventory` output (what already exists)
- `list-available-fields` metadata (field types, names)
- Existing calculated fields (dont recreate what exists)
- Current worksheet state (whats already on shelves)

**17. Formatting Standards** — Does the skill enforce consistent output formatting?

- **1** — Formatting undefined — output shape varies randomly
- **2** — Basic structure defined but inconsistently applied
- **3** — Consistent structure; formatting details not specified
- **4** — Well-defined output format with clear templates
- **5** — Explicit report skeleton with all headers, table schemas, overflow handling, severity labels, and notes section

**Mac-safe file format check (hard cap):** Cross-platform loading is part of formatting standards — a skill that loads on PC but errors on Mac is not consistently formatted. Grep the SKILL.md and every file under `skill-expertise/` for `^---$` lines:
- SKILL.md must contain exactly **2** such lines (frontmatter open + close). More than 2 means body-level `---` horizontal rules are present, which crash Mac Studios YAML parser (confirmed Aug 2026, 42 of 53 files failed).
- Reference files without frontmatter must contain **0** such lines.
- Body-level horizontal rules must use `***` instead of `---`.

If ANY file in the skill fails this check, cap criterion #17 at **3** regardless of other formatting quality, and call the failure out explicitly in the Weaknesses section with a Rewrite Suggestion to replace body `---` with `***`.

#### TIER 8 — Ecosystem (Weight 0.46)

**15. Documentation Clarity** — Is the skill itself readable, well-organized, and maintainable?

- **1** — Chaotic, hard to parse, inconsistent structure
- **2** — Readable but poorly organized
- **3** — Logical sections but navigation is slow
- **4** — Well-organized, clear headers, easy to find any section
- **5** — Exemplary structure — reference files are cleanly separated, consistent internal format per section, easy to extend

**11. Composability** — Can the skill work alongside other Desktop skills without conflict?

- **1** — Hardcodes assumptions that break when other skills are present
- **2** — Independent but unaware of other skills
- **3** — No conflicts but no explicit composability support (baseline)
- **4** — Acknowledges adjacent skills; avoids naming conflicts; output could be consumed by other workflows
- **5** — Explicitly designed to chain: output format parseable by other skills, naming conventions avoid collisions, handoff points defined

***

### Step 3: Generate the Report

#### Header
- **Skill name**
- **Weighted Score**: X / 100 (rounded to 1 decimal)
- **Grade**: A+ (97-100), A (93-96), A- (90-92), B+ (87-89), B (83-86), B- (80-82), C+ (77-79), C (73-76), C- (70-72), D+ (67-69), D (63-66), D- (60-62), F (below 60)
- **One-line verdict**: single sentence capturing the skills core strength or weakness

#### Mutation Risk Observation (unscored)
For any skill that proposes or applies fixes to calcs, worksheets, or workbook XML: state in 1-3 sentences whether the skill requires explicit user confirmation before mutating shared workbook state, prefers additive/reversible fixes over destructive edits, and treats direct XML editing as a last resort behind supported authoring verbs. This is a qualitative flag, not a scored criterion — call it out plainly (e.g. No confirmation gate before applying fixes — flag this to the user regardless of weighted score) rather than folding it into any of the 20 weighted numbers. Omit this section entirely for skills that dont touch workbook state.

#### Without-Skill Comparison (brief)
In 2-3 sentences, describe what the Desktop agent would produce for a typical request in this skills domain WITHOUT the skill loaded. This establishes the baseline and makes the impact score tangible.

#### Category Breakdown
Present as nested bullets, one per category:
- **Category name** — Criteria included, Weighted Max, Weighted Score, %

Use these eight categories exactly:
- **Core Capability** — #3, #20 — Weighted Max 15.30
- **Quality Assurance** — #4, #6 — Weighted Max 13.74
- **Reliability & Activation** — #1, #7, #16, #19 — Weighted Max 24.44
- **Robustness** — #2, #9 — Weighted Max 10.68
- **Execution Depth** — #5, #8, #10 — Weighted Max 13.74
- **User Experience** — #12, #14, #18 — Weighted Max 11.46
- **Polish** — #13, #17 — Weighted Max 6.10
- **Ecosystem** — #11, #15 — Weighted Max 4.58

#### Detailed Scores
For each criterion (ordered by weight, highest first), present as a nested bullet record:
- **Criterion name and number** — Raw score (1-5), Weight, Weighted contribution (raw x weight)
  - One sentence justification
  - One actionable recommendation (if score < 5)

#### Top 3 Strengths
What the skill does best — patterns worth replicating.

#### Top 3 Weaknesses
Highest-impact improvements — focus on changes that would move the weighted score the most.

#### Rewrite Suggestions
If grade is C or below, provide 1-3 concrete before/after snippets showing how specific sections could be improved.

***

### Step 4: Validate the Evaluation

Before presenting the report, perform these checks:

1. **Math check**: Verify each weighted contribution = raw x weight. Verify category subtotals sum to the total weighted score. If they dont match, recompute from raw scores — do not round or silently adjust the total to fit. Flag any discrepancy found and fixed in the report.
2. **Consistency check**: Re-read each justification sentence. Does it support the score given?
3. **Spread check**: If more than 12 criteria scored the same value, recalibrate — real skills have variance.
4. **Independence check**: If you authored or recently worked on this skill, were you stricter than you would be for a strangers skill? If unsure, deduct 0.5 from your two highest scores and recompute.
5. **Calibration check**: Does the total weighted score place the skill in a believable position relative to the calibration anchors below?

***

### Step 5: Impact/Effort Improvement Matrix

Identify **every criterion that scored below 5** and classify each potential improvement:

#### Feasibility Categories

- **Ready Now** (symbol: Ready) — Can be fixed immediately using existing knowledge
- **Needs Input** (symbol: Input) — Requires answers from the user or access to Desktop API docs
- **Blocked** (symbol: Blocked) — Requires tool capabilities or platform features that dont yet exist

#### Matrix Format
Present each item as a nested bullet record:
- **Priority N — Criterion** — Raw to Target, Points Recoverable, Feasibility, Effort
  - What To Do

**Effort levels:** Low (< 15 min rewrite), Medium (15-60 min), High (60+ min)

#### Quick Wins Summary
Top items that are Ready + Low Effort.

#### Questions to Unlock Input Items
Specific questions that need answering.

#### Blocked Items
Whats blocking and whether theres a partial workaround.

#### Projected Score After Quick Wins
Calculate projected improvement.

***

### Step 6: Offer Next Steps

After delivering the full report, offer:
1. Want me to implement all the Quick Wins right now?
2. Want me to ask you the Input questions so we can unlock those improvements too?
3. Want me to grade another Desktop skill for comparison?

***

### Step 7: Implementing Improvements

When the user approves improvements:

0. **Confirm before editing.** State exactly which sections youre about to change and why. Do not modify the skills files until the user confirms — grading is read-only, but implementing improvements changes a real, shared file, so treat it with the same care as any other authoring action.
1. **Edit section-by-section** — one improvement at a time, preserving what works.
2. **Re-read the modified section** after writing to verify coherence.
3. **Offer to re-grade** after saving to confirm the score improvement.

**Implementation priority order:** Always implement in Impact/Effort Matrix order (highest weighted gap + lowest effort first).

***

## Evaluation-Process Error Handling

When the grading process itself encounters problems, use this recovery guidance:

- **Skill file unreadable** (cause: path wrong, file missing, or permission denied) — State limitation clearly. If content was pasted in conversation, grade from that. Otherwise, ask user to provide the file or paste the content.
- **Unknown tools referenced** (cause: skill names tools not in the known Desktop tool list) — Score Tool Utilization (#8) based on what IS recognizable. Note the unknowns and ask: Are these real tool names in your Desktop environment, or typos?
- **Skill exceeds context window** (cause: SKILL.md + reference files too large for single pass) — Read in sections. Note if any section was truncated. Score based on what was readable; flag partial read in the report header.
- **User disputes a score** (cause: disagreement on criterion rating) — Present the anchor definition and your justification side-by-side. Offer to rescore that specific criterion with the users reasoning factored in. Do not silently adjust other scores to compensate.

***

## Grading Principles

- **Be calibrated, not generous.** A raw 3 is the median. Desktop skills from first-time authors typically land 40-65. Experienced authors with deep Tableau knowledge produce skills in the 70-85 range. Reserve A grades (90+) for genuinely exceptional skills.
- **Weight impact over effort.** A short skill that nails Tier 1-2 criteria outscores a lengthy skill thats vague where it matters.
- **Tier 1 criteria are make-or-break.** A skill scoring 1-2 on Instruction Specificity or Measurable Impact cannot earn above a C regardless of other scores.
- **Be specific in feedback.** Add a 5-row error table covering: field not found, timeout, syntax error, disconnect, permission denied is useful. Improve error handling is not.
- **If score >= 85, collapse the matrix.** Only show items with weighted gap > 1.0.

***

## Calibration Reference Points — Desktop Skills

No Desktop skills have been empirically graded yet. Until real graded skills exist, use these as *target profiles*, not measured scores — do not present them to the user as empirical data:

- **Comprehensive + specific** — Score Range 85-92, Grade A-/A — Full workflow, locked detection thresholds/regex, explicit error playbook, pre-report validation gate, severity framework, additive-only fixes, anti-pattern list
- **Comprehensive but generic** — Score Range 78-84, Grade B+/A- — Full workflow and report template, but detection logic/thresholds left to model judgment
- **Solid workflow, thin robustness** — Score Range 68-76, Grade C+/B- — Clear happy path; missing error handling, validation gates, or locked thresholds
- **Principled but vague** — Score Range 55-65, Grade C-/D+ — States intent (check for issues, fix problems) without concrete mechanics

As real Desktop skills are graded, replace these target profiles with actual scored anchors and label them empirically scored.

**How to use this anchor:**
- If a Desktop skill youre grading has similar comprehensiveness (full workflow, error handling, detection logic, report template) but is less specific in detection patterns, it should land 78-84.
- If it has a solid workflow but lacks error handling, validation, or locked thresholds, it should land 68-76.
- If its principled but vague (check for issues, fix problems), it should land 55-65.
- As more Desktop skills are graded, additional anchors will be added here.

**Important context for Desktop skills:**
- The Desktop agent environment is experimental. Some limitations (no persistent memory, no formal API documentation, natural-language-only routing) are platform constraints, not skill deficiencies. Score these as 3 (baseline/N/A) rather than penalizing the skill for what the platform cant do.
- This carve-out applies only when the platform genuinely lacks the capability AND no workaround is documented anywhere (see the Platform Limitations Reference section above for the full rule, including when a documented-and-ignored gap should be scored on merit instead of baseline). When in doubt, ask: could a well-written skill have done better within todays platform, per `platform_limitations.md`? If yes, score on merit, not baseline.
- Desktop tools accept natural language for field references (unlike Claude tools which have strict parameter schemas). This means exact parameters in Tool Utilization (#8) looks different here: specificity is about describing the right tool for the right phase with the right intent, not about JSON parameter shapes.