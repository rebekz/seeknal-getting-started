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