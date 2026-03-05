# Module 6: Feature Engineering for ML

> **Duration:** ~45 minutes | **Difficulty:** Intermediate

In this module, you will build ML-ready features using Seeknal's built-in feature store — the capability that separates Seeknal from traditional pipeline tools. You will create customer-level features, implement RFM analysis, understand point-in-time joins, and build second-order aggregations.

---

## Why This Matters in Industry

Feature engineering is **80% of ML work**. Every major ML platform confirms this:

- **Google** published research showing that most ML engineering effort goes into data preparation and feature pipelines, not model architecture.
- **Uber's Michelangelo** platform was built specifically to manage feature pipelines at scale — computing, storing, and serving features for thousands of ML models across ride pricing, fraud detection, and ETA prediction.
- **Spotify** uses feature pipelines to transform raw listening events into recommendation signals: "average listening duration per genre," "skip rate by time of day," "playlist diversity score."
- **Airbnb** reported that their search ranking model's biggest accuracy gains came from better features, not better algorithms.

Without a feature store, teams run into three recurring problems:

| Problem | What Goes Wrong | Real-World Impact |
|---------|----------------|-------------------|
| **Duplicated feature code** | Five teams independently write "total customer orders" | Inconsistent definitions, wasted engineering time |
| **Training/serving skew** | Training uses pandas, serving uses SQL — results differ | Model performs well offline, fails in production |
| **Data leakage** | Features include future data during training | Artificially high accuracy, catastrophic production failure |

Feature stores like **Feast**, **Tecton**, and **Seeknal** solve all three by providing a single system to define, compute, version, and serve ML features.

---

## Prerequisites

- Completed [Module 1](01_introduction_and_setup.md) through [Module 5](05_dry_config_and_python_api.md)
- Python pipeline basics from Module 5 (`@source`, `@transform`, `ctx`)
- `source.transactions` and `transform.customer_daily_agg` from Module 5

---

## What You'll Build

By the end of this module, you will have:

1. A **feature group** with customer-level ML features (total orders, revenue, order history)
2. **RFM analysis** (Recency, Frequency, Monetary) — a classic marketing analytics framework
3. A **second-order aggregation** that rolls customer-level metrics up to region-level features
4. A clear understanding of **point-in-time joins** and why they prevent data leakage

---

## Step 6.1: What Are Features in ML?

A **feature** is a measurable property used as input to an ML model. Features are computed from raw data through transformations.

| Term | Definition | Example |
|------|-----------|---------|
| **Feature** | A single computed property | `total_orders` for a customer |
| **Feature group** | A collection of related features | All customer purchase metrics |
| **Entity** | The thing a feature describes | "customer", "product", "region" |
| **Join key** | The column that identifies an entity instance | `customer_id`, `product_id` |

Consider a churn prediction model. Its input features might include:

```
customer_id | total_orders | avg_order_value | days_since_last_order | total_revenue
CUST-100    | 5            | 85.50           | 12                    | 427.50
CUST-101    | 2            | 120.00          | 45                    | 240.00
CUST-102    | 1            | 25.00           | 90                    | 25.00
```

Each row is one entity instance (a customer). Each column is a feature.

---

## Step 6.2: Entities

An **entity** defines WHAT your features describe — the anchor that ties features to real-world objects.

| Entity | Join Key | Example Features |
|--------|----------|-----------------|
| `customer` | `customer_id` | total_orders, avg_order_value |
| `product` | `product_id` | units_sold, return_rate |
| `region` | `region` | avg_customer_spend, order_density |

When you declare `entity="customer"` in Seeknal, it auto-infers that the join key is `customer_id`. This convention eliminates boilerplate — no need to manually specify `join_keys=["customer_id"]`.

---

## Step 6.3: Create Customer Features

Create the feature group file that computes core customer features from raw transaction data.

**`seeknal/pipelines/customer_features.py`**

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

### @feature_group vs @transform

| Capability | `@transform` | `@feature_group` |
|------------|-------------|-------------------|
| Entity awareness | No | Yes — knows features describe a `customer` |
| Automatic versioning | No | Yes — schema changes create new versions |
| Feature store integration | No | Yes — features can be materialized and served |
| Point-in-time support | No | Yes — `event_time` enables temporal joins |

### Key Parameters

- `entity="customer"` — tells Seeknal these features describe customers. Auto-infers `join_keys=["customer_id"]`.
- `event_time` — marks WHEN each feature row's data was generated. Critical for point-in-time joins (Step 6.5).

### Features Computed

