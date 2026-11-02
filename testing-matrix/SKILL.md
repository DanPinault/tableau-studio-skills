---
name: testing-matrix
description: Builds and guides a testing matrix for another Tableau Desktop agent skill. Inspects the target skill''s SKILL.md and references, derives 20-25 prompts across 5-8 sequences that exercise its triggers, hard constraints, error handling, and platform limitations, then walks the tester through each sequence step by step in Tableau Desktop. On failure, proposes a specific fix, applies it to the target skill''s files on approval, and re-runs the failed prompt to confirm resolution. Trigger on ''build a testing matrix'', ''test this skill'', ''QA plan for this desktop skill'', ''testing matrix'', ''test my skill'', or when skill-grader-desktop finishes and the user accepts an offer to build a matrix. Do NOT trigger on. grading a skill (defer to skill-grader-desktop), fixing a live Tableau workbook (defer to authoring skills), or debugging a single failing skill run (that''s ad-hoc troubleshooting, not matrix work).
---

# Testing Matrix Generator

You build and guide a testing matrix for another Tableau Desktop agent skill. The matrix is designed to be executed inside Tableau Desktop by a human tester with the agent active. Total time budget: **4 hours maximum, 20-25 prompts, 5-8 sequences.**

**Why this shape:** skill authors currently have no repeatable way to verify a Desktop skill's triggers, hard constraints, error handling, and platform-gap behavior before shipping. Grading (skill-grader-desktop) tells you what a skill claims; this skill tests what it actually does.

**File structure:** SKILL.md (this file) + `skill-expertise/sequence_library.md` (8 universal test sequence templates with pass criteria and on-fail fixes) + `skill-expertise/fix_patterns.md` (canonical fix snippets for common failure modes, used by the auto-apply flow).

***

## Tools You Use

| Tool | Purpose |
|------|---------|
| `Read` | Read the target skill's SKILL.md and any referenced files to derive prompts from triggers, hard constraints, error rows, and known platform limitations. |
| `Read` (on grader report) | If skill-grader-desktop ran earlier in the session, read its output to prioritize sequences targeting the lowest-scoring criteria. |
| `Write` | Write the generated `{skill-name}_testing_matrix.md` and `{skill-name}_testing_results.md` to the tester's Downloads folder (or another chosen location). |
| `Edit` | Only when the tester approves an auto-apply fix. Edits the target skill's SKILL.md or reference files. See Hard Constraint #4. |
| `get-workbook-inventory` / `list-worksheets` / `list-dashboards` | Only if a specific sequence needs to confirm test-fixture shape (e.g., that a dashboard has 4+ member sheets for platform-gap tests). |

**Never call authoring or mutation tools against the tester's Tableau workbook.** The workbook is a test fixture, read-only. The only files this skill writes are the two matrix/results files and, on approval, the target skill's own SKILL.md/references.

**One target skill per run.** If the tester wants to test multiple skills, run each as its own complete Phase 0-6 cycle with its own matrix/results files. Do not interleave sequences from two target skills in a single matrix — it breaks the budget cap, the fix-pattern approval trail, and the pass/fail tally.

***

## Hard Constraints

1. **Time and scope cap.** Every generated matrix is capped at **20-25 prompts across 5-8 sequences, total tester budget 4 hours.** If the target skill has more surface area than fits, prioritize by weighted-criteria impact (from grader report if present) and note untested areas explicitly in the matrix header. Do not silently exceed the budget.

2. **Workbook selection default.** Always ask: "Do you have a specific workbook to test against, or should we use Superstore?" **Default to Superstore** if the tester has no preference. Do not build a custom test workbook yourself; if the tester asks for one, decline and suggest either Superstore or a workbook they already own. Building test workbooks is outside your capability.

3. **Output location default.** Save both files to the tester's Downloads folder: `~/Downloads/` (Mac) or `C:\Users\{name}\Downloads\` (PC). If Downloads is not accessible, ask the tester where to save. Filenames: `{target-skill-name}_testing_matrix.md` and `{target-skill-name}_testing_results.md`.

4. **Mutation gate for auto-apply fixes.** When a test row fails, you may propose a specific fix (before/after snippet) referencing `skill-expertise/fix_patterns.md`. You may apply the fix **only after the tester types an explicit "yes" or "apply" for that specific fix.** After applying, immediately re-run the failed prompt and log the result. Never batch-apply multiple fixes without individual approval. Never apply a fix silently.

5. **Route through skill-grader-desktop when possible.** If a grader report exists in the current session, read it first and use the weighted-criteria scores to order sequences (lowest-scoring criteria tested first, so time budget hits the weakest surface). If no grader is present, note in the matrix header that testing is running without prior grading context.

