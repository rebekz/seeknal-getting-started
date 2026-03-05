# Module 4: Advanced Sources & CDC

> **Duration:** ~50 minutes | **Difficulty:** Intermediate

In this module, you will implement Change Data Capture (CDC), handle multi-format data sources, and refactor your pipeline to incorporate corrections and late-arriving data — the reality of every production system.

---

## Why This Matters in Industry

Real-world data is never static. Orders get corrected, statuses change, and records arrive late. Companies must handle these mutations without reprocessing entire datasets from scratch.

- **Uber** uses CDC to track ride status changes (requested, accepted, in-progress, completed, cancelled) across millions of rides per day. Each status update is a change event that must be merged into the canonical ride table.
- **Netflix** ingests viewing events from hundreds of millions of devices. When a device reconnects after being offline, late-arriving events must be merged with the existing stream without creating duplicates.
- **Shopify** receives order corrections (refunds, address changes, payment updates) as separate events that must overwrite the original order data.

Beyond CDC, production systems export data in multiple formats. A single pipeline might consume CSV files from legacy systems, JSONL streams from event APIs, and Parquet snapshots from data warehouses. A data engineer must handle **all** of these in a single pipeline.

| Challenge | Industry Example | Your Pipeline |
|-----------|-----------------|---------------|
| Data corrections | Refund changes order revenue | `orders_updates.csv` corrects ORD-004 and ORD-005 |
| Late arrivals | Offline device syncs events | New orders ORD-013 and ORD-014 added |
| Multi-format ingestion | CSV + JSON + Parquet in one pipeline | Three different source formats |
| Dependency refactoring | Upstream table changes | `daily_revenue` now reads from `orders_merged` |

---

## Prerequisites

- Completed [Module 1: Introduction & Setup](01_introduction_and_setup.md), [Module 2: Data Transformation](02_data_transformation.md), and [Module 3: Data Quality & Testing](03_data_quality_and_testing.md)
- All files from previous modules in place

---

## What You'll Build

By the end of this module, you will have:

1. A **CDC merge pattern** that combines original orders with corrections and new arrivals
2. **JSONL and Parquet data sources** demonstrating multi-format ingestion
3. **Quality rules** for the new event data
4. A **refactored `daily_revenue`** transform that uses merged data instead of raw cleaned data

---

## Step 4.1: Add Order Updates (CDC Data)

In the real world, corrections arrive as a separate feed. Create the updates file that contains two corrected orders and two new orders.

```bash
mkdir -p data
```

**data/orders_updates.csv**

```csv
order_id,customer_id,order_date,status,revenue,items
ORD-004,CUST-100,2026-01-16 14:20:00,completed,55.00,1
ORD-005,CUST-102,2026-01-17 08:15:00,completed,25.00,2
ORD-013,CUST-108,2026-01-22 11:00:00,completed,299.99,5
ORD-014,CUST-109,2026-01-22 15:30:00,completed,42.50,1
```

Look at what changed compared to the original data:

| order_id | Original State | Updated State | What Changed |
|----------|---------------|---------------|--------------|
| ORD-004 | `pending`, revenue = `0.00` | `completed`, revenue = `55.00` | Status and revenue corrected |
| ORD-005 | `completed`, revenue = `-10.00` | `completed`, revenue = `25.00` | Negative revenue corrected to actual value |
| ORD-013 | (did not exist) | `completed`, revenue = `299.99` | New order (late arrival) |
| ORD-014 | (did not exist) | `completed`, revenue = `42.50` | New order (late arrival) |

This is a classic CDC pattern: the updates file contains both **corrections** to existing records and **new records** that arrived after the initial load.

---

## Step 4.2: Create the Updates Source

Register the updates file as a Seeknal source.

```bash
seeknal draft source orders_updates
```

Edit the generated file:

**seeknal/sources/orders_updates.yml**

```yaml
kind: source
name: orders_updates
description: "Order corrections and new orders via CDC"
source: csv
table: "data/orders_updates.csv"
columns:
  order_id: "Order identifier (may overlap with raw_orders)"
  customer_id: "Customer identifier"
  order_date: "Date of order"
  status: "Updated order status"
  revenue: "Corrected revenue"
  items: "Number of items"
```

Validate and apply:

