# Module 2: Data Transformation

**Duration:** ~45 minutes | **Difficulty:** Beginner

In this module, you will clean messy raw data and build aggregation transforms — the core daily work of a data engineer.

---

## Why This Matters in Industry

Raw data is **always** messy in production systems. Consider these real-world disasters:

- **Knight Capital Group (2012):** A bad data transformation in their trading system caused $440 million in losses in 45 minutes. The firm nearly went bankrupt.
- **NASA Mars Climate Orbiter (1999):** A unit conversion error (pounds vs. newtons) destroyed a $327 million spacecraft. A single missing transform.
- **Healthcare.gov (2013):** Data quality issues in the enrollment pipeline caused weeks of outages during the ACA launch.

Data engineers spend **60-80% of their time** cleaning and transforming data. The four core transform patterns you will use throughout your career:

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Cleaning** | Fix nulls, whitespace, invalid values | `TRIM(status)`, `WHERE col IS NOT NULL` |
| **Normalization** | Standardize formats and types | `CAST(date_str AS DATE)` |
| **Deduplication** | Remove duplicate records | `ROW_NUMBER() OVER (PARTITION BY id ...)` |
| **Aggregation** | Summarize detail into metrics | `SUM(revenue) GROUP BY date` |

---

## Prerequisites

- Completed [Module 1: Your First Pipeline](01_your_first_pipeline.md)
- Files from Module 1: `seeknal_project.yml`, `data/orders.csv`, `seeknal/sources/raw_orders.yml`

---

## What You'll Build

By the end of this module, you will have:

1. A **cleaning transform** that fixes all 5 quality issues discovered in Module 1
2. An **aggregation transform** that produces daily revenue metrics
3. An understanding of the **DAG** (Directed Acyclic Graph) — how Seeknal decides execution order
4. Practice with the **safety workflow**: draft, dry-run, apply

---

## Step 2.1: Create the Cleaning Transform

Recall the 5 quality issues you found in Module 1's REPL exploration:

| Row | Issue | Fix |
|-----|-------|-----|
| ORD-003 | Missing `customer_id` (NULL) | Filter out the row |
| ORD-005 | Negative revenue (-10.00) | Set to 0 |
| ORD-006 | Whitespace in status ("  Completed  ") | Trim whitespace |
| ORD-007 | Negative items (-1) | Set to 0 |
| ORD-001 | Duplicate `order_id` (appears twice) | Keep latest record |

Draft the cleaning transform:

```bash
seeknal draft transform orders_cleaned
```

Edit the generated file with the cleaning logic.

**`seeknal/transforms/orders_cleaned.yml`**

```yaml
kind: transform
name: orders_cleaned
description: "Clean and validate raw order data"
inputs:
  - ref: source.raw_orders
transform: |
  SELECT
      order_id,
      customer_id,
      CAST(order_date AS DATE) AS order_date,
      TRIM(status) AS status,
      CASE WHEN revenue < 0 THEN 0 ELSE revenue END AS revenue,
      CASE WHEN items < 0 THEN 0 ELSE items END AS items,
      CURRENT_TIMESTAMP AS processed_at
  FROM ref('source.raw_orders')
  WHERE customer_id IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
      PARTITION BY order_id
      ORDER BY order_date DESC
  ) = 1
columns:
  order_id: "Deduplicated order identifier"
  customer_id: "Validated customer identifier (nulls removed)"
  order_date: "Order date cast to DATE type"
  status: "Trimmed order status"
  revenue: "Non-negative revenue (negatives set to 0)"
  items: "Non-negative item count"
  processed_at: "Timestamp when this transform ran"
```

Here is what each piece does:

| Line(s) | Purpose |
|----------|---------|
| `inputs: - ref: source.raw_orders` | Declares this transform depends on the `raw_orders` source |
| `ref('source.raw_orders')` in `FROM` | References the upstream data so Seeknal resolves it at runtime |
| `CAST(order_date AS DATE)` | Normalizes the date column to a proper `DATE` type |
| `TRIM(status)` | Removes leading/trailing whitespace from status values |
| `CASE WHEN revenue < 0 THEN 0 ...` | Replaces negative revenue with 0 |
| `CASE WHEN items < 0 THEN 0 ...` | Replaces negative item counts with 0 |
| `WHERE customer_id IS NOT NULL` | Drops rows where `customer_id` is missing |
| `QUALIFY ROW_NUMBER() OVER (...)` | Keeps only the latest record per `order_id` (deduplication) |
| `CURRENT_TIMESTAMP AS processed_at` | Adds an audit column recording when the transform ran |

Validate and apply:

```bash
seeknal dry-run seeknal/transforms/orders_cleaned.yml
seeknal apply seeknal/transforms/orders_cleaned.yml
```

---

### DuckDB Feature: QUALIFY

> **What is QUALIFY?**
>
> The `QUALIFY` clause is a DuckDB (and Snowflake) extension to standard SQL. It filters the results of **window functions**, similar to how `HAVING` filters results of `GROUP BY` aggregations.
>
> In standard SQL, you would need a subquery to achieve the same deduplication:
>
> ```sql
> SELECT * FROM (
>     SELECT
>         *,
>         ROW_NUMBER() OVER (
>             PARTITION BY order_id
>             ORDER BY order_date DESC
>         ) AS rn
>     FROM source_data
> ) sub
> WHERE rn = 1
> ```
>
> With `QUALIFY`, you write it in fewer lines and without a subquery:
>
> ```sql
> SELECT *
> FROM source_data
> QUALIFY ROW_NUMBER() OVER (
>     PARTITION BY order_id
>     ORDER BY order_date DESC
> ) = 1
> ```
>
> **Why this matters:** You will encounter `QUALIFY` frequently in modern data warehouses. Snowflake, DuckDB, and Teradata all support it. BigQuery and Postgres do not (yet), so you would use the subquery form there.

---

## Step 2.2: Understand the ref() Function

The `ref()` function is the backbone of Seeknal's dependency management. When you write `ref('source.raw_orders')` inside a transform's SQL, two things happen:

1. **At parse time:** Seeknal registers that `orders_cleaned` depends on `raw_orders`
2. **At runtime:** Seeknal replaces `ref('source.raw_orders')` with the actual table reference

Seeknal uses these declared dependencies to build a **DAG** (Directed Acyclic Graph). A DAG is a graph with no cycles — data flows in one direction, from sources through transforms to outputs.

Your current DAG looks like this:

```
source.raw_orders ──> transform.orders_cleaned
```

This is simple now, but DAGs in production can have hundreds of nodes. The key rule: **Seeknal guarantees that a node only runs after all its dependencies have completed.**

---

## Step 2.3: Create the Aggregation Transform

Now build a second transform that summarizes the cleaned orders into daily revenue metrics. This transform depends on `orders_cleaned`, not on the raw source.

Draft, edit, validate, and apply:

```bash
seeknal draft transform daily_revenue
```

**`seeknal/transforms/daily_revenue.yml`**

```yaml
kind: transform
name: daily_revenue
description: "Daily revenue aggregation from cleaned orders"
inputs:
  - ref: transform.orders_cleaned
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
      ROUND(
          SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
          2
      ) AS completion_rate
  FROM ref('transform.orders_cleaned')
  GROUP BY order_date
  ORDER BY order_date
```

Validate and apply:

```bash
seeknal dry-run seeknal/transforms/daily_revenue.yml
seeknal apply seeknal/transforms/daily_revenue.yml
```

Notice the `inputs` field references `transform.orders_cleaned` — not the raw source. This creates a chain of dependencies.

Your DAG now has three nodes:

```
source.raw_orders ──> transform.orders_cleaned ──> transform.daily_revenue
```

Seeknal will execute these left to right. If you later add a transform that also depends on `orders_cleaned`, Seeknal will run it in parallel with `daily_revenue` since they share the same dependency but do not depend on each other.

> **Note:** In Module 4, you will refactor `daily_revenue` to reference `transform.orders_merged` when you learn about Change Data Capture (CDC). For now, this direct chain is correct.

---

## Step 2.4: The Safety Workflow