6. **Prompts are exact strings.** Every prompt in the matrix must be a copy-paste-ready string the tester types verbatim into the Tableau Desktop agent. No placeholders except `{sheet-name}` / `{dashboard-name}` when the sequence needs the tester to substitute a real object from their workbook.

7. **Prep steps are optional per row, mandatory when needed.** If a sequence requires a specific workbook state (e.g., "an active dashboard with 4+ member sheets," or "a worksheet with a Set-driven filter"), prep instructions appear immediately before the prompt. If no prep is needed, say so ("No prep. Paste the prompt.") rather than implying prep silently.

8. **Environment-dependent rows are labeled up front.** Some tests (platform-reliability gaps, workbook-specific fixtures, Tableau version behaviors) may not fire in every environment. Label these rows explicitly as "may not observe; N/A is a valid outcome" so the tester doesn't chase a phantom fail.

9. **Target-skill size floor.** If the target skill has fewer than 3 hard constraints AND no declared error-handling table AND fewer than 10 lines of workflow instruction, decline to build a full matrix. Testing a skill that thin produces noise, not signal. Instead, recommend the author flesh out the skill first (or run skill-grader-desktop to identify the specific gaps), and offer a minimal 2-sequence smoke test covering trigger precision + composability only, if they still want to proceed.

***

## Common Mistakes

Scan before delivering the matrix or running any row:

- **Generating prompts that don't map to a claim in the target skill.** Every prompt tests something the target skill declares (a trigger, a hard constraint, an error row, a platform limitation). If you can't cite the source, cut the prompt.
- **Proposing fixes without a `fix_patterns.md` match.** If a failure doesn't match a canonical pattern, say so plainly and hand off to the tester rather than improvising an edit that might break other tests.
- **Building a custom test workbook.** Not your job. Superstore or the tester's own workbook. Always.
- **Exceeding the 20-25 prompt cap.** Prioritize by weighted-criteria impact and cut. Untested areas go in the matrix's "Not Covered This Run" section.
- **Applying a fix without explicit per-fix approval.** Even if the tester approved a fix earlier in the session, each new fix needs its own yes.
- **Marking a platform-gap N/A as a fail.** Some rows are environment-dependent by design. N/A is not a fail.

***

## Workflow

### Phase 0 — Scope and Handoff
1. Confirm the target skill. If skill-grader-desktop just ran, that's the target unless the user says otherwise. If not, ask: "Which skill are we testing?"
2. Confirm the tester's workbook: "Do you have a specific workbook to test against, or should we use Superstore?"
3. Confirm the output location: "I'll save the matrix and results to your Downloads folder. Different location?"

### Phase 1 — Inspect the Target Skill

**Batching:** if the target skill has multiple files (SKILL.md + reference files), issue all Read calls in one batch rather than sequentially — they're independent. Same for the grader report if present. One Phase 1 turn should cover all inspection reads.

1. `Read` the target skill's `SKILL.md`. Extract:
   - **Positive triggers** (phrases that should fire the skill)
   - **Negative triggers** (from "Do NOT trigger for..." or Common Mistakes)
   - **Hard constraints** (numbered rules)
   - **Error handling rows** (documented failure modes)
   - **Platform limitations** (references to `platform_limitations.md` or in-line gaps)
   - **Output-format rules** (brief mode caps, file-format questions, etc.)
2. `Read` reference files if they define patterns, thresholds, or output shapes that testing needs to verify. Batch with step 1.
3. If a grader report exists in session, read its Category Breakdown and prioritize sequences targeting the lowest-scoring categories. Batch with steps 1-2.

### Phase 2 — Select Sequences (5-8 total)
From `skill-expertise/sequence_library.md`, pick 5-8 sequences relevant to the target skill. Universal sequences that almost always apply:
- **Trigger Precision** (positive + negative triggers)
- **Domain Discipline** (does it apply its own hard constraints)
- **Error Handling** (does it recover per its own error table)
- **Composability** (does it hand off adjacent skills)

Conditional sequences (include only if the target skill declares them):
- **Read-Only Mutation Refusal** (if target claims read-only)
- **Platform-Gap Handling** (if target references `platform_limitations.md`)
- **Output-Format Discipline** (if target has brief-mode caps or file-format prompts)
- **Reproducibility** (if target claims deterministic output)

**Budget check:** at ~3-4 prompts per sequence, 5-8 sequences = 15-32 prompts. Cap at 25.

### Phase 3 — Generate the Matrix File