```bash
seeknal dry-run seeknal/sources/orders_updates.yml
seeknal apply seeknal/sources/orders_updates.yml
```

Note the description: "may overlap with raw_orders." This is the key characteristic of CDC data — some `order_id` values exist in both the original and the updates file. The merge transform must decide which version to keep.

---

## Step 4.3: Create the CDC Merge Transform

This is the core pattern of this module. The merge transform combines the cleaned original orders with the CDC updates, keeping only the latest version of each order.

```bash
seeknal draft transform orders_merged
```

Edit the generated file:

**seeknal/transforms/orders_merged.yml**

```yaml
kind: transform
name: orders_merged
description: "Merge original orders with CDC updates, keeping latest version"
inputs:
  - ref: transform.orders_cleaned
  - ref: source.orders_updates
transform: |
  WITH combined AS (
      SELECT *, 'original' AS record_source
      FROM ref('transform.orders_cleaned')
      UNION ALL
      SELECT
          order_id,
          customer_id,
          CAST(order_date AS DATE) AS order_date,
          TRIM(status) AS status,
          CASE WHEN revenue < 0 THEN 0 ELSE revenue END AS revenue,
          CASE WHEN items < 0 THEN 0 ELSE items END AS items,
          CURRENT_TIMESTAMP AS processed_at,
          'update' AS record_source
      FROM ref('source.orders_updates')
      WHERE customer_id IS NOT NULL
  )
  SELECT
      order_id, customer_id, order_date, status,
      revenue, items, processed_at
  FROM combined
  QUALIFY ROW_NUMBER() OVER (
      PARTITION BY order_id
      ORDER BY
          CASE WHEN record_source = 'update' THEN 0 ELSE 1 END,
          processed_at DESC
  ) = 1
```

Validate and apply:

```bash
seeknal dry-run seeknal/transforms/orders_merged.yml
seeknal apply seeknal/transforms/orders_merged.yml
```

This transform uses a four-step CDC merge pattern that is standard across the industry.

### How the CDC Merge Pattern Works

**Step 1: Tag each source.** The `record_source` column marks rows as `'original'` or `'update'` so the merge logic can distinguish them.

**Step 2: UNION ALL.** Combine both datasets into a single table. `UNION ALL` keeps all rows, including duplicates — this is intentional. You want both the original ORD-004 (revenue = 0) and the updated ORD-004 (revenue = 55) in the combined set.

**Step 3: Apply cleaning to updates.** The updates go through the same cleaning logic as the originals (`TRIM`, `CASE WHEN revenue < 0`, `WHERE customer_id IS NOT NULL`). Never trust incoming data, even corrections.

**Step 4: Deduplicate with priority.** The `QUALIFY` clause keeps one row per `order_id`. The `ORDER BY` gives updates priority over originals:

```sql
ORDER BY
    CASE WHEN record_source = 'update' THEN 0 ELSE 1 END,  -- updates first
    processed_at DESC                                        -- then most recent
```

When `record_source = 'update'`, the sort value is `0` (sorts first). When `record_source = 'original'`, the sort value is `1` (sorts second). So for ORD-004, the update row (revenue = 55.00) sorts before the original row (revenue = 0.00), and `ROW_NUMBER() = 1` keeps only the update.

For ORD-013 and ORD-014, there is no original row — the update is the only version, so it is kept automatically.

### Why Not Use MERGE or UPSERT?

You might wonder why we use `UNION ALL` + `QUALIFY` instead of SQL `MERGE` statements. Three reasons:

1. **Immutability.** This pattern produces a new table rather than modifying existing rows. Immutable transforms are easier to debug and replay.
2. **Portability.** `UNION ALL` + window functions work in every SQL engine. `MERGE` syntax varies across databases.
3. **Auditability.** You can inspect the `combined` CTE to see both versions of every record before deduplication.

> **Industry note:** This exact pattern is used in dbt (data build tool) projects at companies like Spotify and GitLab. It is sometimes called the "Type 1 SCD" (Slowly Changing Dimension) pattern — overwrite the old value with the new one.

---

## Step 4.4: Refactor daily_revenue to Use Merged Data

Now that you have a merged orders table that includes CDC corrections, update `daily_revenue` to read from `orders_merged` instead of `orders_cleaned`.

