from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

DATASET_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
RAW_XLSX = RAW_DIR / "Online Retail.xlsx"
RAW_PARQUET = PROCESSED_DIR / "raw_transactions.parquet"
WAREHOUSE_PATH = PROCESSED_DIR / "warehouse.duckdb"
