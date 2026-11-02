# Workbook context and data shapes (Step 2)

## Suggest measures from the workbook (when the user hasn't named them)

For an open ask like "build Pulse metrics for this data source":

**First, once per run:** search the available tools for one that suggests or
recommends Pulse metrics (for example, a search for "pulse metric suggest
recommend"). One search only; don't repeat it with other wording. If a tool
turns up, use it and offer its suggestions first, labelled as Tableau's
recommendations, then continue with the user's choices at Step 3. If nothing
turns up (the case when this was written), say nothing about it and do the steps
below.

1. Read the workbook's sheets and dashboards. The inventory gives sheet names and
   which data source each sheet uses; it doesn't list fields. Sheet names are the
   hint ("Profit by Region", "Sales Trend by Category").
2. If a name doesn't make the measure clear, read that sheet's summary data to see
   which measures it shows.
3. Match those measures to the `fields` list by caption. Propose them first, ahead
   of other measures, and say where each came from ("your Growth Overview
   dashboard charts Sales and Profit").
4. Drop any measure and aggregation that `definitions` shows already exists.
5. Calculated fields the workbook charts: say whether each is an aggregate calc
   (Step 3). Use the published data source's version of the calc, not a
   workbook-only calc, because Pulse can only see fields in the published data
   source.
6. Offer at most five suggestions. The user can ask for more. Order them by the
   number of sheets that chart the measure, most first; break ties by the order
   `fields` lists them.

If the workbook has no sheets yet, suggest from `fields` alone: the numeric
measures first, in the order `fields` lists them.

## Data shapes

| Situation | What to do |
|---|---|
| No categorical (string) field in the data source | Stop. Pulse needs at least one filter dimension. Tell the user to add a simple string calc (for example, a constant label) in the data source and republish, then start again at Step 2. Bins don't count. |
| Wide data source (over 50 fields) | Don't print every field. Show the measures, the date fields and your three chosen filter dimensions; offer the rest on request. |
| Many definitions already on the site | `definitions --datasource` pages through all of them and filters locally, so it's complete but can be slow. Always pass the data source. |
| Many metrics in one ask (over 10) | Put them in one spec and one dry run, but show the plan in groups of 10 so it stays readable. Create only after the user approves the whole plan. |
| Several Tableau sites or accounts | Use `--profile <name>` on every command and say which profile you're using in the plan. |
| Extract versus live published data source | No difference to Pulse; it queries the published data source either way. If values look stale, the extract may need a refresh. |
| The only date field is a calculated date | Allowed as the time dimension. Use its `Calculation_…` name from `fields` and say so in the plan. |
| More than one published data source with the same name | Confirm by project name, and match the LUID, not the name. |