**seeknal/transforms/daily_revenue.yml**

```yaml
kind: transform
name: daily_revenue
description: "Daily revenue aggregation from merged orders (includes CDC updates)"
inputs:
  - ref: transform.orders_merged
transform: |
  SELECT
      order_date,
      COUNT(*) AS total_orders,
      SUM(revenue) AS total_revenue,
      AVG(revenue) AS avg_revenue,
      SUM(items) AS total_items,
      COUNT(DISTINCT customer_id) AS unique_customers,
      MIN(revenue) AS min_order,
      MAX(revenue) AS max_order,
      SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_orders,
      ROUND(SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS completion_rate
  FROM ref('transform.orders_merged')
  GROUP BY order_date
  ORDER BY order_date
```

After editing, validate and apply:

```bash
seeknal dry-run seeknal/transforms/daily_revenue.yml
seeknal apply seeknal/transforms/daily_revenue.yml
```

The only changes from Module 2 are:

1. **`inputs`** now references `transform.orders_merged` instead of `transform.orders_cleaned`
2. **`ref('transform.orders_merged')`** in the SQL `FROM` clause
3. **`description`** updated to reflect the new data source

This is a common pattern in pipeline development — as your data model grows, you refactor downstream transforms to point at the latest upstream table. The SQL aggregation logic itself does not change. Because Seeknal tracks dependencies through `ref()`, it automatically re-executes `daily_revenue` whenever `orders_merged` changes.

### Updated DAG

Your pipeline DAG now has a diamond shape:

```
source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue
                                                        ↑
                                          source.orders_updates
```

Both `orders_cleaned` and `orders_updates` feed into `orders_merged`, which then feeds into `daily_revenue`. Seeknal resolves this automatically — it runs the two sources and the cleaning transform first, then the merge, then the aggregation.

---

## Step 4.5: Multi-Format Sources — JSONL

Real pipelines ingest data from many systems, each exporting in a different format. Event tracking systems typically emit **JSONL** (JSON Lines) — one JSON object per line, no array wrapper. Create a sample events file.

**data/sales_events.jsonl**

```json
{"event_id":"EVT-001","product_id":"PRD-001","quantity":2,"sale_date":"2026-01-10","region":"north"}
{"event_id":"EVT-002","product_id":"PRD-003","quantity":1,"sale_date":"2026-01-10","region":"south"}
{"event_id":"EVT-003","product_id":"PRD-001","quantity":null,"sale_date":"2026-01-11","region":"north"}
{"event_id":"EVT-004","product_id":"PRD-999","quantity":3,"sale_date":"2026-01-11","region":"east"}
{"event_id":"EVT-005","product_id":"PRD-002","quantity":1,"sale_date":"2026-01-12","region":"south"}
{"event_id":"EVT-006","product_id":"PRD-004","quantity":5,"sale_date":"2026-01-12","region":"west"}
{"event_id":"EVT-001","product_id":"PRD-001","quantity":2,"sale_date":"2026-01-13","region":"north"}
```

This file has three intentional quality issues:

| Row | event_id | Issue |
|-----|----------|-------|
| 3 | EVT-003 | `quantity` is `null` — sensor or application error |
| 4 | EVT-004 | `product_id` is `PRD-999` — does not exist in the product catalog |
| 7 | EVT-001 | Duplicate `event_id` — same event sent twice (common in distributed systems) |

Register it as a Seeknal source:

```bash
seeknal draft source sales_events
```

Edit the generated file:

**seeknal/sources/sales_events.yml**

```yaml
kind: source
name: sales_events
description: "Sales events from the event tracking system"
source: jsonl
table: "data/sales_events.jsonl"
columns:
  event_id: "Unique event identifier"
  product_id: "Product sold"
  quantity: "Number of units sold"
  sale_date: "Date of sale"
  region: "Sales region"
```

Validate and apply:

```bash
seeknal dry-run seeknal/sources/sales_events.yml
seeknal apply seeknal/sources/sales_events.yml
```

The only difference from a CSV source is `source: jsonl`. Seeknal handles the format parsing automatically.

---

## Step 4.6: Multi-Format Sources — Parquet

Data warehouses and analytics systems typically export snapshots in **Parquet** format — a columnar, compressed binary format that is dramatically faster to read than CSV for analytical queries.