| Feature | SQL Expression | What It Measures |
|---------|---------------|-----------------|
| `total_orders` | `COUNT(*)` | How many orders the customer placed |
| `total_revenue` | `SUM(revenue)` | Total spending across all orders |
| `avg_order_value` | `AVG(revenue)` | Average amount per order |
| `first_order_date` | `MIN(order_date)` | When the customer first purchased |
| `last_order_date` | `MAX(order_date)` | When the customer most recently purchased |
| `event_time` | `MAX(order_date)` | Timestamp for point-in-time join support |

---

## Step 6.4: RFM Analysis

RFM is a classic marketing analytics framework used at companies from Amazon to local retailers.

| Dimension | Question | Your Feature |
|-----------|----------|-------------|
| **Recency** | How recently did the customer purchase? | `last_order_date` |
| **Frequency** | How often do they purchase? | `total_orders` |
| **Monetary** | How much do they spend? | `total_revenue` |

Your `customer_features` feature group already provides the RFM building blocks. After running the pipeline (Step 6.7), use the REPL to compute RFM segments.

```sql
-- RFM analysis from customer features
SELECT
    customer_id,
    -- Recency: days since last order
    DATEDIFF('day', last_order_date, CURRENT_DATE) AS recency_days,
    -- Frequency: total orders
    total_orders AS frequency,
    -- Monetary: total revenue
    total_revenue AS monetary,
    -- RFM Score (simple quartile-based)
    CASE
        WHEN total_orders >= 3 THEN 'High'
        WHEN total_orders >= 2 THEN 'Medium'
        ELSE 'Low'
    END AS frequency_segment
FROM "feature_group.customer_features"
ORDER BY total_revenue DESC;
```

In production, data scientists use these features to train churn prediction models, customer lifetime value models, and personalized recommendation engines. The feature group pattern ensures every model uses the **same** feature definitions — when `avg_order_value` is updated, the change propagates to all downstream models automatically.

---

## Step 6.5: Point-in-Time Joins

This is the most important ML engineering concept in this module. Point-in-time joins prevent **data leakage** — the single most dangerous pitfall in ML.

### The Problem: Data Leakage

Suppose you are training a churn prediction model on January 15.

```
THE PROBLEM — DATA LEAKAGE

Timeline:
  Jan 1          Jan 15              Feb 15
    |               |                   |
    |  historical   |  PREDICTION       |  future
    |  data         |  DATE             |  (unknown)
    |               |                   |

WRONG approach:
  You compute features using ALL data, including data from Jan 16 - Feb 15.
  The model "sees the future" during training.

  Example: Customer CUST-100 placed 3 orders after Jan 15.
  Your feature total_orders = 8 (includes future orders).
  The model learns "customers with 8+ orders don't churn" —
  but at prediction time on Jan 15, you only know about 5 orders.

  Result: Model accuracy during training = 95%
          Model accuracy in production = 55%
```

This is not a theoretical concern. **Data leakage is the #1 cause of ML models failing in production.** Teams at Google, Meta, and Netflix have all documented incidents where leaked features caused catastrophic production failures.

### The Solution: Point-in-Time Joins

A point-in-time join ensures that for each training example, only feature values from data **before** the prediction date are used.

```
THE SOLUTION — POINT-IN-TIME JOIN

For training example (CUST-100, Jan 15):
  Only use data from before Jan 15.
  total_orders = 5 (not 8)
  total_revenue = $427.50 (not $680.00)

For training example (CUST-101, Jan 15):
  Only use data from before Jan 15.
  total_orders = 2 (not 3)

Each training row gets the features AS THEY WOULD HAVE BEEN
at the time the prediction was needed.
```

### How Seeknal Handles This

Seeknal uses three key columns to enforce temporal correctness:

| Column | Purpose | Set By |
|--------|---------|--------|
| `event_time` | When the feature data was generated | The feature group query (Step 6.3) |
| `feature_date_col` | The date column in the source data | Aggregation configuration |
| `application_date_col` | The date to evaluate features at | Aggregation configuration |

When you declared `event_time = MAX(order_date)` in the customer features, you told Seeknal: "this feature row reflects data up to this date." The feature store engine uses this to filter features during joins:

```sql
-- Point-in-time join logic (simplified)
SELECT features.*
FROM training_examples t
JOIN features f
  ON t.customer_id = f.customer_id
  AND f.event_time <= t.prediction_date   -- ONLY past data
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY t.customer_id, t.prediction_date
  ORDER BY f.event_time DESC              -- Most recent past value
) = 1
```

