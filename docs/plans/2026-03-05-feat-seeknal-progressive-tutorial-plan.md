---
title: "feat: Seeknal Progressive Tutorial — 8-Module E-Commerce Data Pipeline"
type: feat
status: completed
date: 2026-03-05
origin: docs/brainstorms/2026-03-05-seeknal-tutorial-brainstorm.md
---

# Seeknal Progressive Tutorial — 8-Module E-Commerce Data Pipeline

## Overview

Create an 8-module progressive tutorial that teaches undergraduate students how to build real-world data pipelines using Seeknal. The tutorial uses an e-commerce scenario with existing sample data, progresses from zero to production-grade patterns, and emphasizes industry context ("why this matters at real companies").

**Key change from brainstorm:** Module 4 was split into two modules (4: Advanced Sources & CDC, 5: DRY Config & Python API) based on SpecFlow analysis showing the original Module 4 was overloaded (~13 files for students to create in 60 minutes). The tutorial is now 8 modules instead of 7.

(see brainstorm: `docs/brainstorms/2026-03-05-seeknal-tutorial-brainstorm.md`)

---

## Problem Statement / Motivation

The `seeknal-getting-started` repository has a complete working example project (36 content files, 7 datasets) but no step-by-step tutorial narrative. Students cloning the repo see finished code without understanding how or why it was built. The dbt ecosystem's success was partly driven by its excellent progressive tutorials — Seeknal needs the same to drive adoption among data engineering students and junior engineers.

---

## Proposed Solution

Write 8 markdown tutorial documents plus 2 reference guides that progressively build the e-commerce pipeline from scratch. Each module:
- Starts with "Why this matters in industry" context
- Provides step-by-step instructions with exact code
- Shows commands to run and expected terminal output
- Includes a "What just happened?" explanation after key execution points
- Ends with a checkpoint summary

### Module Restructure (from original 7 to 8)

| # | Module | Files Created | Time Est. |
|---|--------|--------------|-----------|
| 1 | Introduction & Setup | `seeknal_project.yml`, `seeknal/sources/raw_orders.yml` | 30 min |
| 2 | Data Transformation | `seeknal/transforms/orders_cleaned.yml`, `seeknal/transforms/daily_revenue.yml` (v1) | 45 min |
| 3 | Data Quality & Testing | `seeknal/rules/order_rules.yml`, `seeknal/sources/products.yml`, `seeknal/profiles/products_stats.yml`, `seeknal/rules/valid_prices.yml`, `seeknal/profiles/products_price_stats.yml`, `seeknal/rules/products_quality.yml` | 45 min |
| 4 | Advanced Sources & CDC | `seeknal/sources/orders_updates.yml`, `seeknal/transforms/orders_merged.yml`, refactor `daily_revenue.yml` (v2), `seeknal/sources/sales_events.yml`, `seeknal/sources/sales_snapshot.yml`, `seeknal/transforms/events_cleaned.yml`, `seeknal/rules/not_null_quantity.yml`, `seeknal/rules/positive_quantity.yml` | 50 min |
| 5 | DRY Config & Python API | `seeknal/common/sources.yml`, `seeknal/common/transformations.yml`, `seeknal/common/rules.yml`, `seeknal/transforms/sales_enriched.yml`, `seeknal/transforms/sales_summary.yml`, `seeknal/pipelines/transactions.py`, `seeknal/pipelines/customer_daily_agg.py` | 50 min |
| 6 | Feature Engineering for ML | `seeknal/pipelines/customer_features.py`, `seeknal/pipelines/region_metrics.py` | 45 min |
| 7 | Semantic Layer & Metrics | `seeknal/semantic_models/orders.yml`, `seeknal/exposures/revenue_export.yml` | 40 min |
| 8 | Production Patterns | `profiles-dev.yml`, `seeknal/pipelines/exchange_rates.py`, `seeknal/pipelines/customer_analytics.py`, `seeknal/pipelines/category_insights.py` | 45 min |

**Reference Guides** (created alongside):
- `QUICKSTART.md` — Quick reference card
- `QUERY_GUIDE.md` — How to query pipeline outputs

