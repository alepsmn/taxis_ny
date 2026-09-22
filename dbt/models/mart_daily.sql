{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key=['trip_date']
) }}

SELECT
    CAST(pickup_at AS DATE) AS trip_date,
    COUNT(*)                AS trip_count,
    SUM(total_amount)       AS total_revenue,
    AVG(trip_distance)      AS avg_distance,
    AVG(duration_min)       AS avg_duration_min
FROM {{ source('curated', 'trips') }}
{% if is_incremental() %} -- True cuando la tabla ya existe en la bbdd y no se pasa --full-refresh por comando
WHERE (source_year, source_month) NOT IN (
    SELECT DISTINCT
        -- al ser agregado por dia, en la fecha ya tiene la info
        EXTRACT(YEAR FROM trip_date)::INTEGER,
        EXTRACT(MONTH FROM trip_date)::INTEGER
    FROM {{ this }}
)
{% endif %}
GROUP BY 1
ORDER BY 1
