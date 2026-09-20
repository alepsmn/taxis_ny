import duckdb

from duckdb import DuckDBPyRelation

def curated_quarantine(validated_rows: DuckDBPyRelation):
    validated_rows.create_view('validated')
    curated_rows = duckdb.sql(
        """
        SELECT *
        FROM validated
        WHERE len(reasons_reject) = 0
    """
    )
    curated_rows.create_view('curated')
    total_curated = duckdb.sql(
        """
        SELECT COUNT(*)
        FROM curated
    """
    ).fetchone()[0]
    quarantine_rows = duckdb.sql(
        """
        SELECT *
        FROM validated
        WHERE len(reasons_reject) > 0
    """
    )
    quarantine_rows.create_views('quarantine')
    total_quarantine = duckdb.sql(
        """
        SELECT COUNT(*)
        FROM quarantine
    """
    ).fetchone()[0]

    return curated_rows, quarantine_rows, total_curated, total_quarantine

def reasons_count(quarantine_rows: DuckDBPyRelation):
    quarantine_rows.create_view('quarantine')
    reject_count = duckdb.sql(
        """
        SELECT reject, COUNT(*)
        FROM quarantine, UNNEST(reasons_reject) AS t(reject)
        WHERE len(reasons_reject) > 0
        GROUP BY reject
    """
    ).fetchall()

    warning_count = duckdb.sql(
            """
            SELECT warning, COUNT(*)
            FROM quarantine, UNNEST(reasons_warning) AS t(warning)
            WHERE len(reasons_reject) > 0
            GROUP BY warning
        """
        ).fetchall()

    each_warning_count = {warning[0]: warning[1] for warning in warning_count}
    each_reject_count = {reject[0]: reject[1] for reject in reject_count}

    return each_reject_count, each_warning_count

def batch_gate(validated_rows: DuckDBPyRelation, row_count: int) -> tuple[dict[str, str], DuckDBPyRelation, DuckDBPyRelation, int, int, dict[str, str], dict[str, str]]:
    # metadata_batch, curated_rows, quarantine_rows, total_curated_rows, total_quarantine_rows, total_reject_count, total_warning_count
    metadata_batch = {
        "reject": [],
        "warn": []
    }
    curated_rows, quarantine_rows, total_curated, total_quarantine = curated_quarantine(validated_rows)
    each_reject_count, each_warning_count = reasons_count(quarantine_rows)
    reject_ratio = quarantine_rows / row_count
    if reject_ratio > 0.05:
        metadata_batch['reject'] = {
            "id": "B-01", "reason": "exceeded_reject_ratio", "reject_ratio": round(reject_ratio, 4)
        }

    duplicated_rows = duckdb.sql(
        """
        SELECT COALESCE(SUM(n) - COUNT(*)) AS duplicated_rows
        FROM (
            SELECT COUNT(*) AS n
            FROM validated
            GROUP BY
            HAVING n > 1
        )
    """
    ).fetchone()[0]

    if duplicated_rows / row_count > 0.001:
        metadata_batch["warn"].append(
            {"id": "B-02", "reason": "exceeded_duplicated_ratio"}
        )

    return metadata_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, each_reject_count, each_warning_count
