# Tableau Studio Skills

Agent skills for Tableau Studio, one folder per skill. Each folder has a `SKILL.md`; most also have a `README.md` and `CHANGELOG.md`.

| Skill | What it does |
|---|---|
| `scrollytelling-demo-builder` | Turns a published datasource into an animated, scrolling data story |
| `pulse-metric-builder` | Creates, lists, renames and deletes Tableau Pulse metrics |
| `publish-packaged-extension` | Publishes a workbook or packaged data app to Tableau Cloud or Server |
| `dashboard-builder` | Router that helps choose which kind of dashboard extension to build |
| `skill-grader-desktop` | Grades Tableau Desktop/Studio agent skills against 20 weighted criteria |
| `testing-matrix` | Builds a test matrix of prompts for another skill |

`platform_limitations.md` lists confirmed Studio agent gaps and is used by the grader.

## Install

Clone straight into your Studio skills folder (it must be empty or not exist yet):

```bash
git clone https://github.com/DanPinault/tableau-studio-skills.git "$HOME/Documents/My Tableau Repository (Beta)/Tableau Agent/skills"
```

Then run `/reload-skills` in Tableau Studio.

If the skills folder already has skills in it, clone to a temporary folder instead and copy the skill folders you want into it.

## Update

**Automatic (per skill).** `pulse-metric-builder`, `publish-packaged-extension` and `scrollytelling-demo-builder` check this repo for a newer version every time they are launched. If one is available, the skill shows what changed and asks whether to install it, skip it this time, or stop reminding you about that version. Installing replaces only that skill's folder (your old copy is saved in `~/.tableau-studio-skills-backups/`); run `/reload-skills` afterwards. Offline, the check is silently skipped.

**Manual (all skills at once).**

```bash
cd "$HOME/Documents/My Tableau Repository (Beta)/Tableau Agent/skills" && git pull
```

Then run `/reload-skills` in Tableau Studio. Check a skill's `CHANGELOG.md` to see what changed. Each skill's version is in its `VERSION` file.

## Notes

- Never put a personal access token or other secret in a skill folder. Credentials belong in your macOS Keychain.
- The `.vendored/` folder in the skills directory holds Tableau's own skills and is not part of this repo.
