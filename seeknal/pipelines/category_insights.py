# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Transform: Category-level insights with pandas analytics."""

from seeknal.pipeline import transform
import pandas as pd


@transform(
    name="category_insights",
    description="Category performance ranking and share analysis",
)
def category_insights(ctx):
    """Compute category market share and performance ranking."""
    enriched = ctx.ref("transform.sales_enriched")

    # Use pandas for operations that are cleaner than SQL
    if not isinstance(enriched, pd.DataFrame):
        enriched = enriched.df()

    # Filter out NULL categories (orphan products)
    df = enriched[enriched["category"].notna()].copy()

    # Aggregate by category
    summary = df.groupby("category").agg(
        order_count=("event_id", "count"),
        total_units=("quantity", "sum"),
        total_revenue=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
    ).reset_index()

    # Add market share (percentage of total revenue)
    total = summary["total_revenue"].sum()
    summary["revenue_share_pct"] = round(summary["total_revenue"] / total * 100, 2)

    # Rank categories
    summary["rank"] = summary["total_revenue"].rank(ascending=False).astype(int)

    return summary.sort_values("rank")