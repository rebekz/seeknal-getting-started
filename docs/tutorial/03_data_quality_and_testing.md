# Module 3: Data Quality & Testing

| Duration | Difficulty | Prerequisites |
|----------|------------|---------------|
| ~45 minutes | Beginner-Intermediate | Modules 1-2 completed |

In Module 2 you cleaned messy data by hand — filtering negatives, removing nulls, casting types.
That works once. In production, new data arrives every hour.
Automated quality checks catch problems the moment they appear, before bad data reaches dashboards or ML models.

---

## Why Data Quality Matters

IBM estimates poor data quality costs US businesses **$3.1 trillion per year**.

Quality failures in practice:

| Failure | Business Impact |
|---------|----------------|
| Incorrect inventory counts | Stockouts, lost sales |
| Wrong customer addresses | Failed deliveries, returns |
| Duplicate transactions | Inflated revenue reports |
| Missing timestamps | Broken time-series analytics |

Data quality has four dimensions:

| Dimension | Question It Answers |
|-----------|---------------------|
| **Completeness** | Are all required fields present? |
| **Accuracy** | Are the values correct and within expected bounds? |
| **Consistency** | Do related fields agree with each other? |
| **Timeliness** | Is the data fresh enough for its use case? |

Modern data teams encode these expectations as **data contracts** — automated rules that run on every pipeline execution.
Seeknal's `rule` and `profile` nodes make this straightforward.

---

## What You Will Build

By the end of this module you will have:

1. Validation rules that detect quality issues in raw data
2. Data profiling for statistical analysis
3. Profile-based quality checks with thresholds
4. A clear understanding of severity levels (`warn` vs `error`)

---

## Step 3.1 — Create a Revenue Validation Rule

In Module 1 you spotted order `ORD-005` with revenue of `-10.00`.
Create a rule that catches this automatically.

```bash
seeknal draft rule order_revenue_valid
```

Edit the draft file:

**`draft_rule_order_revenue_valid.yml`**

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
  severity: warn
  error_message: "Found orders with invalid revenue values"
```

Key fields:

- `kind: rule` — declares a data quality validation node.
- `type: range` — checks whether every value in the column falls within `min_val` and `max_val`.
- `severity: warn` — the pipeline **logs a warning** but continues execution. (Use `severity: error` in production when a violation should halt the pipeline.)
- The rule references `source.raw_orders`, which still contains the original messy data including that negative revenue row.

Validate and apply:

```bash
seeknal dry-run draft_rule_order_revenue_valid.yml
seeknal apply draft_rule_order_revenue_valid.yml
```

---

## Step 3.2 — Create a Null Check Rule

The raw orders data also contains null values in critical fields.
Add a second rule to catch those.

```bash
seeknal draft rule order_not_null
```

Edit the draft file:

**`draft_rule_order_not_null.yml`**

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
  severity: warn
  error_message: "Found null values in critical order fields"
```

Two rule types compared:

| Property | `type: range` | `type: "null"` |
|----------|---------------|----------------|
| Purpose | Check numeric bounds | Check for missing values |
| Target | Single `column` | Multiple `columns` |
| Key param | `min_val`, `max_val` | `max_null_percentage` |

Setting `max_null_percentage: 0.0` means zero tolerance — even a single null triggers a warning.

Validate and apply:

```bash
seeknal dry-run draft_rule_order_not_null.yml
seeknal apply draft_rule_order_not_null.yml
```

---

## Step 3.3 — Run Rules and See Warnings

Execute the pipeline.

```bash
seeknal run
```

Expected output — the rules detect issues and **warn**:

```
Planning pipeline...
Executing 5 node(s)...
  ✓ source.raw_orders (13 rows)
  ⚠ rule.order_revenue_valid — WARN: Found orders with invalid revenue values
    1 row(s) outside range [0, 100000]
  ⚠ rule.order_not_null — WARN: Found null values in critical order fields
    customer_id: 1 null(s) (7.7%)
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.daily_revenue (7 rows)
```

### What just happened?

