# Seeknal Example: E-Commerce Pipeline

A hands-on example project demonstrating [Seeknal](https://github.com/mta-tech/seeknal)'s core capabilities through an e-commerce data pipeline. Covers all three persona tutorials (Data Engineer, ML Engineer, Analytics Engineer) and the Advanced Guide.

## Prerequisites

- Python 3.11+
- [uv](https://astral.sh/uv) package manager
- Seeknal installed (`uv pip install seeknal`)

## Project Structure

```
.
├── data/                           # Sample datasets
│   ├── orders.csv                  # Raw e-commerce orders (DE Path)
│   ├── orders_updates.csv          # Order corrections for CDC (DE Path Ch.2)
│   ├── products.csv                # Product catalog (Advanced Guide)
│   ├── sales_events.jsonl          # Sales events in JSONL (Advanced Guide)
│   ├── sales_snapshot.parquet      # Quarterly snapshot (Advanced Guide)
│   ├── transactions.csv            # Customer transactions (ML Path)
│   └── exchange_rates.csv          # Currency rates by region (Advanced Guide)
│
├── seeknal/                        # Pipeline definitions
│   ├── sources/                    # Data source declarations
│   │   ├── raw_orders.yml          #   CSV source (DE Path)
│   │   ├── orders_updates.yml      #   CDC updates source (DE Path)
│   │   ├── products.yml            #   Product catalog CSV (Advanced)
│   │   ├── sales_events.yml        #   JSONL source (Advanced)
│   │   └── sales_snapshot.yml      #   Parquet source (Advanced)
│   │
│   ├── transforms/                 # SQL transformations
│   │   ├── orders_cleaned.yml      #   Data cleaning & validation (DE Path)
│   │   ├── orders_merged.yml       #   CDC merge with dedup (DE Path)
│   │   ├── daily_revenue.yml       #   Daily revenue aggregation (DE Path)
│   │   ├── events_cleaned.yml      #   Event dedup with common config (Advanced)
│   │   ├── sales_enriched.yml      #   JOIN products + events (Advanced)
│   │   └── sales_summary.yml       #   Category aggregation (Advanced)
│   │
│   ├── rules/                      # Data quality rules
│   │   ├── not_null_quantity.yml    #   Null check on events (Advanced)
│   │   ├── positive_quantity.yml   #   Range validation (Advanced)
│   │   ├── valid_prices.yml        #   Price range warning (Advanced)
│   │   └── products_quality.yml    #   Profile-based threshold checks (Advanced)
│   │
│   ├── profiles/                   # Data profiling
│   │   ├── products_stats.yml      #   Full statistical profile (Advanced)
│   │   └── products_price_stats.yml#   Focused column profile (Advanced)
│   │
│   ├── pipelines/                  # Python pipeline nodes
│   │   ├── transactions.py         #   @source: CSV transactions (ML Path)
│   │   ├── customer_features.py    #   @feature_group: ML features (ML Path)
│   │   ├── customer_daily_agg.py   #   @transform: daily agg for SOA (ML Path)
│   │   ├── region_metrics.py       #   @second_order_aggregation (ML Path)
│   │   ├── exchange_rates.py       #   @source: currency rates (Advanced)
│   │   ├── customer_analytics.py   #   @transform: YAML+Python cross-ref (Advanced)
│   │   └── category_insights.py    #   @transform: pandas analytics (Advanced)
│   │
│   ├── semantic_models/            # Semantic layer
│   │   └── orders.yml              #   Entities, dimensions, measures, metrics (AE Path)
│   │
│   ├── exposures/                  # Downstream consumers
│   │   └── revenue_export.yml      #   CSV export for finance team (DE Path)
│   │
│   └── common/                     # Shared configuration
│       ├── sources.yml             #   Column mappings (Advanced)
│       ├── transformations.yml     #   Reusable SQL snippets (Advanced)
│       └── rules.yml               #   Shared rule expressions (Advanced)
│
├── seeknal_project.yml             # Project configuration
├── profiles.yml                    # Default profile
├── profiles-dev.yml                # Dev environment connections
└── foundations-test/               # Standalone subproject (Advanced Guide Ch.1-3)
```

## What Each Tutorial Path Covers

### Data Engineer Path

Build a complete ELT pipeline from raw CSV data to production-ready analytics.

**Pipeline flow:**
```
source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue
                                                        ↑
                                          source.orders_updates
```

| Chapter | Topic | Nodes Built |
|---------|-------|-------------|
| 1. ELT Pipeline | Source ingestion, SQL transforms, data validation | `raw_orders`, `orders_cleaned` |
| 2. Incremental Models | CDC merge, deduplication, update handling | `orders_updates`, `orders_merged` |
| 3. Production Environments | `seeknal env plan/apply`, namespace isolation | `daily_revenue`, `revenue_export` |

**Try it:**
```bash
seeknal run --select source.raw_orders transform.orders_cleaned transform.orders_merged transform.daily_revenue
```

### ML Engineer Path

Build a feature store and second-order aggregation engine for ML models.

**Pipeline flow:**
```
source.transactions (Python) ──→ feature_group.customer_features (Python)
                             ──→ transform.customer_daily_agg (Python)
                                          ↓
                                 second_order_aggregation.region_metrics (Python)
```

| Chapter | Topic | Nodes Built |
|---------|-------|-------------|
| 1. Feature Store | `@source`, `@feature_group`, schema evolution | `transactions`, `customer_features` |
| 2. Second-Order Aggregation | `@transform`, `@second_order_aggregation` with SOA engine | `customer_daily_agg`, `region_metrics` |
| 3. Training & Serving | Model training inside `@transform`, REPL queries | (conceptual) |

**Try it:**
```bash
seeknal run --select source.transactions feature_group.customer_features transform.customer_daily_agg second_order_aggregation.region_metrics
```

### Analytics Engineer Path

Define semantic models with metrics for self-serve analytics.

**Semantic model:**
```
transform.orders_cleaned ──→ semantic_model.orders
                                  ├── Entities: order_id, customer_id
                                  ├── Dimensions: order_date, status
                                  ├── Measures: total_revenue, order_count, avg_order_value
                                  └── Metrics: avg_order_value_ratio, cumulative_revenue, revenue_per_customer
```

| Chapter | Topic | Nodes Built |
|---------|-------|-------------|
| 1. Semantic Models | Entities, dimensions, measures | `orders` semantic model |
| 2. Business Metrics | Ratio, cumulative, derived metrics | Metric definitions |
| 3. Self-Serve Analytics | `seeknal query`, StarRocks deployment | (conceptual) |

**Try it:**
```bash
seeknal query --metrics total_revenue,order_count --dimensions status
seeknal query --metrics avg_order_value_ratio --dimensions order_date --compile
```

### Advanced Guide

Deep-dive features spanning all persona paths.

| Chapter | Topic | Nodes Built |
|---------|-------|-------------|
| 1. File Sources | CSV, JSONL, Parquet ingestion | `products`, `sales_events`, `sales_snapshot` |
| 2. Transformations | JOINs, aggregations, `ref()` syntax | `events_cleaned`, `sales_enriched`, `sales_summary` |
| 3. Data Rules | null, range, sql_assertion checks | `not_null_quantity`, `positive_quantity`, `valid_prices` |
| 4. Lineage | HTML visualization, ASCII tree, column-level trace | (CLI commands) |
| 5. Named References | `ref('source.products')` vs `input_0` | Refactored transforms |
| 6. Common Configuration | `{{ dotted.key }}` templates, shared SQL | `common/sources.yml`, `common/rules.yml` |
| 7. Data Profiling | Statistical profiles, threshold-based checks | `products_stats`, `products_quality` |
| 8. Python Pipelines | `@source`, `@transform`, mixed YAML+Python | `exchange_rates`, `customer_analytics`, `category_insights` |

**Try it:**
```bash
# Run the full pipeline
seeknal run

# Visualize lineage
seeknal lineage
seeknal lineage --ascii

# Inspect intermediate results
seeknal inspect transform.sales_enriched
seeknal inspect transform.customer_analytics

# Explore interactively
seeknal repl
```

## Quick Start

```bash
# 1. Clone and enter the project
cd seeknal-v2.1-test-3

# 2. Initialize (already done — seeknal.db exists)
#    For a fresh start: seeknal init --name ecommerce-pipeline

# 3. Plan the pipeline
seeknal plan

# 4. Run everything
seeknal run

# 5. Explore results
seeknal repl
```

## Sample Data

| File | Format | Rows | Description |
|------|--------|------|-------------|
| `orders.csv` | CSV | 12 | Raw orders with intentional quality issues (nulls, negatives, duplicates) |
| `orders_updates.csv` | CSV | 4 | Corrections and new orders for CDC merge |
| `products.csv` | CSV | 6 | Product catalog across 5 categories |
| `sales_events.jsonl` | JSONL | 7 | Sales events with nulls and orphan product refs |
| `sales_snapshot.parquet` | Parquet | — | Quarterly snapshot for Parquet source demo |
| `transactions.csv` | CSV | 10 | Customer transactions for ML feature engineering |
| `exchange_rates.csv` | CSV | 4 | Currency rates for multi-region revenue conversion |

## Foundations Subproject

The `foundations-test/` directory is a standalone Seeknal project (`retail-foundations`) covering Advanced Guide Chapters 1-3 in isolation. It has its own `seeknal_project.yml`, data files, and target directory.

```bash
cd foundations-test
seeknal plan
seeknal run
```

## Key Concepts Demonstrated

- **YAML + Python pipelines** — Mix declarative YAML nodes with Python `@source`/`@transform`/`@feature_group` decorators
- **Named references** — `ref('source.products')` for self-documenting, reorder-safe SQL
- **Common configuration** — `{{ events.quantityCol }}` templates for DRY column mappings
- **Data quality rules** — Null checks, range validation, profile-based threshold checks
- **Data profiling** — Auto-computed statistics (row count, avg, stddev, null%, distinct count)
- **Semantic models** — Entities, dimensions, measures, and composable metrics
- **CDC / incremental** — Merge original + update batches with deduplication
- **Second-order aggregation** — Hierarchical ML features (basic, window, ratio) via SOA engine
- **Cross-node references** — Python nodes referencing YAML nodes and vice versa

## Learn More

- [Seeknal Documentation](https://github.com/mta-tech/seeknal)
- [Data Engineer Path](https://mta-tech.github.io/seeknal/getting-started/data-engineer-path/)
- [ML Engineer Path](https://mta-tech.github.io/seeknal/getting-started/ml-engineer-path/)
- [Analytics Engineer Path](https://mta-tech.github.io/seeknal/getting-started/analytics-engineer-path/)
- [Advanced Guide](https://mta-tech.github.io/seeknal/getting-started/advanced/)