---

## Technical Approach

### Writing Conventions (from dbt tutorial analysis)

Apply these patterns consistently across all 8 modules:

1. **Bold file paths before every code block**: `**seeknal/sources/raw_orders.yml**`
2. **Language-tagged code blocks always**: `yaml`, `sql`, `bash`, `csv`, `python`
3. **"What just happened?"** numbered explanation after pipeline execution steps
4. **Code-heavy, prose-light**: 1-3 sentences max between code blocks. 70-80% code by volume
5. **Horizontal rules (`---`)** between major sections within each module
6. **No prose transitions**: Headings carry the flow between sections
7. **Comments inside code blocks** for inline explanation
8. **Complete, runnable code**: Never use ellipsis or fragments
9. **Imperative voice**: "Create `file.yml`:", "Run your pipeline:"
10. **Bold-key bullet lists**: `- **Key**: explanation text`

### Module Template Structure

Each module markdown file follows this structure:

```markdown
# Module N: Title

> **Duration:** ~NN minutes | **Difficulty:** Beginner/Intermediate

## Why This Matters in Industry

[2-3 paragraphs with real company examples. Industry context for interviews.]

---

## Prerequisites

- Completed Module N-1
- [Any specific tools/knowledge]

## What You'll Build

[Bullet list of files to create and concepts to learn]

---

## Step N.1: [First Task]

[1-2 sentence instruction]

**seeknal/path/to/file.yml**
```yaml
[complete code]
```

[Optional 1-sentence explanation of non-obvious aspects]

---

## Step N.2: [Second Task]

[...]

---

## Run Your Pipeline

```bash
seeknal run
```

**What just happened?**
1. `seeknal run` [what it did]
2. [Additional explanations]

---

## Explore the Results

```bash
seeknal repl
```

```sql
SELECT * FROM [table] LIMIT 5;
```

**Expected output:**
```
[sample table output]
```

---

## Checkpoint

By the end of this module, you should have:
- [ ] Created [files]
- [ ] Understood [concepts]
- [ ] Run [commands] successfully

**Your project structure should now look like:**
```
ecommerce-pipeline/
├── seeknal_project.yml
├── seeknal/
│   ├── sources/
│   │   └── raw_orders.yml
│   └── ...
```

---

Continue to [Module N+1: Title](0N+1_title.md)
```

---

### Implementation Phases

#### Phase 1: Foundation Modules (1-3) — YAML-Only Pipeline

**Module 1: `docs/tutorial/01_introduction_and_setup.md`**

Concepts: What is a data pipeline, ETL/ELT lifecycle, why specialized tools
Seeknal features: `seeknal init`, project structure, CSV sources, `seeknal run`, `seeknal repl`

Steps:
1. Explain data pipelines with industry examples (Netflix, Uber, Shopify)
2. Install prerequisites (Python 3.11+, uv, seeknal)
3. `seeknal init --name ecommerce-pipeline` — create project
4. Walk through generated `seeknal_project.yml` fields:
   - `name`: project identifier
   - `version`: semantic versioning
   - `profile`: connection profile name
   - `config-version`: YAML schema version
   - `state_backend: file`: pipeline state stored locally
5. Copy `data/orders.csv` into the project
6. **Data exploration exercise**: Use `seeknal repl` to query raw CSV:
   ```sql
   SELECT * FROM read_csv('data/orders.csv') LIMIT 5;
   ```
   Guide students to discover intentional quality issues (null customer_id, negative revenue, duplicate ORD-001, whitespace status)
7. Create `seeknal/sources/raw_orders.yml` — first YAML source definition
8. `seeknal run` — execute pipeline
9. `seeknal repl` — query the loaded source:
   ```sql
   SELECT * FROM "source.raw_orders" LIMIT 10;
   ```
10. "What just happened?" explanation

