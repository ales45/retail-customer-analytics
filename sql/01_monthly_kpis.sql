-- Monthly business KPIs: revenue, orders, active customers and average order value.
CREATE OR REPLACE TABLE monthly_kpis AS
SELECT
    CAST(date_trunc('month', invoice_date) AS DATE) AS month,
    ROUND(SUM(revenue), 2)                          AS revenue,
    COUNT(DISTINCT invoice_no)                      AS orders,
    COUNT(DISTINCT customer_id)                     AS customers,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS avg_order_value
FROM sales
GROUP BY 1
ORDER BY 1;
