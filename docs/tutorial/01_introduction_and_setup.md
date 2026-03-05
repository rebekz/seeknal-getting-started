# Module 1: Introduction & Setup

> **Duration:** ~30 minutes | **Difficulty:** Beginner

## Why This Matters in Industry

Every modern company runs on data pipelines. Netflix processes billions of viewing events daily through pipelines that feed its recommendation engine — when you see "Because you watched...", that suggestion was computed by a data pipeline that extracted your watch history, transformed it into preference signals, and loaded it into a model-serving layer. Uber uses real-time pipelines to calculate surge pricing: ride requests, driver locations, and traffic data flow through a pipeline that outputs dynamic prices every few seconds.

Shopify processes millions of e-commerce transactions through data pipelines that compute merchant analytics, detect fraud, and generate financial reports. Without pipelines, each of these tasks would require brittle, hand-written Python scripts that break when data formats change, fail silently when rows are missing, and cannot scale beyond a single machine.

The data pipeline lifecycle follows a consistent pattern across all these companies: **Extract** raw data from sources (databases, APIs, files), **Transform** it into clean, business-ready tables, **Load** it into a destination (data warehouse, dashboard, ML model), and **Serve** it to end users. Seeknal is a tool built for this lifecycle — it gives you a declarative way to define each stage, handles execution order automatically, and tracks pipeline state so you never reprocess data unnecessarily.

---

## Prerequisites