1. Seeknal loaded the raw orders source (all 13 rows, including bad data).
2. `order_revenue_valid` scanned the `revenue` column and found one row outside `[0, 100000]` — that is `ORD-005` with `-10.00`.
3. `order_not_null` scanned `customer_id`, `order_date`, and `status` and found one null `customer_id` — that is `ORD-008`.
4. Both rules reported **WARN** because their severity is `warn`. The pipeline continues to completion, but the warnings are logged for investigation.
5. The downstream transforms (`orders_cleaned`, `daily_revenue`) executed successfully because they reference the cleaned data, not the raw source directly.

> **Tip:** In production, you would typically set `severity: error` for critical violations (like null primary keys or negative revenue) so the pipeline **halts** before bad data reaches dashboards. We use `warn` here so you can run the full tutorial pipeline end-to-end. See the severity table in Step 3.6 for guidance on when to use each level.

**Teaching moment:** These rules detected exactly the same problems you found manually in Module 1. The difference is that now the checks are automated. Every time the pipeline runs — whether triggered by a cron job at 3 AM or a CI/CD deploy — these rules execute. This is how production data teams catch problems before they reach dashboards and ML models.

---

## Step 3.4 — Add a New Data Source: Products

Introduce a second dataset to practice profiling and additional quality checks.

**`data/products.csv`**

```csv
product_id,name,category,price,launch_date
PRD-001,Wireless Headphones,Electronics,79.99,2025-09-01
PRD-002,Running Shoes,Apparel,120.00,2025-08-15
PRD-003,Coffee Maker,Kitchen,49.99,2025-10-01
PRD-004,Yoga Mat,Sports,35.00,2025-07-20
PRD-005,Desk Lamp,Office,28.50,2025-11-01
PRD-006,Noise Cancelling Headphones,Electronics,199.99,2025-10-15
```

Six products across five categories with prices ranging from $28.50 to $199.99.
This dataset is intentionally clean — no nulls, no negatives, no duplicates.

Register it as a source:

```bash
seeknal draft source products
```

Edit the draft file:

**`draft_source_products.yml`**

```yaml
kind: source
name: products
description: "Product catalog with pricing and categories"
source: csv
table: "data/products.csv"
columns:
  product_id: "Unique product identifier"
  name: "Product display name"
  category: "Product category"
  price: "Product price in USD"
  launch_date: "Product launch date"
```

Validate and apply:

```bash
seeknal dry-run draft_source_products.yml
seeknal apply draft_source_products.yml
```

This follows the same pattern as `raw_orders.yml` from Module 1.

---

## Step 3.5 — Data Profiling

Before writing quality rules for a new dataset, profile it first.
Profiling computes statistics that reveal the shape and distribution of your data.

### Full Profile

```bash
seeknal draft profile products_stats
```

**`draft_profile_products_stats.yml`**

```yaml
kind: profile
name: products_stats
description: "Full statistical profile of the products catalog"
inputs:
  - ref: source.products
```

A full profile with no column restrictions computes the following for every column:

| Metric | Description |
|--------|-------------|
| `row_count` | Total number of rows |
| `null_count` | Number of null values |
| `null_percent` | Percentage of nulls |
| `distinct_count` | Number of unique values |
| `mean` | Average (numeric columns) |
| `stddev` | Standard deviation (numeric columns) |
| `min` | Minimum value |
| `max` | Maximum value |

Validate and apply:

```bash
seeknal dry-run draft_profile_products_stats.yml
seeknal apply draft_profile_products_stats.yml
```

### Focused Profile

Sometimes you only care about specific columns.

```bash
seeknal draft profile products_price_stats
```

**`draft_profile_products_price_stats.yml`**

```yaml
kind: profile
name: products_price_stats
description: "Focused profile on price and category columns"
inputs:
  - ref: source.products
profile:
  columns: [price, category]
  params:
    max_top_values: 3
```

Key differences from the full profile:

- `columns: [price, category]` — restricts profiling to only these two columns.
- `max_top_values: 3` — reports the 3 most frequent values per column.

Validate and apply:

```bash
seeknal dry-run draft_profile_products_price_stats.yml
seeknal apply draft_profile_products_price_stats.yml
```

Profile results are not just informational — downstream `rule` nodes can reference them to enforce thresholds based on actual statistics.

