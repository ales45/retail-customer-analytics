import duckdb
import pandas as pd
import pytest

from retail_analytics.load import build_models


@pytest.fixture
def con():
    sales = pd.DataFrame(
        {
            "invoice_no": ["1", "2", "3", "4", "5"],
            "stock_code": ["A"] * 5,
            "description": ["x"] * 5,
            "quantity": [1, 2, 1, 5, 1],
            "invoice_date": pd.to_datetime(
                ["2011-01-05", "2011-02-10", "2011-01-20", "2011-03-01", "2011-03-15"]
            ),
            "unit_price": [10.0, 10.0, 50.0, 10.0, 20.0],
            "customer_id": pd.array([1, 1, 2, 1, 3], dtype="Int64"),
            "country": ["UK", "UK", "France", "UK", "Germany"],
        }
    )
    sales["revenue"] = sales["quantity"] * sales["unit_price"]
    connection = duckdb.connect()
    connection.register("sales_df", sales)
    connection.execute("CREATE TABLE sales AS SELECT * FROM sales_df")
    build_models(connection)
    yield connection
    connection.close()


def test_monthly_kpis(con):
    df = con.execute("SELECT * FROM monthly_kpis ORDER BY month").df()
    assert df["revenue"].tolist() == [60.0, 20.0, 70.0]
    assert df["orders"].tolist() == [2, 1, 2]
    assert df["customers"].tolist() == [2, 1, 2]


def test_rfm_metrics(con):
    df = (
        con.execute("SELECT * FROM customer_rfm ORDER BY customer_id").df().set_index("customer_id")
    )
    # Snapshot date is the day after the last invoice: 2011-03-16
    assert df.loc[1, "recency_days"] == 15
    assert df.loc[1, "frequency"] == 3
    assert df.loc[1, "monetary"] == 80.0
    assert df.loc[3, "recency_days"] == 1
    assert set(df["segment"]).issubset(
        {"Champions", "Loyal", "Potential Loyalist", "At Risk", "Hibernating", "Others"}
    )


def test_cohort_retention(con):
    df = con.execute("SELECT * FROM cohort_retention").df()
    jan = df[df["cohort_month"] == pd.Timestamp("2011-01-01")].set_index("months_since_first")
    assert jan.loc[0, "cohort_size"] == 2
    assert jan.loc[0, "retention_rate"] == 1.0
    assert jan.loc[1, "active_customers"] == 1
    assert jan.loc[1, "retention_rate"] == 0.5


def test_country_revenue_sorted_desc(con):
    df = con.execute("SELECT * FROM country_revenue").df()
    assert df["country"].tolist()[0] == "UK"
    assert df["revenue_share"].sum() == pytest.approx(1.0)
