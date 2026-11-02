# Skill Grader (Desktop Edition)

Evaluates the effectiveness of a Tableau Desktop agent skill against 20 weighted criteria adapted for the Desktop tool environment. Reads the SKILL.md, all supporting files, and the platform limitations reference. Returns a weighted score out of 100, a letter grade, category breakdowns, and an Impact/Effort matrix showing which improvements would move the score most.

**Example:** "Grade this skill" returns a header (Skill name, Weighted Score: 82.4/100, Grade B+, one-line verdict), Mutation Risk Observation if the skill touches workbook state, Without-Skill Comparison, Category Breakdown, Detailed Scores per criterion, Top 3 Strengths, Top 3 Weaknesses, Rewrite Suggestions (if grade is C or below), and an Impact/Effort Improvement Matrix showing exactly which changes recover the most points.

***

## What it does

Scores a skill on 20 weighted criteria across 8 categories: Core Capability, Quality Assurance, Reliability & Activation, Robustness, Execution Depth, User Experience, Polish, Ecosystem. Weighted score maxes at 100.00, letter grades from F to A+.

Every criterion has a 1-5 scoring anchor with Desktop-specific notes. Tier 1 criteria (Instruction Specificity, Measurable Impact) are make-or-break — a skill scoring 1-2 on either cannot earn above a C regardless of other scores.

Reads `platform_limitations.md` at the skills/ root before scoring. Skills that correctly design around confirmed platform gaps get credit as a strength. Skills that silently ignore documented gaps get capped at 3 on Domain Accuracy and Output Quality Floor with the specific ignored gap named in the justification.

Runs a Post-Instruction Gate at criterion #17 (Formatting Standards) that hard-caps at 3 for Mac-unsafe formatting (body-level `---` dividers or `description: >-` block scalars) or wrapping-quote violations on the YAML `name`/`description` values.

## When to use it

- "Grade this desktop skill"
- "How's this skill looking, quick grade"
- "Score this Tableau skill"
- "Audit the skill I just wrote for Desktop"
- "Where would I gain the most points on this skill"

## When NOT to use it

