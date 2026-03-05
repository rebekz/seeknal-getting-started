# Module 7: Semantic Layer & Metrics

> **Duration:** ~40 minutes | **Difficulty:** Intermediate

In this module, you will build a semantic layer that defines business metrics once and makes them available to every consumer — dashboards, reports, APIs — with guaranteed consistency.

---

## Why This Matters in Industry

Ask three teams "What is our revenue?" and you will get three different answers. Marketing includes refunds (gross revenue), Finance excludes them (net revenue), Product divides by active users (ARPU). The CEO opens three dashboards and sees three different numbers.

| Company | Semantic Layer Approach | Result |
|---------|------------------------|--------|
| **Airbnb** | Central metrics layer defining "bookings," "revenue," "active listings" | Every team sees the same numbers |
| **Spotify** | Shared metric definitions for "monthly active users," "stream counts" | Consistent reporting across teams |
| **Uber** | Semantic layer for "trip completed," "gross bookings," "take rate" | Single source of truth across 6,000+ employees |

The semantic layer bridges data engineering (pipelines) and business stakeholders (dashboards). Without it: "dashboard says X, report says Y, spreadsheet says Z."

---

## Prerequisites

- Completed [Module 1](01_introduction_and_setup.md) through [Module 6](06_pipeline_orchestration.md)
- `transform.orders_cleaned` from Module 2

---

## What You'll Build

1. A **semantic model** with entities, dimensions, measures, and metrics
2. An **exposure** declaring downstream data delivery to a finance team
3. Queries against the semantic layer via **REPL**

---

## Step 7.1: Semantic Model Components

A semantic model has four building blocks:

| Component | Purpose | Example |
|-----------|---------|---------|
| **Entity** | Primary/foreign keys that identify records | `order_id` (primary), `customer_id` (foreign) |
| **Dimension** | Axes for grouping and filtering | `order_date` (time), `status` (categorical) |
| **Measure** | Base aggregations on raw columns | `SUM(revenue)`, `COUNT(*)`, `AVG(revenue)` |
| **Metric** | Computed from one or more measures | `revenue / order_count`, cumulative revenue |

```
Entities         →  identify WHICH records
Dimensions       →  define HOW to slice
Measures         →  define WHAT to aggregate
Metrics          →  define HOW to compute business KPIs from measures
```

---

## Step 7.2: Create the Semantic Model

Draft the semantic model:

```bash
seeknal draft semantic-model orders
```

Edit the draft file:

**`draft_semantic_model_orders.yml`**

```yaml
kind: semantic_model
name: orders
description: "Business metrics for order analysis"
model: "ref('transform.orders_cleaned')"
default_time_dimension: order_date

entities:
  - name: order_id
    type: primary

  - name: customer_id
    type: foreign

dimensions:
  - name: order_date
    type: time
    expr: order_date
    time_granularity: day
    description: "Date the order was placed"

  - name: status
    type: categorical
    expr: status
    description: "Order status (Completed, Pending, etc.)"

measures:
  - name: total_revenue
    expr: revenue
    agg: sum
    description: "Sum of all order revenue"

  - name: order_count
    expr: "1"
    agg: sum
    description: "Count of all orders"

  - name: avg_order_value
    expr: revenue
    agg: average
    description: "Average revenue per order"

  - name: unique_customers
    expr: customer_id
    agg: count_distinct
    description: "Count of distinct customers"

metrics:
  - name: avg_order_value_ratio
    type: ratio
    numerator: total_revenue
    denominator: order_count
    description: "Revenue per order (ratio)"

  - name: cumulative_revenue
    type: cumulative
    measure: total_revenue
    grain_to_date: month
    description: "Running total revenue within each month"

  - name: revenue_per_customer
    type: derived
    expr: "total_revenue / unique_customers"
    metrics:
      - total_revenue
      - unique_customers
    description: "Average revenue per unique customer"
```

Validate and apply:

```bash
seeknal dry-run draft_semantic_model_orders.yml
seeknal apply draft_semantic_model_orders.yml
```

Walk through each section.

**model and default_time_dimension** — `model: "ref('transform.orders_cleaned')"` declares which transform feeds this semantic model. `default_time_dimension` sets the default time axis for time-series queries.

**Entities** — Keys that identify records. `primary` = unique identifier for each row. `foreign` = reference to another entity, signaling that joins are possible across semantic models.

**Dimensions** — Axes for slicing data. `time` dimensions support granularity levels (`day`, `week`, `month`, `quarter`, `year`). `categorical` dimensions support grouping and filtering.

**Measures** — Base aggregations. Each specifies an expression (`expr`) and an aggregation function (`agg`):

| `agg` | SQL Equivalent | Use Case |
|--------|---------------|----------|
| `sum` | `SUM(expr)` | Totals: revenue, items |
| `count_distinct` | `COUNT(DISTINCT expr)` | Unique values: customers |
| `average` | `AVG(expr)` | Averages: order value |
| `min` / `max` | `MIN(expr)` / `MAX(expr)` | Extremes |

