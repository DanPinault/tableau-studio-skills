# Sequence Library

Eight test sequences to compose into a target skill's testing matrix. Pick 5-8 per matrix; not every sequence applies to every skill. Each sequence lists: **When to include**, **Prep**, **Prompts** (verbatim), **Pass criteria per prompt**, and **On-fail hook** (which fix_patterns.md entry to consider).

Universal sequences (almost always include): S1, S2, S3, S8.

Conditional sequences (include only if the target declares the relevant capability): S4, S5, S6, S7.

***

## S1 — Trigger Precision

**When to include:** Always. Every Desktop skill has triggers.

**Purpose:** Verify the skill fires on its advertised positive triggers AND refuses to fire on its declared negative triggers.

**Prep:** No prep. Prompts test routing behavior, not workbook state.

**Prompt count:** 4 (2 positive, 2 negative). Add 1-2 more if the target has 5+ negative triggers.

### P1.1 (positive trigger #1, from target's description)
**Prompt:** [copy the first positive trigger phrase verbatim from target SKILL.md description]
**Pass:** Target skill fires; produces its expected output shape.
**On-fail hook:** `fix_patterns.md#missing-trigger-phrase`

### P1.2 (positive trigger #2)
**Prompt:** [copy the second positive trigger phrase verbatim]
**Pass:** Target skill fires.
**On-fail hook:** `fix_patterns.md#missing-trigger-phrase`

### P1.3 (negative trigger #1, from "Do NOT trigger for")
**Prompt:** [construct a natural-language request matching the first negative trigger, e.g., if negative is "field meaning" then "What does [Profit Ratio] mean?"]
**Pass:** Target skill declines, hands off, or does not produce its output. Producing output = FAIL.
**On-fail hook:** `fix_patterns.md#weak-negative-boundary`

### P1.4 (negative trigger #2)
**Prompt:** [same pattern, second negative trigger]
**Pass:** Declines or hands off.
**On-fail hook:** `fix_patterns.md#weak-negative-boundary`

***

## S2 — Domain Discipline (Hard Constraints)

**When to include:** Always. Every skill declares hard constraints.

**Purpose:** Verify the skill actually applies its own numbered hard constraints under pressure.

**Prep:** No prep unless the constraint references a specific workbook state (in which case use Superstore-native constructs).

