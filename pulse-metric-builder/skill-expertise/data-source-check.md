# Published or local? (Step 2a)

Decide by each connection, not by name: a published and a local data source can
share a name, and a `sqlproxy.…` id means published.

- **Published:** go straight to Step 2. Match it by name to the `datasources` list
  to get its LUID.
- **Local** (file, extract, or unpublished database): stop and explain it must be
  published first. Ask the user to use **Server > Publish Data Source**, to a
  project they can see, and wait for them to say it's done. There is no tool to
  publish it for them. Confirm it appears in `datasources`, and tell them to
  switch the workbook to the published copy if cards will be placed. Don't build
  on a different data source without asking.
- **Several open:** ask which one the metrics are for.
- **Nothing open:** ask the user to open the data source they want metrics on
  (connect to it, or **Data > New Data Source > Tableau Server / Tableau Cloud**),
  and explain it must be published. Or they can name a published data source and
  you find it with `datasources`. Then apply the checks above.

Verbose mode: also explain why publishing is required. Short mode: one line.
