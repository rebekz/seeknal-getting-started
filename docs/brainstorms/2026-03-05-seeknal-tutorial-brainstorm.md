# Brainstorm: Seeknal Getting Started Tutorial

**Date:** 2026-03-05
**Status:** Draft

---

## What We're Building

A progressive, 7-module industry tutorial that teaches undergraduate students how to build real-world data pipelines using Seeknal. The tutorial uses an e-commerce scenario (orders, products, sales events, transactions) and builds from zero to production-grade pipeline patterns.

### Goals

- Teach **data engineering concepts** through Seeknal (not just Seeknal syntax)
- Mirror real industry practices so students learn transferable skills
- Progressive learning: each module builds on the previous
- Students build everything from scratch, hands-on
- Cover the full end-to-end data pipeline lifecycle

### Target Audience

Undergraduate students learning real data pipelines for the first time. They have basic Python and SQL knowledge but are new to data engineering tools and concepts.

---

## Why This Approach

We chose a **7-module progressive build-from-scratch approach** because:

1. **Progressive learning** works best for beginners — smaller modules are less overwhelming than large monolithic documents
2. **Building from scratch** creates deeper understanding than exploring existing code
3. **Industry framing** ("Why this matters at real companies") gives students context they'll need in interviews and jobs
4. **YAML-first, then Python** matches how SQL-oriented learners naturally progress
5. **E-commerce domain** is familiar, has rich data relationships, and matches existing sample data

---

## Key Decisions

### 1. Tutorial Structure: 7 Progressive Modules

| Module | Title | Core Concepts | Seeknal Features |
|--------|-------|---------------|-----------------|
| 1 | Introduction & Setup | What is a data pipeline? Industry examples | `seeknal init`, project structure, CSV sources |
| 2 | Data Transformation | SQL transforms, dependencies, DAG | `ref()`, transforms, `draft`/`dry-run`/`apply` |
| 3 | Data Quality & Testing | Why quality matters, validation | Rules, profiling, quality checks |
| 4 | Advanced Transformations | CDC, multi-format data, DRY config | Incremental, JSONL/Parquet, common config, Python API |
| 5 | Feature Engineering for ML | Features, entities, segmentation | Feature groups, entities, RFM, point-in-time joins |
| 6 | Semantic Layer & Metrics | Business metrics, data delivery | Semantic models, measures, exposures, REPL |
| 7 | Production Patterns | Environments, materialization, lineage | Dev/prod profiles, multi-target, lineage visualization |

### 2. Audience: Undergraduate Students

- Basic Python and SQL knowledge assumed
- No prior data engineering tool experience
- Each module starts with "Why this matters in industry"
- Include real company examples and interview-relevant context

### 3. API Style: YAML-First, Then Python

- Modules 1-3: Pure YAML pipeline definitions with SQL transforms
- Module 4: Introduce Python decorator API alongside YAML
- Modules 5-7: Mix of YAML and Python, showing when each is appropriate

### 4. Domain: E-Commerce (Existing Data)

Use the existing 7 sample datasets already in `/data/`:
- `orders.csv` — Raw orders with intentional quality issues
- `orders_updates.csv` — CDC updates for incremental patterns
- `products.csv` — Product catalog
- `sales_events.jsonl` — Sales events (multi-format example)
- `sales_snapshot.parquet` — Quarterly snapshot
- `transactions.csv` — Customer transactions
- `exchange_rates.csv` — Currency rates

### 5. Build From Scratch

Students start with an empty project and add files one by one. Each module provides:
- Conceptual explanation with industry context
- Step-by-step instructions with exact code to write
- Commands to run and expected output
- "What just happened?" explanations after each step
- End-of-module checkpoint/summary

### 6. Standalone Tutorial (No dbt Comparison)

The tutorial stands on its own without referencing dbt or other tools. Seeknal concepts are explained from first principles.

### 7. Feature Store + ML Pipeline as Key Differentiator

Module 5 (Feature Engineering) is the showcase module highlighting what makes Seeknal unique:
- Feature groups with automatic versioning
- Entity-based feature organization
- Point-in-time joins to prevent data leakage
- Customer RFM segmentation as a practical ML use case

---

## Module Outlines

### Module 1: Introduction & Setup

