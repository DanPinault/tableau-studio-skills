# Changelog

The current version is in the `VERSION` file. The skill offers to update itself
when launched; or replace this folder with the newer one and run `/reload-skills`.

## 1.1.0 — 2026-11-02

Update check on launch: the skill now checks the DanPinault/tableau-studio-skills
repository for a newer version before doing anything else, and offers to
install it (old copy is backed up), skip it, or stop reminding for that
version. Works offline (silently skipped). Adds `scripts/check_update.py`.

## 1.0.0 — 2026-10-13

First release in Tableau Studio Skills. Passed a 24-row test matrix and was
graded 84.7 (B).

- Creates, lists, renames and deletes Tableau Pulse metric definitions and
  metrics on a published data source, through the Pulse REST API with a bundled
  script.
- Outputs the settings for Studio's Pulse Metric dashboard object.
- Reference files for setup, data source checks, measure suggestions, the metric
  spec, output formats, API notes and card placement.