Note: `order_count` uses `expr: "1"` with `agg: sum` — equivalent to `COUNT(*)`.

**Metrics** — Computed from measures. Three types covered in the next step.

---

## Step 7.3: Understanding Metric Types

### Ratio Metric

```yaml
- name: avg_order_value_ratio
  type: ratio
  numerator: total_revenue
  denominator: order_count
```

**Business question:** "How much revenue does each order generate on average?"

```
avg_order_value_ratio = total_revenue / order_count = SUM(revenue) / SUM(1)
```

### Cumulative Metric

```yaml
- name: cumulative_revenue
  type: cumulative
  measure: total_revenue
  grain_to_date: month
```

**Business question:** "How is revenue accumulating throughout the month?"

```
cumulative_revenue = running SUM(total_revenue) within each month
```

On January 1, cumulative revenue equals that day's revenue. On January 15, it equals the sum of January 1 through 15. On February 1, it resets.

### Derived Metric

```yaml
- name: revenue_per_customer
  type: derived
  expr: "total_revenue / unique_customers"
  metrics:
    - total_revenue
    - unique_customers
```

**Business question:** "How much does each unique customer spend?"

```
revenue_per_customer = SUM(revenue) / COUNT(DISTINCT customer_id)
```

### Comparison

| Type | Input | Reset Behavior | Example |
|------|-------|---------------|---------|
| `ratio` | Two measures (numerator/denominator) | None | Revenue per order |
| `cumulative` | One measure + grain boundary | Resets at boundary | Month-to-date revenue |
| `derived` | Expression over multiple metrics | None | Revenue per customer |

---

## Step 7.4: Create an Exposure

Exposures define how downstream consumers access your data — the final link from pipeline to delivery.

```bash
seeknal draft exposure revenue_export
```

Edit the draft file:

**`draft_exposure_revenue_export.yml`**

```yaml
kind: exposure
name: revenue_export
description: "Daily revenue CSV export for the finance team"
owner: "analytics-team@example.com"
type: file
depends_on:
  - ref: transform.daily_revenue
tags: [finance, daily]
params:
  format: csv
  path: "target/exports/revenue_export.csv"
```

| Field | Purpose |
|-------|---------|
| `owner` | Who is responsible for this data delivery |
| `type` | Delivery mechanism (`file`, `api`, or `database`) |
| `depends_on` | Which nodes feed this exposure |
| `tags` | Labels for filtering and organization |
| `params` | Format and destination configuration |

Validate and apply:

```bash
seeknal dry-run draft_exposure_revenue_export.yml
seeknal apply draft_exposure_revenue_export.yml
```

Exposures answer critical operational questions: "Who breaks if I change this transform?" "Who owns this data?" "How often is it delivered?"

---

## Step 7.5: Run and Query the Semantic Layer

Run the full pipeline.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing nodes...
  ✓ source.raw_orders (13 rows)
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.daily_revenue (7 rows)
  ✓ semantic_model.orders — registered
  ✓ exposure.revenue_export — registered
Pipeline completed successfully.
```

Open the REPL to query the semantic layer.

```bash
seeknal repl
```

**Total revenue by status:**

```sql
SELECT status, SUM(revenue) AS total_revenue, COUNT(*) AS order_count
FROM "transform.orders_cleaned"
GROUP BY status;
```

**Revenue per customer:**

```sql
SELECT
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(revenue) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
FROM "transform.orders_cleaned";
```

This query manually implements the `revenue_per_customer` derived metric. With the semantic layer, every consumer uses the same formula — no one can accidentally forget the `DISTINCT` or use a different rounding strategy.

**Monthly cumulative revenue:**

```sql
SELECT
    order_date,
    SUM(revenue) AS daily_revenue,
    SUM(SUM(revenue)) OVER (
        PARTITION BY DATE_TRUNC('month', order_date)
        ORDER BY order_date
    ) AS cumulative_revenue
FROM "transform.orders_cleaned"
GROUP BY order_date
ORDER BY order_date;
```

Query metrics directly through the CLI without writing SQL.

```bash
seeknal query --metrics total_revenue --dimensions status
```

```bash
seeknal query --metrics avg_order_value_ratio --dimensions order_date
```

Exit the REPL:

```bash
.exit
```

### What just happened?

1. The semantic model defined a consistent set of business metrics on top of `orders_cleaned`.
2. Anyone querying `total_revenue`, `order_count`, or `revenue_per_customer` gets the same definitions and calculations — regardless of which tool they use.
3. The exposure declared that `daily_revenue` data is delivered to the finance team as a daily CSV export.
4. You queried metrics both manually (REPL SQL) and declaratively (CLI `--metrics` flag), demonstrating the two access patterns the semantic layer supports.

---

## Step 7.6: Why This Matters — Before and After

### Without a Semantic Layer

```sql
-- Marketing's "revenue" (includes refunds)
SELECT SUM(revenue) FROM orders;