**Objective:** Understand what data pipelines are and create your first Seeknal project.

- What is a data pipeline? (real industry examples: Netflix recommendations, Uber pricing, e-commerce analytics)
- The data pipeline lifecycle: Extract → Transform → Load → Serve
- Why specialized tools exist (vs raw Python scripts)
- Install Seeknal and prerequisites (Python 3.11+, uv)
- Create project: `seeknal init`
- Project structure walkthrough
- Load first data source: `raw_orders.yml` pointing to `orders.csv`
- Run first pipeline: `seeknal run`
- Explore output with `seeknal repl`

### Module 2: Data Transformation

**Objective:** Clean, join, and aggregate data using SQL transforms.

- Why data transformation matters (raw data is messy)
- Examine the raw orders data (intentional quality issues)
- Create first transform: `orders_cleaned.yml` — handle nulls, validate types
- Understand `ref()` for dependency management
- The DAG concept: how transforms connect
- Create `daily_revenue.yml` — aggregation transform
- The safety workflow: `seeknal draft` → `seeknal dry-run` → `seeknal apply`
- Why safety matters in production (horror stories)
- View the transformation DAG

### Module 3: Data Quality & Testing

**Objective:** Add data quality rules and profiling to catch problems early.

- Why data quality matters (real industry cost of bad data)
- Types of data quality checks: completeness, accuracy, consistency
- Create validation rules: `not_null_quantity.yml`, `positive_quantity.yml`, `valid_prices.yml`
- Add data source: `products.yml`
- Create data profiles: `products_stats.yml`
- Profile-based quality checks with thresholds
- What happens when quality checks fail?
- Industry practice: data contracts and SLAs

### Module 4: Advanced Transformations

**Objective:** Handle real-world data complexity with CDC, multi-format data, and Python.

- Change Data Capture (CDC): why data changes over time
- Add `orders_updates.yml` source
- Create `orders_merged.yml` — merge original + updates with deduplication
- Multiple data formats: add `sales_events.yml` (JSONL format)
- Add `sales_snapshot.yml` (Parquet format)
- DRY configuration: common sources, transformations, rules
- Introduction to Python decorator API: `transactions.py` with `@source`
- Create `customer_daily_agg.py` with `@transform`
- When to use YAML vs Python

### Module 5: Feature Engineering for ML

**Objective:** Build ML-ready features using Seeknal's feature store.

- What are features in ML? Why feature engineering matters
- The feature store concept: organize, version, serve features
- Entities: defining what your features describe (customers, products)
- Create `customer_features.py` — feature group with `@feature_group`
- RFM analysis: Recency, Frequency, Monetary value
- Customer segmentation based on features
- Point-in-time joins: preventing data leakage (critical ML concept)
- Second-order aggregation: `region_metrics.py`
- Feature versioning and selection

### Module 6: Semantic Layer & Metrics

**Objective:** Define business metrics and make data accessible to stakeholders.

- What is a semantic layer? (bridge between data eng and business)
- Entities, dimensions, and measures
- Create `orders.yml` semantic model
- Define business metrics: avg_order_value, cumulative_revenue, revenue_per_customer
- Exposures: delivering data to downstream consumers
- Create `revenue_export.yml` — CSV export for finance team
- Query metrics with `seeknal repl`
- Query with `seeknal query --metrics --dimensions`

### Module 7: Production Patterns

**Objective:** Learn how real companies run data pipelines in production.

- Development vs production environments
- Create `profiles-dev.yml` for environment configuration
- Environment-aware pipeline execution
- Multi-target materialization (PostgreSQL + Iceberg)
- Data lineage: understanding data flow
- `seeknal lineage` visualization
- Cross-referencing YAML and Python pipelines
- Best practices summary
- What to learn next: Spark engine, CI/CD, monitoring

---

## Open Questions

*None remaining — all key decisions have been resolved through discussion.*

---

## Success Criteria

1. A student with basic Python/SQL can complete all 7 modules independently
2. Each module takes 30-60 minutes to complete
3. All code examples work against the included sample data
4. Students understand WHY each concept matters in industry, not just HOW
5. The tutorial demonstrates Seeknal's unique value (feature store, safety workflow, multi-format)
6. Tutorial documents live alongside the working code in the same repository