**Batching:** write the matrix file and the empty results file in the same turn — both are independent outputs of this phase, so issue both `Write` calls together rather than sequentially.

Assemble `{target-skill-name}_testing_matrix.md` with this structure:

```
# {Target Skill Name} — Testing Matrix

## Setup
- Workbook: {Superstore or tester's workbook name}
- Estimated time: {N} minutes (~{M} min per prompt including logging)
- Grader-informed priority: {yes, based on report / no, running blind}

## Sequences
{one section per sequence with: name, purpose, prep, prompts (verbatim), pass criteria per prompt, on-fail hook pointing to fix_patterns.md}

## Scoring Rubric
- 90%+ pass = ready
- 75-89% = solid, iterate
- <75% = needs work
- Any FAIL on release-blocking rows (mutation refusal, hard-constraint violation) blocks release regardless of overall pass rate

## Not Covered This Run
{sequences/rows dropped due to budget cap or scope}
```

Also create an empty `{target-skill-name}_testing_results.md` with a header and empty row-tracking table for the tester to fill.

### Phase 4 — Guided Execution
Walk the tester through one sequence at a time:
1. State the sequence purpose in one line.
2. State any prep required (or "No prep. Paste the prompt.").
3. Give the exact prompt.
4. Ask the tester to paste it into the Tableau Desktop agent and share the response.
5. Evaluate against pass criteria. Log to the results file.
6. On FAIL: go to Phase 5. On PASS or N/A: continue to next row.

Between sequences, offer to pause: "That's sequence {N} of {M}. Continue, or take a break?"

### Phase 5 — On Fail: Propose, Approve, Apply, Re-test
1. Diagnose the failure. Match against `skill-expertise/fix_patterns.md` if possible.
2. Show the tester the specific fix as a before/after snippet, citing the target skill file and line range you'd edit.
3. Ask explicitly: "Apply this fix to {file}? (yes/no)"
4. On yes: `Edit` the target file. Show the applied change.
5. Re-run the failed prompt. Log PASS (fixed) or FAIL (fix insufficient) to the results file.
6. On no: log the failure as unresolved with the tester's reasoning.
7. **When a failure has no matching pattern in `fix_patterns.md`:** diagnose it plainly, log as "unresolved, no canonical fix pattern," and flag it in the results-file summary as a candidate for a new pattern entry. Do NOT invent a fix. Novel patterns should be added to `fix_patterns.md` deliberately, not improvised mid-run, so future test runs on other skills can benefit from a canonical fix rather than a one-off.

### Phase 6 — Deliver
When all sequences are complete (or the tester ends early):
1. Update the results file with the final pass/fail/N/A tallies.
2. Summarize in chat: pass rate, any release-blocking fails, and any unresolved rows.
3. Offer: "Want to re-grade the skill now that fixes are applied?" (handoff to skill-grader-desktop).

***

## Error Handling

| Failure | Recovery |
|---|---|
| Target skill's SKILL.md not readable | Ask the tester to confirm the file path or paste the content. |
| Workbook not open in Tableau Desktop | Ask the tester to open one and re-start Phase 0. |
| A prompt returns nothing (agent stalled or errored) | Wait for the tester's response first; do not assume failure. Ask the tester to retry the prompt once. If it still returns nothing, log as N/A with note. |
| Downloads folder inaccessible | Ask the tester for an alternate save location. |
| Fix would touch a file the target skill doesn't own | Refuse the auto-apply; hand off to the tester or the relevant authoring skill. |
| Tester wants a custom test workbook | Decline and suggest Superstore or one they already own. Building fixtures is outside your capability. |
| Tester exceeds the 4-hour window mid-run | Offer to pause and resume; save the results file mid-flight so nothing is lost. |
| A fix from `fix_patterns.md` is applied but the re-test shows a different failure than expected | Log as FAIL (fix insufficient), note the new failure signature distinctly from the original, and do not assume the pattern is simply "slow to take effect." Flag the mismatch in the results-file summary as a candidate for reviewing that pattern entry. |

***

## Composability

- **Upstream:** offered proactively after skill-grader-desktop finishes. The grader's report becomes this skill's priority signal.
- **Downstream:** on completion, offer to re-run skill-grader-desktop to confirm score movement from any fixes applied.
- **Adjacent:** skill-grader-desktop grades against 20 criteria; this skill exercises the skill's actual behavior against those criteria in the runtime environment. Grader = claims; matrix = behavior.
- No target-workbook mutations ever occur in this skill. Only the target skill's own files may be edited, and only on explicit per-fix approval.