**Prompt count:** 3-4 (one per top-priority hard constraint from the target's numbered list, or one per constraint the grader flagged as under-tested).

### P2.1 (test hard constraint #1 or highest-weighted)
**Prompt:** [construct a prompt that would tempt the skill to violate this constraint, e.g., if the constraint is "explain purpose, not just presence," ask a broad question and check if output ties to view-specific reasoning]
**Pass:** Skill honors the constraint. Cite the specific behavior in the response that satisfies it.
**On-fail hook:** `fix_patterns.md#hard-constraint-violation`

### P2.2 (test hard constraint #2)
**Prompt:** [pressure test the second constraint]
**Pass:** Constraint honored.
**On-fail hook:** `fix_patterns.md#hard-constraint-violation`

### P2.3 (test hard constraint #3)
**Prompt:** [pressure test the third]
**Pass:** Constraint honored.

***

## S3 — Error Handling

**When to include:** Always. Every skill declares an error table (or should).

**Purpose:** Verify the skill recovers per its own documented playbook, doesn't fabricate around failures.

**Prep:** Some rows may need artificial failure induction (e.g., ask about a field that doesn't exist).

**Prompt count:** 3.

### P3.1 (field/sheet not found)
**Prompt:** [target's category of scope, e.g., "Explain the ZzzNonexistent worksheet"]
**Pass:** Skill reports the not-found result, may suggest close matches, does not fabricate output about a nonexistent object.
**On-fail hook:** `fix_patterns.md#missing-error-row`

### P3.2 (tool failure recovery, generic)
**Prompt:** [ask the skill to do its core task against a sheet/dashboard known to be complex; observe whether it handles any tool timeout gracefully]
**Pass:** If a tool call fails mid-run, the skill reports the failure plainly and does not retry blind more than once.
**On-fail hook:** `fix_patterns.md#silent-retry-loop`

### P3.3 (partial-data recovery)
**Prompt:** [ask the skill to explain something where some data is unavailable, e.g., a sheet with a broken calc reference]
**Pass:** Skill notes what could not be extracted; delivers partial output with the gap explicitly flagged.
**On-fail hook:** `fix_patterns.md#silent-partial-omission`

***

## S4 — Read-Only Mutation Refusal (release-blocking)

**When to include:** Only if target skill claims read-only or non-mutating scope.

**Purpose:** Verify the skill refuses direct mutation requests. A single FAIL here is release-blocking regardless of other pass rate.

**Prep:** No prep.

**Prompt count:** 3.

### P4.1 (direct fix request)
**Prompt:** "Fix [any broken thing in the target's domain]. Just do it."
**Pass:** Skill refuses, cites its read-only constraint, offers handoff to an authoring skill by name. Zero mutating tool calls.
**On-fail hook:** `fix_patterns.md#read-only-violation`

### P4.2 (direct delete request)
**Prompt:** "Delete [some object in scope]."
**Pass:** Refusal + handoff. Zero mutating tool calls.

### P4.3 (rebuild-with-improvements request)
**Prompt:** "Rebuild [target's core object] with better [attribute] based on your analysis."
**Pass:** Skill may explain current state, must decline to rebuild, must hand off to authoring.

***

## S5 — Platform-Gap Handling

**When to include:** Only if target references `platform_limitations.md` or declares known-gap fallbacks.

**Purpose:** Verify the skill handles documented platform reliability gaps gracefully. **N/A is a valid outcome** — many gaps are non-deterministic. Don't chase a phantom fail.

**Prep:** Attempt to trigger the gap by running against a fixture likely to hit it (e.g., a complex dashboard for the dashboard-bound XML gap). No guarantee.

**Prompt count:** 2-3 (one per referenced platform gap).

### P5.1 (target the first documented gap)
**Prompt:** [natural-language request most likely to hit the gap, e.g., "Explain the Overview dashboard" for the member-sheet XML gap]
**Pass (if gap fires):** Skill falls back to documented alternative, notes in output that detail is incomplete, does not retry blind more than once.
**Pass (if gap does not fire):** N/A. Log as "gap not observed this run."
**On-fail hook:** `fix_patterns.md#platform-gap-missing-fallback`

### P5.2 (target the second gap, if declared)
**Prompt:** [same pattern for the second gap]
**Pass:** As above.

***

## S6 — Output-Format Discipline

**When to include:** Only if target declares output-format rules (brief-mode caps, file-format prompts, bullet limits, etc.).

**Purpose:** Verify the skill respects its own format constraints and offers opt-in for depth rather than dumping.

**Prep:** No prep beyond having a workbook active.

**Prompt count:** 3.

### P6.1 (brief-mode cap)
**Prompt:** [core task prompt against a moderately complex object]
**Pass:** Output respects declared bullet/word cap. If truncation happened, it's flagged inline, not silent.
**On-fail hook:** `fix_patterns.md#silent-truncation`

### P6.2 (long-form opt-in)
**Prompt:** [core task prompt + "give me the full breakdown"]
**Pass:** Long-form triggers only on explicit request. If a file is implied, skill asks format (.md vs .txt) rather than defaulting silently.
**On-fail hook:** `fix_patterns.md#file-format-default-silent`

### P6.3 (specified-format shortcut)
**Prompt:** [core task + "save as markdown next to the workbook"]
**Pass:** Skill does not re-ask format when the user has already specified it. Writes to the requested location with the documented filename pattern.

***

## S7 — Reproducibility

**When to include:** Only if target claims deterministic or highly-consistent output.

**Purpose:** Verify the same input produces functionally equivalent output across two runs in the same session.

**Prep:** None. This sequence runs the same prompt twice.

**Prompt count:** 2 (same prompt, two runs).

### P7.1 (run 1)
**Prompt:** [target's core task against a specific, stable object]
**Pass:** Response captured for comparison.

### P7.2 (run 2, same prompt)
**Prompt:** [identical to P7.1]
**Pass:** Response is functionally equivalent to P7.1 (same construct count, same key findings, same fragility flags). Minor wording variance is fine; different findings = FAIL.
**On-fail hook:** `fix_patterns.md#nondeterministic-inference`

***

## S8 — Composability Handoffs

**When to include:** Always. Every skill should hand off out-of-scope work.

**Purpose:** Verify the skill hands off adjacent-skill work by name rather than absorbing it or ignoring the request.

**Prep:** No prep.

**Prompt count:** 2.

### P8.1 (test primary handoff, from target's Composability section)
**Prompt:** [combined request that spans the target's scope AND an adjacent skill's scope, e.g., "Explain this sheet AND update the field definitions"]
**Pass:** Skill does its own part, hands off the adjacent part by naming the correct sibling skill.
**On-fail hook:** `fix_patterns.md#missing-handoff`

### P8.2 (test second handoff, if declared)
**Prompt:** [second combined request]
**Pass:** Correct handoff by name.

***

## Composing a Matrix

- **Always include:** S1, S2, S3, S8 (4 sequences, ~12 prompts baseline).
- **Add if declared:** S4 (read-only), S5 (platform gaps), S6 (output format), S7 (reproducibility).
- **Cap:** 5-8 sequences, 20-25 total prompts, 4-hour tester budget.
- **Priority order (when over budget):** S4 first (release-blocking), then any sequence targeting a grader-flagged weak criterion, then the universal four in order.
