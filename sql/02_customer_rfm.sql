-- RFM segmentation: Recency, Frequency and Monetary value per customer,
-- scored 1-5 with quintiles and mapped to actionable segments.
CREATE OR REPLACE TABLE customer_rfm AS
WITH snapshot AS (
    SELECT CAST(MAX(invoice_date) AS DATE) + INTERVAL 1 DAY AS snapshot_date FROM sales
),
metrics AS (
    SELECT
        customer_id,
        date_diff('day', CAST(MAX(invoice_date) AS DATE), CAST(s.snapshot_date AS DATE)) AS recency_days,
        COUNT(DISTINCT invoice_no)  AS frequency,
        ROUND(SUM(revenue), 2)      AS monetary
    FROM sales, snapshot AS s
    GROUP BY customer_id, s.snapshot_date
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary)          AS m_score
    FROM metrics
)
SELECT
    *,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 4 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 3 THEN 'Potential Loyalist'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
        ELSE 'Others'
    END AS segment
FROM scored;
