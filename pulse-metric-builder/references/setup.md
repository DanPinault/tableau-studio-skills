# Setup details (Step 1)

Run `check`. It returns `missing` (any of `server`, `site`, `pat_name`,
`pat_secret`) or `signed_in: true`.

If anything is missing, ask only for what's missing:

- **server / site**: ask the user to paste any URL from their Tableau Cloud
  site; `configure --server "<url>"` pulls the pod and site out of it. Confirm the
  site content URL if the URL had no `/site/` part.
- **pat_name**: the PAT's name (not the secret). If they don't have one: My
  Account Settings > Personal Access Tokens > Create.
- **pat_secret**: tell the user to open Terminal and run:
  `python3 "<this skill folder>/scripts/pulse.py" store-secret`
  It prompts with hidden input (twice) and saves to the Keychain. Wait for them
  to say done, then run `check` again.

Then save with `configure --server ... --site ... --pat-name ...` and re-run `check`.
On a 401, have them check the PAT name and re-run `store-secret`; PATs expire
if unused for 15 days. Signing in with the same PAT elsewhere ends the earlier
session, so warn them if another script uses the same token.

Several sites? Use `--profile <name>` on every command (`configure` makes it the
active one).
