# Module 8: Production Patterns

> **Duration:** ~45 minutes | **Difficulty:** Intermediate

In this final module, you will configure environment profiles, cross-reference YAML and Python pipeline nodes, visualize data lineage, and review production best practices that prepare you for real-world data engineering.

---

## Why This Matters in Industry

Everything you have built so far runs locally against sample data. In production, the stakes are different: wrong data costs money, broken pipelines delay business decisions, and credential leaks create security incidents.

- **Development vs production environments**: Real companies maintain separate dev, staging, and production environments with different databases, credentials, and access controls. A junior engineer who runs an experimental query against the production database can corrupt data that serves millions of users. Environment profiles prevent this.
- **Data lineage**: When a dashboard shows wrong numbers at 2 AM, you need to trace the data flow backward from the dashboard to the broken node. Lineage visualization makes this possible in seconds instead of hours.
- **Cross-referencing**: Production pipelines are not pure YAML or pure Python. They mix both, using YAML for straightforward SQL transforms and Python for complex analytics. Seeknal's DAG treats them identically.

| Production Concern | What Goes Wrong Without It | Your Pipeline |
|-------------------|---------------------------|---------------|
| Environment profiles | Developer accidentally queries production DB | `profiles-dev.yml` isolates dev connections |
| Data lineage | Hours spent debugging a broken dashboard | `seeknal lineage` shows the full DAG |
| Cross-referencing | Duplicate logic across YAML and Python | Python nodes reference YAML nodes via `ctx.ref()` |
| Naming conventions | Team members cannot find or understand nodes | Consistent `source.`, `transform.`, `feature_group.` prefixes |

---

## Prerequisites

- Completed [Module 1: Introduction & Setup](01_introduction_and_setup.md) through [Module 7](07_semantic_layer.md)
- All files from previous modules in place

---

## What You'll Build

By the end of this module, you will have:

1. **Environment profiles** for dev database connections
2. **Cross-referencing pipelines** that mix YAML and Python nodes
3. **Data lineage** visualization of your complete DAG
4. A **best practices reference** for production-grade pipelines

---

## Step 8.1: Environment Profiles

Every company separates environments. The pattern is simple: one profile file per environment, with production credentials never committed to git.

Open the existing profiles file at the project root.

**`profiles-dev.yml`**

```yaml
connections:
  local_pg:
    type: postgresql
    host: localhost
    port: 5434
    database: ecommerce_dev
    user: dev_user
    password: dev_pass

source_defaults:
  postgresql:
    connection: local_pg
```

This file already exists in your project. Here is what each section does:

1. **`connections.local_pg`** defines a named database connection with type, host, port, database, and credentials
2. **`source_defaults`** sets the default connection for all PostgreSQL sources, so individual source files do not repeat connection details
3. The `port: 5434` uses a non-standard port to avoid conflicts with any existing PostgreSQL installation

Run the pipeline with a specific profile:

```bash
seeknal run --profile profiles-dev.yml
```

### Industry Environment Pattern

In a real company, you would maintain separate profile files:

| Environment | Profile File | Database | Who Uses It |
|-------------|-------------|----------|-------------|
| Development | `profiles-dev.yml` | `ecommerce_dev` (local) | Individual engineers |
| Staging | `profiles-staging.yml` | `ecommerce_staging` (shared) | QA team, integration tests |
| Production | `profiles.yml` | `ecommerce_prod` (restricted) | CI/CD pipeline only |

The critical rule: **`profiles.yml` (production) is gitignored.** Never commit production credentials to version control.

Add this to your `.gitignore`:

```bash
echo "profiles.yml" >> .gitignore
```

The production profile would look similar but with real credentials:

```yaml
# profiles.yml — NEVER COMMIT THIS FILE
connections:
  prod_pg:
    type: postgresql
    host: prod-db.company.internal
    port: 5432
    database: ecommerce_prod
    user: "${POSTGRES_USER}"        # from environment variable
    password: "${POSTGRES_PASSWORD}" # from environment variable

source_defaults:
  postgresql:
    connection: prod_pg
```

Notice the `${POSTGRES_USER}` syntax. Production credentials come from environment variables set by your deployment system (Kubernetes secrets, AWS Parameter Store, etc.), not from the file itself.

---

## Step 8.2: Cross-Referencing YAML and Python

One of Seeknal's most powerful features is that YAML nodes and Python nodes are interchangeable in the DAG. A Python transform can reference a YAML source, and a YAML transform could reference a Python source. The DAG engine does not care how a node was defined — only what it produces.

### Python Source: Exchange Rates

