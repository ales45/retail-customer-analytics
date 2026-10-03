"""Extract step: download the UCI Online Retail dataset and cache it as Parquet."""

import logging
import urllib.request
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from retail_analytics.config import DATASET_URL, RAW_DIR, RAW_PARQUET, RAW_XLSX

logger = logging.getLogger(__name__)


def download_dataset(url: str = DATASET_URL, dest_dir: Path = RAW_DIR) -> Path:
    """Download and unzip the dataset if it is not already present."""
    if RAW_XLSX.exists():
        logger.info("Raw file already present: %s", RAW_XLSX)
        return RAW_XLSX

    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "online_retail.zip"
    logger.info("Downloading dataset from %s", url)
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest_dir)
    return RAW_XLSX


def extract(force: bool = False) -> pd.DataFrame:
    """Return the raw transactions, reading the slow XLSX only once and caching to Parquet."""
    if RAW_PARQUET.exists() and not force:
        logger.info("Reading cached raw data: %s", RAW_PARQUET)
        return duckdb.sql(f"SELECT * FROM read_parquet('{RAW_PARQUET.as_posix()}')").df()

    xlsx_path = download_dataset()
    logger.info("Reading XLSX (this takes ~1 minute the first time)")
    raw = pd.read_excel(xlsx_path, dtype={"InvoiceNo": str, "StockCode": str})

    RAW_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    duckdb.register("raw_df", raw)
    duckdb.sql(f"COPY raw_df TO '{RAW_PARQUET.as_posix()}' (FORMAT parquet)")
    return raw
