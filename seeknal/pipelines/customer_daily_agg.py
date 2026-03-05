# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Transform: Daily aggregation per customer for SOA input."""

from seeknal.pipeline import transform


@transform(
    name="customer_daily_agg",
    description="Daily aggregation per customer with region context",
)
def customer_daily_agg(ctx):
    """Aggregate transactions to daily customer level."""
    txn = ctx.ref("source.transactions")

    return ctx.duckdb.sql("""
        SELECT
            customer_id,
            region,
            CAST(order_date AS DATE) AS order_date,
            CURRENT_DATE AS application_date,
            CAST(SUM(revenue) AS DOUBLE) AS daily_amount,
            CAST(COUNT(*) AS BIGINT) AS daily_count
        FROM txn
        GROUP BY customer_id, region, CAST(order_date AS DATE)
    """).df()