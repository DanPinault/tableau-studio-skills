# Setup details (Step 1)

Run `check`. It returns `missing` (any of `server`, `site`, `pat_name`,
`pat_secret`) or `signed_in: true`.

If anything is missing, ask only for what's missing:

- **server / site**: ask the user to paste any URL from their Tableau Cloud
  site; `configure --server "<url>"` pulls the pod and site out of it. It must
  be an `https://` URL; anything else is rejected. Confirm the
  site content URL if the URL had no `/site/` part.
- **pat_name**: the PAT's name (not the secret). If they don't have one: My
  Account Settings > Personal Access Tokens > Create.
- **pat_secret**: the user stores it themselves, never in chat.
  - macOS: open Terminal and run
    `python3 "<this skill folder>/skill-expertise/pulse.py" store-secret`.
    It prompts with hidden input (twice) and saves to the Keychain. If
    `TABLEAU_PAT_SECRET` is also set in the environment, it is used instead of
    the Keychain (`check` shows `found (env)`); unset it to use the Keychain.
  - Windows: the user opens PowerShell and runs
    `py -3 "<this skill folder>\skill-expertise\pulse.py" store-secret`.
    It shows `PAT secret (typing is hidden):`, asks twice, saves to Windows
    Credential Manager and reads it back. No restart is needed. It prints a
    `remove_later: cmdkey /delete:"..."` line for removing it later. If you run
    it from your own shell it refuses (exit 2); ask the user to run it in
    PowerShell. If it reports an error, use the fallback below.
  - Windows fallback, if Credential Manager is blocked: open PowerShell and run
    this (hidden input, kept out of the command history):
    `$s = Read-Host -AsSecureString 'PAT secret'; $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); [Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b), 'User'); [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)`
    Then fully quit and reopen Tableau Studio so it sees the variable. Tell them
    it is stored unencrypted in their user profile, and that
    `[Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', $null, 'User')` removes it later.
  - Linux, or a macOS terminal without the Keychain:
    `read -s TABLEAU_PAT_SECRET && export TABLEAU_PAT_SECRET` in the terminal
    session that runs the agent.
  Wait for them to say done, then run `check` again.

Then save with `configure --server ... --site ... --pat-name ...` and re-run `check`.
On a 401, have them check the PAT name and store the secret again (re-run
`store-secret`, or set the variable again if they used the fallback); PATs expire if unused for
15 days. Signing in with the same PAT elsewhere ends the earlier session, so run
this skill's commands one at a time and warn them if another script uses the
same token.

Several sites? Use `--profile <name>` on every command (`configure` makes it the
active one).
