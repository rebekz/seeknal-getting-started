# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Second-order aggregation: Region-level meta-features."""

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
)
def region_metrics(ctx):
    """Load data for SOA engine — the engine handles aggregation."""
    return ctx.ref("transform.customer_daily_agg")