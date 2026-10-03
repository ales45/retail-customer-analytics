"""Transform step: clean raw transactions and report every row that was dropped."""

import pandas as pd

COLUMN_MAP = {
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "UnitPrice": "unit_price",
    "CustomerID": "customer_id",
    "Country": "country",
}


def clean_transactions(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean raw sales lines for customer analytics.

    Rules, applied in order so each dropped row is counted exactly once:
      1. exact duplicate lines
      2. cancellations (invoice numbers starting with "C")
      3. lines without a customer id (cannot be attributed to a customer)
      4. non-positive quantity or unit price (adjustments, bad debt, free samples)
    """
    df = raw.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())].copy()
    df["invoice_no"] = df["invoice_no"].astype(str).str.strip()
    report = {"rows_in": len(df)}

    deduped = df.drop_duplicates()
    report["duplicates"] = len(df) - len(deduped)
    df = deduped

    is_cancellation = df["invoice_no"].str.startswith("C")
    report["cancellations"] = int(is_cancellation.sum())
    df = df[~is_cancellation]

    has_customer = df["customer_id"].notna()
    report["missing_customer_id"] = int((~has_customer).sum())
    df = df[has_customer]

    is_valid = (df["quantity"] > 0) & (df["unit_price"] > 0)
    report["non_positive_quantity_or_price"] = int((~is_valid).sum())
    df = df[is_valid]

    df = df.assign(
        stock_code=df["stock_code"].astype(str).str.strip(),
        description=df["description"].astype("string").str.strip(),
        invoice_date=pd.to_datetime(df["invoice_date"]),
        customer_id=df["customer_id"].astype("Int64"),
        country=df["country"].str.strip(),
        revenue=(df["quantity"] * df["unit_price"]).round(2),
    ).reset_index(drop=True)

    report["rows_out"] = len(df)
    return df, report
