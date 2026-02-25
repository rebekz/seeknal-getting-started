# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
#     "duckdb",
# ]
# ///

"""Source: Customer transaction data for feature engineering."""

from seeknal.pipeline import source


@source(
    name="transactions",
    source="csv",
    table="data/transactions.csv",
    description="Raw customer transactions with order details",
)
def transactions(ctx=None):
    """Declare transaction data source from CSV."""
    pass