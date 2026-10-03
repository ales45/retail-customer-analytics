"""Report step: render charts and a Markdown summary from the DuckDB models."""

import logging
from pathlib import Path

import duckdb
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

from retail_analytics.config import FIGURES_DIR, REPORTS_DIR  # noqa: E402

logger = logging.getLogger(__name__)

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.titlecolor": TEXT_PRIMARY,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "font.size": 10,
    }
)


def _money(value: float, _pos=None) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:.0f}K"
    return f"£{value:.0f}"


def _save(fig: plt.Figure, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", path)
    return path


def plot_monthly_revenue(con: duckdb.DuckDBPyConnection) -> Path:
    # The dataset ends on 2011-12-09, so the last month is partial and excluded.
    df = con.execute(
        "SELECT * FROM monthly_kpis WHERE month < (SELECT MAX(month) FROM monthly_kpis)"
    ).df()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["month"], df["revenue"], color=SERIES, linewidth=2, marker="o", markersize=5)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(FuncFormatter(_money))
    ax.set_ylim(bottom=0)
    peak = df.loc[df["revenue"].idxmax()]
    ax.annotate(
        f"Peak: {_money(peak['revenue'])}",
        (peak["month"], peak["revenue"]),
        textcoords="offset points",
        xytext=(-10, -4),
        ha="right",
        color=TEXT_PRIMARY,
    )
    ax.set_title("Monthly revenue, Dec 2010 – Nov 2011")
    fig.text(0.125, -0.02, "Dec 2011 excluded (data ends on Dec 9).", color=TEXT_SECONDARY)
    return _save(fig, "monthly_revenue")


def plot_rfm_segments(con: duckdb.DuckDBPyConnection) -> Path:
    df = con.execute(
        """
        SELECT segment, COUNT(*) AS customers,
               SUM(monetary) / SUM(SUM(monetary)) OVER () AS share
        FROM customer_rfm GROUP BY segment ORDER BY share
        """
    ).df()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(df["segment"], df["share"], color=SERIES, height=0.6)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    for bar, customers in zip(bars, df["customers"], strict=True):
        ax.text(
            bar.get_width() + 0.005,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.0%} · {customers:,} customers",
            va="center",
            color=TEXT_PRIMARY,
        )
    ax.set_xlim(0, df["share"].max() * 1.4)
    ax.set_title("Share of revenue by RFM segment")
    return _save(fig, "rfm_segments")


def plot_cohort_retention(con: duckdb.DuckDBPyConnection) -> Path:
    # Drop activity in the partial last month (Dec 2011), which would understate retention.
    df = con.execute(
        """
        SELECT * FROM cohort_retention
        WHERE cohort_month + to_months(months_since_first)
              < (SELECT MAX(month) FROM monthly_kpis)
        """
    ).df()
    matrix = df.pivot(index="cohort_month", columns="months_since_first", values="retention_rate")
    matrix = matrix.drop(columns=0).dropna(how="all")  # month 0 is always 100%
    fig, ax = plt.subplots(figsize=(11, 6))
    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQUENTIAL)
    image = ax.imshow(matrix.values, cmap=cmap, aspect="auto", vmin=0, vmax=0.5)
    ax.grid(visible=False)
    ax.set_xticks(range(matrix.shape[1]), matrix.columns)
    ax.set_yticks(range(matrix.shape[0]), [d.strftime("%b %Y") for d in matrix.index])
    ax.set_xlabel("Months since first purchase")
    for (row, col), value in np.ndenumerate(matrix.values):
        if np.isnan(value):
            continue
        ax.text(
            col,
            row,
            f"{value:.0%}",
            ha="center",
            va="center",
            fontsize=8,
            color="#ffffff" if value > 0.3 else TEXT_PRIMARY,
        )
    cbar = fig.colorbar(image, ax=ax, format=PercentFormatter(1.0, decimals=0))
    cbar.outline.set_visible(False)
    ax.set_title("Customer retention by monthly cohort")
    return _save(fig, "cohort_retention")