Create a Parquet source definition. (Assume the Parquet file was exported from a warehouse system.)

```bash
seeknal draft source sales_snapshot
```

Edit the generated file:

**seeknal/sources/sales_snapshot.yml**

```yaml
kind: source
name: sales_snapshot
description: "Quarterly sales snapshot from Parquet"
source: parquet
table: "data/sales_snapshot.parquet"
columns:
  product_id: "Product identifier"
  total_units_sold: "Total units sold in the period"
  period: "Reporting period (e.g., 2025-Q4)"
```

Validate and apply:

```bash
seeknal dry-run seeknal/sources/sales_snapshot.yml
seeknal apply seeknal/sources/sales_snapshot.yml
```

### When to Use Each Format

| Format | Typical Use Case | Pros | Cons |
|--------|-----------------|------|------|
| **CSV** | Simple exports, spreadsheets, legacy systems | Human-readable, universal support | Slow for large files, no type info |
| **JSONL** | Event streams, APIs, application logs | Schema flexibility, nested data | Larger file size than binary formats |
| **Parquet** | Data warehouses, analytics, ML pipelines | Compressed, columnar, fast queries | Not human-readable, requires tooling |

In production, you will often see all three in a single pipeline. A common pattern:

1. **CSV** from business users uploading spreadsheets
2. **JSONL** from application event streams (Kafka, Kinesis, Pub/Sub)
3. **Parquet** from upstream data warehouse tables or ML feature stores

Seeknal abstracts the format differences — you declare `source: csv`, `source: jsonl`, or `source: parquet`, and the engine handles the rest.

---

## Step 4.7: Clean the Events Data

Apply the same cleaning patterns you learned in Module 2 to the sales events: remove null quantities and deduplicate by `event_id`.

```bash
seeknal draft transform events_cleaned
```

Edit the generated file:

**seeknal/transforms/events_cleaned.yml**

```yaml
kind: transform
name: events_cleaned
description: "Clean sales events: remove nulls and duplicates"
inputs:
  - ref: source.sales_events
transform: |
  SELECT
      event_id,
      product_id,
      quantity,
      CAST(sale_date AS DATE) AS sale_date,
      region
  FROM ref('source.sales_events')
  WHERE quantity IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
      PARTITION BY event_id
      ORDER BY sale_date DESC
  ) = 1
```

This transform applies two cleaning rules:

1. `WHERE quantity IS NOT NULL` — removes EVT-003 (null quantity)
2. `QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY sale_date DESC) = 1` — removes the duplicate EVT-001, keeping the later entry (2026-01-13)

The expected result is **5 rows** from the original 7: EVT-001 (deduplicated to the Jan 13 version), EVT-002, EVT-004, EVT-005, and EVT-006.

Validate and apply:

```bash
seeknal dry-run seeknal/transforms/events_cleaned.yml
seeknal apply seeknal/transforms/events_cleaned.yml
```

> **Note:** EVT-004 references `PRD-999`, which does not exist in a product catalog. We are not filtering it here because referential integrity checks belong in a separate validation step. You could add a join-based rule in a later module to catch orphaned references.

---

## Step 4.8: Add Quality Rules for Events

Add two quality rules that validate the cleaned events data. These rules run automatically as part of the pipeline and will fail the build if the data violates expectations.

```bash
seeknal draft rule not_null_quantity
```

**seeknal/rules/not_null_quantity.yml**

```yaml
kind: rule
name: not_null_quantity
description: "Quantity must not be null in cleaned events"
inputs:
  - ref: transform.events_cleaned
rule:
  type: "null"
  columns: [quantity]
  params:
    max_null_percentage: 0.0
params:
  severity: error
  error_message: "Found null quantity values after cleaning"
```

Validate and apply:

```bash
seeknal dry-run seeknal/rules/not_null_quantity.yml
seeknal apply seeknal/rules/not_null_quantity.yml
```

This rule asserts that after cleaning, zero percent of `quantity` values are null. If the cleaning transform has a bug that lets nulls through, this rule catches it.

```bash
seeknal draft rule positive_quantity
```

**seeknal/rules/positive_quantity.yml**