The SOA engine applies this same temporal filtering automatically in aggregation pipelines. Point-in-time correctness must be designed into your feature pipeline from the start — retrofitting it requires rewriting every feature query. By using `@feature_group` with `event_time` from the beginning, Seeknal handles this automatically.

---

## Step 6.6: Second-Order Aggregation

So far, all features have been **first-order** — computed directly from raw data, grouped by a single entity. Second-order features aggregate first-order features at a higher level.

| Order | Input | Output | Example |
|-------|-------|--------|---------|
| First-order | Raw transactions | Per-customer features | "CUST-100 has 5 total orders" |
| Second-order | Per-customer features | Per-region aggregates | "North region customers average 3.2 orders" |

Second-order features capture **contextual** information. Consider two customers with identical purchases:

```
CUST-100 in North region:  total_orders = 3, region avg = 2.0 → ABOVE average
CUST-200 in South region:  total_orders = 3, region avg = 5.0 → BELOW average
```

Same raw features, completely different stories. This context improves model accuracy significantly.

### Create the Second-Order Aggregation

**`seeknal/pipelines/region_metrics.py`**

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

### Parameters Explained

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `id_col` | `"region"` | The column to aggregate BY — each region gets its own row |
| `feature_date_col` | `"order_date"` | The date column in the input data (from `customer_daily_agg`) |
| `application_date_col` | `"application_date"` | The date to evaluate features at — enables point-in-time filtering |
| `features` | dict | Which columns to aggregate and which functions to apply |

### Auto-Generated Output Columns

The `features` dict maps input columns to aggregation functions. The SOA engine automatically generates output columns using the `{column}_{function}` naming convention:

| Input Column | Aggregation | Output Column |
|-------------|-------------|--------------|
| `daily_amount` | sum | `daily_amount_sum` |
| `daily_amount` | mean | `daily_amount_mean` |
| `daily_amount` | max | `daily_amount_max` |
| `daily_amount` | stddev | `daily_amount_stddev` |
| `daily_count` | sum | `daily_count_sum` |
| `daily_count` | mean | `daily_count_mean` |

Six output features from two input columns and one configuration dict. The `feature_date_col` and `application_date_col` parameters enforce the same temporal correctness described in Step 6.5, but at the aggregation level.

---

## Step 6.7: Run and Explore

Run the full pipeline to materialize the feature group and second-order aggregation.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing N node(s)...
  ...
  ✓ feature_group.customer_features
  ✓ second_order_aggregation.region_metrics
Pipeline completed successfully.
```

### What just happened?

1. Seeknal resolved all dependencies, running sources and transforms before feature computations.
2. `customer_features` read from `source.transactions`, grouped by `customer_id`, and produced one row per customer with 6 features each.
3. `region_metrics` read from `transform.customer_daily_agg`, grouped by `region`, and computed 6 aggregated features (4 for `daily_amount`, 2 for `daily_count`).
4. Both outputs were materialized and registered in the feature store for downstream use.

### Explore Customer Features

```bash
seeknal repl
```

```sql
-- View all customer features
SELECT * FROM "feature_group.customer_features";
```

```sql
-- View region-level second-order aggregation
SELECT * FROM "second_order_aggregation.region_metrics";
```

```sql
-- How many customers have features?
SELECT COUNT(*) AS customer_count
FROM "feature_group.customer_features";
```

Exit the REPL:

```bash
.exit
```

---

## Step 6.8: Feature Versioning

When you change a feature group's schema — adding a new column, removing an old one, or changing a computation — Seeknal automatically creates a new version.

```
Version 1: customer_features
  Columns: customer_id, total_orders, total_revenue, avg_order_value,
           first_order_date, last_order_date, event_time

You add a new feature:
  + days_since_first_order

Version 2: customer_features
  Columns: customer_id, total_orders, total_revenue, avg_order_value,
           first_order_date, last_order_date, event_time,
           days_since_first_order
```

| Capability | Without Versioning | With Versioning |
|-----------|-------------------|----------------|
| **Rollback** | Cannot revert to previous features | Restore version 1 with one command |
| **Comparison** | No way to compare feature distributions | Compare v1 vs v2 side by side |
| **Audit** | "Which features did model X use?" — unknown | Model X trained on customer_features v1 |
| **Reproducibility** | Cannot reproduce last month's training data | Exact feature values available per version |

In production ML systems, feature versioning is critical for model governance. When a model's predictions degrade, the first question is always: "Did the features change?"

---

## Common Mistakes

### Mistake 1: Forgetting event_time

```python
# WRONG — no event_time column
return ctx.duckdb.sql("""
    SELECT
        customer_id,
        COUNT(*) AS total_orders,
        SUM(revenue) AS total_revenue
    FROM df
    GROUP BY customer_id
""").df()