Key code — **seeknal/sources/raw_orders.yml**:
```yaml
kind: source
name: raw_orders
description: "Raw e-commerce order data with intentional quality issues"
source: csv
table: "data/orders.csv"
columns:
  order_id: "Unique order identifier"
  customer_id: "Customer who placed the order"
  order_date: "Date the order was placed"
  status: "Order status (Pending, Completed, Cancelled)"
  revenue: "Order revenue in USD"
  items: "Number of items in the order"
```

**Critical note**: The tutorial must explain what students should expect to see in the terminal after `seeknal run`. Include a sample output block showing success message and row count.

---

**Module 2: `docs/tutorial/02_data_transformation.md`**

Concepts: Data cleaning, SQL transforms, DAG dependencies, safety workflow
Seeknal features: `ref()`, transforms, `seeknal draft`, `seeknal dry-run`, `seeknal apply`

Steps:
1. Explain why raw data is messy (industry examples of data quality incidents)
2. Recall the quality issues discovered in Module 1's data exploration
3. Create `seeknal/transforms/orders_cleaned.yml` — cleaning transform:
   - Filter null customer_id
   - Fix negative revenue (set to 0 or filter)
   - Trim whitespace from status
   - Deduplicate using `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_date DESC) = 1`
   - **Callout box**: Explain DuckDB's `QUALIFY` clause vs standard SQL subquery pattern
4. Introduce `ref('source.raw_orders')` — dependency references
5. Introduce the DAG concept with ASCII diagram:
   ```
   source.raw_orders → transform.orders_cleaned
   ```
6. Create `seeknal/transforms/daily_revenue.yml` (v1) — aggregation transform:
   - **CRITICAL FIX**: This v1 references `transform.orders_cleaned` (NOT `orders_merged`)
   - GROUP BY order_date with SUM, COUNT, AVG metrics
7. The safety workflow:
   - `seeknal draft transform daily_revenue` — generate template (or manual creation)
   - `seeknal dry-run seeknal/transforms/daily_revenue.yml` — validate without executing
   - `seeknal apply seeknal/transforms/daily_revenue.yml` — execute after review
   - Explain WHY safety matters: production horror stories
8. `seeknal run` — execute full pipeline
9. REPL exploration of `transform.orders_cleaned` and `transform.daily_revenue`
10. "What just happened?" explanation

Key code — **seeknal/transforms/orders_cleaned.yml** (Module 2 version):
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

