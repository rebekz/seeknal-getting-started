# Seeknal Query Reference

## Starting the REPL

```bash
# Interactive mode
seeknal repl

# Run a single query and exit
seeknal repl --exec "SELECT * FROM \"source.raw_orders\" LIMIT 5"

# Output as CSV
seeknal repl --format csv

# Save results to file
seeknal repl --output results.csv

# Combine: query, format, and save
seeknal repl --exec "SELECT * FROM \"transform.daily_revenue\"" --format csv --output daily_revenue.csv
```

---

## REPL Commands

```
.tables          -- List all available tables (node outputs)
.schema <table>  -- Show column names and types for a table
.exit            -- Exit the REPL (or Ctrl+D)
```

---

## Querying Node Outputs

Node outputs are referenced by `"<kind>.<name>"`.

### Sources

```sql
SELECT * FROM "source.raw_orders" LIMIT 10;
```

### Transforms

```sql
SELECT * FROM "transform.orders_cleaned" LIMIT 10;

SELECT * FROM "transform.daily_revenue" LIMIT 10;
```

### Feature Groups

```sql
SELECT * FROM "feature_group.customer_features";
```

### Second-Order Aggregations

```sql
SELECT * FROM "second_order_aggregation.region_metrics";
```

---

## Common Query Patterns

### Row Counts

```sql
SELECT COUNT(*) AS row_count FROM "transform.orders_cleaned";
```

### Check for Nulls

```sql
SELECT *
FROM "source.raw_orders"
WHERE customer_id IS NULL;
```

```sql
-- Count nulls per column
SELECT
  COUNT(*) AS total_rows,
  SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN revenue IS NULL THEN 1 ELSE 0 END) AS null_revenue
FROM "source.raw_orders";
```

### Aggregation

```sql
SELECT
  status,
  COUNT(*) AS order_count,
  SUM(revenue) AS total_revenue,
  AVG(revenue) AS avg_revenue
FROM "transform.orders_cleaned"
GROUP BY status;
```

### Distinct Values

```sql
SELECT DISTINCT status FROM "transform.orders_cleaned";
```

### Date Filtering

```sql
SELECT *
FROM "transform.orders_cleaned"
WHERE order_date >= '2024-01-01'
  AND order_date < '2024-02-01';
```

### Sorting

```sql
SELECT *
FROM "transform.daily_revenue"
ORDER BY order_date DESC
LIMIT 20;
```

### Join Across Nodes

```sql
SELECT
  c.*,
  d.total_revenue AS daily_total
FROM "transform.orders_cleaned" c
JOIN "transform.daily_revenue" d
  ON c.order_date = d.order_date;
```

### Window Functions

```sql
SELECT
  order_date,
  revenue,
  SUM(revenue) OVER (ORDER BY order_date) AS cumulative_revenue,
  ROW_NUMBER() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM "transform.orders_cleaned";
```

### Subqueries

```sql
SELECT *
FROM "transform.orders_cleaned"
WHERE revenue > (
  SELECT AVG(revenue) FROM "transform.orders_cleaned"
);
```

---

## Querying Semantic Metrics

### Single Metric with Dimension

```bash
seeknal query --metrics total_revenue --dimensions status
```

### Derived Metric

```bash
seeknal query --metrics avg_order_value_ratio --dimensions order_date
```

### Compile Without Executing

Preview the generated SQL without running it.

```bash
seeknal query --metrics cumulative_revenue --dimensions order_date --compile
```

### Multiple Metrics

```bash
seeknal query --metrics total_revenue,order_count --dimensions status
```

### Time-Based Metrics

```bash
seeknal query --metrics total_revenue --dimensions order_date
```

---

## Inspecting Nodes

### View Node Output

```bash
# Default output (first rows)
seeknal inspect source.raw_orders

# Limit rows
seeknal inspect source.raw_orders --limit 5

# View transform output
seeknal inspect transform.orders_cleaned --limit 10
```

### View Schema Only

```bash
seeknal inspect transform.orders_cleaned --schema
```

### List All Available Nodes

```bash
seeknal inspect --list
```

---

## Exporting Results

### Export to CSV

```bash
seeknal repl --exec "SELECT * FROM \"transform.daily_revenue\"" --format csv --output daily_revenue.csv
```

### Export Filtered Data

```bash
seeknal repl --exec "SELECT * FROM \"transform.orders_cleaned\" WHERE status = 'completed'" --format csv --output completed_orders.csv
```

### Export Aggregated Results

```bash
seeknal repl --exec "SELECT status, COUNT(*) AS cnt, SUM(revenue) AS total FROM \"transform.orders_cleaned\" GROUP BY status" --format csv --output summary.csv
```

---

## Quick Debugging Queries

### Compare Source vs Transform Row Counts

```sql
SELECT 'source' AS stage, COUNT(*) AS rows FROM "source.raw_orders"
UNION ALL
SELECT 'transform', COUNT(*) FROM "transform.orders_cleaned";
```

### Find Duplicate Keys

```sql
SELECT order_id, COUNT(*) AS occurrences
FROM "transform.orders_cleaned"
GROUP BY order_id
HAVING COUNT(*) > 1;
```

### Check Value Distribution

```sql
SELECT
  status,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM "transform.orders_cleaned"
GROUP BY status
ORDER BY count DESC;
```

### Data Freshness

```sql
SELECT
  MIN(order_date) AS earliest,
  MAX(order_date) AS latest,
  COUNT(DISTINCT order_date) AS distinct_dates
FROM "transform.orders_cleaned";
```

### Revenue Outliers

```sql
SELECT *
FROM "transform.orders_cleaned"
WHERE revenue > (
  SELECT AVG(revenue) + 3 * STDDEV(revenue)
  FROM "transform.orders_cleaned"
);
```
