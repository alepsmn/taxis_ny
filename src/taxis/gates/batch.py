import duckdb
from duckdb import DuckDBPyRelation

def curated_quarantine(validated_rows: DuckDBPyRelation) -> tuple[DuckDBPyRelation, DuckDBPyRelation, int, int]:
    validated_rows.create_view("validated_rows")

    curated_rows = duckdb.sql(
        f"""
        SELECT *
        FROM validated_rows
        WHERE len(reasons_rejected) = 0
    """
    )
    curated_rows.create_view("curated_rows")
    total_curated = int(duckdb.sql(
        """
        SELECT COUNT(*)
        FROM curated_rows
    """
    ).fetchone()[0])

    quarantine_rows = duckdb.sql(
        f"""
        SELECT *
        FROM validated_rows
        WHERE len(reasons_rejected) > 0
    """
    )
    quarantine_rows.create_view("quarantine_rows")
    total_quarantine = duckdb.sql(
        """
        SELECT COUNT(*)
        FROM quarantine_rows
    """
    ).fetchone()[0]

    return curated_rows, quarantine_rows, total_curated, total_quarantine

def reasons_count(quarantine_rows: DuckDBPyRelation) -> tuple[dict[str, str], dict[str, str]]:
    reasons_rejected = duckdb.sql(
        """
        SELECT reason, COUNT(*)
        FROM quarantine_rows, UNNEST(reasons_rejected) AS t(reason)
        WHERE len(reasons_rejected) > 0
        GROUP BY reason
    """
    ).fetchall()

    reasons_warning = duckdb.sql(
        """
        SELECT warning, COUNT(*)
        FROM quarantine_rows, UNNEST(reasons_warning) AS t(warning)
        WHERE len(reasons_warning) > 0
        GROUP BY warning
    """
    ).fetchall()

    reasons_rejected_count = {reasons[0]: reasons[1] for reasons in reasons_rejected}
    reasons_warning_count = {reasons[0]: reasons[1] for reasons in reasons_warning}

    return reasons_rejected_count, reasons_warning_count


def batch_gate(validated_rows: DuckDBPyRelation, row_count: int) -> tuple[dict[str, str], DuckDBPyRelation, DuckDBPyRelation, int, int, dict[str, str], dict[str, str]]:
    meta_batch = {
            "block": [],
            "warn": []
        }
    curated_rows, quarantine_rows, total_curated, total_quarantine = curated_quarantine(validated_rows)
    reasons_rejected_count, reasons_warning_count = reasons_count(quarantine_rows)

    reject_ratio = total_quarantine / row_count
    if reject_ratio > 0.05:
        meta_batch["block"].append(
            {"id": "B-01", "reason": "reject_ratio_exceeded", "reject_ratio": round(reject_ratio, 4), "threshold": 0.05}
        )

    duplicated_rows = duckdb.sql(
        f"""
        SELECT COALESCE(SUM(n) - COUNT(*), 0) AS duplicated_rows
        FROM (
            SELECT COUNT(*) AS n
            FROM validated_rows
            GROUP BY vendor_id, pickup_at, dropoff_at, passenger_count, trip_distance,
                ratecode_id, store_and_fwd_flag, pu_location_id, do_location_id,
                payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount,
                improvement_surcharge, total_amount, congestion_surcharge, airport_fee,
                cbd_congestion_fee, duration_min
            HAVING n > 1
        )
    """
    ).fetchone()[0]

    if duplicated_rows / row_count > 0.001:
        meta_batch["warn"].append(
            {"id": "B-02", "reason": "exact_duplicates", "duplicated_rows": int(duplicated_rows), "threshold": 0.001}
        )

    return meta_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, reasons_rejected_count, reasons_warning_count
    #     return meta_batch, curated, quarantine, total_curated, total_quarantine, rejected_count, warning_count