---

## Step 3.6 — Price Range Validation

Add a validation rule for product prices.

```bash
seeknal draft rule valid_prices
```

**`draft_rule_valid_prices.yml`**

```yaml
kind: rule
name: valid_prices
description: "Product prices must be within a reasonable range"
inputs:
  - ref: source.products
rule:
  type: range
  column: price
  params:
    min_val: 0
    max_val: 10000
params:
  severity: warn
  error_message: "Found products with unusual price values"
```

Notice the difference: `severity: warn` instead of `error`.
A warning logs the issue but does **not** halt the pipeline.

When to use each severity:

| Severity | Pipeline Behavior | Example Use Case |
|----------|-------------------|------------------|
| `error` | **Halts** execution | Negative revenue, null primary keys |
| `warn` | **Continues**, warning logged | Unusually high prices, unexpected categories |

Use `error` for violations that would corrupt downstream results.
Use `warn` for anomalies that deserve investigation but are not necessarily wrong.

Validate and apply:

```bash
seeknal dry-run draft_rule_valid_prices.yml
seeknal apply draft_rule_valid_prices.yml
```

---

## Step 3.7 — Profile-Based Quality Checks

The most powerful quality checks use profile statistics as inputs.
Instead of checking individual rows, you check aggregate metrics.

```bash
seeknal draft rule products_quality
```

**`draft_rule_products_quality.yml`**

```yaml
kind: rule
name: products_quality
description: "Quality checks based on profile statistics"
inputs:
  - ref: profile.products_stats
rule:
  type: profile_check
  checks:
    - metric: row_count
      fail: "< 1"
    - column: price
      metric: avg
      warn: "> 500"
    - column: price
      metric: null_percent
      fail: "> 0"
    - column: category
      metric: distinct_count
      warn: "< 2"
```

Walk through each check:

| # | Check | Threshold | Severity | Meaning |
|---|-------|-----------|----------|---------|
| 1 | `row_count` | `< 1` | `fail` | Table must not be empty |
| 2 | `price` → `avg` | `> 500` | `warn` | Flag if average price seems too high |
| 3 | `price` → `null_percent` | `> 0` | `fail` | Every product must have a price |
| 4 | `category` → `distinct_count` | `< 2` | `warn` | Flag if all products are in one category |

Notice the input: `ref: profile.products_stats`.
This rule does **not** read the raw data — it reads the statistical profile computed in Step 3.5.
The dependency chain is:

```
source.products → profile.products_stats → rule.products_quality
```

Seeknal resolves this automatically. The profile runs first, then the rule reads its output.

Validate and apply:

```bash
seeknal dry-run draft_rule_products_quality.yml
seeknal apply draft_rule_products_quality.yml
```

---

## Step 3.8 — Run the Full Pipeline

Execute everything together.

```bash
seeknal run
```

Expected output:

```
Planning pipeline...
Executing 10 node(s)...
  ✓ source.raw_orders (13 rows)
  ✓ source.products (6 rows)
  ⚠ rule.order_revenue_valid — WARN: Found orders with invalid revenue values
    1 row(s) outside range [0, 100000]
  ⚠ rule.order_not_null — WARN: Found null values in critical order fields
    customer_id: 1 null(s) (7.7%)
  ✓ rule.valid_prices — PASSED
  ✓ profile.products_stats — completed
  ✓ profile.products_price_stats — completed
  ✓ rule.products_quality — PASSED
  ✓ transform.orders_cleaned (11 rows)
  ✓ transform.daily_revenue (7 rows)
```

### What just happened?

1. Seeknal planned the execution order, respecting dependencies (sources first, then profiles, then rules and transforms).
2. Both sources loaded successfully — 13 raw orders and 6 products.
3. The **order rules warned** as expected: the raw orders still contain a negative revenue row and a null customer ID. Because these rules use `severity: warn`, the pipeline continues.
4. The **product rules passed**: all prices are between $0 and $10,000, no nulls exist, average price ($85.58) is well under $500, and there are 5 distinct categories.
5. Both profiles computed statistics that the `products_quality` rule consumed.
6. The cleaned transforms still produced correct output because `orders_cleaned` filters out the bad rows before aggregation.