In Module 7, you created Python pipeline files. Review the exchange rates source that loads currency conversion data.

**`seeknal/pipelines/exchange_rates.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
# ]
# ///

"""Source: Currency exchange rates for multi-region revenue analysis."""

from seeknal.pipeline import source
import pandas as pd


@source(
    name="exchange_rates",
    source="csv",
    table="data/exchange_rates.csv",
    description="Currency exchange rates by region",
)
def exchange_rates(ctx=None):
    """Declare exchange rate lookup source from CSV."""
    pass
```

This Python source loads from the CSV file you created earlier.

**`data/exchange_rates.csv`**

```csv
region,currency,rate_to_usd
north,USD,1.0
south,EUR,1.08
east,GBP,1.27
west,JPY,0.0067
```

### Python Transform: Customer Analytics (Cross-References Both YAML and Python)

This is where cross-referencing shines. The `customer_analytics` transform references a YAML transform (`sales_enriched`) and a Python source (`exchange_rates`) in the same function.

**`seeknal/pipelines/customer_analytics.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Transform: Customer analytics from enriched sales data."""

from seeknal.pipeline import transform


@transform(
    name="customer_analytics",
    description="Per-region revenue analytics with currency conversion",
)
def customer_analytics(ctx):
    """Join enriched sales with exchange rates for USD-normalized revenue."""
    # Reference existing YAML transform
    enriched = ctx.ref("transform.sales_enriched")

    # Reference Python source
    rates = ctx.ref("source.exchange_rates")

    return ctx.duckdb.sql("""
        SELECT
            e.region,
            r.currency,
            r.rate_to_usd,
            COUNT(*) AS order_count,
            SUM(e.total_amount) AS local_revenue,
            ROUND(SUM(e.total_amount) * r.rate_to_usd, 2) AS revenue_usd
        FROM enriched e
        LEFT JOIN rates r ON e.region = r.region
        GROUP BY e.region, r.currency, r.rate_to_usd
        ORDER BY revenue_usd DESC
    """).df()
```

**What just happened?**

1. `ctx.ref("transform.sales_enriched")` pulls data from a YAML-defined transform in `seeknal/transforms/sales_enriched.yml` — the SQL join you built in Module 2
2. `ctx.ref("source.exchange_rates")` pulls data from the Python-defined source above
3. The DuckDB SQL joins both datasets, computes USD-normalized revenue per region, and returns a pandas DataFrame
4. Seeknal automatically resolves the dependency order: sources run first, then `sales_enriched`, then `customer_analytics`

The key insight: **`ctx.ref()` does not care whether the referenced node is YAML or Python.** The DAG resolves dependencies by name, not by file type.

### Python Transform: Category Insights (Pure Pandas)

Sometimes SQL is not the right tool. Statistical computations, ranking, and percentage calculations are often cleaner in pandas.

