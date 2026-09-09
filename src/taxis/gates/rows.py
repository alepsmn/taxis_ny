import duckdb
from duckdb import DuckDBPyRelation
from taxis.contract import RULES

def row_rule(result_trans: duckdb.DuckDBPyRelation,) -> duckdb.DuckDBPyRelation:
    result_trans.create_view("transformed")

    reject_cases = []
    warn_cases = []
    for rule in RULES:
        # {"id": "R-01", "severity": "reject", "reason": "missing_timestamp", "sql": "pickup_at IS NULL OR dropoff_at IS NULL"},
        # {"id": "R-02", "severity": "reject", "reason": "negative_duration", "sql": "dropoff_at < pickup_at"},
        # 1er CASE WHEN pickup_at IS NULL OR dropoff_at IS NULL THEN 'missing_timestamp' END - no hay else, si no cumple NULL
        # 2do CASE WHEN dropoff_at < pickup_at THEN 'negative_duration' END
        case = f"CASE WHEN {rule['sql']} THEN '{rule['reason']}' END"
        if rule["severity"] == 'reject':
            reject_cases.append(case)
        else:
            warn_cases.append(case)

    result_rules = duckdb.sql(
        f"""
        SELECT *,
            -- lista[NULL, 'negative_duration'] se filtra quitando aquellos que no son NULLS
            -- cada fila tiene cols con listas de reasons [...] o warnings [...]
            list_filter([{', '.join(reject_cases)}], x -> x IS NOT NULL) AS reasons,
            list_filter([{', '.join(warn_cases)}], x -> x IS NOT NULL) AS warnings
        FROM transformed
    """
    )

    return result_rules