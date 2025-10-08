from great_tables.data import sp500
import polars as pl

sp500 = pl.from_pandas(sp500)
