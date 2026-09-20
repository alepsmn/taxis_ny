{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key=['source_year', 'source_month']
) }}

SELECT
    source_year,
    source_month,
    pu_location_id,
    do_location_id,
    COUNT(*)         AS trip_count,
    AVG(fare_amount) AS avg_fare
FROM {{ source('curated', 'trips') }}
{% if is_incremental() %}
WHERE (source_year, source_month) NOT IN (
    SELECT DISTINCT source_year, source_month FROM {{ this }}
)
{% endif %}
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) >= 10