def plot_top_countries(con: duckdb.DuckDBPyConnection, top_n: int = 10) -> Path:
    df = con.execute(f"SELECT * FROM country_revenue LIMIT {top_n}").df().iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(df["country"], df["revenue"], color=SERIES, height=0.6)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(FuncFormatter(_money))
    for bar, share in zip(bars, df["revenue_share"], strict=True):
        ax.text(
            bar.get_width() + df["revenue"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{share:.1%}",
            va="center",
            color=TEXT_PRIMARY,
        )
    ax.set_xlim(right=df["revenue"].max() * 1.12)
    ax.set_title(f"Top {top_n} countries by revenue")
    return _save(fig, "top_countries")


def write_summary(con: duckdb.DuckDBPyConnection, quality: dict[str, int]) -> Path:
    revenue, orders, customers, start, end = con.execute(
        """
        SELECT SUM(revenue), COUNT(DISTINCT invoice_no), COUNT(DISTINCT customer_id),
               MIN(invoice_date)::DATE, MAX(invoice_date)::DATE
        FROM sales
        """
    ).fetchone()
    top_decile_share = con.execute(
        """
        WITH ranked AS (
            SELECT monetary, NTILE(10) OVER (ORDER BY monetary DESC) AS decile
            FROM customer_rfm
        )
        SELECT SUM(monetary) FILTER (WHERE decile = 1) / SUM(monetary) FROM ranked
        """
    ).fetchone()[0]
    one_time_share = con.execute(
        "SELECT AVG(CASE WHEN frequency = 1 THEN 1.0 ELSE 0 END) FROM customer_rfm"
    ).fetchone()[0]
    m1_retention = con.execute(
        """
        SELECT AVG(retention_rate) FROM cohort_retention
        WHERE months_since_first = 1
          AND cohort_month + to_months(1) < (SELECT MAX(month) FROM monthly_kpis)
        """
    ).fetchone()[0]
    uk_share = con.execute(
        "SELECT revenue_share FROM country_revenue WHERE country = 'United Kingdom'"
    ).fetchone()[0]
    segments = con.execute(
        """
        SELECT segment, COUNT(*) AS customers, AVG(recency_days) AS avg_recency,
               AVG(frequency) AS avg_frequency, AVG(monetary) AS avg_monetary,
               SUM(monetary) / SUM(SUM(monetary)) OVER () AS revenue_share
        FROM customer_rfm GROUP BY segment ORDER BY revenue_share DESC
        """
    ).df()

    segment_rows = "\n".join(
        f"| {r.segment} | {r.customers:,} | {r.avg_recency:.0f} | {r.avg_frequency:.1f} "
        f"| £{r.avg_monetary:,.0f} | {r.revenue_share:.1%} |"
        for r in segments.itertuples()
    )
    quality_rows = "\n".join(f"| {k} | {v:,} |" for k, v in quality.items())

    content = f"""# Analysis summary

> Auto-generated by `python -m retail_analytics.pipeline`. Do not edit by hand.

**Period:** {start} → {end} · **Revenue:** £{revenue:,.0f} · **Orders:** {orders:,} \
· **Customers:** {customers:,}

## Key findings

- **Revenue is concentrated:** the top 10% of customers generate **{top_decile_share:.0%}** \
of revenue.
- **Retention is the main lever:** on average only **{m1_retention:.0%}** of a cohort buys \
again the month after its first purchase, and **{one_time_share:.0%}** of customers bought \
only once.
- **Single-market dependency:** the United Kingdom accounts for **{uk_share:.0%}** of revenue.

## RFM segments

| Segment | Customers | Avg recency (days) | Avg orders | Avg spend | Revenue share |
|---|---:|---:|---:|---:|---:|
{segment_rows}

## Data quality

| Check | Rows |
|---|---:|
{quality_rows}

## Charts

![Monthly revenue](figures/monthly_revenue.png)
![RFM segments](figures/rfm_segments.png)
![Cohort retention](figures/cohort_retention.png)
![Top countries](figures/top_countries.png)
"""
    path = REPORTS_DIR / "summary.md"
    path.write_text(content, encoding="utf-8")
    logger.info("Saved %s", path)
    return path


def build_report(con: duckdb.DuckDBPyConnection, quality: dict[str, int]) -> None:
    plot_monthly_revenue(con)
    plot_rfm_segments(con)
    plot_cohort_retention(con)
    plot_top_countries(con)
    write_summary(con, quality)