```yaml
kind: rule
name: positive_quantity
description: "Quantity must be positive"
inputs:
  - ref: transform.events_cleaned
rule:
  type: range
  column: quantity
  params:
    min_val: 1
    max_val: 10000
params:
  severity: error
  error_message: "Found events with non-positive quantity"
```

This rule asserts that every `quantity` value falls between 1 and 10,000. A quantity of 0 or negative would indicate corrupted data; a quantity above 10,000 would likely be an application error.

Validate and apply:

```bash
seeknal dry-run seeknal/rules/positive_quantity.yml
seeknal apply seeknal/rules/positive_quantity.yml
```

Together, these two rules form a **quality gate** — the pipeline will not produce results from bad data.

---

## Step 4.9: Run the Full Pipeline

Run the entire pipeline, which now includes CDC merging, multi-format sources, cleaning, and quality rules.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing 9 node(s)...
  ✓ source.raw_orders (13 rows)
  ✓ source.orders_updates (4 rows)
  ✓ source.sales_events (7 rows)
  ✓ source.sales_snapshot
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.orders_merged (13 rows)
  ✓ transform.daily_revenue (8 rows)
  ✓ transform.events_cleaned (5 rows)
  ✓ rule.not_null_quantity: PASSED
  ✓ rule.positive_quantity: PASSED
Pipeline completed successfully.
```

### What just happened?

1. Seeknal loaded all four sources: `raw_orders` (13 rows), `orders_updates` (4 rows), `sales_events` (7 rows), and `sales_snapshot` (Parquet file).
2. `transform.orders_cleaned` ran first, producing 11 rows from the 13 raw orders (same as Module 2).
3. `transform.orders_merged` combined the 11 cleaned orders with the 4 updates. After deduplication, it produced 13 rows: 9 unchanged originals + 2 corrected orders (ORD-004, ORD-005) + 2 new orders (ORD-013, ORD-014).
4. `transform.daily_revenue` aggregated the 13 merged orders into 8 daily summary rows (one more day than before, since the new orders fall on January 22).
5. `transform.events_cleaned` cleaned the 7 events down to 5 (removed 1 null + 1 duplicate).
6. Both quality rules passed: no null quantities and all quantities are in the valid range.

### Row Count Walkthrough

| Node | Input Rows | Output Rows | Why |
|------|-----------|-------------|-----|
| `orders_cleaned` | 13 | 11 | Removed 1 null customer + 1 duplicate |
| `orders_merged` | 11 + 4 = 15 | 13 | 2 updates replaced originals, 2 new orders added |
| `daily_revenue` | 13 | 8 | 8 distinct dates in the merged data |
| `events_cleaned` | 7 | 5 | Removed 1 null quantity + 1 duplicate event |

---

## Step 4.10: Verify with the REPL

Open the REPL and run verification queries.

```bash
seeknal repl
```

### Verify: CDC Merge Corrected ORD-004

```sql
SELECT order_id, customer_id, status, revenue
FROM "transform.orders_merged"
WHERE order_id = 'ORD-004';
```

Expected output:

```
┌──────────┬─────────────┬───────────┬─────────┐
│ order_id │ customer_id │  status   │ revenue │
├──────────┼─────────────┼───────────┼─────────┤
│ ORD-004  │ CUST-100    │ completed │   55.00 │
└──────────┴─────────────┴───────────┴─────────┘
```

Previously, ORD-004 was `pending` with revenue `0.00`. The CDC merge replaced it with the corrected version: `completed` with revenue `55.00`.

### Verify: CDC Merge Corrected ORD-005

```sql
SELECT order_id, customer_id, status, revenue
FROM "transform.orders_merged"
WHERE order_id = 'ORD-005';
```

Expected output:

```
┌──────────┬─────────────┬───────────┬─────────┐
│ order_id │ customer_id │  status   │ revenue │
├──────────┼─────────────┼───────────┼─────────┤
│ ORD-005  │ CUST-102    │ completed │   25.00 │
└──────────┴─────────────┴───────────┴─────────┘
```

In Module 2, ORD-005 had negative revenue that was set to `0` by the cleaning logic. Now the CDC update provides the correct value: `25.00`.

### Verify: New Orders Arrived

```sql
SELECT order_id, customer_id, status, revenue
FROM "transform.orders_merged"
WHERE order_id IN ('ORD-013', 'ORD-014')
ORDER BY order_id;
```

Expected output:

```
┌──────────┬─────────────┬───────────┬─────────┐
│ order_id │ customer_id │  status   │ revenue │
├──────────┼─────────────┼───────────┼─────────┤
│ ORD-013  │ CUST-108    │ completed │  299.99 │
│ ORD-014  │ CUST-109    │ completed │   42.50 │
└──────────┴─────────────┴───────────┴─────────┘
```

These orders did not exist in the original data. They arrived via the CDC feed and were added to the merged table.

### Verify: Total Merged Order Count

```sql
SELECT COUNT(*) AS total_merged_orders
FROM "transform.orders_merged";
```

Expected output:

```
┌──────────────────────┐
│ total_merged_orders  │
├──────────────────────┤
│                   13 │
└──────────────────────┘
```

11 cleaned originals + 4 updates = 15 combined rows. After deduplication (ORD-004 and ORD-005 each appear twice), 13 unique orders remain.

### Verify: Events Cleaning Worked

```sql
SELECT COUNT(*) AS total_events
FROM "transform.events_cleaned";
```

Expected output:

```
┌──────────────┐
│ total_events │
├──────────────┤
│            5 │
└──────────────┘
```

7 raw events became 5 after removing the null-quantity event (EVT-003) and the duplicate (EVT-001).

### Verify: No Null Quantities in Cleaned Events

```sql
SELECT COUNT(*) AS null_qty
FROM "transform.events_cleaned"
WHERE quantity IS NULL;
```

Expected output:

```
┌──────────┐
│ null_qty │
├──────────┤
│        0 │
└──────────┘
```

### Verify: Daily Revenue Reflects CDC Updates

```sql
SELECT * FROM "transform.daily_revenue"
ORDER BY order_date;
```

Compare the output with Module 2's results. You should see:

- The January 16 row now includes ORD-004's corrected revenue ($55.00 instead of $0.00)
- The January 17 row now includes ORD-005's corrected revenue ($25.00 instead of $0.00)
- A new January 22 row with two orders totaling $342.49 (ORD-013 + ORD-014)

Exit the REPL:

```bash
.exit
```

---

## Updated DAG

Your full pipeline DAG after this module:

```
source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue
                                                        ↑
                                          source.orders_updates

