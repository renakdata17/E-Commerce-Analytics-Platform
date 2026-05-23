-- Placeholder staging model — replace sources with your RAW schema / external tables.
SELECT
    'stub-order'::text AS order_id,
    TIMESTAMP '1970-01-01'::timestamp_tz AS occurred_at,
    CAST(0 AS NUMERIC(18, 2)) AS amount_usd;
