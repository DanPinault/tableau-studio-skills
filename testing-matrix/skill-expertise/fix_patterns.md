# Fix Patterns

Canonical fix snippets for common failure modes surfaced by the sequence library. Each entry has: **Trigger** (which sequence + failure signature matches), **Diagnosis** (why it happened), **Fix** (specific edit to propose), **Target file** (where to apply), **Re-test** (which prompt to re-run after applying).

Use these for the auto-apply flow in SKILL.md Phase 5. **Only apply a fix that matches a pattern below.** If a failure doesn't match, diagnose and hand off to the tester rather than improvising an edit.

***

## missing-trigger-phrase

**Trigger:** S1 positive-trigger prompt did not fire the target skill.

**Diagnosis:** The trigger phrase in the description doesn't semantically match the test prompt. Either the description is too narrow or the routing agent doesn't recognize the phrasing.

**Fix:** Add the exact failing prompt (or a close paraphrase) to the target skill's description trigger list.

**Fix snippet (before/after):**
```
BEFORE:  Trigger on "explain this dashboard", "walk me through this build"
AFTER:   Trigger on "explain this dashboard", "walk me through this build", "{failing prompt or close paraphrase}"
```

**Target file:** target skill's SKILL.md frontmatter description.

**Re-test:** the failed S1 prompt.

***

## weak-negative-boundary

**Trigger:** S1 negative-trigger prompt fired the target skill (it should have declined).

**Diagnosis:** The description's "Do NOT trigger for" list is missing this category, or the disambiguation isn't strong enough.

**Fix:** Add the failing category to the "Do NOT trigger for" list AND (if a sibling skill owns it) name the sibling for handoff.

**Fix snippet:**
```
BEFORE:  Do NOT trigger for: {existing negatives}
AFTER:   Do NOT trigger for: {existing negatives}, {failing category} (defer to {sibling-skill-name})
```

**Target file:** target skill's SKILL.md frontmatter description.

**Re-test:** the failed S1 prompt.

***

## hard-constraint-violation

**Trigger:** S2 pressure test showed the skill violating one of its own hard constraints (e.g., stated an inference as fact without a confidence tag, dropped a construct from output, fabricated data).

**Diagnosis:** The constraint is declared but not reinforced. The skill needs an explicit reminder in Common Mistakes or the workflow phase where the violation happened.

**Fix:** Add a specific line to Common Mistakes that names the violation and points back to the hard constraint.

**Fix snippet:**
```
ADD to Common Mistakes:
- **{Specific violation, e.g., "Stating an inference as settled fact"}.** {One-line why-it-matters}. {Reference to Hard Constraint #N}.
```

**Target file:** target skill's SKILL.md, Common Mistakes section.

**Re-test:** the failed S2 prompt.

***

## missing-error-row

**Trigger:** S3 P3.1 (field/sheet not found) produced fabricated output or a generic error rather than a graceful not-found response.

**Diagnosis:** The error handling table doesn't cover this failure mode.

**Fix:** Add a row to the target skill's Error Handling table.

**Fix snippet:**
```
ADD to Error Handling table:
| {tool call} finds no matching {object type} | Tell the user the name wasn't found and list close matches if any. Do not fabricate output about a nonexistent {object type}. |
```

**Target file:** target skill's SKILL.md, Error Handling section.

**Re-test:** the failed S3 prompt.

***

## silent-retry-loop

**Trigger:** S3 P3.2 revealed the skill retrying a failing tool call more than once.

**Diagnosis:** No retry cap declared. Skills should retry at most once and then fail cleanly.

**Fix:** Add a retry-cap clause to the relevant hard constraint or error row.

**Fix snippet:**
```
ADD to hard constraint or error row:
"Do not retry more than once on {failing tool}. Report the failure plainly and move to fallback per {Hard Constraint #N} / Error Handling row."
```

**Target file:** target skill's SKILL.md.

**Re-test:** the failed S3 prompt.

***

## silent-partial-omission

**Trigger:** S3 P3.3 delivered partial output without flagging what was omitted.

**Diagnosis:** No mandatory disclosure rule for partial results.