-- Finance's "revenue" (excludes refunds)
SELECT SUM(revenue) FROM orders WHERE status != 'Refunded';

-- Product's "revenue" (per active user)
SELECT SUM(revenue) / COUNT(DISTINCT user_id) FROM orders WHERE status = 'Completed';
```

Three teams, three definitions, three different numbers.

### With a Semantic Layer

Revenue is defined **once**:

```yaml
measures:
  - name: total_revenue
    expr: revenue
    agg: sum
```

Every consumer uses this definition. Change it in one place and the change propagates everywhere.

| Aspect | Without | With |
|--------|---------|------|
| Metric definitions | Scattered across SQL queries | Centralized in YAML |
| Changing a formula | Find and update every query | Change one file |
| Onboarding new analysts | "Ask Sarah how she calculates it" | Read the semantic model |
| Consistency | Hope everyone uses the same logic | Guaranteed by the system |

---

## Step 7.7: Best Practices

**Use business-oriented names:**

```yaml
# GOOD
measures:
  - name: total_revenue
  - name: unique_customers

# BAD
measures:
  - name: sum_rev_col
  - name: cnt_dist_cust
```

**Write descriptions for everything.** Every entity, dimension, measure, and metric should have a `description` field. These become documentation that both engineers and business users can read.

**One semantic model per business domain.** Organize by domain, not by table:

```
seeknal/semantic_models/
├── orders.yml        # Order metrics: revenue, AOV, order count
├── customers.yml     # Customer metrics: lifetime value, churn rate
└── products.yml      # Product metrics: units sold, return rate
```

---

## Common Mistakes

### Mistake 1: Duplicating Metric Logic in SQL

```sql
-- WRONG — hardcoding the formula in every query
SELECT SUM(revenue) / COUNT(*) AS aov FROM orders;
SELECT SUM(revenue) / COUNT(*) AS aov FROM orders WHERE region = 'north';
```

```yaml
# CORRECT — define it once
metrics:
  - name: avg_order_value_ratio
    type: ratio
    numerator: total_revenue
    denominator: order_count
```

### Mistake 2: Missing Descriptions

```yaml
# WRONG — no one knows what this means in 6 months
measures:
  - name: uc
    expr: customer_id
    agg: count_distinct

# CORRECT — self-documenting
measures:
  - name: unique_customers
    expr: customer_id
    agg: count_distinct
    description: "Count of distinct customers who placed at least one order"
```

### Mistake 3: Wrong Metric Type

```yaml
# WRONG — using derived when ratio is cleaner
metrics:
  - name: avg_order_value
    type: derived
    expr: "total_revenue / order_count"
    metrics: [total_revenue, order_count]

# CORRECT — ratio type is purpose-built for this
metrics:
  - name: avg_order_value
    type: ratio
    numerator: total_revenue
    denominator: order_count
```

Use `ratio` when dividing one measure by another. Use `derived` when the expression is more complex than a simple division.

---

## Checkpoint

Verify you have completed every step:

- [ ] Created `seeknal/semantic_models/orders.yml` with entities, dimensions, measures, and metrics
- [ ] Created `seeknal/exposures/revenue_export.yml` for finance team data delivery
- [ ] Ran the pipeline and saw the semantic model and exposure registered
- [ ] Queried the semantic layer via REPL (revenue by status, revenue per customer, cumulative revenue)
- [ ] Understood the three metric types: ratio, cumulative, derived
- [ ] Understood why a semantic layer prevents "different numbers" problems

### Project Structure

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
│   │   ├── order_revenue_valid.yml
│   │   ├── order_not_null.yml
│   │   ├── not_null_quantity.yml
│   │   ├── positive_quantity.yml
│   │   ├── valid_prices.yml
│   │   └── products_quality.yml
│   ├── profiles/
│   │   ├── products_stats.yml
│   │   └── products_price_stats.yml
│   ├── semantic_models/
│   │   └── orders.yml
│   ├── exposures/
│   │   └── revenue_export.yml
│   ├── pipelines/
│   └── common/
└── target/
    ├── intermediate/
    │   ├── source.raw_orders.parquet
    │   ├── source.orders_updates.parquet
    │   ├── source.sales_events.parquet
    │   ├── source.sales_snapshot.parquet
    │   ├── transform.orders_cleaned.parquet
    │   ├── transform.orders_merged.parquet
    │   ├── transform.daily_revenue.parquet
    │   └── transform.events_cleaned.parquet
    └── exports/
        └── revenue_export.csv
```

---

Continue to [Module 8: Production Patterns](08_production_patterns.md)
