import pytest

from retail_analytics.transform import clean_transactions


def test_output_columns_are_snake_case(raw_sample):
    clean, _ = clean_transactions(raw_sample)
    assert list(clean.columns) == [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
        "revenue",
    ]


def test_removes_cancellations_invalid_prices_and_missing_customers(raw_sample):
    clean, _ = clean_transactions(raw_sample)
    assert not clean["invoice_no"].str.startswith("C").any()
    assert (clean["unit_price"] > 0).all()
    assert (clean["quantity"] > 0).all()
    assert clean["customer_id"].notna().all()
    assert len(clean) == 3


def test_computes_revenue_and_strips_descriptions(raw_sample):
    clean, _ = clean_transactions(raw_sample)
    first = clean.iloc[0]
    assert first["revenue"] == pytest.approx(15.3)
    assert first["description"] == "WHITE HANGING HEART"


def test_customer_id_is_integer(raw_sample):
    clean, _ = clean_transactions(raw_sample)
    assert str(clean["customer_id"].dtype) == "Int64"


def test_quality_report_accounts_for_every_dropped_row(raw_sample):
    clean, report = clean_transactions(raw_sample)
    assert report == {
        "rows_in": 7,
        "duplicates": 1,
        "cancellations": 1,
        "missing_customer_id": 1,
        "non_positive_quantity_or_price": 1,
        "rows_out": 3,
    }
    dropped = sum(v for k, v in report.items() if k not in ("rows_in", "rows_out"))
    assert report["rows_in"] - dropped == len(clean)


def test_does_not_mutate_input(raw_sample):
    before = raw_sample.copy()
    clean_transactions(raw_sample)
    assert raw_sample.equals(before)