Key code — **seeknal/transforms/daily_revenue.yml** (v1, targets orders_cleaned):
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
      ROUND(SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS completion_rate
  FROM ref('transform.orders_cleaned')
  GROUP BY order_date
  ORDER BY order_date
```

---

**Module 3: `docs/tutorial/03_data_quality_and_testing.md`**

Concepts: Data quality dimensions (completeness, accuracy, consistency), validation, profiling, data contracts
Seeknal features: rules, profiles, quality checks

**CRITICAL FIX from SpecFlow**: Module 3's rules now target data that exists at this point (`transform.orders_cleaned`, `source.raw_orders`) rather than `transform.events_cleaned` (which is Module 4).

Steps:
1. Industry context: Cost of bad data (IBM: $3.1T/year), data quality dimensions
2. **New**: Create rules against orders data (exists from Modules 1-2):
   - `seeknal/rules/order_revenue_valid.yml` — rule: revenue must be >= 0 on `source.raw_orders`
   - `seeknal/rules/order_not_null.yml` — rule: customer_id must not be null on `source.raw_orders`
   - Demonstrate rule FAILURE on `source.raw_orders` (which has the quality issues)
   - Show that `transform.orders_cleaned` passes the same rules (cleaning fixed the problems)
3. Add new data source: Create `seeknal/sources/products.yml` — products catalog
4. Data profiling:
   - Create `seeknal/profiles/products_stats.yml` — full statistical profile
   - Create `seeknal/profiles/products_price_stats.yml` — focused column profile
   - Run and explore the profile output
5. Profile-based quality checks:
   - Create `seeknal/rules/valid_prices.yml` — price range validation on `source.products`
   - Create `seeknal/rules/products_quality.yml` — profile-based threshold checks
6. Explain what happens when rules fail:
   - `severity: error` → pipeline halts
   - `severity: warn` → pipeline continues with warning
7. Industry context: data contracts and SLAs
8. `seeknal run` and `seeknal dq` — data quality dashboard

Key code — **seeknal/rules/order_revenue_valid.yml** (new, Module 3):
```yaml
kind: rule
name: order_revenue_valid
description: "Revenue must not be negative in raw orders"
inputs:
  - ref: source.raw_orders
rule:
  type: range
  column: revenue
  params:
    min_val: 0
    max_val: 100000
params:
  severity: error
  error_message: "Found orders with invalid revenue values"
```

Key code — **seeknal/rules/order_not_null.yml** (new, Module 3):
```yaml
kind: rule
name: order_not_null
description: "Critical fields must not be null in raw orders"
inputs:
  - ref: source.raw_orders
rule:
  type: "null"
  columns: [customer_id, order_date, status]
  params:
    max_null_percentage: 0.0
params:
  severity: error
  error_message: "Found null values in critical order fields"
```

**Teaching moment**: Students run rules against `source.raw_orders` and see FAILURES. Then run against `transform.orders_cleaned` and see SUCCESS. This demonstrates the value of the cleaning transform from Module 2.

---

#### Phase 2: Advanced Patterns (4-5) — Multi-Format, Config, Python

**Module 4: `docs/tutorial/04_advanced_sources_and_cdc.md`**

Concepts: CDC (Change Data Capture), multi-format ingestion, incremental processing
Seeknal features: JSONL/Parquet sources, CDC merge, QUALIFY dedup, incremental refs

Steps:
1. Industry context: Why data changes over time (corrections, late-arriving data, system migrations)
2. CDC pattern:
   - Copy `data/orders_updates.csv` — examine the corrections (ORD-004, ORD-005 fixed)
   - Create `seeknal/sources/orders_updates.yml`
   - Create `seeknal/transforms/orders_merged.yml` — UNION ALL + QUALIFY dedup
   - **Refactor** `seeknal/transforms/daily_revenue.yml` (v2) — now targets `transform.orders_merged`
   - Explain why the refactor is necessary (CDC data must flow through the merge before aggregation)
3. Multi-format sources:
   - Copy `data/sales_events.jsonl` — examine the JSONL format
   - Create `seeknal/sources/sales_events.yml` — JSONL source
   - Copy `data/sales_snapshot.parquet`
   - Create `seeknal/sources/sales_snapshot.yml` — Parquet source
   - Explain when each format is used in industry
4. Create `seeknal/transforms/events_cleaned.yml` — filter nulls, deduplicate
5. **Now** create the events-based rules (moved from original Module 3):
   - Create `seeknal/rules/not_null_quantity.yml` — validates `transform.events_cleaned`
   - Create `seeknal/rules/positive_quantity.yml` — validates `transform.events_cleaned`
6. `seeknal run` and explore results
7. Updated DAG visualization:
   ```
   source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue
                                                             ↑
                                              source.orders_updates

   source.sales_events ──→ transform.events_cleaned
   ```

Key code — **seeknal/transforms/orders_merged.yml**:
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

Key code — **seeknal/transforms/daily_revenue.yml** (v2, now targets orders_merged):
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

---

**Module 5: `docs/tutorial/05_dry_config_and_python_api.md`**

Concepts: DRY principle, configuration-as-code, Python decorator API, YAML+Python interop
Seeknal features: Common config (`{{ }}`), `@source`, `@transform`, `ctx.ref()`, `ctx.duckdb.sql()`

Steps:
1. Industry context: Why DRY matters at scale (100+ transforms, team collaboration)
2. Common configuration:
   - Create `seeknal/common/sources.yml` — column name aliases
   - Create `seeknal/common/transformations.yml` — reusable SQL expressions
   - Create `seeknal/common/rules.yml` — shared rule expressions
   - **Callout**: Distinguish `common/rules.yml` (reusable SQL expressions) from `seeknal/rules/*.yml` (validation rule nodes) — different concepts sharing the word "rules"
3. Create transforms that USE common config:
   - Create `seeknal/transforms/sales_enriched.yml` — LEFT JOIN events + products
   - **Teaching moment**: Explain LEFT JOIN producing NULL rows for orphan PRD-999 reference in sales_events
   - Create `seeknal/transforms/sales_summary.yml` — uses `{{ }}` template variables
4. Introduction to Python decorator API:
   - **Environment setup**: Explain PEP 723 `# /// script` metadata block, verify `seeknal` package is installed
   - Explain WHEN to use Python vs YAML: complex logic, external libraries, ML computation
   - Create `seeknal/pipelines/transactions.py` — `@source` decorator (passive source, `pass` body)
   - Explain `ctx` object: `ctx.ref()`, `ctx.duckdb.sql()`, `.df()`
   - Create `seeknal/pipelines/customer_daily_agg.py` — `@transform` decorator with DuckDB SQL
   - **Teaching moment**: Show that Python nodes can reference YAML nodes and vice versa
5. `seeknal run` and explore results in REPL

Key code — **seeknal/pipelines/transactions.py**:
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

Key code — **seeknal/pipelines/customer_daily_agg.py**:
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
            CAST('2026-01-21' AS DATE) AS application_date,
            SUM(revenue) AS daily_amount,
            COUNT(*) AS daily_count
        FROM df
        GROUP BY customer_id, region, CAST(order_date AS DATE)
    """).df()
```

---

#### Phase 3: ML & Analytics (6-7)

**Module 6: `docs/tutorial/06_feature_engineering_for_ml.md`**

Concepts: ML features, feature stores, entities, RFM analysis, point-in-time joins, second-order aggregation
Seeknal features: `@feature_group`, entity, `@second_order_aggregation`, feature versioning

Steps:
1. Industry context: Why feature engineering is 80% of ML work, what feature stores solve
2. Entities: What your features describe (customers, products, orders)
   - `entity="customer"` auto-infers `join_keys=["customer_id"]`
3. Create `seeknal/pipelines/customer_features.py`:
   - `@feature_group` decorator with `entity="customer"`
   - Compute 6 features: total_orders, total_revenue, avg_order_value, first_order_date, last_order_date, event_time
   - Explain how feature groups differ from transforms (versioned, entity-aware, materializable)
4. RFM Analysis (Recency, Frequency, Monetary):
   - Explain the business concept with customer segmentation examples
   - Show how `customer_features.py` produces the building blocks for RFM
   - SQL example computing RFM scores from the feature group output
5. Point-in-time joins (conceptual + code):
   - Explain data leakage problem with a clear before/after diagram
   - Show `feature_date_col` and `application_date_col` parameters
   - Explain how Seeknal prevents future data from contaminating training features
6. Second-order aggregation:
   - Create `seeknal/pipelines/region_metrics.py` — `@second_order_aggregation`
   - Explain: first-order = customer features, second-order = region-level aggregates of customer features
   - Parameters: `id_col`, `feature_date_col`, `application_date_col`, `features` dict
7. `seeknal run` and inspect feature group output
8. Feature versioning: explain auto-versioning when schema changes

Key code — **seeknal/pipelines/customer_features.py**:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

from seeknal.pipeline import feature_group

@feature_group(
    name="customer_features",
    entity="customer",
    description="Core customer features for ML models",
)
def customer_features(ctx):
    df = ctx.ref("source.transactions")
    return ctx.duckdb.sql("""
        SELECT
            customer_id,
            COUNT(*) AS total_orders,
            SUM(revenue) AS total_revenue,
            AVG(revenue) AS avg_order_value,
            MIN(CAST(order_date AS DATE)) AS first_order_date,
            MAX(CAST(order_date AS DATE)) AS last_order_date,
            MAX(CAST(order_date AS DATE)) AS event_time
        FROM df
        GROUP BY customer_id
    """).df()
```

Key code — **seeknal/pipelines/region_metrics.py**:
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

from seeknal.pipeline import second_order_aggregation

@second_order_aggregation(
    name="region_metrics",
    id_col="region",
    feature_date_col="order_date",
    application_date_col="application_date",
    features={
        "daily_amount": {"basic": ["sum", "mean", "max", "stddev"]},
        "daily_count": {"basic": ["sum", "mean"]},
    },
    description="Region-level aggregation of customer daily metrics",
)
def region_metrics(ctx):
    return ctx.ref("transform.customer_daily_agg")
```

---

**Module 7: `docs/tutorial/07_semantic_layer_and_metrics.md`**

Concepts: Semantic layer, business metrics, dimensions, measures, exposures, data delivery
Seeknal features: Semantic models, metrics, exposures, `seeknal query`, `seeknal repl`

Steps:
1. Industry context: Why a semantic layer matters (single source of truth for business metrics, bridge between data eng and business stakeholders)
2. Semantic model components:
   - **Entities**: Primary and foreign keys (order_id, customer_id)
   - **Dimensions**: Time dimensions (order_date with day granularity) and categorical (status)
   - **Measures**: Aggregations (sum of revenue, count of orders, average of revenue)
   - **Metrics**: Computed from measures (ratio, cumulative, derived)
3. Create `seeknal/semantic_models/orders.yml`:
   - Model references `transform.orders_cleaned`
   - Define entities, dimensions, measures
   - Define metrics: `avg_order_value_ratio`, `cumulative_revenue`, `revenue_per_customer`
   - **FIX**: Add `unique_customers` measure (`expr: customer_id, agg: count_distinct`) to resolve the broken reference
4. Exposures — data delivery:
   - Explain the concept: how do downstream consumers (dashboards, reports, APIs) access data?
   - Create `seeknal/exposures/revenue_export.yml` — CSV export for finance team
5. Query the semantic layer:
   - `seeknal repl` with SQL against the semantic model
   - `seeknal query --metrics total_revenue --dimensions status` (if supported)
6. "What just happened?" explaining how the semantic layer abstracts the pipeline

Key code — **seeknal/semantic_models/orders.yml** (with fix):
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
  - name: status
    type: categorical
    expr: status

measures:
  - name: total_revenue
    expr: revenue
    agg: sum
    description: "Sum of all order revenue"
  - name: order_count
    expr: 1
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

---

#### Phase 4: Production (8) + Reference Guides

**Module 8: `docs/tutorial/08_production_patterns.md`**

Concepts: Environment management, multi-target materialization, data lineage, cross-referencing, best practices
Seeknal features: Profiles, `seeknal lineage`, YAML+Python cross-reference, `seeknal inspect`

Steps:
1. Industry context: Dev vs staging vs production environments, why isolation matters
2. Environment profiles:
   - Create `profiles-dev.yml` — PostgreSQL dev connection
   - Explain profile fields (connection name, host, port, database)
   - Explain `.gitignore` for `profiles.yml` (production secrets)
3. Cross-referencing YAML and Python:
   - Create `seeknal/pipelines/exchange_rates.py` — Python `@source` for CSV
   - Create `seeknal/pipelines/customer_analytics.py` — Python `@transform` that references YAML `transform.sales_enriched` AND Python `source.exchange_rates`
   - Create `seeknal/pipelines/category_insights.py` — Python `@transform` using pandas for market share analysis
   - **Teaching moment**: Show the full DAG with YAML and Python nodes mixed
4. Data lineage:
   - `seeknal lineage` — generate lineage visualization
   - `seeknal lineage --ascii` — terminal-friendly view
   - Explain lineage for debugging and impact analysis
5. Best practices summary:
   - Naming conventions (source.*, transform.*, feature_group.*)
   - File organization
   - When to use YAML vs Python
   - Testing and quality at every layer
   - The draft/dry-run/apply safety workflow
6. What to learn next:
   - Spark engine for large-scale processing
   - CI/CD pipeline automation
   - Monitoring and alerting
   - Online feature serving
   - Incremental processing with watermarks

---

**Reference Guide: `docs/tutorial/QUICKSTART.md`**

Quick reference card with:
- Installation commands
- Common CLI commands with flags
- YAML node type templates (one-liner each)
- Python decorator templates
- Project structure tree

**Reference Guide: `docs/tutorial/QUERY_GUIDE.md`**

How to query pipeline outputs:
- `seeknal repl` usage (interactive + `--exec`)
- Common SQL patterns for exploring node outputs
- Querying semantic model metrics
- Export query results

---

### Codebase Fixes Required

Before writing tutorials, these issues in existing code must be fixed:

1. **`seeknal/semantic_models/orders.yml`**: Add `unique_customers` measure with `agg: count_distinct`
2. **`seeknal/transforms/daily_revenue.yml`**: Must support being created in two stages (v1 with `orders_cleaned`, v2 with `orders_merged`). The final repo version should be v2.
3. **`seeknal/pipelines/customer_daily_agg.py`**: Replace hardcoded `'2026-01-21'` date with `CURRENT_DATE` or add a comment explaining why it's fixed for reproducibility
4. **`seeknal/sources/sales_snapshot.yml`**: Add a `columns` documentation block
5. **`README.md`**: Remove references to non-existent `foundations-test/` directory and reconcile with 8-module structure
6. **Create new rule files**: `seeknal/rules/order_revenue_valid.yml` and `seeknal/rules/order_not_null.yml` for Module 3

---

## Acceptance Criteria

### Functional Requirements

- [x] 8 tutorial markdown files in `docs/tutorial/` following the module template
- [x] 2 reference guide markdown files (`QUICKSTART.md`, `QUERY_GUIDE.md`)
- [x] Each module's code examples match the actual files in the repository
- [x] All `seeknal` CLI commands shown are valid and produce the described output
- [x] Each module includes a "Why this matters in industry" section
- [x] Each module includes a "What just happened?" explanation after execution steps
- [x] Each module includes expected terminal output for every command
- [x] Each module includes a checkpoint with project structure tree
- [x] Navigation links between modules (Continue to Module N+1)
- [x] All YAML and Python code blocks are complete and runnable (no fragments)
- [x] `docs/tutorial/01_introduction_and_setup.md` — Module 1
- [x] `docs/tutorial/02_data_transformation.md` — Module 2
- [x] `docs/tutorial/03_data_quality_and_testing.md` — Module 3
- [x] `docs/tutorial/04_advanced_sources_and_cdc.md` — Module 4
- [x] `docs/tutorial/05_dry_config_and_python_api.md` — Module 5
- [x] `docs/tutorial/06_feature_engineering_for_ml.md` — Module 6
- [x] `docs/tutorial/07_semantic_layer_and_metrics.md` — Module 7
- [x] `docs/tutorial/08_production_patterns.md` — Module 8
- [x] `docs/tutorial/QUICKSTART.md` — Quick reference
- [x] `docs/tutorial/QUERY_GUIDE.md` — Query guide

### Codebase Fixes

- [x] Fix `seeknal/semantic_models/orders.yml` — add `unique_customers` measure
- [x] Create `seeknal/rules/order_revenue_valid.yml` — Module 3 rule
- [x] Create `seeknal/rules/order_not_null.yml` — Module 3 rule
- [x] Update `seeknal/pipelines/customer_daily_agg.py` — fix hardcoded date
- [x] Add `columns` block to `seeknal/sources/sales_snapshot.yml`
- [x] Update `README.md` to match 8-module tutorial structure

### Quality Gates

- [ ] Each module is completable in 30-60 minutes by an undergraduate student
- [ ] Code examples are syntactically correct YAML/SQL/Python
- [ ] No module references nodes or files that haven't been created yet
- [ ] DAG dependency chain is valid at every module boundary
- [ ] Writing follows the code-heavy/prose-light convention (70-80% code by volume)

---

## Success Metrics

1. A student with basic Python/SQL can complete all 8 modules independently
2. Each module takes 30-60 minutes
3. All code examples work against the included sample data
4. Students understand WHY each concept matters in industry, not just HOW
5. The tutorial demonstrates Seeknal's unique value (feature store, safety workflow, multi-format)
6. Tutorial documents live alongside working code in the same repository

---

## Dependencies & Prerequisites

- Working Seeknal CLI (`seeknal` command available)
- Python 3.11+
- `uv` package manager
- All 7 data files in `data/` directory
- No external database required (DuckDB file backend)

---

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Seeknal CLI behavior doesn't match documented commands | Students hit errors on first run | Test every command before writing, include exact version requirements |
| `seeknal run` output format changes between versions | Expected output blocks become stale | Pin Seeknal version in prerequisites, use pattern-based output descriptions |
| Module 4 (Advanced Sources) still too long | Students drop off | Include time checkpoints within the module, suggest breaks |
| Students skip modules | Later modules reference earlier work | Include clear prerequisites and "you should have these files" verification |
| DuckDB QUALIFY syntax unfamiliar | Confusion, frustration | Add callout box explaining QUALIFY as DuckDB extension |

---

## File Creation Summary

### Tutorial Documents (10 files)

| File | Phase | Approx. Length |
|------|-------|---------------|
| `docs/tutorial/01_introduction_and_setup.md` | Phase 1 | ~800 lines |
| `docs/tutorial/02_data_transformation.md` | Phase 1 | ~900 lines |
| `docs/tutorial/03_data_quality_and_testing.md` | Phase 1 | ~800 lines |
| `docs/tutorial/04_advanced_sources_and_cdc.md` | Phase 2 | ~900 lines |
| `docs/tutorial/05_dry_config_and_python_api.md` | Phase 2 | ~1000 lines |
| `docs/tutorial/06_feature_engineering_for_ml.md` | Phase 3 | ~900 lines |
| `docs/tutorial/07_semantic_layer_and_metrics.md` | Phase 3 | ~700 lines |
| `docs/tutorial/08_production_patterns.md` | Phase 4 | ~800 lines |
| `docs/tutorial/QUICKSTART.md` | Phase 4 | ~200 lines |
| `docs/tutorial/QUERY_GUIDE.md` | Phase 4 | ~250 lines |

### Codebase Fixes (6 files)

| File | Action |
|------|--------|
| `seeknal/semantic_models/orders.yml` | Edit: add `unique_customers` measure |
| `seeknal/rules/order_revenue_valid.yml` | Create: new Module 3 rule |
| `seeknal/rules/order_not_null.yml` | Create: new Module 3 rule |
| `seeknal/pipelines/customer_daily_agg.py` | Edit: fix hardcoded date |
| `seeknal/sources/sales_snapshot.yml` | Edit: add columns block |
| `README.md` | Edit: reconcile with 8-module structure |

---

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-05-seeknal-tutorial-brainstorm.md](docs/brainstorms/2026-03-05-seeknal-tutorial-brainstorm.md)
  - Key decisions carried forward:
    - YAML-first then Python (Modules 1-3 YAML, Module 5 introduces Python)
    - Build from scratch (not explore existing)
    - E-commerce domain with existing data
    - Feature store + ML pipeline as key differentiator
    - Standalone tutorial (no dbt comparison)
  - Adjustment: Original 7 modules expanded to 8 (Module 4 split based on SpecFlow analysis)

### Internal References

- Seeknal CLI commands: `~/project/mta/signal/src/seeknal/cli/main.py`
- YAML schema reference: `~/project/mta/signal/docs/reference/yaml-schema.md`
- Python decorator API: `~/project/mta/signal/src/seeknal/pipeline/decorators.py`
- dbt tutorial patterns: `~/project/self/dbt_get_started/dbt_tutorial.md`
- dbt module format: `~/project/self/dbt_get_started/shopmart-analytics/docs/modules/`

### SpecFlow Findings Addressed

- **Gap 2 (blocking):** `daily_revenue` dependency → v1/v2 approach (Module 2/Module 4)
- **Gap 3 (blocking):** Module 3 rules target wrong data → new order-based rules created
- **Gap 1:** Module 4 overloaded → split into Modules 4 and 5
- **Gap 7:** Missing `unique_customers` metric → added to semantic model
- **Gap 8:** QUALIFY syntax → callout box in Module 2
- **Gap 16:** No data exploration → added to Module 1
- **Gap 22:** No expected output → included in every module