**`seeknal/pipelines/category_insights.py`**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Transform: Category-level insights with pandas analytics."""

from seeknal.pipeline import transform
import pandas as pd


@transform(
    name="category_insights",
    description="Category performance ranking and share analysis",
)
def category_insights(ctx):
    """Compute category market share and performance ranking."""
    enriched = ctx.ref("transform.sales_enriched")

    # Use pandas for operations that are cleaner than SQL
    if not isinstance(enriched, pd.DataFrame):
        enriched = enriched.df()

    # Filter out NULL categories (orphan products)
    df = enriched[enriched["category"].notna()].copy()

    # Aggregate by category
    summary = df.groupby("category").agg(
        order_count=("event_id", "count"),
        total_units=("quantity", "sum"),
        total_revenue=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
    ).reset_index()

    # Add market share (percentage of total revenue)
    total = summary["total_revenue"].sum()
    summary["revenue_share_pct"] = round(summary["total_revenue"] / total * 100, 2)

    # Rank categories
    summary["rank"] = summary["total_revenue"].rank(ascending=False).astype(int)

    return summary.sort_values("rank")
```

**What just happened?**

1. `ctx.ref("transform.sales_enriched")` loads the same YAML transform used by `customer_analytics` — nodes can have multiple downstream consumers
2. The pandas `groupby().agg()` computes per-category totals in a single call
3. Market share percentages and ranking are computed with pandas arithmetic — no SQL window functions needed
4. The function returns a sorted DataFrame that Seeknal registers as `transform.category_insights`

**When to choose pandas over SQL:**
- Percentage-of-total calculations with `groupby`
- Ranking and labeling with conditional logic
- Statistical functions (standard deviation, percentiles, rolling windows)
- String manipulation beyond what SQL handles cleanly

### Run the Cross-Referenced Pipeline

Execute the full pipeline to see YAML and Python nodes run together:

```bash
seeknal run
```

Query the cross-referenced results:

```bash
seeknal repl --exec "SELECT * FROM \"transform.customer_analytics\""
```

```bash
seeknal repl --exec "SELECT * FROM \"transform.category_insights\""
```

**What just happened?**

1. Seeknal discovered all YAML files in `seeknal/` and all Python files in `seeknal/pipelines/`
2. It built a unified DAG with nodes from both YAML and Python definitions
3. Dependency resolution ensured sources ran before transforms, regardless of definition language
4. Both `customer_analytics` and `category_insights` consumed the YAML `sales_enriched` node

---

## Step 8.3: Data Lineage

Data lineage answers two critical questions: "Where did this data come from?" and "What will break if I change this node?"

### Interactive Lineage Visualization

Generate an interactive HTML visualization of your complete DAG:

```bash
seeknal lineage
```

This opens a browser window with an interactive graph. You can click nodes to see their definitions, zoom in on subgraphs, and trace data flow.

### Terminal Lineage

For quick checks in the terminal (useful when SSH-ing into servers):

```bash
seeknal lineage --ascii
```

### Your Complete DAG

Here is the full data flow across all 8 modules. Every node you built is connected:

```
                        YAML SOURCES                         YAML TRANSFORMS                          OUTPUTS
                        ============                         ===============                          =======

                                                                                                     semantic_model.orders
                                                                                                           ↑
source.raw_orders ────→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue ──→ exposure.revenue_export
                                                            ↑
                        source.orders_updates ──────────────┘


source.sales_events ──→ transform.events_cleaned ──→ transform.sales_enriched ──→ transform.sales_summary
                                                            ↑       │
                        source.products ───────────────────┘       │
                                                                    ├──→ transform.customer_analytics  (Python)
                                                                    │           ↑
                        source.exchange_rates  (Python) ───────────┘
                                                                    │
                                                                    └──→ transform.category_insights   (Python)


                        PYTHON SOURCES                       PYTHON TRANSFORMS / FEATURES
                        ==============                       ============================

source.transactions ──→ feature_group.customer_features                                              (Python)
          │
          └───────────→ transform.customer_daily_agg ──→ second_order_aggregation.region_metrics      (Python)


                        SNAPSHOT SOURCE
                        ===============

source.sales_snapshot                                                                                (Parquet)
```

### Reading the DAG

Trace a few paths to understand the data flow:

**Path 1: Orders to Revenue Export**
`source.raw_orders` --> `transform.orders_cleaned` --> `transform.orders_merged` (with CDC from `source.orders_updates`) --> `transform.daily_revenue` --> `exposure.revenue_export`

**Path 2: Sales Events to USD Analytics**
`source.sales_events` + `source.products` --> `transform.events_cleaned` --> `transform.sales_enriched` --> `transform.customer_analytics` (joined with `source.exchange_rates`)

**Path 3: Transactions to Feature Store**
`source.transactions` --> `feature_group.customer_features` (ML features)
`source.transactions` --> `transform.customer_daily_agg` --> `second_order_aggregation.region_metrics`

### Lineage Use Cases

**Debugging**: A dashboard shows revenue dropped 90% overnight. Run `seeknal lineage` and trace backward from `exposure.revenue_export` through `daily_revenue` --> `orders_merged` --> `orders_cleaned` --> `raw_orders`. You discover that `orders.csv` was truncated during an upstream export. Fix the source, re-run, and the dashboard recovers.

**Impact analysis**: You need to change the `price` column name in `products.csv`. Run `seeknal lineage` and trace forward from `source.products`: it feeds `transform.sales_enriched`, which feeds `transform.sales_summary`, `transform.customer_analytics`, and `transform.category_insights`. You now know exactly which four downstream nodes need updating.

**Onboarding**: A new team member joins and asks "How does the revenue export work?" Instead of reading every YAML file, they run `seeknal lineage`, click on `exposure.revenue_export`, and see the complete upstream chain in seconds.

---

## Step 8.4: Best Practices Summary

This section is your production reference card. Bookmark it.

### Naming Conventions

Consistent naming makes nodes discoverable across large pipelines with hundreds of nodes.

| Node Type | Prefix | Example | Defined In |
|-----------|--------|---------|------------|
| Source | `source.` | `source.raw_orders` | `seeknal/sources/*.yml` or `seeknal/pipelines/*.py` |
| Transform | `transform.` | `transform.orders_cleaned` | `seeknal/transforms/*.yml` or `seeknal/pipelines/*.py` |
| Feature Group | `feature_group.` | `feature_group.customer_features` | `seeknal/pipelines/*.py` |
| Second-Order Agg | `second_order_aggregation.` | `second_order_aggregation.region_metrics` | `seeknal/pipelines/*.py` |
| Rule | `rule.` | `rule.order_not_null` | `seeknal/rules/*.yml` |
| Profile | `profile.` | `profile.products_stats` | `seeknal/profiles/*.yml` |
| Semantic Model | `semantic_model.` | `semantic_model.orders` | `seeknal/semantic_models/*.yml` |
| Exposure | `exposure.` | `exposure.revenue_export` | `seeknal/exposures/*.yml` |

### File Organization

```
seeknal-getting-started/
├── seeknal_project.yml              # Project config (name, version, engine)
├── profiles-dev.yml                 # Dev database connections (committed)
├── profiles.yml                     # Prod database connections (GITIGNORED)
├── data/                            # Raw data files
│   ├── orders.csv
│   ├── orders_updates.csv
│   ├── products.csv
│   ├── sales_events.jsonl
│   ├── sales_snapshot.parquet
│   ├── exchange_rates.csv
│   └── transactions.csv
├── seeknal/
│   ├── sources/                     # YAML source definitions
│   │   ├── raw_orders.yml
│   │   ├── orders_updates.yml
│   │   ├── products.yml
│   │   ├── sales_events.yml
│   │   └── sales_snapshot.yml
│   ├── transforms/                  # YAML SQL transforms
│   │   ├── orders_cleaned.yml
│   │   ├── orders_merged.yml
│   │   ├── daily_revenue.yml
│   │   ├── events_cleaned.yml
│   │   ├── sales_enriched.yml
│   │   └── sales_summary.yml
│   ├── pipelines/                   # Python pipeline nodes
│   │   ├── transactions.py
│   │   ├── exchange_rates.py
│   │   ├── customer_features.py
│   │   ├── customer_daily_agg.py
│   │   ├── region_metrics.py
│   │   ├── customer_analytics.py
│   │   └── category_insights.py
│   ├── rules/                       # Data quality rules
│   │   ├── order_not_null.yml
│   │   ├── order_revenue_valid.yml
│   │   ├── not_null_quantity.yml
│   │   ├── positive_quantity.yml
│   │   ├── products_quality.yml
│   │   └── valid_prices.yml
│   ├── profiles/                    # Data profiling definitions
│   │   ├── products_stats.yml
│   │   └── products_price_stats.yml
│   ├── common/                      # Shared DRY config
│   │   ├── sources.yml
│   │   ├── transformations.yml
│   │   └── rules.yml
│   ├── semantic_models/             # Business metric layer
│   │   └── orders.yml
│   └── exposures/                   # Output declarations
│       └── revenue_export.yml
└── docs/
    └── tutorial/
        ├── 01_introduction_and_setup.md
        ├── 02_data_transformation.md
        ├── 03_data_quality_and_testing.md
        ├── 04_advanced_sources_and_cdc.md
        ├── 05_dry_config_and_exposures.md
        ├── 06_python_pipelines_and_features.md
        ├── 07_semantic_layer.md
        ├── 08_production_patterns.md
        ├── QUICKSTART.md
        └── QUERY_GUIDE.md
```

### When to Use YAML vs Python

| Use Case | Choose YAML | Choose Python |
|----------|-------------|---------------|
| SQL transforms | Yes | No |
| Source definitions | Yes (simple) | Yes (custom loading logic) |
| Data quality rules | Yes | No |
| Data profiles | Yes | No |
| Semantic models | Yes | No |
| Complex analytics | No | Yes |
| ML feature engineering | No | Yes |
| External library integration | No | Yes |
| Pandas/NumPy computation | No | Yes |
| Statistical aggregations | Sometimes | Yes |

**Rule of thumb:** If the logic fits in a SQL query, use YAML. If it needs loops, conditionals, or library imports, use Python.

### Safety Workflow

Follow this sequence for every production change:

```bash
# 1. Validate — check syntax and references
seeknal validate

# 2. Plan — see what will execute without running anything
seeknal plan

# 3. Dry run — execute against data but do not persist results
seeknal dry-run

# 4. Apply — persist results to the target (production)
seeknal apply
```

**What each command prevents:**

| Command | Prevents |
|---------|----------|
| `seeknal validate` | Typos in node names, broken `ref()` calls, invalid YAML |
| `seeknal plan` | Unexpected node execution (e.g., a transform you did not intend to re-run) |
| `seeknal dry-run` | Data errors (NULL columns, wrong joins, type mismatches) |
| `seeknal apply` | Nothing — this is the real run. Use the previous three to catch issues first |

### Credential Safety Checklist

- [ ] `profiles.yml` is in `.gitignore`
- [ ] Production credentials use environment variables (`${VAR}` syntax)
- [ ] `profiles-dev.yml` uses a local database with sample data
- [ ] No passwords appear in YAML source definitions
- [ ] CI/CD injects credentials at deploy time, not at commit time

---

## Step 8.5: What to Learn Next

You have completed the foundational tutorial. Here are the production-grade topics to explore next, ordered by typical learning path:

### Immediate Next Steps

**Materialization** — Write pipeline outputs to PostgreSQL, Apache Iceberg, or Delta Lake instead of keeping them in memory. This is how production pipelines persist results for dashboards and APIs.

```yaml
# Example: materialize to PostgreSQL
kind: transform
name: daily_revenue
materialization:
  type: postgresql
  connection: prod_pg
  table: analytics.daily_revenue
  strategy: merge
```

**Incremental Processing** — Use watermarks to process only new data instead of reprocessing the entire dataset on every run. Critical for pipelines with billions of rows.

```yaml
# Example: incremental source
kind: source
name: raw_orders
incremental:
  watermark_column: updated_at
  strategy: append
```

### Scaling Up

**Spark Engine** — Replace DuckDB with Apache Spark for datasets exceeding 100 million rows. Seeknal swaps the execution engine without changing your YAML or Python definitions.

```bash
seeknal run --engine spark
```

**CI/CD Integration** — Automate pipeline runs with GitHub Actions, Airflow, or Dagster. Run `seeknal validate` on every pull request and `seeknal apply` on merge to main.

```yaml
# Example: GitHub Actions step
- name: Validate pipeline
  run: seeknal validate --profile profiles-staging.yml

- name: Run pipeline
  run: seeknal apply --profile profiles-staging.yml
```

### Advanced Topics

**Monitoring and Alerting** — Set up alerts for pipeline failures, data quality violations, and SLA breaches. Integrate with PagerDuty, Slack, or email.

**Online Feature Serving** — Serve features computed by `feature_group` nodes in real-time for ML inference. Connect your feature store to a low-latency serving layer.

**Multi-Tenant Pipelines** — Run the same pipeline for multiple clients or business units with different source data and connection profiles.

---

## Congratulations

You have completed all 8 modules of the Seeknal tutorial.

Here is everything you built, module by module:

| Module | What You Built | Key Concepts |
|--------|---------------|--------------|
| 1. Introduction & Setup | Project scaffold, first source, first `seeknal run` | Project structure, CSV ingestion, REPL |
| 2. Data Transformation | `orders_cleaned`, `daily_revenue`, `events_cleaned`, `sales_enriched`, `sales_summary` | SQL transforms, joins, aggregations, `ref()` |
| 3. Data Quality & Testing | 6 quality rules, 2 data profiles | `not_null`, `positive`, `accepted_values`, profiling |
| 4. Advanced Sources & CDC | JSONL/Parquet sources, `orders_merged` with CDC | Multi-format ingestion, Change Data Capture |
| 5. DRY Config & Exposures | Shared `common/` config, `revenue_export` exposure | Variable interpolation, output declarations |
| 6. Python Pipelines & Features | `transactions`, `customer_features`, `customer_daily_agg`, `region_metrics` | Python sources, feature store, second-order aggregation |
| 7. Semantic Layer | `orders` semantic model with entities, dimensions, measures, metrics | Business metrics, MetricFlow-style queries |
| 8. Production Patterns | Environment profiles, cross-referencing, lineage, best practices | Dev/prod separation, DAG visualization |

Your final pipeline contains:

- **6 sources** (4 YAML, 2 Python) across 3 file formats (CSV, JSONL, Parquet)
- **9 transforms** (6 YAML, 3 Python) with SQL and pandas
- **1 feature group** with customer-level ML features
- **1 second-order aggregation** for region metrics
- **6 data quality rules** covering NULL checks, range validation, and category constraints
- **2 data profiles** for statistical summaries
- **1 semantic model** with entities, dimensions, measures, and derived metrics
- **1 exposure** declaring an output for downstream consumers
- **1 environment profile** for development database connections

You are ready to build production data pipelines.

---

## Quick Reference

- [QUICKSTART.md](QUICKSTART.md) — CLI commands and common operations
- [QUERY_GUIDE.md](QUERY_GUIDE.md) — REPL queries and SQL patterns for exploring pipeline data