- Python 3.11+
- `uv` package manager ([https://astral.sh/uv](https://astral.sh/uv))
- Terminal/command line basics
- Basic SQL knowledge

---

## What You'll Build

In this module you will:

- Create your first Seeknal project
- Load a CSV data source
- Run your first pipeline
- Explore data interactively with the REPL

---

## Step 1.1: Install Seeknal

Install Seeknal using `uv`:

```bash
uv pip install seeknal
```

Verify the installation:

```bash
seeknal --version
```

Expected output:

```
seeknal 0.x.x
```

---

## Step 1.2: Create Your Project

Create a **new folder** outside this tutorial repository for your project work. The tutorial docs are reference material — your actual pipeline code goes in a separate directory.

```bash
mkdir ~/ecommerce-pipeline && cd ~/ecommerce-pipeline
seeknal init --name ecommerce-pipeline
```

> **Important:** Do not work inside the tutorial repository itself. Create a fresh directory (e.g., `~/ecommerce-pipeline`) so you have a clean workspace. You can keep the tutorial docs open in another window for reference.

Seeknal generates a project scaffold. Inspect it:

```bash
tree -L 2
```

Expected output:

```
ecommerce-pipeline/
├── seeknal_project.yml
├── seeknal/
│   ├── sources/
│   ├── transforms/
│   ├── pipelines/
│   └── common/
└── target/
```

| Directory | Purpose |
|-----------|---------|
| `seeknal/sources/` | Data source definitions (CSV, Parquet, databases) |
| `seeknal/transforms/` | SQL or Python transformations |
| `seeknal/pipelines/` | Pipeline orchestration configs |
| `seeknal/common/` | Shared macros and utilities |
| `target/` | Build artifacts and cached intermediate data |

---

## Step 1.3: Understand seeknal_project.yml

**seeknal_project.yml**

```yaml
# Project configuration — the root of every Seeknal project
name: ecommerce-pipeline       # Project identifier used in logs and metadata
version: 1.0.0                 # Semantic versioning for your pipeline
profile: default               # Which connection profile to use (defined in profiles.yml)
config-version: 1              # YAML schema version for this config file
state_backend: file            # Pipeline state stored locally as files (also supports remote backends)
```

- `name` — uniquely identifies this project; appears in logs and the REPL prompt.
- `version` — semantic versioning so you can track pipeline releases.
- `profile` — selects which connection profile to use (database credentials, warehouse endpoints). The `default` profile uses local file-based storage.
- `config-version` — tells Seeknal which YAML schema version to parse.
- `state_backend: file` — pipeline execution state (which nodes ran, checksums) is stored as local files in `target/`. In production you would use `s3` or `gcs`.

---

## Step 1.4: Add Sample Data

Create a `data/` directory at the project root:

```bash
mkdir -p data
```

Create the sample orders file.

**data/orders.csv**

```csv
order_id,customer_id,order_date,status,revenue,items
ORD-001,CUST-100,2026-01-15 10:30:00,completed,149.99,3
ORD-002,CUST-101,2026-01-15 11:45:00,completed,89.50,2
ORD-003,,2026-01-16 09:00:00,completed,250.00,5
ORD-004,CUST-100,2026-01-16 14:20:00,pending,0.00,1
ORD-005,CUST-102,2026-01-17 08:15:00,completed,-10.00,2
ORD-006,CUST-103,2026-01-17 16:30:00,  Completed  ,75.25,1
ORD-007,CUST-101,2026-01-18 12:00:00,completed,320.00,-1
ORD-008,CUST-104,2026-01-18 15:45:00,completed,45.99,2
ORD-001,CUST-100,2026-01-19 10:30:00,completed,149.99,3
ORD-009,CUST-105,2026-01-19 09:00:00,completed,199.95,4
ORD-010,CUST-106,2026-01-20 10:00:00,completed,175.50,3
ORD-011,CUST-100,2026-01-20 14:30:00,completed,89.99,2
ORD-012,CUST-107,2026-01-21 09:15:00,pending,0.00,1
```

This dataset has **intentional quality issues** that mimic real-world data problems. You will discover them in the next step.

---

## Step 1.5: Explore the Raw Data

Before building any pipeline, explore the data using Seeknal's built-in REPL (powered by DuckDB).

```bash
seeknal repl
```

Preview the first 5 rows:

```sql
SELECT * FROM read_csv('data/orders.csv') LIMIT 5;
```

Expected output:

```
┌──────────┬─────────────┬─────────────────────┬───────────┬─────────┬───────┐
│ order_id │ customer_id │     order_date      │  status   │ revenue │ items │
│ varchar  │   varchar   │      timestamp      │  varchar  │ double  │ int64 │
├──────────┼─────────────┼─────────────────────┼───────────┼─────────┼───────┤
│ ORD-001  │ CUST-100    │ 2026-01-15 10:30:00 │ completed │  149.99 │     3 │
│ ORD-002  │ CUST-101    │ 2026-01-15 11:45:00 │ completed │   89.50 │     2 │
│ ORD-003  │             │ 2026-01-16 09:00:00 │ completed │  250.00 │     5 │
│ ORD-004  │ CUST-100    │ 2026-01-16 14:20:00 │ pending   │    0.00 │     1 │
│ ORD-005  │ CUST-102    │ 2026-01-17 08:15:00 │ completed │  -10.00 │     2 │
└──────────┴─────────────┴─────────────────────┴───────────┴─────────┴───────┘
```

Now discover the quality issues hidden in the data.

Find rows with missing customer_id:

```sql
-- Find rows with missing customer_id
SELECT * FROM read_csv('data/orders.csv')
WHERE customer_id IS NULL OR customer_id = '';
```

Expected output:

```
┌──────────┬─────────────┬─────────────────────┬───────────┬─────────┬───────┐
│ order_id │ customer_id │     order_date      │  status   │ revenue │ items │
├──────────┼─────────────┼─────────────────────┼───────────┼─────────┼───────┤
│ ORD-003  │             │ 2026-01-16 09:00:00 │ completed │  250.00 │     5 │
└──────────┴─────────────┴─────────────────────┴───────────┴─────────┴───────┘
```

Find rows with negative revenue:

```sql
-- Find rows with negative revenue
SELECT * FROM read_csv('data/orders.csv')
WHERE revenue < 0;
```

Expected output:

```
┌──────────┬─────────────┬─────────────────────┬───────────┬─────────┬───────┐
│ order_id │ customer_id │     order_date      │  status   │ revenue │ items │
├──────────┼─────────────┼─────────────────────┼───────────┼─────────┼───────┤
│ ORD-005  │ CUST-102    │ 2026-01-17 08:15:00 │ completed │  -10.00 │     2 │
└──────────┴─────────────┴─────────────────────┴───────────┴─────────┴───────┘
```

Find duplicate order_ids:

```sql
-- Find duplicate order_ids
SELECT order_id, COUNT(*) as cnt
FROM read_csv('data/orders.csv')
GROUP BY order_id
HAVING cnt > 1;
```

Expected output:

```
┌──────────┬─────┐
│ order_id │ cnt │
├──────────┼─────┤
│ ORD-001  │   2 │
└──────────┴─────┘
```

Find status values with extra whitespace or inconsistent casing:

```sql
-- Find status values with extra whitespace
SELECT DISTINCT status, LENGTH(status) as len
FROM read_csv('data/orders.csv');
```

Expected output:

```
┌──────────────┬─────┐
│    status    │ len │
├──────────────┼─────┤
│ completed    │   9 │
│ pending      │   7 │
│   Completed  │  13 │
└──────────────┴─────┘
```

Notice that `  Completed  ` has length 13 instead of 9 — extra whitespace and different casing.

### Summary of Quality Issues

| Row | order_id | Issue |
|-----|----------|-------|
| 3 | ORD-003 | Missing `customer_id` |
| 5 | ORD-005 | Negative revenue (`-10.00`) |
| 6 | ORD-006 | Status has extra whitespace and capitalization (`  Completed  `) |
| 7 | ORD-007 | Negative items (`-1`) |
| 9 | ORD-001 | Duplicate `order_id` (appears on row 1 and row 9) |
| 4, 12 | ORD-004, ORD-012 | Revenue is `0.00` (may be invalid) |

We will fix these in Module 2 when we learn about data transformation.

Exit the REPL:

```bash
.exit
```

---

## Step 1.6: Create Your First Source

A **source node** tells Seeknal where to find raw data and how to read it. You will use the **draft → dry-run → apply** workflow — the standard safety process for creating pipeline artifacts.

### Draft the source template

```bash
seeknal draft source raw_orders
```

This generates `draft_source_raw_orders.yml` in your project root. Edit it with the actual source configuration.

### Edit the draft file

**draft_source_raw_orders.yml**

```yaml
kind: source                    # This node loads external data into the pipeline
name: raw_orders                # Unique identifier for this node
description: "Raw e-commerce order data with intentional quality issues"

source: csv                     # File format (also supports: parquet, jsonl, postgresql)
table: "data/orders.csv"        # Path to the data file (relative to project root)

columns:                        # Column documentation (optional but recommended)
  order_id: "Unique order identifier"
  customer_id: "Customer who placed the order"
  order_date: "Date the order was placed"
  status: "Order status (Pending, Completed, Cancelled)"
  revenue: "Order revenue in USD"
  items: "Number of items in the order"
```

### Validate with dry-run

```bash
seeknal dry-run draft_source_raw_orders.yml
```

This checks that the YAML syntax is correct, the referenced file exists, and the schema can be inferred — all without loading any data.

### Apply the source

```bash
seeknal apply draft_source_raw_orders.yml
```

This validates the draft, moves it to `seeknal/sources/raw_orders.yml`, and executes the source node.

> **The draft → dry-run → apply workflow** is how you will create every pipeline artifact throughout this tutorial. `draft` scaffolds a draft file in the project root, `dry-run` validates the draft without executing, and `apply` moves it to the proper location and executes it. This three-step process prevents broken pipelines from reaching production.

Key fields explained:

| Field | Purpose |
|-------|---------|
| `kind: source` | Declares this node as a data source (as opposed to `transform` or `pipeline`) |
| `name` | Unique identifier referenced by downstream nodes |
| `source: csv` | Tells Seeknal the file format so it picks the right reader |
| `table` | Path to the data file, relative to the project root |
| `columns` | Human-readable documentation for each column; does not enforce types |

---

## Step 1.7: Run Your First Pipeline

You already applied the source individually in the previous step. Now run the full pipeline to see Seeknal's orchestration in action:

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing 1 node(s)...
  ✓ source.raw_orders (13 rows)
Pipeline completed successfully.
```

### What just happened?

1. `seeknal run` scanned your `seeknal/` directory for all node definition files (YAML files with `kind:` declarations).
2. It found `raw_orders.yml`, identified it as a source node, and read `data/orders.csv` using the CSV reader.
3. The 13 rows were loaded and registered under the name `source.raw_orders` for downstream use.
4. Results were cached in `target/intermediate/` as Parquet files so that subsequent runs skip unchanged sources.

Verify the cached output exists:

```bash
ls target/intermediate/
```

Expected output:

```
source.raw_orders.parquet
```

Parquet is a columnar storage format used across the data industry. It is faster to read and smaller on disk than CSV. Seeknal automatically converts your sources to Parquet during execution.

---

## Step 1.8: Query Your Source with the REPL

Now that the pipeline has run, you can query the materialized source by its node name.

```bash
seeknal repl
```

Query the source node:

```sql
SELECT * FROM "source.raw_orders" LIMIT 5;
```

Expected output:

```
┌──────────┬─────────────┬─────────────────────┬───────────┬─────────┬───────┐
│ order_id │ customer_id │     order_date      │  status   │ revenue │ items │
│ varchar  │   varchar   │      timestamp      │  varchar  │ double  │ int64 │
├──────────┼─────────────┼─────────────────────┼───────────┼─────────┼───────┤
│ ORD-001  │ CUST-100    │ 2026-01-15 10:30:00 │ completed │  149.99 │     3 │
│ ORD-002  │ CUST-101    │ 2026-01-15 11:45:00 │ completed │   89.50 │     2 │
│ ORD-003  │             │ 2026-01-16 09:00:00 │ completed │  250.00 │     5 │
│ ORD-004  │ CUST-100    │ 2026-01-16 14:20:00 │ pending   │    0.00 │     1 │
│ ORD-005  │ CUST-102    │ 2026-01-17 08:15:00 │ completed │  -10.00 │     2 │
└──────────┴─────────────┴─────────────────────┴───────────┴─────────┴───────┘
```

Count total rows:

```sql
SELECT COUNT(*) as total_rows FROM "source.raw_orders";
```

Expected output:

```
┌────────────┐
│ total_rows │
│   int64    │
├────────────┤
│         13 │
└────────────┘
```

Notice you are now querying `"source.raw_orders"` (the pipeline node name) instead of `read_csv('data/orders.csv')` (the raw file). The pipeline node reads from the cached Parquet file, which is faster and ensures you are working with the same data that downstream transforms will see.

Exit the REPL:

```bash
.exit
```

---

## Key Concepts Recap

| Concept | What It Means |
|---------|---------------|
| **Data Pipeline** | An automated sequence of steps that extracts, transforms, and loads data |
| **Source Node** | A pipeline node that reads raw data from an external file or database |
| **REPL** | An interactive SQL shell for exploring data without writing pipeline code |
| **Parquet** | A columnar file format used for efficient storage of intermediate pipeline data |
| **State Backend** | Where Seeknal tracks which nodes have run and their checksums |
| **Node Name** | The `kind.name` identifier (e.g., `source.raw_orders`) used to reference data in queries |

---

## Checkpoint

By the end of this module, you should have:

- [ ] Installed Seeknal and created a project
- [ ] Understood what data pipelines are and why they matter
- [ ] Added sample CSV data with intentional quality issues
- [ ] Explored data interactively and discovered 5 quality problems
- [ ] Created your first source node (`raw_orders.yml`)
- [ ] Run your first pipeline and queried results in the REPL

Your project structure should now look like:

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   └── orders.csv
├── seeknal/
│   ├── sources/
│   │   └── raw_orders.yml
│   ├── transforms/
│   ├── pipelines/
│   └── common/
└── target/
    └── intermediate/
        └── source.raw_orders.parquet
```

---

Continue to [Module 2: Data Transformation](02_data_transformation.md)
