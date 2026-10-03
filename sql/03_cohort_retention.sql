-- Monthly cohort retention: share of each first-purchase cohort that buys again N months later.
CREATE OR REPLACE TABLE cohort_retention AS
WITH customer_months AS (
    SELECT DISTINCT
        customer_id,
        CAST(date_trunc('month', invoice_date) AS DATE) AS order_month
    FROM sales
),
cohorts AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM customer_months
    GROUP BY customer_id
),
activity AS (
    SELECT
        c.cohort_month,
        date_diff('month', c.cohort_month, m.order_month) AS months_since_first,
        COUNT(DISTINCT m.customer_id) AS active_customers
    FROM customer_months AS m
    JOIN cohorts AS c USING (customer_id)
    GROUP BY 1, 2
)
SELECT
    cohort_month,
    months_since_first,
    active_customers,
    FIRST_VALUE(active_customers) OVER (
        PARTITION BY cohort_month ORDER BY months_since_first
    ) AS cohort_size,
    ROUND(active_customers / cohort_size, 4) AS retention_rate
FROM activity
ORDER BY cohort_month, months_since_first;
