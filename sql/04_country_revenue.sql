-- Revenue concentration by country.
CREATE OR REPLACE TABLE country_revenue AS
SELECT
    country,
    ROUND(SUM(revenue), 2)                      AS revenue,
    COUNT(DISTINCT customer_id)                 AS customers,
    SUM(revenue) / SUM(SUM(revenue)) OVER ()    AS revenue_share
FROM sales
GROUP BY country
ORDER BY revenue DESC;