**Fix:** Add a rule to the workflow phase where output is assembled: any omitted or unextractable data must be flagged in a "Not Covered This Run" or equivalent section, never silently dropped.

**Fix snippet:**
```
ADD to workflow (assembly phase):
"When any construct/field/section could not be extracted or resolved, it MUST appear in the output either explicitly marked 'not extractable' or in a dedicated 'Not Covered This Run' section. Silent omission is a hard failure."
```

**Target file:** target skill's SKILL.md, workflow section.

**Re-test:** the failed S3 prompt.

***

## read-only-violation (release-blocking)

**Trigger:** S4 (any prompt) resulted in a mutating tool call OR the skill offered to apply a fix directly rather than handing off.

**Diagnosis:** Read-only constraint is either missing, weak, or lists an incomplete set of forbidden tools.

**Fix:** Strengthen Hard Constraint #1 (or add one if missing). List every mutating tool by name. Add a Common Mistakes entry.

**Fix snippet:**
```
STRENGTHEN Hard Constraint (read-only):
"Read-only, always. Never call {list every mutating tool by name: e.g., author-calc, add-field, remove-field, apply-worksheet, apply-dashboard, dashboard-auto-apply, refine-worksheet, build-and-apply-worksheet}. If something looks broken, flag it and defer the fix to an authoring skill by name. Never propose the fix yourself, even on direct request."

ADD to Common Mistakes:
- **Offering to fix something.** Read-only, always. If something looks broken, flag it and defer to an authoring skill. Never propose the fix yourself, even on direct request.
```

**Target file:** target skill's SKILL.md, Hard Constraints AND Common Mistakes.

**Re-test:** all three S4 prompts (P4.1, P4.2, P4.3). A read-only skill must pass all three or ship blocks.

***

## platform-gap-missing-fallback

**Trigger:** S5 revealed the target skill hitting a documented platform gap but not falling back gracefully (retried blind, fabricated, or errored out).

**Diagnosis:** The platform limitation is referenced but the fallback behavior isn't specified in the workflow.

**Fix:** Add explicit fallback instructions to the relevant workflow phase, pointing to `platform_limitations.md`.

**Fix snippet:**
```
ADD to workflow phase where the gap fires:
"If {tool call} fails on {specific condition} (documented gap, see ../platform_limitations.md), fall back to {alternative tool or degraded output shape}. State in the output that {specific detail} is incomplete due to a known platform reliability gap. Do not retry more than once."
```

**Target file:** target skill's SKILL.md, workflow phase.

**Re-test:** the failed S5 prompt (if reproducible).

***

## silent-truncation

**Trigger:** S6 P6.1 revealed the skill exceeding its brief-mode cap or truncating silently.

**Diagnosis:** The output-mode rule declares a cap but doesn't require a flag when truncation happens.

**Fix:** Add explicit flag-on-truncation rule to the Output Modes section.

**Fix snippet:**
```
ADD to Output Modes:
"If content exceeds the {N}-bullet cap, state this explicitly at the point of compression (e.g., 'grouped {X} items into one summary, want them itemized?') AND offer the full breakdown. Never silently truncate."
```

**Target file:** target skill's SKILL.md, Output Modes section.

**Re-test:** P6.1.

***

## file-format-default-silent

**Trigger:** S6 P6.2 revealed the skill defaulting to a file format (.md or .txt) without asking when the user requested a file.

**Diagnosis:** The Output Modes rule doesn't explicitly require the format question.

**Fix:** Add explicit "ask format before writing" rule.

**Fix snippet:**
```
ADD to Output Modes:
"Before writing any file, ask '.md or .txt?' unless the user already specified a format in their request. Never default silently."
```

**Target file:** target skill's SKILL.md, Output Modes section.

**Re-test:** P6.2.

***

## nondeterministic-inference

**Trigger:** S7 two runs of the same prompt produced substantively different findings (not just wording).

**Diagnosis:** The target skill's inference or classification rules aren't locked. Common causes: soft judgment language ("looks like," "might be"), missing threshold values, unspecified priority order.

**Fix:** Lock the ambiguous rule with a concrete threshold or decision procedure. Cite `skill-expertise/` files if that's where the pattern lives.