- Not for Claude or Cowork skills that run in the Claude desktop app rather than inside Tableau (use skill-grader instead)
- Not for code review or general code quality assessment
- Not for debugging skill execution failures (that's runtime troubleshooting, not effectiveness scoring)
- Not for troubleshooting whether a skill is firing correctly (that's a routing/description issue; use prompt-coach)
- Not for grading general prompts that aren't structured as skills

## How to trigger it

- "Grade this desktop skill"
- "Evaluate my desktop skill"
- "Score this tableau skill"
- "Desktop skill audit"
- "Skill-grader-desktop"

## What you'll need

- The skill to grade, either as a folder path or pasted directly into chat
- The MCP tools Skill Grader (Desktop Edition) uses: `Read`, `Glob`, Memory index files
- Access to `platform_limitations.md` at the skills/ root (Skill Grader reads it before scoring; it catalogs confirmed Desktop tool-surface gaps and shapes the "designed around a gap" vs "ignored a gap" scoring)
- The MEMORY.md index (checked for any prior feedback about the specific skill by name)

## Example walkthrough

**Input:** "Grade my new orphan-calc-finder skill."

**Output:**

```
Skill: orphan-calc-finder
Weighted Score: 78.6 / 100
Grade: B+
Verdict: Strong workflow and reproducibility, held back by thin error
handling and no acknowledgment of the sets-invisibility gap.

Mutation Risk Observation
  No workbook mutation. Read-only skill. No confirmation gate needed.

Without-Skill Comparison
  Without this skill, the Desktop agent would enumerate calculated
  fields via list-available-fields but wouldn't systematically cross-
  reference against every worksheet's shelf placements. The skill
  adds the cross-reference logic and the "used only in tooltips"
  disambiguation.

Category Breakdown
  - Core Capability          - #3, #20  - 15.30 max - 12.24 - 80%
  - Quality Assurance        - #4, #6   - 13.74 max - 11.68 - 85%
  - Reliability & Activation - #1,#7,#16,#19 - 24.44 max - 20.23 - 83%
  - Robustness               - #2, #9   - 10.68 max -  8.02 - 75%
  - Execution Depth          - #5,#8,#10 - 13.74 max -  9.62 - 70%
  - User Experience          - #12,#14,#18 - 11.46 max - 9.55 - 83%
  - Polish                   - #13, #17 -  6.10 max -  4.88 - 80%
  - Ecosystem                - #11, #15 -  4.58 max -  4.12 - 90%

Detailed Scores (top 3 by weight):
  #3 Instruction Specificity - Raw 4, Weight 1.53, Contribution 6.12
     Locked detection logic (calc used = placed on any shelf/encoding).
     Would score 5 with an explicit threshold for "low-visibility use"
     (e.g. tooltip-only).
  #20 Measurable Impact - Raw 4, Weight 1.53, Contribution 6.12
     Clear improvement over the without-skill baseline.
  #6 Output Quality Floor - Raw 4, Weight 1.37, Contribution 5.48

Top 3 Weaknesses:
  1. #5 Error Handling (Raw 3) - covers 2 common failures; misses RLS
     denial, disconnected datasource mid-scan, and dashboard-bound
     sheet XML gap.
  2. #16 Domain Accuracy (Raw 3) - doesn't mention that Sets are
     invisible to field-resolution tools per platform_limitations.md,
     so any calc referencing a Set may be incorrectly flagged as
     orphan.
  3. #10 Adaptability (Raw 3) - no branching for multi-datasource
     workbooks.

Impact/Effort Improvement Matrix
  Priority 1: #16 Domain Accuracy: Raw 3 -> 4. Points Recoverable: 1.22.
    Ready. Low Effort. Add a Sets-invisibility note to the workflow.
  Priority 2: #5 Error Handling: Raw 3 -> 4. Points Recoverable: 0.92.
    Ready. Medium Effort. Add 3 error rows.

Projected Score After Quick Wins: 80.7 (A- reachable with all Ready
items).
```

## What you get back

- **Weighted score out of 100** with letter grade (F through A+) and a one-line verdict.
- **Mutation Risk Observation** for any skill that touches workbook state (calcs, worksheets, XML). Unscored qualitative flag, called out plainly rather than folded into a criterion.
- **Without-Skill Comparison** describing what the Desktop agent would produce in this skill's domain without the skill loaded. Makes the Measurable Impact score tangible.
- **Category Breakdown** across 8 categories with each category's max, actual, and percentage.
- **Detailed Scores** per criterion, ordered by weight highest-first, each with a one-sentence justification and one actionable recommendation.
- **Top 3 Strengths** — patterns worth replicating in other skills.
- **Top 3 Weaknesses** — highest-impact improvements.
- **Rewrite Suggestions** with concrete before/after snippets if grade is C or below.
- **Impact/Effort Improvement Matrix** identifying every criterion below 5 and classifying each as Ready Now, Needs Input, or Blocked, with effort estimates (Low/Medium/High) and points recoverable.
- **Quick Wins Summary, Questions to Unlock Input Items, Blocked Items, and Projected Score After Quick Wins.**
- **Independence disclosure** at the top of the report if the grader participated in creating or recently working on the skill being evaluated.
- **Modes:** Full report (default) or Quick Grade (Header + Category Breakdown + Quick Wins only).

## Limitations

- **Independence caveat.** If the grader authored or recently worked on the skill, it discloses this at the top of the report and scores with extra scrutiny. Independence is asserted, not guaranteed by tooling.
- **Calibration anchors are target profiles, not empirical.** No Desktop skills have been empirically graded yet as reference points. Score ranges (85-92 for comprehensive + specific, 78-84 for comprehensive but generic, etc.) are target profiles until real graded skills accumulate.
- **Reads what the file surface exposes.** If a supporting file is genuinely load-bearing but the grader can't access it, it flags "partial read" in the report header rather than pretending it scored the missing content.
- **Not a runtime executor.** Skill Grader reads the skill file; it doesn't execute the skill against a real workbook. A skill can score well on paper and still misbehave at runtime for reasons outside the scoring rubric.
- **Not a code review tool.** Prose, structure, and behavior are in scope; underlying code quality of any embedded scripts isn't.
- **Not for firing/routing issues.** A skill that scores well but doesn't fire on real prompts has a description problem, which is prompt-coach territory, not grading.
- **Mac-safe formatting hard cap on criterion #17.** Any file in the skill with body-level `---` dividers or a `description: >-` block scalar caps #17 at 3 regardless of other formatting quality. Same cap applies to wrapping-quote violations on YAML `name`/`description` values.

## Troubleshooting

- **"I got a B+ but I disagreed with the score on criterion #5."** Present the anchor definition and your justification side by side. Skill Grader will re-score that specific criterion with your reasoning factored in. It will not silently adjust other scores to compensate.
- **"The math on the category breakdown doesn't add up."** Verify each weighted contribution equals raw × weight, and that category subtotals sum to the total. Skill Grader runs this math check before returning the report; if there's a discrepancy, ask it to recompute from raw scores.
- **"Every criterion scored the same value."** Real skills have variance. If more than 12 criteria scored the same, Skill Grader recalibrates automatically. If it didn't, ask for a spread check.
- **"The verdict said 'Domain Accuracy capped at 3 for ignoring the sets-invisibility gap' but I don't touch sets."** Sets don't have to be central to the skill; if the domain plausibly intersects the gap (field-resolution, IN/OUT filtering, dimension-based logic) and the skill is silent about it, the cap applies. If your skill genuinely has no intersection, ask for a re-score explaining why.
- **"It said 'no prior memory found' but I've graded this skill before."** MEMORY.md is checked for entries referencing the skill's name. If prior grades don't appear there, either the memory wasn't saved or it's indexed under a different name. Ask Skill Grader to search for related memory entries by keyword.
- **"The projected score after Quick Wins doesn't match my math."** Skill Grader computes projected improvement using the Ready Now + Low Effort items. If a fix would move a raw score up multiple levels (e.g. 2 → 5), the projection uses the realistic next-step (2 → 3 or 2 → 4), not the theoretical ceiling.

## Support

File issues in the same channel you use for other Tableau Desktop skill feedback. Include the skill name, the criterion you disagreed with, the score Skill Grader assigned, and the justification you'd expect instead.