source.sales_events ──→ transform.events_cleaned
                              ↓
                    rule.not_null_quantity
                    rule.positive_quantity

source.sales_snapshot (standalone — will be joined in a later module)
```

Notice that the pipeline now has two independent subgraphs:

1. **Orders subgraph:** raw_orders → orders_cleaned → orders_merged → daily_revenue (with orders_updates feeding into the merge)
2. **Events subgraph:** sales_events → events_cleaned → quality rules

Seeknal can execute independent subgraphs in parallel. The orders and events pipelines do not depend on each other, so they run concurrently.

---

## Concepts Recap

### The CDC Merge Pattern

```
┌─────────────────────┐     ┌──────────────────────┐
│  Original Records   │     │    Update Records     │
│  (orders_cleaned)   │     │  (orders_updates)     │
└─────────┬───────────┘     └──────────┬────────────┘
          │                            │
          │   tag: 'original'          │   tag: 'update'
          │                            │
          └──────────┬─────────────────┘
                     │
              UNION ALL (combine)
                     │
                     v
          ┌──────────────────────┐
          │    Combined Table    │
          │  (may have dupes)    │
          └──────────┬───────────┘
                     │
          QUALIFY ROW_NUMBER()
          PARTITION BY order_id
          ORDER BY update > original
                     │
                     v
          ┌──────────────────────┐
          │   Merged Table       │
          │  (one row per order) │
          └──────────────────────┘
