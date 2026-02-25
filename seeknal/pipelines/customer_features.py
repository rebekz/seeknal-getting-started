# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Feature Group: Customer purchase behavior features."""

from seeknal.pipeline import feature_group


@feature_group(
    name="customer_features",
    entity="customer",
    description="Customer purchase behavior features for ML models",
)
def customer_features(ctx):
    """Compute customer-level features from transaction data."""
    # Reference the Python source
    txn = ctx.ref("source.transactions")

    return ctx.duckdb.sql("""
        SELECT
            customer_id,
            CAST(COUNT(DISTINCT order_id) AS BIGINT) AS total_orders,
            CAST(SUM(revenue) AS DOUBLE) AS total_revenue,
            CAST(AVG(revenue) AS DOUBLE) AS avg_order_value,
            MIN(order_date) AS first_order_date,
            MAX(order_date) AS last_order_date,
            CURRENT_TIMESTAMP AS event_time
        FROM txn
        GROUP BY customer_id
    """).df()