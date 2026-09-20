import duckdb

from duckdb import DuckDBPyRelation

from taxis.contract import RULES

def validate_row_quality(transformed_cols: DuckDBPyRelation, ) -> DuckDBPyRelation:
    rejects = []
    warns = []
    for rule in RULES:
        clause = f"CASE WHEN {rule["sql"]} THEN {rule["reason"]} END"
        if rule["severit"] == 'reject':
            rejects.append(clause)
        else:
            warns.append(clause)
    transformed_cols.create_view('transformed')
    validated_rows = duckdb.sql(
        f"""
        SELECT *,
            list_filter([{', '.join(rejects)}], x -> x IS NOT NULL) AS reasons_reject,
            list_filter([{', '.join(warns)}], x -> x IS NOT NULL) AS reasons_warning,
        FROM transformed
    """
    )
    return validated_rows