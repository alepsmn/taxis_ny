import duckdb
from duckdb import DuckDBPyRelation

def batch_door(rows_ruled: DuckDBPyRelation, row_count: int) -> tuple[dict[str, str], DuckDBPyRelation, DuckDBPyRelation, int, int, dict[str, str]]:

    rows_ruled.create_view("rows_ruled")

    rejected_reasons = duckdb.sql(
        """
        SELECT reason, COUNT(*)
        FROM rows_ruled, UNNEST(reasons) as t(reason) -- ['negative_amount', 'negative_duration'] da lugar a dos filas identicas, una con cada razon
        WHERE len(reasons) > 0
        GROUP BY reason --duckdb permite usar alias antes
    """
    ).fetchall()
    rejected_count = {reason[0]: reason[1] for reason in rejected_reasons}

    warning_reasons = duckdb.sql(
        """
        SELECT warning, COUNT(*)
        FROM rows_ruled, UNNEST(warnings) AS t(warning) -- t para la tabla virtual que genera el UNNEST
        WHERE len(warnings) > 0
        GROUP BY warning
    """
    ).fetchall()
    warning_count = {warning[0]: warning[1] for warning in warning_reasons}

    curated = duckdb.sql(
        f"""
        SELECT *
        FROM rows_ruled
        WHERE len(reasons) = 0
    """
    )
    curated.create_view("curated")
    total_curated = int(duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM curated
    """
    ).fetchone()[0])

    quarantine = duckdb.sql(
        f"""
        SELECT *
        FROM rows_ruled
        WHERE len(reasons) > 0
    """
    )
    quarantine.create_view("quarantine")
    total_quarantine = int(duckdb.execute(
        """
        SELECT COUNT(*)
        FROM quarantine
    """
    ).fetchone()[0])

    meta_batch = {
        "block": [],
        "warn": []
    }

    reject_ratio = total_quarantine / row_count
    if reject_ratio > 0.05:
        meta_batch["block"].append(
            {
                "id": "B-01", "severity": "block",
                "reason_code": "reject_ratio_exceeded"
            }
        )

    duplicated_rows = duckdb.execute(
        """
        -- coalesce: asigna un valor por defecto si el campo vale NULL
        SELECT COALESCE(SUM(n) - COUNT(*), 0) AS duplicated_rows -- SUM(n): filas en todos los grupos con duplicados, COUNT(*): cuenta una fila por grupo
        FROM (
            SELECT COUNT(*) AS n -- cuenta cuantas filas iguales hay por grupo
            FROM rows_ruled
            -- si agrupo por todos los grupos, estoy agrupando aquellas filas que compartan valores en todo -> 100 identicas: duplicado exacto
            -- asi no es necesario un ID unico
            GROUP BY vendor_id, pickup_at, dropoff_at, passenger_count, trip_distance,
                ratecode_id, store_and_fwd_flag, pu_location_id, do_location_id,
                payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount,
                improvement_surcharge, total_amount, congestion_surcharge, airport_fee,
                cbd_congestion_fee, duration_min
            HAVING n > 1 -- deja los grupos con mas de una fila igual por grupo
        )
    """
    ).fetchone()[0]

    if duplicated_rows > row_count * 0.001:
        meta_batch["warn"].append(
            {
                "id": "B-02", "severity": "warn",
                "reason_code": "exact_duplicates"
            }
        )

    return meta_batch, curated, quarantine, total_curated, total_quarantine, rejected_count, warning_count