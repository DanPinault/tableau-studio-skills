# Before you begin

Show this checklist only if the user asks for it. Adapt the wording to their
prompting level (short: the bold lines only; verbose: add the notes).

Open the checklist with this line: "If you need step-by-step instructions for any
of these, just ask which one." End it with the same offer.

## Required

- **A published data source** on a Tableau Cloud site, in a project they can see.
  Pulse can't build on a local file or database; it has to be published first
  (Server > Publish Data Source).
- **A personal access token (PAT) for that site.** They need its name and its
  secret. Create one in My Account Settings > Personal Access Tokens. PATs expire
  after 15 days of no use, and signing in with the same PAT elsewhere ends the
  earlier session.
- **Python 3.** Standard library only; nothing to install.
- **Terminal or PowerShell access.** They run the secret-storage command
  themselves, so the secret never goes through chat. On macOS it's saved in the
  Keychain; on Windows, in Windows Credential Manager. See "Store the secret"
  below.
- **A URL from their Tableau Cloud site.** The skill reads the pod and site from
  it and saves them for them. They don't need to edit `config.json` by hand.
- **Permission to author Pulse metrics, with Pulse turned on for the site.**
  Without it, creating a metric fails with a 403.
- **Access to the data source** (permission to see it in its project).

## The data source needs

- A numeric measure to aggregate.
- A date field for the time dimension. A calculated date works too.
- At least one categorical field people can filter by (Region, Category, and so on).

## Only for dashboard cards

- Tableau Desktop signed in to the same site.
- The published data source connected in the workbook.
- A Desktop version that has the Pulse Metric dashboard object.

## Step-by-step help (give only the one they ask about)

Give explicit, numbered steps for the requirement they name. Wait for them to say
each part is done before moving on. Never ask them to paste a secret.

- **Publish a data source:** 1) In Desktop, open the workbook with the data source.
  2) Choose Server > Publish Data Source and pick the data source. 3) Sign in to
  Tableau Cloud if asked. 4) Pick a project they can see, give it a name, and
  choose Publish. 5) Tell me when it's done so I can find it.
- **Create a PAT:** 1) Sign in to Tableau Cloud in a browser. 2) Open the profile
  icon > My Account Settings. 3) Under Personal Access Tokens, enter a name and
  choose Create token. 4) Copy the secret when it appears (it's shown once) and
  keep it out of chat. 5) Tell me the token's name, not the secret.
- **Store the secret (macOS):** 1) Open Terminal. 2) Run the `store-secret`
  command from the setup step. 3) Type the secret when prompted (nothing shows as
  they type), then again to confirm. 4) Tell me when it's done.
- **Store the secret (Windows):** 1) Open PowerShell. 2) Run the `store-secret`
  command from the setup step (`py -3 "<path>\pulse.py" store-secret`). 3) Type
  the secret at `PAT secret (typing is hidden):`, then again to confirm. It's
  saved in Windows Credential Manager; no restart needed. 4) Tell me when it's
  done.
- **Store the secret (Windows fallback, if Credential Manager is blocked):**
  1) Open PowerShell. 2) Run
  `$s = Read-Host -AsSecureString 'PAT secret'; $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); [Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b), 'User'); [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)`
  (input is hidden and stays out of the command history). 3) Fully quit and
  reopen Tableau Studio. 4) Tell me when it's done. The variable is stored
  unencrypted in their user profile; to remove it later, run
  `[Environment]::SetEnvironmentVariable('TABLEAU_PAT_SECRET', $null, 'User')`.
- **Check Python 3:** 1) Open Terminal (PowerShell on Windows). 2) Run
  `python3 --version` (on Windows, `py -3 --version`). 3) If it isn't
  found, install Python 3 from python.org, then reopen Terminal and re-run it.
- **Find the site URL:** 1) Sign in to Tableau Cloud in a browser. 2) Copy any URL
  from the address bar and give it to me.
- **Pulse authoring rights:** I can't check these from here. If creating a metric
  fails with a 403, ask your Tableau site admin to turn on Pulse and grant you
  permission to create metrics.