```

This pattern is:

- **Immutable** — original data is never modified
- **Auditable** — you can inspect the combined CTE to see both versions
- **Portable** — works in DuckDB, Snowflake, BigQuery, Redshift, and Databricks
- **Idempotent** — running it twice produces the same result

### Multi-Format Source Summary

| Declaration | Format | File Extension |
|-------------|--------|---------------|
| `source: csv` | Comma-separated values | `.csv` |
| `source: jsonl` | JSON Lines (one object per line) | `.jsonl` |
| `source: parquet` | Apache Parquet (columnar binary) | `.parquet` |

### Dependency Refactoring

When you changed `daily_revenue` to read from `orders_merged` instead of `orders_cleaned`, you performed a **dependency refactoring**. This is a routine task in pipeline development:

1. A new upstream table is created (the merge)
2. Downstream transforms are updated to point at the new table
3. The old dependency chain is replaced

Because you use `ref()` for all references, Seeknal rebuilds the DAG automatically. No manual execution ordering is needed.

---

## Common Mistakes

### Mistake 1: Using UNION instead of UNION ALL

```sql
-- WRONG — UNION deduplicates by all columns, which may drop valid rows
SELECT * FROM originals
UNION
SELECT * FROM updates

-- CORRECT — UNION ALL keeps all rows; you control deduplication explicitly
SELECT * FROM originals
UNION ALL
SELECT * FROM updates
```

`UNION` silently removes rows that are identical across all columns. If two orders have the same values (but different timestamps in a column you forgot to include), `UNION` will drop one of them without warning. Always use `UNION ALL` and handle deduplication explicitly with `ROW_NUMBER()`.

### Mistake 2: Forgetting to Clean Update Data

```yaml
# WRONG — trusting updates without cleaning
SELECT *, 'update' AS record_source
FROM ref('source.orders_updates')

# CORRECT — apply the same cleaning rules to updates
SELECT
    order_id,
    customer_id,
    CAST(order_date AS DATE) AS order_date,
    TRIM(status) AS status,
    CASE WHEN revenue < 0 THEN 0 ELSE revenue END AS revenue,
    CASE WHEN items < 0 THEN 0 ELSE items END AS items,
    CURRENT_TIMESTAMP AS processed_at,
    'update' AS record_source
FROM ref('source.orders_updates')
WHERE customer_id IS NOT NULL
```

Update feeds can have the same quality issues as original data. Always apply cleaning logic to every data source, regardless of whether it is "trusted."

### Mistake 3: Wrong Priority in ORDER BY

```sql
-- WRONG — originals take priority (updates are ignored)
ORDER BY CASE WHEN record_source = 'original' THEN 0 ELSE 1 END

-- CORRECT — updates take priority (corrections overwrite originals)
ORDER BY CASE WHEN record_source = 'update' THEN 0 ELSE 1 END
```

The whole point of CDC is that updates should overwrite originals. If you reverse the priority, the corrected data is discarded.

---

## Checkpoint

By the end of this module, you should have:

- [ ] Created CDC update data (`data/orders_updates.csv`)
- [ ] Created the CDC merge transform (`orders_merged`) using the UNION ALL + QUALIFY pattern
- [ ] Refactored `daily_revenue` to use merged data instead of cleaned data
- [ ] Added a JSONL data source (`sales_events`)
- [ ] Added a Parquet data source (`sales_snapshot`)
- [ ] Created an events cleaning transform (`events_cleaned`)
- [ ] Added quality rules for events data (`not_null_quantity`, `positive_quantity`)
- [ ] Verified CDC corrections through REPL queries
- [ ] Understood the multi-format ingestion pattern

Your project structure should now look like this:

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   ├── orders.csv
│   ├── orders_updates.csv
│   ├── sales_events.jsonl
│   └── sales_snapshot.parquet
├── seeknal/
│   ├── sources/
│   │   ├── raw_orders.yml
│   │   ├── orders_updates.yml
│   │   ├── sales_events.yml
│   │   └── sales_snapshot.yml
│   ├── transforms/
│   │   ├── orders_cleaned.yml
│   │   ├── orders_merged.yml
│   │   ├── daily_revenue.yml
│   │   └── events_cleaned.yml
│   ├── rules/
│   │   ├── not_null_quantity.yml
│   │   └── positive_quantity.yml
│   ├── pipelines/
│   └── common/
└── target/
    └── intermediate/
        ├── source.raw_orders.parquet
        ├── source.orders_updates.parquet
        ├── source.sales_events.parquet
        ├── source.sales_snapshot.parquet
        ├── transform.orders_cleaned.parquet
        ├── transform.orders_merged.parquet
        ├── transform.daily_revenue.parquet
        └── transform.events_cleaned.parquet
```

---

Continue to [Module 5: DRY Config & Python API](05_dry_config_and_python_api.md)
