# Pulse Metric Builder — a Tableau Studio skill

Create Tableau Pulse metrics on a published data source by asking Studio, then
drop them on a dashboard as Pulse cards.

Studio's agent can read Pulse but can't create it, so this skill ships a small
script (`skill-expertise/pulse.py`) that calls the Pulse REST API with your personal
access token (PAT). The agent walks you through what it needs, shows a dry-run
plan, and only creates after you confirm.

## Requirements

- Tableau Cloud site with Pulse turned on, and a user who can author Pulse.
- A **personal access token** (My Account Settings → Personal Access Tokens).
- Python 3 (`python3 --version`; on Windows, `py -3 --version` or
  `python --version`). Standard library only — nothing to install.
- macOS (secret in the Keychain) or Windows (secret in Windows Credential
  Manager). See First run.

## First run

The agent checks setup and asks for your server/site URL and PAT **name**. It
saves those to `~/.config/tableau-pulse-metric-builder/config.json` — never into
this folder, so the skill is safe to share.

The PAT **secret** never goes in chat.

**macOS:** when asked, open Terminal and run:

```
python3 "<path to this folder>/skill-expertise/pulse.py" store-secret
```

Paste the secret (hidden, asked twice). It's saved in the macOS Keychain under
`tableau-pulse-metric-builder`. To remove it: Keychain Access → search that
name → delete, or
`security delete-generic-password -s tableau-pulse-metric-builder`.
If the `TABLEAU_PAT_SECRET` environment variable is set, it is used instead of
the Keychain or Credential Manager.

**Windows:** when asked, open PowerShell and run:

```
py -3 "<path to this folder>\skill-expertise\pulse.py" store-secret
```

Type the secret at `PAT secret (typing is hidden):`, then again to confirm. It's
saved in Windows Credential Manager and works right away; no restart needed. The
command prints a `cmdkey /delete:...` line you can use to remove it later. The
scrollytelling demo builder skill reuses this saved secret.

**Windows fallback, if Credential Manager is blocked:** run this in PowerShell
(input is hidden and the secret stays out of your command history):

```
$s = Read-Host -AsSecureString 'PAT secret'; $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); [Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b), 'User'); [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)
```

Then fully quit and reopen Tableau Studio so it picks up the variable. The
variable is stored unencrypted in your user profile. To remove it later:
`[Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', $null, 'User')`

**Linux, or a macOS terminal without the Keychain:** run
`read -s TABLEAU_PAT_SECRET && export TABLEAU_PAT_SECRET` in the same terminal
session that runs the agent.

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
- `skill-expertise/pulse.py` — the API client (run with `--help`)
- `skill-expertise/setup.md` — sign-in setup details
- `skill-expertise/before-you-begin.md` — the optional checklist
- `skill-expertise/data-source-check.md` — published or local data source cases
- `skill-expertise/data-shapes.md` — suggesting measures; unusual data sources
- `skill-expertise/spec-fields.md` — spec keys, time field, locked defaults
- `skill-expertise/spec-example.md` — metric spec template
- `skill-expertise/output-formats.md` — the plan and report layouts
- `skill-expertise/api-notes.md` — Pulse API rules and error causes
- `skill-expertise/placing-cards.md` — putting Pulse cards on a dashboard
- `skill-expertise/studio-card.md` — Pulse Metric dashboard object XML
