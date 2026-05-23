WITH staged AS (
    SELECT * FROM {{ ref('stg_events_orders') }}
)

SELECT
    date_trunc('day', occurred_at)::date AS reporting_day,
    COUNT(*) AS staged_order_lines,
    SUM(amount_usd) AS gmv_placeholder_usd
FROM staged
GROUP BY 1;
