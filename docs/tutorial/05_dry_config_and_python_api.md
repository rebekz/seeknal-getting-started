# Module 5: DRY Config & Python API

> **Duration:** ~50 minutes | **Difficulty:** Intermediate

In this module, you will eliminate duplicated configuration using Seeknal's common config system, then write your first Python pipeline nodes — unlocking the full power of code-based data processing alongside declarative YAML.

---

## Why This Matters in Industry

At scale, companies operate **hundreds** of transforms. Column names change, SQL expressions get copy-pasted across files, and teams lose track of shared logic. The consequences are real:

- **Stripe** manages thousands of payment data transforms. When a column is renamed in an upstream source, every downstream reference must update. Without centralized config, engineers miss references and pipelines break silently.
- **Airbnb** standardized their metric definitions in a shared configuration layer after discovering that 5 different teams had 5 different definitions of "active user" — each producing different numbers on different dashboards.
- **Spotify** uses Python-based pipeline nodes for ML feature computation that cannot be expressed in pure SQL: windowed statistics, external API calls, and custom encodings.

Two principles drive this module:

| Principle | Problem It Solves |
|-----------|-------------------|
| **DRY (Don't Repeat Yourself)** | Column names and SQL expressions defined once, referenced everywhere |
| **Right tool for the job** | YAML for declarative SQL transforms, Python when you need libraries and logic |

---

## Prerequisites

- Completed [Module 1](01_introduction_and_setup.md), [Module 2](02_data_transformation.md), [Module 3](03_data_quality_and_testing.md), and [Module 4](04_advanced_sources_and_cdc.md)
- All files from previous modules in place, including `seeknal/sources/products.yml`, `seeknal/transforms/events_cleaned.yml`, and `seeknal/sources/sales_events.yml`

---

## What You'll Build

By the end of this module, you will have:

1. **Common configuration files** — column aliases, reusable SQL expressions, and shared rule fragments
2. **Transforms using `{{ }}` template variables** — referencing common config instead of hardcoding values
3. **Your first Python source node** — using the `@source` decorator
4. **Your first Python transform node** — using the `@transform` decorator and the `ctx` object
5. A clear understanding of **when to use YAML vs Python**

---

## Step 5.1: Create Common Source Configuration

When you write SQL transforms, you hardcode column names like `product_id`, `quantity`, `price` directly. If the upstream schema changes — say `quantity` becomes `qty` — you must find and update every reference across every file.

Common source configuration solves this. Define column aliases once, reference them everywhere with `{{ }}` template syntax.

Create the common sources file.

**`seeknal/common/sources.yml`**

```yaml
sources:
- id: events
  ref: source.sales_events
  params:
    idCol: event_id
    productCol: product_id
    quantityCol: quantity
    dateCol: sale_date
    regionCol: region
- id: products
  ref: source.products
  params:
    idCol: product_id
    nameCol: name
    categoryCol: category
    priceCol: price
```

Each entry has three parts:

| Field | Purpose |
|-------|---------|
| `id` | The alias prefix used in templates (e.g., `events`, `products`) |
| `ref` | The actual Seeknal source node this maps to |
| `params` | Key-value pairs that become template variables |

After this file exists, you can write `{{events.quantityCol}}` in any transform, and Seeknal replaces it with `quantity` at execution time. If the column is later renamed to `qty`, you change it in one place — this file — and every transform updates automatically.

---

## Step 5.2: Create Reusable SQL Expressions

Beyond column names, you can centralize entire SQL expressions that appear in multiple transforms.

**`seeknal/common/transformations.yml`**

```yaml
transformations:
- id: totalAmount
  sql: '{{events.quantityCol}} * {{products.priceCol}}'
- id: revenueShare
  sql: ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER (), 2)
```

Notice that `totalAmount` itself uses template variables from the sources config. Templates compose — Seeknal resolves them recursively:

1. `{{transformations.totalAmount}}` resolves to `{{events.quantityCol}} * {{products.priceCol}}`
2. `{{events.quantityCol}}` resolves to `quantity`
3. `{{products.priceCol}}` resolves to `price`
4. Final SQL: `quantity * price`

The `revenueShare` expression computes a percentage-of-total using a window function. Any transform that needs this calculation references `{{transformations.revenueShare}}` instead of duplicating the formula.

---

## Step 5.3: Create Shared Rule Expressions

Rule expressions are reusable SQL boolean fragments for `WHERE` clauses and filter conditions.

**`seeknal/common/rules.yml`**

```yaml
rules:
- id: hasQuantity
  value: quantity IS NOT NULL AND quantity > 0
- id: validPrice
  value: price >= 0 AND price < 10000
- id: completedOrder
  value: category IS NOT NULL
```

When you write `WHERE {{rules.hasQuantity}}` in a transform, Seeknal injects the SQL fragment `quantity IS NOT NULL AND quantity > 0`.

> **Don't confuse these two — they share the word "rules" but serve completely different purposes!**
>
> | File | Location | Purpose | How It's Used |
> |------|----------|---------|---------------|
> | **Common rule expressions** | `seeknal/common/rules.yml` | Reusable SQL fragments | Referenced as `{{rules.hasQuantity}}` in transform SQL |
> | **Validation rule nodes** | `seeknal/rules/*.yml` | Quality checks that pass or fail | Declared with `kind: rule`, run automatically by the pipeline |
>
> `seeknal/common/rules.yml` is a **configuration file** that defines text substitutions.
> `seeknal/rules/positive_quantity.yml` is a **pipeline node** that validates data and halts on failure.
>
> If you put a `kind: rule` node definition in `seeknal/common/`, it will not work.
> If you put a text substitution in `seeknal/rules/`, it will not work either.

---

## Step 5.4: Build sales_enriched Using Common Config

Now use the common configuration to build a transform that joins sales events with the product catalog. Instead of hardcoding column names, reference the template variables.

```bash
seeknal draft transform sales_enriched
```

Edit the draft file:

**`draft_transform_sales_enriched.yml`**

```yaml
kind: transform
name: sales_enriched
description: "Join sales events with product catalog"
inputs:
  - ref: transform.events_cleaned
  - ref: source.products
transform: |
  SELECT
      e.{{events.idCol}} AS event_id,
      e.{{events.productCol}} AS product_id,
      p.{{products.nameCol}} AS product_name,
      p.{{products.categoryCol}} AS category,
      e.{{events.quantityCol}} AS quantity,
      p.{{products.priceCol}} AS price,
      {{transformations.totalAmount}} AS total_amount,
      e.{{events.dateCol}} AS sale_date,
      e.{{events.regionCol}} AS region
  FROM ref('transform.events_cleaned') e
  LEFT JOIN ref('source.products') p
      ON e.{{events.productCol}} = p.{{products.idCol}}
```

### What the template variables expand to

Here is the SQL that Seeknal actually executes after resolving all `{{ }}` variables:

```sql
SELECT
    e.event_id AS event_id,
    e.product_id AS product_id,
    p.name AS product_name,
    p.category AS category,
    e.quantity AS quantity,
    p.price AS price,
    quantity * price AS total_amount,
    e.sale_date AS sale_date,
    e.region AS region
FROM ref('transform.events_cleaned') e
LEFT JOIN ref('source.products') p
    ON e.product_id = p.product_id
```

Validate and apply:

```bash
seeknal dry-run draft_transform_sales_enriched.yml
seeknal apply draft_transform_sales_enriched.yml
```

The `LEFT JOIN` is intentional. Recall from Module 4 that `events_cleaned` contains EVT-004 with `product_id = PRD-999`, which does not exist in the product catalog. A LEFT JOIN keeps this row with NULL product fields instead of silently dropping it. In production, orphan references like this are investigated — they might indicate a catalog sync delay, a data entry error, or a product that was deleted.

---

## Step 5.5: Build sales_summary Using Common Config

Create an aggregation transform that summarizes revenue by product category, using template variables for column references and the shared `revenueShare` expression.

```bash
seeknal draft transform sales_summary
```

Edit the draft file:

**`draft_transform_sales_summary.yml`**

```yaml
kind: transform
name: sales_summary
description: "Category-level sales aggregation"
inputs:
  - ref: transform.sales_enriched
transform: |
  SELECT
      {{products.categoryCol}} AS category,
      COUNT(*) AS total_events,
      SUM({{events.quantityCol}}) AS total_quantity,
      SUM(total_amount) AS total_revenue,
      {{transformations.revenueShare}} AS revenue_share_pct
  FROM ref('transform.sales_enriched')
  WHERE {{rules.completedOrder}}
  GROUP BY {{products.categoryCol}}
  ORDER BY total_revenue DESC
```

Three common config references in one transform:

| Template | Resolves To | Source File |
|----------|-------------|-------------|
| `{{products.categoryCol}}` | `category` | `common/sources.yml` |
| `{{events.quantityCol}}` | `quantity` | `common/sources.yml` |
| `{{transformations.revenueShare}}` | `ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER (), 2)` | `common/transformations.yml` |
| `{{rules.completedOrder}}` | `category IS NOT NULL` | `common/rules.yml` |

Validate and apply:

```bash
seeknal dry-run draft_transform_sales_summary.yml
seeknal apply draft_transform_sales_summary.yml
```

The `WHERE {{rules.completedOrder}}` clause filters out the orphan EVT-004 row (where `category IS NULL` because `PRD-999` does not exist). This is the same row that came through the LEFT JOIN with NULLs — now it is excluded from the summary.

---

## Step 5.6: When to Use YAML vs Python

So far, every pipeline node has been a YAML file with SQL. This works well for declarative data transformations. But some tasks require imperative logic, external libraries, or computation that SQL cannot express cleanly.

| Use YAML When... | Use Python When... |
|---|---|
| SQL transformations (SELECT, JOIN, GROUP BY) | Complex business logic with conditionals and loops |
| Simple source definitions (CSV, Parquet, JSONL) | External library integration (pandas, scikit-learn, requests) |
| Standard aggregations and window functions | ML feature computation (rolling stats, embeddings) |
| Team prefers declarative, auditable config | Custom data processing (API calls, parsing, encoding) |

The key insight: **Python nodes and YAML nodes live in the same DAG.** A Python transform can reference a YAML source, and a YAML transform can reference a Python transform's output. They are interchangeable from the dependency graph's perspective.

---

## Step 5.7: Create Your First Python Source

Python source nodes live in `seeknal/pipelines/` and use the `@source` decorator. Create a transaction data source.

First, create the data file.

**`data/transactions.csv`**

```csv
customer_id,order_id,order_date,revenue,product_category,region
CUST-100,ORD-1001,2026-01-10,49.99,electronics,north
CUST-100,ORD-1002,2026-01-15,99.99,clothing,north
CUST-101,ORD-1003,2026-01-11,199.50,electronics,south
CUST-101,ORD-1004,2026-01-18,210.00,electronics,south
CUST-102,ORD-1005,2026-01-13,75.25,food,east
CUST-103,ORD-1006,2026-01-14,45.99,clothing,west
CUST-104,ORD-1007,2026-01-16,199.95,electronics,north
CUST-105,ORD-1008,2026-01-12,250.00,electronics,south
CUST-100,ORD-1009,2026-01-19,35.00,food,north
CUST-101,ORD-1010,2026-01-20,89.99,clothing,south
```

Now create the Python source node.

**`seeknal/pipelines/transactions.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

from seeknal.pipeline import source

@source(
    name="transactions",
    source="csv",
    table="data/transactions.csv",
    description="Customer transaction history for feature engineering",
)
def transactions(ctx=None):
    pass
```

### Anatomy of a Python Source

Every piece of this file has a purpose:

| Component | What It Does |
|-----------|--------------|
| `# /// script` block | PEP 723 inline metadata — declares Python version and package dependencies |
| `from seeknal.pipeline import source` | Imports the `@source` decorator from the Seeknal SDK |
| `@source(name=..., source=..., table=...)` | Registers this function as a data source node in the pipeline DAG |
| `def transactions(ctx=None):` | The function signature — `ctx` is an optional context object |
| `pass` | The body is empty because Seeknal handles CSV loading automatically |

Why is the function body `pass`? For file-based sources (CSV, Parquet, JSONL), Seeknal reads the file using the `source` and `table` parameters. The function exists only to provide the decorator a place to attach metadata. The `ctx=None` parameter is included by convention — it becomes useful in transform nodes.

### YAML Source vs Python Source

Compare the two approaches for the same result:

**YAML approach** (from Module 4):

```yaml
kind: source
name: sales_events
source: jsonl
table: "data/sales_events.jsonl"
```

**Python approach** (this module):

```python
@source(
    name="transactions",
    source="csv",
    table="data/transactions.csv",
)
def transactions(ctx=None):
    pass
```

For simple file sources, both are equivalent. The Python approach becomes valuable when you need to add preprocessing logic inside the function body — something YAML cannot do.

---

## Step 5.8: Create Your First Python Transform

Python transforms are where the real power lives. Create a daily aggregation of transaction data using the `@transform` decorator and the `ctx` object.

**`seeknal/pipelines/customer_daily_agg.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

from seeknal.pipeline import transform

@transform(
    name="customer_daily_agg",
    description="Aggregate transactions to daily customer level with region context",
)
def customer_daily_agg(ctx):
    df = ctx.ref("source.transactions")
    return ctx.duckdb.sql("""
        SELECT
            customer_id,
            region,
            CAST(order_date AS DATE) AS order_date,
            CURRENT_DATE AS application_date,
            CAST(SUM(revenue) AS DOUBLE) AS daily_amount,
            CAST(COUNT(*) AS BIGINT) AS daily_count
        FROM df
        GROUP BY customer_id, region, CAST(order_date AS DATE)
    """).df()
```

### The ctx Object — Your Pipeline Interface

The `ctx` parameter is the bridge between your Python code and the Seeknal pipeline. It provides three critical methods:

| Method | What It Does | Returns |
|--------|-------------|---------|
| `ctx.ref("node.name")` | Loads the output of any upstream node | pandas DataFrame |
| `ctx.duckdb.sql("...")` | Executes a DuckDB SQL query | DuckDB relation object |
| `.df()` | Converts a DuckDB relation to a pandas DataFrame | pandas DataFrame |

### Step-by-step execution flow

Here is what happens when Seeknal executes this transform:

1. **`df = ctx.ref("source.transactions")`** — Seeknal looks up `source.transactions` in the DAG, loads its cached Parquet output, and returns it as a pandas DataFrame stored in the variable `df`.

2. **`ctx.duckdb.sql("SELECT ... FROM df ...")`** — DuckDB can query pandas DataFrames by variable name. The `df` variable is automatically accessible inside the SQL string. This gives you the expressiveness of SQL with the flexibility of Python.

3. **`CAST(SUM(revenue) AS DOUBLE)`** — Explicit type casting ensures consistent output types regardless of input data quirks.

4. **`.df()`** — Converts the DuckDB query result back to a pandas DataFrame.

5. **`return ...`** — The returned DataFrame becomes this node's output. Downstream nodes that reference `transform.customer_daily_agg` will receive this exact DataFrame.

### Cross-language References

Python nodes can reference YAML nodes and vice versa. The DAG does not care what language defined a node:

```python
# In a Python transform, reference a YAML source:
df = ctx.ref("source.raw_orders")        # defined in seeknal/sources/raw_orders.yml

# Or reference another Python source:
df = ctx.ref("source.transactions")       # defined in seeknal/pipelines/transactions.py

# Or reference a YAML transform:
df = ctx.ref("transform.orders_cleaned")  # defined in seeknal/transforms/orders_cleaned.yml
```

Similarly, a YAML transform can reference a Python transform's output:

```yaml
# In a YAML transform:
inputs:
  - ref: transform.customer_daily_agg    # defined in seeknal/pipelines/customer_daily_agg.py
transform: |
  SELECT * FROM ref('transform.customer_daily_agg') WHERE daily_amount > 100
```

This interoperability is what makes Seeknal powerful — use the right tool for each node without being locked into a single approach.

---

## Step 5.9: Run and Explore

Run the full pipeline, which now includes common config resolution, template expansion, and Python node execution.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing 14 node(s)...
  ✓ source.raw_orders (13 rows)
  ✓ source.orders_updates (4 rows)
  ✓ source.sales_events (7 rows)
  ✓ source.sales_snapshot
  ✓ source.products (6 rows)
  ✓ source.transactions (10 rows)
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.orders_merged (13 rows)
  ✓ transform.daily_revenue (8 rows)
  ✓ transform.events_cleaned (5 rows)
  ✓ transform.sales_enriched (5 rows)
  ✓ transform.sales_summary (4 rows)
  ✓ transform.customer_daily_agg (9 rows)
  ✓ rule.not_null_quantity: PASSED
  ✓ rule.positive_quantity: PASSED
Pipeline completed successfully.
```

### What just happened?

1. Seeknal scanned `seeknal/common/` and loaded all template variables from `sources.yml`, `transformations.yml`, and `rules.yml`.
2. When processing `sales_enriched.yml`, it expanded every `{{ }}` variable — `{{events.idCol}}` became `event_id`, `{{transformations.totalAmount}}` became `quantity * price`, and so on.
3. `sales_enriched` joined `events_cleaned` (5 rows) with `products` (6 rows) via LEFT JOIN, producing 5 rows (one per event, with product details attached where the product exists).
4. `sales_summary` aggregated the enriched data by category, filtering out rows where `category IS NULL` (the orphan EVT-004 / PRD-999 row), producing 4 category rows.
5. Seeknal detected `transactions.py` in `seeknal/pipelines/`, executed the `@source` decorator, and loaded the CSV as `source.transactions` (10 rows).
6. Seeknal executed `customer_daily_agg.py`, which called `ctx.ref("source.transactions")` to load the 10 transactions, then aggregated them to 9 daily customer-region rows.

---

## Step 5.10: Verify with the REPL

Open the REPL and verify each new node.

```bash
seeknal repl
```

### Verify: Common Config Template Expansion

Check that `sales_enriched` correctly joined events with products.

```sql
SELECT * FROM "transform.sales_enriched" LIMIT 5;
```

Expected output:

```
┌──────────┬────────────┬──────────────────────┬─────────────┬──────────┬───────┬──────────────┬────────────┬────────┐
│ event_id │ product_id │    product_name       │  category   │ quantity │ price │ total_amount │ sale_date  │ region │
├──────────┼────────────┼──────────────────────┼─────────────┼──────────┼───────┼──────────────┼────────────┼────────┤
│ EVT-001  │ PRD-001    │ Wireless Headphones  │ Electronics │        2 │ 79.99 │       159.98 │ 2026-01-13 │ north  │
│ EVT-002  │ PRD-003    │ Coffee Maker         │ Kitchen     │        1 │ 49.99 │        49.99 │ 2026-01-10 │ south  │
│ EVT-004  │ PRD-999    │                      │             │        3 │       │              │ 2026-01-11 │ east   │
│ EVT-005  │ PRD-002    │ Running Shoes        │ Apparel     │        1 │120.00 │       120.00 │ 2026-01-12 │ south  │
│ EVT-006  │ PRD-004    │ Yoga Mat             │ Sports      │        5 │ 35.00 │       175.00 │ 2026-01-12 │ west   │
└──────────┴────────────┴──────────────────────┴─────────────┴──────────┴───────┴──────────────┴────────────┴────────┘
```

### Verify: Orphan Product Reference

Confirm that EVT-004 (product PRD-999) appears with NULL product fields.

```sql
SELECT event_id, product_id, product_name, category, total_amount
FROM "transform.sales_enriched"
WHERE product_name IS NULL;
```

Expected output:

```
┌──────────┬────────────┬──────────────┬──────────┬──────────────┐
│ event_id │ product_id │ product_name │ category │ total_amount │
├──────────┼────────────┼──────────────┼──────────┼──────────────┤
│ EVT-004  │ PRD-999    │              │          │              │
└──────────┴────────────┴──────────────┴──────────┴──────────────┘
```

This row exists because of the LEFT JOIN. The `sales_summary` transform filters it out with `WHERE {{rules.completedOrder}}` (which expands to `WHERE category IS NOT NULL`).

### Verify: Sales Summary

```sql
SELECT * FROM "transform.sales_summary";
```

Expected output (4 rows — EVT-004 excluded):

```
┌─────────────┬──────────────┬────────────────┬───────────────┬───────────────────┐
│  category   │ total_events │ total_quantity │ total_revenue │ revenue_share_pct │
├─────────────┼──────────────┼────────────────┼───────────────┼───────────────────┤
│ Sports      │            1 │              5 │        175.00 │             34.65 │
│ Electronics │            1 │              2 │        159.98 │             31.68 │
│ Apparel     │            1 │              1 │        120.00 │             23.76 │
│ Kitchen     │            1 │              1 │         49.99 │              9.90 │
└─────────────┴──────────────┴────────────────┴───────────────┴───────────────────┘
```

Notice that `revenue_share_pct` sums to approximately 100% — this is the `{{transformations.revenueShare}}` expression at work.

### Verify: Python Source

```sql
SELECT * FROM "source.transactions" LIMIT 5;
```

Expected output:

```
┌─────────────┬──────────┬─────────────────────┬─────────┬──────────────────┬────────┐
│ customer_id │ order_id │     order_date      │ revenue │ product_category │ region │
├─────────────┼──────────┼─────────────────────┼─────────┼──────────────────┼────────┤
│ CUST-100    │ ORD-1001 │ 2026-01-10          │   49.99 │ electronics      │ north  │
│ CUST-100    │ ORD-1002 │ 2026-01-15          │   99.99 │ clothing         │ north  │
│ CUST-101    │ ORD-1003 │ 2026-01-11          │  199.50 │ electronics      │ south  │
│ CUST-101    │ ORD-1004 │ 2026-01-18          │  210.00 │ electronics      │ south  │
│ CUST-102    │ ORD-1005 │ 2026-01-13          │   75.25 │ food             │ east   │
└─────────────┴──────────┴─────────────────────┴─────────┴──────────────────┴────────┘
```

### Verify: Python Transform

```sql
SELECT * FROM "transform.customer_daily_agg" ORDER BY customer_id, order_date;
```

Expected output (9 rows — daily aggregation per customer per region):

```
┌─────────────┬────────┬────────────┬──────────────────┬──────────────┬─────────────┐
│ customer_id │ region │ order_date │ application_date │ daily_amount │ daily_count │
├─────────────┼────────┼────────────┼──────────────────┼──────────────┼─────────────┤
│ CUST-100    │ north  │ 2026-01-10 │ 2026-03-05       │        49.99 │           1 │
│ CUST-100    │ north  │ 2026-01-15 │ 2026-03-05       │        99.99 │           1 │
│ CUST-100    │ north  │ 2026-01-19 │ 2026-03-05       │        35.00 │           1 │
│ CUST-101    │ south  │ 2026-01-11 │ 2026-03-05       │       199.50 │           1 │
│ CUST-101    │ south  │ 2026-01-18 │ 2026-03-05       │       210.00 │           1 │
│ CUST-101    │ south  │ 2026-01-20 │ 2026-03-05       │        89.99 │           1 │
│ CUST-102    │ east   │ 2026-01-13 │ 2026-03-05       │        75.25 │           1 │
│ CUST-103    │ west   │ 2026-01-14 │ 2026-03-05       │        45.99 │           1 │
│ CUST-104    │ north  │ 2026-01-16 │ 2026-03-05       │       199.95 │           1 │
│ CUST-105    │ south  │ 2026-01-12 │ 2026-03-05       │       250.00 │           1 │
└─────────────┴────────┴────────────┴──────────────────┴──────────────┴─────────────┘
```

Each row represents one customer's transactions on one day in one region. The `application_date` is the date the transform ran (`CURRENT_DATE`). This aggregated structure is the foundation for feature engineering in Module 6.

Exit the REPL:

```bash
.exit
```

---

## Updated DAG

Your pipeline DAG now has two additional branches — the common-config-powered sales transforms and the Python-based transaction transforms:

```
source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue
                                                        ↑
                                          source.orders_updates

source.sales_events ──→ transform.events_cleaned ──→ transform.sales_enriched ──→ transform.sales_summary
                              ↓                            ↑
                    rule.not_null_quantity        source.products
                    rule.positive_quantity

source.transactions (Python) ──→ transform.customer_daily_agg (Python)

source.sales_snapshot (standalone)
```

Notice the mix of YAML and Python nodes in the same DAG. Seeknal resolves dependencies regardless of how nodes are defined.

---

## Common Mistakes

### Mistake 1: Referencing Common Config That Doesn't Exist

```yaml
# WRONG — 'customers' is not defined in common/sources.yml
SELECT {{customers.nameCol}} FROM ...

# CORRECT — use only IDs defined in your common config files
SELECT {{products.nameCol}} FROM ...
```

If you reference a template variable that does not exist, Seeknal will raise an error at planning time — before any SQL executes. Check your `common/sources.yml` for available IDs.

### Mistake 2: Confusing common/rules.yml with seeknal/rules/*.yml

```yaml
# WRONG — trying to use a validation rule node as a template variable
WHERE {{not_null_quantity}}

# CORRECT — reference common rule expressions
WHERE {{rules.hasQuantity}}
```

`seeknal/rules/not_null_quantity.yml` is a pipeline node (with `kind: rule`). It runs quality checks. You cannot reference it with `{{ }}` template syntax.

`seeknal/common/rules.yml` defines text substitutions. Only entries in this file are available as `{{rules.*}}`.

### Mistake 3: Forgetting to Return a DataFrame in Python Transforms

```python
# WRONG — no return statement; downstream nodes receive None
@transform(name="my_transform")
def my_transform(ctx):
    df = ctx.ref("source.transactions")
    ctx.duckdb.sql("SELECT * FROM df")  # result is discarded

# CORRECT — return the DataFrame
@transform(name="my_transform")
def my_transform(ctx):
    df = ctx.ref("source.transactions")
    return ctx.duckdb.sql("SELECT * FROM df").df()
```

The `return` statement is what makes the node's output available to the rest of the pipeline. Without it, any downstream node that calls `ctx.ref("transform.my_transform")` will receive nothing.

### Mistake 4: Using ctx in a Source Node

```python
# WRONG — source nodes don't receive upstream data
@source(name="my_source", source="csv", table="data/file.csv")
def my_source(ctx):
    df = ctx.ref("source.other")  # sources don't reference other nodes
    return df

# CORRECT — source body is pass for file-based sources
@source(name="my_source", source="csv", table="data/file.csv")
def my_source(ctx=None):
    pass
```

Sources are entry points in the DAG — they have no upstream dependencies. The `ctx=None` default signals that the context object is not used.

---

## Concepts Recap

### Common Configuration

| Config File | What It Centralizes | Template Syntax |
|-------------|--------------------|--------------------|
| `common/sources.yml` | Column name aliases for data sources | `{{events.quantityCol}}` |
| `common/transformations.yml` | Reusable SQL expressions | `{{transformations.totalAmount}}` |
| `common/rules.yml` | Reusable SQL boolean fragments | `{{rules.hasQuantity}}` |

### Python Pipeline Nodes

| Decorator | Purpose | Function Body |
|-----------|---------|---------------|
| `@source(...)` | Declare a data source | `pass` for file-based; custom logic for API/computed sources |
| `@transform(...)` | Declare a data transformation | Must return a pandas DataFrame |

### The ctx Object

| Method | Returns | When to Use |
|--------|---------|-------------|
| `ctx.ref("node.name")` | pandas DataFrame | Load any upstream node's output |
| `ctx.duckdb.sql("...")` | DuckDB relation | Run SQL on DataFrames by variable name |
| `.df()` | pandas DataFrame | Convert DuckDB result for return |

---

## Checkpoint

By the end of this module, you should have:

- [ ] Created 3 common config files (`common/sources.yml`, `common/transformations.yml`, `common/rules.yml`)
- [ ] Created `sales_enriched` transform using `{{ }}` template variables
- [ ] Created `sales_summary` transform referencing shared expressions and rules
- [ ] Understood the difference between `seeknal/common/rules.yml` and `seeknal/rules/*.yml`
- [ ] Created your first Python source (`seeknal/pipelines/transactions.py`)
- [ ] Created your first Python transform (`seeknal/pipelines/customer_daily_agg.py`)
- [ ] Understood when to use YAML vs Python
- [ ] Understood the `ctx` object: `ctx.ref()`, `ctx.duckdb.sql()`, and `.df()`

Your project structure should now look like this:

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   ├── orders.csv
│   ├── orders_updates.csv
│   ├── products.csv
│   ├── sales_events.jsonl
│   ├── sales_snapshot.parquet
│   └── transactions.csv                  ← NEW
├── seeknal/
│   ├── sources/
│   │   ├── raw_orders.yml
│   │   ├── orders_updates.yml
│   │   ├── products.yml
│   │   ├── sales_events.yml
│   │   └── sales_snapshot.yml
│   ├── transforms/
│   │   ├── orders_cleaned.yml
│   │   ├── orders_merged.yml
│   │   ├── daily_revenue.yml
│   │   ├── events_cleaned.yml
│   │   ├── sales_enriched.yml            ← NEW
│   │   └── sales_summary.yml             ← NEW
│   ├── rules/
│   │   ├── order_revenue_valid.yml
│   │   ├── order_not_null.yml
│   │   ├── not_null_quantity.yml
│   │   └── positive_quantity.yml
│   ├── pipelines/
│   │   ├── transactions.py               ← NEW (Python source)
│   │   └── customer_daily_agg.py         ← NEW (Python transform)
│   └── common/
│       ├── sources.yml                   ← NEW
│       ├── transformations.yml           ← NEW
│       └── rules.yml                     ← NEW
└── target/
    └── intermediate/
        ├── source.raw_orders.parquet
        ├── source.orders_updates.parquet
        ├── source.sales_events.parquet
        ├── source.sales_snapshot.parquet
        ├── source.products.parquet
        ├── source.transactions.parquet
        ├── transform.orders_cleaned.parquet
        ├── transform.orders_merged.parquet
        ├── transform.daily_revenue.parquet
        ├── transform.events_cleaned.parquet
        ├── transform.sales_enriched.parquet
        ├── transform.sales_summary.parquet
        └── transform.customer_daily_agg.parquet
```

---

Continue to [Module 6: Feature Engineering for ML](06_feature_engineering_for_ml.md)
