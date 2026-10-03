"""Entry point: run the full Extract -> Transform -> Load -> Report pipeline."""

import argparse
import logging

from retail_analytics.extract import extract
from retail_analytics.load import load
from retail_analytics.report import build_report
from retail_analytics.transform import clean_transactions

logger = logging.getLogger("retail_analytics")


def run(force_extract: bool = False) -> None:
    raw = extract(force=force_extract)
    clean, quality = clean_transactions(raw)
    logger.info("Data quality: %s", quality)
    con = load(clean)
    try:
        build_report(con, quality)
    finally:
        con.close()
    logger.info("Pipeline finished")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-extract", action="store_true", help="re-read the raw XLSX")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run(force_extract=args.force_extract)


if __name__ == "__main__":
    main()
