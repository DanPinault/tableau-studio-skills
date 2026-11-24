# Spec example

A complete example of the spec file the skill builds before running `create`. See `spec-fields.md` for what each field means. Save the JSON below as a `.json` file to use it with `pulse.py`. The names follow the metric-name rule in `spec-fields.md` for a data source named `Superstore_orders`.

```json
{
  "defaults": {
    "datasource": "<published data source LUID from `datasources`>",
    "time_dimension": "Order Date",
    "dimensions": ["Region", "Category"],
    "period": "ytd",
    "sentiment": "UP",
    "format": "NUMBER"
  },
  "metrics": [
    {
      "name": "Superstore_orders Sales",
      "measure": "Sales",
      "aggregation": "SUM",
      "format": "CURRENCY",
      "currency": "USD",
      "description": "Total sales across all regions."
    },
    {
      "name": "Superstore_orders Distinct Order ID",
      "measure": "Order ID",
      "aggregation": "COUNT_DISTINCT",
      "units": ["order", "orders"]
    },
    {
      "name": "Superstore_orders Distinct Order ID - Yes",
      "measure": "Order ID",
      "aggregation": "COUNT_DISTINCT",
      "sentiment": "DOWN",
      "units": ["order", "orders"],
      "filters": [{"field": "Returned", "values": ["Yes"]}]
    },
    {
      "name": "Superstore_orders Average Profitable Order Flag",
      "measure": "Profitable Order Flag",
      "aggregation": "AVERAGE",
      "format": "PERCENT",
      "description": "Share of orders with positive profit. Averages a row-level 1/0 calc."
    }
  ]
}
```
