import duckdb
from duckdb import DuckDBPyRelation
from taxis.contract import RULES


def validate_row_quality(transformed_cols: DuckDBPyRelation, ) -> DuckDBPyRelation:
    reasons_rejected = []
    reasons_warning = []

    for col in RULES:
        clause = f"CASE WHEN {col['sql']} THEN '{col['reason']}' END" #
        if col['severity'] == 'reject':
            reasons_rejected.append(clause)
        else:
            reasons_warning.append(clause)

    transformed_cols.create_view('transformed')
    validated_rows = duckdb.sql(
        f"""
        SELECT  *,
            list_filter([{', '.join(reasons_rejected)}], x->x IS NOT NULL) AS reasons_rejected,
            list_filter([{', '.join(reasons_warning)}], x->x IS NOT NULL) AS reasons_warning
        FROM transformed
    """
    )

    return validated_rows