Production data pipelines power dashboards, ML models, and business decisions. A broken transform can cascade into bad reports, wrong predictions, and lost revenue. Seeknal provides a three-step safety workflow to prevent this.

### draft — Generate a Template

The `draft` command scaffolds a new node file with the correct structure.

```bash
seeknal draft transform my_new_transform
```

This creates a template YAML file you can fill in. You do not need to memorize the YAML schema — `draft` gives you the skeleton.

### dry-run — Validate Without Executing

The `dry-run` command checks a node file for errors without actually running it.

```bash
seeknal dry-run seeknal/transforms/daily_revenue.yml
```

This validates:

- YAML syntax is correct
- SQL parses without errors
- All `ref()` dependencies exist
- Output schema can be inferred

If there is a typo in your SQL or a missing dependency, `dry-run` catches it before any data is touched.

### apply — Execute After Validation

The `apply` command runs a single node (and its dependencies if needed).

```bash
seeknal apply seeknal/transforms/daily_revenue.yml
```

This executes the transform and materializes the output.

### The Full Workflow

```
draft  ──>  dry-run  ──>  apply
(scaffold)  (validate)    (execute)
```

> **Industry context:** At companies like Stripe and Airbnb, data pipeline changes go through a review process similar to code review. You would never deploy code without testing it first — the same principle applies to data pipelines. A bad transform can corrupt downstream dashboards, ML models, and business reports. The draft, dry-run, apply workflow is Seeknal's built-in safety net.

---

## Step 2.5: Run the Full Pipeline

Run the entire pipeline with a single command.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing 3 node(s)...
  ✓ source.raw_orders (13 rows)
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.daily_revenue (7 rows)
Pipeline completed successfully.
```

The row counts tell the story of your cleaning logic: **13 rows in, 11 rows out.**

| Rows removed | Reason |
|--------------|--------|
| 1 row | ORD-003 filtered out (`customer_id IS NULL`) |
| 1 row | Duplicate ORD-001 removed (`QUALIFY ROW_NUMBER()`) |

The remaining 11 rows have trimmed statuses, non-negative revenues, and non-negative item counts.

### What just happened?

1. `seeknal run` read all node definitions and built the DAG
2. It executed `source.raw_orders` first — loaded 13 rows from `data/orders.csv`
3. Then `transform.orders_cleaned` ran, applying all 5 cleaning rules (13 rows became 11)
4. Finally `transform.daily_revenue` aggregated the 11 cleaned rows into 7 daily summary rows

---

## Step 2.6: Explore the Results

Open the Seeknal REPL to verify the cleaning worked.

```bash
seeknal repl
```

### Verify: No NULL customer_ids

```sql
SELECT COUNT(*) AS null_customers
FROM "transform.orders_cleaned"
WHERE customer_id IS NULL;
```

Expected result:

```
┌────────────────┐
│ null_customers │
├────────────────┤
│              0 │
└────────────────┘
```

### Verify: No negative revenue

```sql
SELECT COUNT(*) AS negative_revenue
FROM "transform.orders_cleaned"
WHERE revenue < 0;
```

Expected result:

```
┌──────────────────┐
│ negative_revenue │
├──────────────────┤
│                0 │
└──────────────────┘
```

### Verify: No duplicate order_ids

```sql
SELECT order_id, COUNT(*) AS cnt
FROM "transform.orders_cleaned"
GROUP BY order_id
HAVING cnt > 1;
```

Expected result: **0 rows returned.** Every `order_id` appears exactly once.

### Verify: Status values are trimmed

```sql
SELECT DISTINCT status, LENGTH(status) AS len
FROM "transform.orders_cleaned";
```

No status should have leading or trailing spaces. Check that the lengths match the visible characters.

### Verify: Negative values were corrected

```sql
SELECT order_id, revenue, items
FROM "transform.orders_cleaned"
WHERE order_id IN ('ORD-005', 'ORD-007');
```

Expected result:

```
┌──────────┬─────────┬───────┐
│ order_id │ revenue │ items │
├──────────┼─────────┼───────┤
│ ORD-005  │    0.00 │     1 │
│ ORD-007  │   15.00 │     0 │
└──────────┘─────────┘───────┘
```

Both negative values have been set to 0.

### Explore: Daily revenue summary

```sql
SELECT * FROM "transform.daily_revenue";
```

This shows one row per date with total orders, revenue, unique customers, and completion rate. Browse the output to confirm the aggregation looks reasonable.

### Exit the REPL

```sql
.exit
```

---

## Concepts Recap

### Transform Types

You built two types of transforms in this module:

| Type | Purpose | Your example |
|------|---------|-------------|
| **Cleaning** | Fix data quality issues | `orders_cleaned` |
| **Aggregation** | Summarize detail into metrics | `daily_revenue` |

Other common transform types you will encounter in later modules:

| Type | Purpose | Module |
|------|---------|--------|
| **Join/Merge** | Combine multiple sources | Module 4 (CDC) |
| **Pivot** | Reshape rows into columns | Module 6 |
| **Window** | Running totals, rankings | Module 5 |

### The DAG

Your pipeline's DAG after this module:

```
                    ┌───────────────────────┐
                    │   source.raw_orders   │
                    └───────────┬───────────┘
                                │
                                v
                    ┌───────────────────────────┐
                    │ transform.orders_cleaned  │
                    └───────────┬───────────────┘
                                │
                                v
                    ┌───────────────────────────┐
                    │  transform.daily_revenue  │
                    └───────────────────────────┘
