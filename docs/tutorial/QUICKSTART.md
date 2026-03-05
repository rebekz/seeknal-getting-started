# Seeknal Quick Reference

## Installation

```bash
uv pip install seeknal
```

## CLI Commands

### Project Setup

```bash
seeknal init --name my-project
```

### Development Workflow

```bash
# Generate a template for any node type
seeknal draft <kind> <name>
# Kinds: source, transform, feature-group, rule, profile, semantic-model, exposure

# Validate a node file without executing
seeknal dry-run <file>

# Execute a node after validation
seeknal apply <file>
```

### Execution

```bash
# Execute full pipeline
seeknal run

# Execute specific nodes
seeknal run --select <node>

# Ignore cache, run everything from scratch
seeknal run --full

# Run only nodes with a specific tag
seeknal run --tags <tag>

# Preview execution plan without running
seeknal run --dry-run
```

### Exploration

```bash
# Interactive SQL REPL
seeknal repl

# One-shot query
seeknal repl --exec "SELECT * FROM \"source.raw_orders\" LIMIT 5"

# View a specific node's output
seeknal inspect <node>

# Generate HTML lineage graph
seeknal lineage

# Terminal-friendly ASCII lineage
seeknal lineage --ascii

# Data quality dashboard
seeknal dq
```

### Environment & Profiles

```bash
# Show execution plan
seeknal plan

# Use a specific profile file
seeknal run --profile profiles-dev.yml
```

---

## YAML Node Templates

### Source (CSV)

```yaml
kind: source
name: raw_orders
source:
  type: csv
  path: data/orders.csv
  options:
    header: true
    inferSchema: true
columns:
  - name: order_id
    type: integer
  - name: customer_id
    type: integer
  - name: order_date
    type: date
  - name: revenue
    type: double
  - name: status
    type: string
```

### Transform

```yaml
kind: transform
name: orders_cleaned
transform:
  sql: |
    SELECT
      order_id,
      customer_id,
      order_date,
      revenue,
      LOWER(status) AS status
    FROM {{ source.raw_orders }}
    WHERE revenue > 0
```

### Rule (Range)

```yaml
kind: rule
name: revenue_range_check
rule:
  type: range
  node: transform.orders_cleaned
  column: revenue
  min: 0
  max: 100000
  severity: warn
```

### Rule (Null)

```yaml
kind: rule
name: order_id_not_null
rule:
  type: "null"
  node: transform.orders_cleaned
  column: order_id
  severity: error
```

### Profile

```yaml
kind: profile
name: orders_profile
profile:
  node: transform.orders_cleaned
  columns:
    - order_id
    - revenue
    - status
```

### Semantic Model

```yaml
kind: semantic_model
name: order_metrics
semantic_model:
  node: transform.orders_cleaned
  entities:
    - name: order_id
      type: primary
  dimensions:
    - name: status
      type: categorical
    - name: order_date
      type: time
  measures:
    - name: total_revenue
      expr: revenue
      agg: sum
    - name: order_count
      expr: order_id
      agg: count
  metrics:
    - name: avg_order_value_ratio
      type: derived
      expr: total_revenue / order_count
```

### Exposure

```yaml
kind: exposure
name: weekly_revenue_report
exposure:
  type: dashboard
  description: Weekly revenue summary
  depends_on:
    - transform.orders_cleaned
    - transform.daily_revenue
  owner:
    name: Data Team
    email: data@example.com
```

---

## Python Decorator Templates

### @source

```python
from seeknal.decorators import source

@source(
    name="raw_orders",
    source_type="csv",
    path="data/orders.csv",
    options={"header": True, "inferSchema": True},
)
def raw_orders():
    pass
```

### @transform

```python
from seeknal.decorators import transform

@transform(name="orders_cleaned")
def orders_cleaned(raw_orders):
    return raw_orders.filter("revenue > 0").withColumn(
        "status", lower(col("status"))
    )
```

### @feature_group

```python
from seeknal.decorators import feature_group

@feature_group(
    name="customer_features",
    entity="customer_id",
    features=["total_orders", "total_revenue", "avg_order_value"],
)
def customer_features(orders_cleaned):
    return orders_cleaned.groupBy("customer_id").agg(
        count("order_id").alias("total_orders"),
        sum("revenue").alias("total_revenue"),
        avg("revenue").alias("avg_order_value"),
    )
```

### @second_order_aggregation

```python
from seeknal.decorators import second_order_aggregation

@second_order_aggregation(
    name="region_metrics",
    group_by=["region"],
    aggregations={
        "avg_customer_revenue": ("total_revenue", "mean"),
        "max_total_orders": ("total_orders", "max"),
    },
)
def region_metrics(customer_features):
    pass
```

---

## Project Structure

```
project/
├── seeknal_project.yml          # Project configuration
├── profiles.yml                 # Local credentials (.gitignored)
├── profiles-dev.yml             # Dev environment profile
├── data/                        # Raw data files
├── seeknal/
│   ├── sources/                 # Source definitions
│   ├── transforms/              # SQL/Python transforms
│   ├── rules/                   # Data quality rules
│   ├── profiles/                # Data profiling configs
│   ├── pipelines/               # Pipeline orchestration
│   ├── semantic_models/         # Metric layer definitions
│   ├── exposures/               # Downstream dependency docs
│   └── common/                  # Shared macros/utilities
└── target/                      # Build artifacts (git-ignored)
```
