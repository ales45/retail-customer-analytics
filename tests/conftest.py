import pandas as pd
import pytest


@pytest.fixture
def raw_sample() -> pd.DataFrame:
    """Small raw extract mimicking the UCI Online Retail schema, with known data issues."""
    return pd.DataFrame(
        {
            "InvoiceNo": ["536365", "536365", "536366", "C536379", "536380", "536381", "536381"],
            "StockCode": ["85123A", "71053", "22633", "D", "22728", "22960", "22960"],
            "Description": [
                " WHITE HANGING HEART ",
                "WHITE METAL LANTERN",
                "HAND WARMER",
                "Discount",
                "ALARM CLOCK",
                "JAM MAKING SET",
                "JAM MAKING SET",
            ],
            "Quantity": [6, 6, 2, -1, 3, 4, 4],
            "InvoiceDate": pd.to_datetime(
                [
                    "2010-12-01 08:26",
                    "2010-12-01 08:26",
                    "2010-12-01 08:28",
                    "2010-12-01 09:41",
                    "2010-12-01 09:45",
                    "2010-12-01 10:00",
                    "2010-12-01 10:00",
                ]
            ),
            "UnitPrice": [2.55, 3.39, 1.85, 27.50, 0.0, 4.25, 4.25],
            "CustomerID": [17850.0, 17850.0, 17850.0, 14527.0, 13047.0, None, None],
            "Country": ["United Kingdom"] * 7,
        }
    )