```

Key properties of a DAG:

- **Directed:** Data flows in one direction (top to bottom)
- **Acyclic:** No circular dependencies allowed (A cannot depend on B if B depends on A)
- **Deterministic execution order:** Seeknal always runs parents before children

### The Safety Workflow

```
┌─────────┐     ┌──────────┐     ┌─────────┐
│  draft   │ ──> │ dry-run  │ ──> │  apply  │
│ scaffold │     │ validate │     │ execute │
└─────────┘     └──────────┘     └─────────┘
```

Always validate before executing. This becomes critical in Modules 6-8 when your pipelines interact with production systems.

---

## Common Mistakes

### Mistake 1: Forgetting ref() in the SQL

```yaml
# WRONG — hardcoded table name
transform: |
  SELECT * FROM raw_orders

# CORRECT — use ref() so Seeknal tracks the dependency
transform: |
  SELECT * FROM ref('source.raw_orders')
```

Without `ref()`, Seeknal cannot build the DAG and will not know to run the source first.

### Mistake 2: Wrong ref() prefix

```yaml
# WRONG — missing the "source." or "transform." prefix
transform: |
  SELECT * FROM ref('raw_orders')

# CORRECT — include the node type prefix
transform: |
  SELECT * FROM ref('source.raw_orders')
```

The format is always `ref('<kind>.<name>')`.

### Mistake 3: Circular dependencies

```yaml
# transform_a.yml
inputs:
  - ref: transform.transform_b

# transform_b.yml
inputs:
  - ref: transform.transform_a
```

This creates a cycle. Seeknal will reject it with an error. If you need shared logic, extract it into a third transform that both depend on.

---

## Checkpoint

By the end of this module, you should have:

- [ ] Created `seeknal/transforms/orders_cleaned.yml` that fixes all 5 quality issues
- [ ] Created `seeknal/transforms/daily_revenue.yml` for daily aggregation
- [ ] Understood how `ref()` creates dependencies in the DAG
- [ ] Learned the draft, dry-run, apply safety workflow
- [ ] Verified the cleaning worked through REPL queries

Your project structure should now look like this:

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   └── orders.csv
├── seeknal/
│   ├── sources/
│   │   └── raw_orders.yml
│   └── transforms/
│       ├── orders_cleaned.yml
│       └── daily_revenue.yml
└── target/
```

---

## What's Next

In [Module 3: Data Quality & Testing](03_data_quality_and_testing.md), you will add automated tests to your pipeline. Instead of manually checking for nulls and duplicates in the REPL, you will define assertions that run automatically and fail the pipeline if data quality degrades. This is how production pipelines stay reliable over time.
