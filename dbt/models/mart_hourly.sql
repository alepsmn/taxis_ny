{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key=['source_year', 'source_month']
) }}

SELECT
    source_year,
    source_month,
    pu_location_id,
    EXTRACT(HOUR FROM pickup_at)::INTEGER AS hour_of_day,
    COUNT(*)                              AS trip_count,
    AVG(fare_amount)                      AS avg_fare,
    AVG(trip_distance)                    AS avg_distance,
    AVG(duration_min)                     AS avg_duration_min
FROM {{ source('curated', 'trips') }}
{% if is_incremental() %} -- True cuando la tabla ya existe en la bbdd y no se pasa --full-refresh por comando
WHERE (source_year, source_month) NOT IN ( -- "la tupla" que filtra no puede estar en la las tuplas del "resultado"
    SELECT DISTINCT source_year, source_month FROM {{ this }} -- this es la mart_hourly
)
{% endif %}
GROUP BY 1, 2, 3, 4
