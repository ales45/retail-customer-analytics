"""Load step: persist clean data into DuckDB and build the SQL analytics models."""

import logging
from pathlib import Path

import duckdb
import pandas as pd

from retail_analytics.config import SQL_DIR, WAREHOUSE_PATH

logger = logging.getLogger(__name__)


def build_models(con: duckdb.DuckDBPyConnection, sql_dir: Path = SQL_DIR) -> list[str]:
    """Run every model in `sql_dir` in filename order. Each file creates one table."""
    built = []
    for sql_file in sorted(sql_dir.glob("*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8"))
        built.append(sql_file.stem)
        logger.info("Built model %s", sql_file.stem)
    return built


def load(clean: pd.DataFrame, db_path: Path = WAREHOUSE_PATH) -> duckdb.DuckDBPyConnection:
    """Replace the `sales` fact table and rebuild downstream models. Returns an open connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.register("clean_df", clean)
    con.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM clean_df")
    con.unregister("clean_df")
    build_models(con)
    return con
