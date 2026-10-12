# Pulse Metric Builder — a Tableau Studio skill

Create Tableau Pulse metrics on a published data source by asking Studio, then
drop them on a dashboard as Pulse cards.

Studio's agent can read Pulse but can't create it, so this skill ships a small
script (`scripts/pulse.py`) that calls the Pulse REST API with your personal
access token (PAT). The agent walks you through what it needs, shows a dry-run
plan, and only creates after you confirm.

## Requirements

- Tableau Cloud site with Pulse turned on, and a user who can author Pulse.
- A **personal access token** (My Account Settings → Personal Access Tokens).
- Python 3 on your PATH (`python3 --version`). Standard library only — nothing
  to install.
- macOS for Keychain storage. On other systems the storage step isn't available;
  set `TABLEAU_PAT_SECRET` in your shell instead, in the same Terminal session
  that runs the agent (for example `read -s TABLEAU_PAT_SECRET && export
  TABLEAU_PAT_SECRET` in bash or zsh). The secret still never goes in chat.

## First run

The agent checks setup and asks for your server/site URL and PAT **name**. It
saves those to `~/.config/tableau-pulse-metric-builder/config.json` — never into
this folder, so the skill is safe to share.

The PAT **secret** never goes in chat. When asked, open Terminal and run:

```
python3 "<path to this folder>/scripts/pulse.py" store-secret
```

Paste the secret (hidden, asked twice). It's saved in the macOS Keychain under
`tableau-pulse-metric-builder`. To remove it: Keychain Access → search that
name → delete, or
`security delete-generic-password -s tableau-pulse-metric-builder`.

## What to ask

- "Create Pulse metrics for Sales and Orders on the Superstore data source"
- "List the Pulse definitions on this data source"
- "Add a last-month metric for Revenue"
- "Put these Pulse metrics on a dashboard"

## Good to know

- The Pulse API sometimes rejects the first definition on a data source. The
  skill tries it anyway; if it is rejected, create any one metric in the Pulse UI,
  then the skill can add the rest.
- Every metric needs at least one categorical dimension to filter by.
- Aggregate calcs (like a profit ratio) are created with aggregation `USER`
  (the UI's "Calculated"); the script sets it for you. SUM on one returns no value.
- Demo data that stops in the past: keep `use_latest_data` on, or use YTD.

## Files

- `SKILL.md` — the agent's procedure
- `scripts/pulse.py` — the API client (run with `--help`)
- `references/setup.md` — sign-in setup details
- `references/before-you-begin.md` — the optional checklist
- `references/data-source-check.md` — published or local data source cases
- `references/data-shapes.md` — suggesting measures; unusual data sources
- `references/spec-fields.md` — spec keys, time field, locked defaults
- `references/spec-example.json` — metric spec template
- `references/output-formats.md` — the plan and report layouts
- `references/api-notes.md` — Pulse API rules and error causes
- `references/placing-cards.md` — putting Pulse cards on a dashboard
- `references/studio-card.md` — Pulse Metric dashboard object XML