This result illustrates the core value of layered quality checks: raw data can be messy, but your pipeline documents exactly **where** and **what** the problems are while still producing clean output downstream.

---

## Severity Levels — A Deeper Look

Understanding when to use `error` vs `warn` is a judgment call that depends on business context.

| Scenario | Recommended Severity | Reasoning |
|----------|---------------------|-----------|
| Null primary key | `error` | Breaks joins, causes duplicates |
| Negative revenue | `error` | Corrupts financial reports |
| Price above $10,000 | `warn` | Unusual but could be legitimate (luxury items) |
| Only 1 category present | `warn` | Might indicate a data load issue, but not necessarily wrong |
| Empty table (0 rows) | `error` | Upstream extraction likely failed |
| Null optional field (e.g., `middle_name`) | `warn` | Expected to be missing sometimes |

### Industry Practice: Data Contracts and SLAs

In professional data engineering, teams formalize quality expectations:

**Data Contracts** define what the data producer guarantees:
- "The `orders` table will have no null `customer_id` values"
- "Revenue will always be non-negative"
- "Data will be refreshed by 6:00 AM UTC daily"

**Service Level Agreements (SLAs)** define consequences:
- Error-severity failures trigger PagerDuty alerts
- Warn-severity failures create Jira tickets for review
- Repeated violations escalate to the data producer's team

The rules you built in this module are a simplified version of data contracts.
In production, tools like Seeknal, Great Expectations, dbt tests, and Monte Carlo automate this pattern at scale.

---

## Recap: Node Types So Far

After three modules, your pipeline uses four Seeknal node types:

| Node Type | Kind | Purpose | Introduced |
|-----------|------|---------|------------|
| Source | `kind: source` | Load raw data | Module 1 |
| Transform | `kind: transform` | Clean, filter, aggregate | Module 2 |
| Rule | `kind: rule` | Validate data quality | Module 3 |
| Profile | `kind: profile` | Compute statistics | Module 3 |

Each node declares its inputs with `ref:`, and Seeknal builds the dependency graph automatically.

---

## Checkpoint

Verify you have completed every step:

- [ ] Created `seeknal/rules/order_revenue_valid.yml` — range check on revenue
- [ ] Created `seeknal/rules/order_not_null.yml` — null check on critical fields
- [ ] Ran the pipeline and saw both order rules **warn** on raw data
- [ ] Created `data/products.csv` with 6 products
- [ ] Created `seeknal/sources/products.yml`
- [ ] Created `seeknal/profiles/products_stats.yml` — full profile
- [ ] Created `seeknal/profiles/products_price_stats.yml` — focused profile
- [ ] Created `seeknal/rules/valid_prices.yml` with `severity: warn`
- [ ] Created `seeknal/rules/products_quality.yml` — profile-based checks
- [ ] Understood the difference between `error` and `warn` severity

### Project Structure

```
ecommerce-pipeline/
├── seeknal_project.yml
├── data/
│   ├── orders.csv
│   └── products.csv
├── seeknal/
│   ├── sources/
│   │   ├── raw_orders.yml
│   │   └── products.yml
│   ├── transforms/
│   │   ├── orders_cleaned.yml
│   │   └── daily_revenue.yml
│   ├── rules/
│   │   ├── order_revenue_valid.yml
│   │   ├── order_not_null.yml
│   │   ├── valid_prices.yml
│   │   └── products_quality.yml
│   └── profiles/
│       ├── products_stats.yml
│       └── products_price_stats.yml
└── target/
```

---

## Key Takeaways

1. **Automate quality checks** — manual inspection does not scale. Rules run on every pipeline execution.
2. **Profile before you validate** — statistics reveal what "normal" looks like for your data.
3. **Choose severity carefully** — `error` for violations that corrupt results, `warn` for anomalies worth investigating.
4. **Layer your defenses** — raw data rules catch ingestion problems, profile-based rules catch distribution shifts.
5. **Rules prove the value of cleaning** — the order rules fail on raw data but the cleaned transforms still produce correct output.

---

Continue to [Module 4: Advanced Sources & CDC](04_advanced_sources_and_cdc.md)
