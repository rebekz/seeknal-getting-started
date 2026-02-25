# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "pyarrow",
# ]
# ///

"""Source: Currency exchange rates for multi-region revenue analysis."""

from seeknal.pipeline import source
import pandas as pd


@source(
    name="exchange_rates",
    source="csv",
    table="data/exchange_rates.csv",
    description="Currency exchange rates by region",
)
def exchange_rates(ctx=None):
    """Declare exchange rate lookup source from CSV."""
    pass