# CORRECT — include event_time for point-in-time join support
return ctx.duckdb.sql("""
    SELECT
        customer_id,
        COUNT(*) AS total_orders,
        SUM(revenue) AS total_revenue,
        MAX(CAST(order_date AS DATE)) AS event_time
    FROM df
    GROUP BY customer_id
""").df()
```

Without `event_time`, the feature store cannot enforce temporal boundaries. Point-in-time joins will either fail or silently use future data.

### Mistake 2: Using @transform Instead of @feature_group

```python
# WRONG — loses entity awareness, versioning, and feature store integration
@transform(name="customer_features")
def customer_features(ctx):
    ...

# CORRECT — feature groups are entity-aware and versioned
@feature_group(
    name="customer_features",
    entity="customer",
    description="Core customer features for ML models",
)
def customer_features(ctx):
    ...
```

A `@transform` works for intermediate data processing. But ML features should always use `@feature_group` to get entity tracking, versioning, and point-in-time support.

### Mistake 3: Leaking Future Data in Feature Computation

```sql
-- WRONG — using CURRENT_DATE bakes in the computation date
SELECT
    customer_id,
    DATEDIFF('day', MAX(order_date), CURRENT_DATE) AS days_since_last_order
FROM transactions
GROUP BY customer_id

-- CORRECT — store the raw date and compute deltas at serving time
SELECT
    customer_id,
    MAX(CAST(order_date AS DATE)) AS last_order_date,
    MAX(CAST(order_date AS DATE)) AS event_time
FROM transactions
GROUP BY customer_id
```

Computing `days_since_last_order` using `CURRENT_DATE` bakes in the current date at computation time. When you retrain using historical data, this value will be wrong. Store `last_order_date` as a raw feature and compute the delta at serving time.

---

## Concepts Recap

### Feature Engineering Pipeline

```
┌──────────────────┐
│   Raw Data       │    source.transactions
│   (transactions) │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  First-Order     │    feature_group.customer_features
│  Features        │    (per-customer: total_orders, total_revenue, ...)
│  (per entity)    │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Second-Order    │    second_order_aggregation.region_metrics
│  Features        │    (per-region: avg customer spend, order density, ...)
│  (per group)     │
└──────────────────┘
```

### Key Concepts

| Concept | Definition |
|---------|-----------|
| **Feature** | A measurable property used as input to an ML model |
| **Feature group** | A versioned collection of related features tied to an entity |
| **Entity** | The real-world object features describe (customer, product, region) |
| **Point-in-time join** | A temporal join that prevents future data from leaking into training |
| **Data leakage** | Using future information during training, causing false accuracy |
| **event_time** | Timestamp marking when a feature row's data was generated |
| **First-order features** | Features computed directly from raw data (per-entity) |
| **Second-order features** | Aggregations of first-order features (per-group) |
| **SOA engine** | Seeknal's Second-Order Aggregation engine for temporal aggregations |

---

## Checkpoint

Verify you have completed every step:

- [ ] Created `seeknal/pipelines/customer_features.py` with `@feature_group` and 6 ML features
- [ ] Understood the RFM analysis framework (Recency, Frequency, Monetary)
- [ ] Understood point-in-time joins and why data leakage is dangerous
- [ ] Created `seeknal/pipelines/region_metrics.py` with `@second_order_aggregation`
- [ ] Understood the difference between features, feature groups, and entities

### Project Structure

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   ├── orders.csv
│   ├── orders_updates.csv
│   ├── products.csv
│   ├── sales_events.jsonl
│   ├── sales_snapshot.parquet
│   └── transactions.csv
├── seeknal/
│   ├── sources/
│   │   ├── raw_orders.yml
│   │   ├── orders_updates.yml
│   │   ├── products.yml
│   │   ├── sales_events.yml
│   │   ├── sales_snapshot.yml
│   │   └── transactions.yml
│   ├── transforms/
│   │   ├── orders_cleaned.yml
│   │   ├── orders_merged.yml
│   │   ├── daily_revenue.yml
│   │   ├── events_cleaned.yml
│   │   └── customer_daily_agg.yml
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
│   ├── pipelines/
│   │   ├── customer_features.py        ← NEW
│   │   └── region_metrics.py           ← NEW
│   └── common/
└── target/
    └── intermediate/
        ├── ...
        ├── feature_group.customer_features.parquet
        └── second_order_aggregation.region_metrics.parquet
```

---

Continue to [Module 7: Semantic Layer & Metrics](07_semantic_layer_and_metrics.md)
