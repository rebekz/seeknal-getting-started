# Seeknal Getting Started: E-Commerce Pipeline Tutorial

A progressive, hands-on tutorial that teaches you how to build real-world data pipelines using [Seeknal](https://github.com/mta-tech/seeknal). Build an e-commerce analytics pipeline from scratch across 8 modules — from loading your first CSV to production-ready feature engineering and semantic metrics.

## Prerequisites

- Python 3.11+
- [uv](https://astral.sh/uv) package manager
- Seeknal installed (`uv pip install seeknal`)
- Basic SQL and Python knowledge

## Tutorial Modules

Start from Module 1 and progress through all 8 modules. Each builds on the previous one.

| Module | Topic | Duration | What You'll Learn |
|--------|-------|----------|-------------------|
| [1. Introduction & Setup](docs/tutorial/01_introduction_and_setup.md) | First pipeline | ~30 min | Data pipelines, project setup, CSV sources, REPL |
| [2. Data Transformation](docs/tutorial/02_data_transformation.md) | SQL transforms | ~45 min | Cleaning, `ref()`, DAG, draft/dry-run/apply |
| [3. Data Quality & Testing](docs/tutorial/03_data_quality_and_testing.md) | Validation | ~45 min | Rules, profiling, severity levels |
| [4. Advanced Sources & CDC](docs/tutorial/04_advanced_sources_and_cdc.md) | Multi-format data | ~50 min | CDC merge, JSONL, Parquet, incremental |
| [5. DRY Config & Python API](docs/tutorial/05_dry_config_and_python_api.md) | Python pipelines | ~50 min | Common config, `@source`, `@transform`, `ctx` |
| [6. Feature Engineering](docs/tutorial/06_feature_engineering_for_ml.md) | ML features | ~45 min | Feature groups, RFM, point-in-time joins, SOA |
| [7. Semantic Layer & Metrics](docs/tutorial/07_semantic_layer_and_metrics.md) | Business metrics | ~40 min | Semantic models, measures, exposures |
| [8. Production Patterns](docs/tutorial/08_production_patterns.md) | Going to prod | ~45 min | Environments, lineage, best practices |

**Reference Guides:**
- [Quick Reference](docs/tutorial/QUICKSTART.md) — CLI commands and YAML/Python templates
- [Query Guide](docs/tutorial/QUERY_GUIDE.md) — How to query pipeline outputs

## Project Structure

```
.
├── data/                           # Sample datasets
│   ├── orders.csv                  # Raw orders with quality issues (Module 1)
│   ├── orders_updates.csv          # CDC corrections (Module 4)
│   ├── products.csv                # Product catalog (Module 3)
│   ├── sales_events.jsonl          # JSONL events (Module 4)
│   ├── sales_snapshot.parquet      # Parquet snapshot (Module 4)
│   ├── transactions.csv            # Customer transactions (Module 5)
│   └── exchange_rates.csv          # Currency rates (Module 8)
│
├── seeknal/                        # Pipeline definitions
│   ├── sources/                    # Data source declarations
│   │   ├── raw_orders.yml          #   CSV source (Module 1)
│   │   ├── orders_updates.yml      #   CDC updates (Module 4)
│   │   ├── products.yml            #   Product catalog (Module 3)
│   │   ├── sales_events.yml        #   JSONL source (Module 4)
│   │   └── sales_snapshot.yml      #   Parquet source (Module 4)
│   │
│   ├── transforms/                 # SQL transformations
│   │   ├── orders_cleaned.yml      #   Data cleaning (Module 2)
│   │   ├── orders_merged.yml       #   CDC merge (Module 4)
│   │   ├── daily_revenue.yml       #   Daily aggregation (Module 2, refactored Module 4)
│   │   ├── events_cleaned.yml      #   Event dedup (Module 4)
│   │   ├── sales_enriched.yml      #   JOIN products + events (Module 5)
│   │   └── sales_summary.yml       #   Category aggregation (Module 5)
│   │
│   ├── rules/                      # Data quality rules
│   │   ├── order_revenue_valid.yml #   Revenue range check (Module 3)
│   │   ├── order_not_null.yml      #   Null check on orders (Module 3)
│   │   ├── valid_prices.yml        #   Price range warning (Module 3)
│   │   ├── products_quality.yml    #   Profile-based checks (Module 3)
│   │   ├── not_null_quantity.yml   #   Null check on events (Module 4)
│   │   └── positive_quantity.yml   #   Quantity range check (Module 4)
│   │
│   ├── profiles/                   # Data profiling
│   │   ├── products_stats.yml      #   Full profile (Module 3)
│   │   └── products_price_stats.yml#   Focused profile (Module 3)
│   │
│   ├── pipelines/                  # Python pipeline nodes
│   │   ├── transactions.py         #   @source (Module 5)
│   │   ├── customer_daily_agg.py   #   @transform (Module 5)
│   │   ├── customer_features.py    #   @feature_group (Module 6)
│   │   ├── region_metrics.py       #   @second_order_aggregation (Module 6)
│   │   ├── exchange_rates.py       #   @source (Module 8)
│   │   ├── customer_analytics.py   #   @transform cross-ref (Module 8)
│   │   └── category_insights.py    #   @transform pandas (Module 8)
│   │
│   ├── semantic_models/            # Semantic layer
│   │   └── orders.yml              #   Business metrics (Module 7)
│   │
│   ├── exposures/                  # Downstream consumers
│   │   └── revenue_export.yml      #   CSV export (Module 7)
│   │
│   └── common/                     # Shared configuration
│       ├── sources.yml             #   Column aliases (Module 5)
│       ├── transformations.yml     #   Reusable SQL (Module 5)
│       └── rules.yml               #   Shared expressions (Module 5)
│
├── seeknal_project.yml             # Project configuration
├── profiles-dev.yml                # Dev environment connections
│
└── docs/
    └── tutorial/                   # 8-module progressive tutorial
        ├── 01_introduction_and_setup.md
        ├── 02_data_transformation.md
        ├── 03_data_quality_and_testing.md
        ├── 04_advanced_sources_and_cdc.md
        ├── 05_dry_config_and_python_api.md
        ├── 06_feature_engineering_for_ml.md
        ├── 07_semantic_layer_and_metrics.md
        ├── 08_production_patterns.md
        ├── QUICKSTART.md
        └── QUERY_GUIDE.md
```

## Quick Start

```bash
# 1. Clone the project
git clone <repo-url> && cd seeknal-getting-started

# 2. Install Seeknal
uv pip install seeknal

# 3. Run the full pipeline
seeknal run

# 4. Explore results
seeknal repl

# 5. Visualize lineage
seeknal lineage --ascii
```

Or follow the [tutorial from Module 1](docs/tutorial/01_introduction_and_setup.md) to build everything from scratch.

## Pipeline Overview

```
source.raw_orders ──→ transform.orders_cleaned ──→ transform.orders_merged ──→ transform.daily_revenue ──→ exposure.revenue_export
                              │                          ↑
                              │               source.orders_updates
                              └──→ semantic_model.orders

source.sales_events ──→ transform.events_cleaned ──→ transform.sales_enriched ──→ transform.sales_summary
                                                          ↑        ├──→ customer_analytics (Python)
                                                   source.products  └──→ category_insights (Python)

source.transactions ──→ feature_group.customer_features
                    └──→ transform.customer_daily_agg ──→ second_order_aggregation.region_metrics
```

## Sample Data

| File | Format | Rows | Description |
|------|--------|------|-------------|
| `orders.csv` | CSV | 13 | Raw orders with intentional quality issues (nulls, negatives, duplicates) |
| `orders_updates.csv` | CSV | 4 | Corrections and new orders for CDC merge |
| `products.csv` | CSV | 6 | Product catalog across 5 categories |
| `sales_events.jsonl` | JSONL | 7 | Sales events with nulls and orphan product refs |
| `sales_snapshot.parquet` | Parquet | 4 | Quarterly snapshot for Parquet source demo |
| `transactions.csv` | CSV | 10 | Customer transactions for ML feature engineering |
| `exchange_rates.csv` | CSV | 4 | Currency rates for multi-region revenue conversion |

## Key Concepts Demonstrated

- **YAML + Python pipelines** — Mix declarative YAML with Python `@source`/`@transform`/`@feature_group` decorators
- **Named references** — `ref('source.products')` for self-documenting, reorder-safe SQL
- **Common configuration** — `{{ events.quantityCol }}` templates for DRY column mappings
- **Data quality rules** — Null checks, range validation, profile-based threshold checks
- **Data profiling** — Auto-computed statistics (row count, avg, stddev, null%, distinct count)
- **Semantic models** — Entities, dimensions, measures, and composable metrics
- **CDC / incremental** — Merge original + update batches with deduplication
- **Feature store** — Feature groups with entity-based organization and versioning
- **Second-order aggregation** — Hierarchical ML features via SOA engine
- **Cross-node references** — Python nodes referencing YAML nodes and vice versa

## Learn More

- [Seeknal Documentation](https://github.com/mta-tech/seeknal)