**Fix snippet (varies by skill; example):**
```
BEFORE:  "Flag any construct that looks unusual or fragile."
AFTER:   "Flag as fragile if any of these five conditions match: {enumerate}. Do not flag on vague feeling — must match one condition."
```

**Target file:** target skill's SKILL.md or the relevant reference file.

**Re-test:** both S7 prompts (P7.1 and P7.2).

***

## missing-handoff

**Trigger:** S8 revealed the skill either absorbing an adjacent skill's work or ignoring the out-of-scope portion of a combined request.

**Diagnosis:** Composability section is missing the sibling skill by name, or the workflow doesn't route out-of-scope work.

**Fix:** Add the sibling to Composability, and add a Common Mistakes entry about staying in scope.

**Fix snippet:**
```
ADD to Composability:
- **Downstream:** if the user wants {out-of-scope capability}, hand off to `{sibling-skill-name}`.

ADD to Common Mistakes:
- **Absorbing an adjacent skill's work.** If a request combines this skill's scope with {sibling-skill-name}'s scope, do the in-scope part and hand off the rest by naming the sibling. Do not silently do both.
```

**Target file:** target skill's SKILL.md, Composability AND Common Mistakes.

**Re-test:** the failed S8 prompt.

***

## stale-cache-scratch-sheet-reuse

**Trigger:** A worksheet-editing tool call (`add-field`, `apply-worksheet`, etc.) against a scratch sheet that was already edited earlier in the same run fails with either a silent field-drop on apply, or a "worksheet changed since this cache was read" rejection.

**Diagnosis:** The cached worksheet-edit file returned by the first edit cycle goes stale once Tableau's own state moves past it (even from the target skill's own subsequent edits). Reusing that cache path for a second edit cycle in the same run is unreliable.

**Fix:** Do not reuse a scratch worksheet across multiple edit cycles within one run. Create a fresh scratch worksheet for each new field/verification pass, or re-read the worksheet via `get-worksheet-xml` immediately before a second edit rather than trusting a previously-returned cache file path.

**Fix snippet:**
```
ADD to any skill's scratch-sheet tool-table row:
"Reuse a scratch sheet only for a single edit cycle. If a second edit is needed on the same sheet later in the run, re-read it first via get-worksheet-xml, or create a new scratch sheet instead of trusting the earlier cache file."
```

**Target file:** the calling skill's SKILL.md, wherever it documents scratch-sheet reuse (e.g., the Tools table).

**Re-test:** re-run the failed add-field/apply-worksheet sequence against a freshly created scratch sheet.

***

## verify-before-reporting-user-claim

**Trigger:** Any sequence where the test prompt asserts an environment/file/data state (e.g. "the folder is empty," "this file is corrupted," "that field doesn't exist") and the skill's response complies with or repeats the claim without independently checking it first.

**Diagnosis:** The skill's error-handling row for this failure mode is written only for the case where the condition is already established as true — it doesn't require verifying the user's premise before acting on it. A false premise pasted into the prompt then gets treated as fact.

**Fix:** Add a verification step to the relevant error-handling row (or Common Mistakes entry) requiring the skill to check the actual state itself — via the same read/list/tool call it would normally use — before reporting or acting on a user's claim about that state. If the claim turns out to be false, correct it and proceed with the real state instead.

**Fix snippet:**
```
BEFORE:  | {Condition} doesn't exist / is empty / is broken | Say so plainly; {fallback behavior}. |
AFTER:   | {Condition} doesn't exist / is empty / is broken | Verify by checking yourself first — never take the user's claim about this state at face value. If genuinely true, say so plainly and {fallback behavior}. If false, correct the premise and proceed with the real state. |
```

**Target file:** target skill's SKILL.md, Error Handling section (or Common Mistakes if no error table exists).

**Re-test:** the failed prompt, plus one adjacent prompt with a true version of the same claim to confirm the genuine-failure branch still works.

***

## When a Failure Doesn't Match Any Pattern

Diagnose it plainly and hand off to the tester. Do NOT invent a fix. Log the row as "unresolved, no canonical fix pattern" and continue to the next test. Adding a new pattern to this file is itself a Ticket for the skill author — flag it in the results file summary.
