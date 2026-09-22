import pytest, duckdb
import pandas as pd

from taxis.cli import ingest
from taxis.gates.structural import get_structural_schema
from taxis.transforms import col_transformations
from taxis.gates.rows import validate_row_quality
from taxis.gates.batch import batch_gate
from taxis.manifest import lookup_sha, register



REGISTRO_VALIDO = {
    "VendorID": 1,
    "tpep_pickup_datetime": pd.Timestamp("2026-09-10 10:00:00"),
    "tpep_dropoff_datetime": pd.Timestamp("2026-09-10 10:15:00"), # 15 min (OK)
    "passenger_count": 2,
    "trip_distance": 5.2, # OK
    "RatecodeID": 1,
    "store_and_fwd_flag": "Y",
    "PULocationID": 100, # OK
    "DOLocationID": 200, # OK
    "payment_type": 1,
    "fare_amount": 15.00,
    "extra": 1.00,
    "mta_tax": 0.50,
    "tip_amount": 3.00,
    "tolls_amount": 0.00,
    "improvement_surcharge": 0.30,
    "total_amount": 19.80,
    "congestion_surcharge": 2.50,
    "airport_fee": 0.00,
    "cbd_congestion_fee": 0.00
}

SCHEMA_COL_DTYPE = {
    'vendorid': 'INTEGER',
    'tpep_pickup_datetime': 'TIMESTAMP',
    'tpep_dropoff_datetime': 'TIMESTAMP',
    'passenger_count': 'INTEGER',
    'trip_distance': 'DOUBLE',
    'ratecodeid': 'INTEGER',
    'store_and_fwd_flag': 'VARCHAR',
    'pulocationid': 'INTEGER',
    'dolocationid': 'INTEGER',
    'payment_type': 'INTEGER',
    'fare_amount': 'DECIMAL(10,2)',
    'extra': 'DECIMAL(10,2)',
    'mta_tax': 'DECIMAL(10,2)',
    'tip_amount': 'DECIMAL(10,2)',
    'tolls_amount': 'DECIMAL(10,2)',
    'improvement_surcharge': 'DECIMAL(10,2)',
    'total_amount': 'DECIMAL(10,2)',
    'congestion_surcharge': 'DECIMAL(10,2)',
    'airport_fee': 'DECIMAL(10,2)',
    'cbd_congestion_fee': 'DECIMAL(10,2)',
}

def test_valid_register_no_rejects(tmp_path):
    ruta = tmp_path / f"test_valido.parquet"
    pd.DataFrame([REGISTRO_VALIDO]).to_parquet(ruta)

    transformed = col_transformations(ruta, SCHEMA_COL_DTYPE, "abc", 2026, 9)
    validated = validate_row_quality(transformed)

    row = validated.fetchone()

    # ambas listas: reasons_rejected/warning vacias
    assert row[-2] == []
    assert row[-1] == []

def test_transform(tmp_path):
    ruta_parquet = tmp_path / f"test.parquet"
    pd.DataFrame([REGISTRO_VALIDO]).to_parquet(ruta_parquet, index=False)

    result = col_transformations(ruta_parquet, SCHEMA_COL_DTYPE, "3232232", 2024, 1)

    assert "vendor_id" in result.columns

    result.create_view("test_transform")
    row = duckdb.sql(
        """
        SELECT duration_min
        FROM test_transform
        LIMIT 1
    """
    ).fetchone()

    assert row[0] == 15


@pytest.mark.parametrize("modificacion, regla, severidad_esperada", [
    # --- REGLAS DE RECHAZO (REJECT) ---
    ({"tpep_pickup_datetime": None}, "missing_timestamp", "reject"),
    ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 09:00:00")}, "negative_duration", "reject"), # dropoff < pickup
    (
        {"tpep_dropoff_datetime": pd.Timestamp("2026-09-11 12:00:00")}, 
        "duration_over_24h", "reject"
    ), # > 24 horas (1440 min)
    (
        {"tpep_pickup_datetime": pd.Timestamp("2026-10-01 00:00:00")}, 
        "pickup_outside_partition", "reject"
    ), # Fuera de partición (asumiendo fichero de Septiembre 2026)
    ({"trip_distance": -1.0}, "negative_distance", "reject"),
    ({"trip_distance": 250.0}, "implausible_distance", "reject"),
    ({"fare_amount": -5.00}, "negative_amount", "reject"),
    ({"fare_amount": None}, "missing_amount", "reject"),
    ({"PULocationID": 999}, "unknown_zone", "reject"), # Zona inválida

    # --- REGLAS DE ADVERTENCIA (WARN) ---
    (
        {"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 14:00:00")}, 
        "long_duration", "warn"
    ), # 4 horas duracion (entre 180 y 1440 min)
    ({"trip_distance": 0.0}, "zero_distance", "warn"),
    ({"total_amount": 0.0}, "zero_amount", "warn"),
    ({"PULocationID": 264}, "unresolved_zone", "warn"), # Zona desconocida/unresolved
    ({"passenger_count": 0}, "passenger_count_unknown", "warn"),
    ({"passenger_count": 7}, "passenger_count_high", "warn"),
    ({"RatecodeID": 9}, "undocumented_ratecode", "warn"),
    ({"payment_type": 9}, "undocumented_payment_type", "warn"),
    ({"VendorID": 9}, "undocumented_vendor", "warn"),
    ({"store_and_fwd_flag": "X"}, "invalid_sf_flag", "warn"),

    # ---  REGLAS DE VALORES LIMITES ---
    ({"trip_distance": 200.0}, "implausible_distance", "ninguna"),
    ({"trip_distance": 200.01}, "implausible_distance", "reject"),
    # pasa un dia y un minuto
    ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-11 10:01:00")}, "duration_over_24h", "reject"),
    # pasa justo un dia
    ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-11 10:00:00")}, "duration_over_24h", "ninguna"),
    # pasa 3h  - umbral viaje anormal
    ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 13:00:00")}, "long_duration", "ninguna"),
 # pasa 3h 1min - viaje anormal
    ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 13:01:00")}, "long_duration", "warn"),
])
def test_regla_calidad_datos(tmp_path, modificacion, regla, severidad_esperada):
    registro_test = REGISTRO_VALIDO.copy()
    registro_test.update(modificacion)

    # creacion del parquet - dict, no Df
    ruta_parquet = tmp_path / f"test_{regla}.parquet"
    pd.DataFrame([registro_test]).to_parquet(ruta_parquet)

    transformed = col_transformations(ruta_parquet, SCHEMA_COL_DTYPE, "abc123", 2026, 9)
    validated = validate_row_quality(transformed)
    row = validated.fetchone()

    reasons_rejected = row[-2]
    reasons_warning = row[-1]

    if severidad_esperada == "reject":
        assert regla in reasons_rejected
    elif severidad_esperada == "ninguna":
        assert regla not in reasons_rejected
        assert regla not in reasons_warning
    else:
        assert regla in reasons_warning

def test_required_col(tmp_path):
    registro_test = REGISTRO_VALIDO.copy()
    del registro_test["VendorID"]

    ruta_parquet = tmp_path / f"test_required.parquet"
    pd.DataFrame([registro_test]).to_parquet(ruta_parquet)

    metadata_cols, row_count, file_schema = get_structural_schema(ruta_parquet)

    assert metadata_cols["block"] == [{"id": "S-01", "reason": "missing_required_column", "column": "VendorID"}]

def test_compatible_types(tmp_path):
    registro_test = REGISTRO_VALIDO.copy()
    registro_test["fare_amount"] = "quince"

    ruta_parquet = tmp_path / f"test_type.parquet"
    pd.DataFrame([registro_test]).to_parquet(ruta_parquet)

    metadata_cols, row_count, file_schema = get_structural_schema(ruta_parquet)

    assert metadata_cols["block"] == [{"id": "S-02", "reason": "incompatible_type", "column": "fare_amount", "expected": "DECIMAL(10,2)", "got": "VARCHAR"}]

def test_unknown_col(tmp_path):
    registro_test = REGISTRO_VALIDO.copy()
    registro_test["extra_col"] = 42

    ruta_parquet = tmp_path / f"extra_col.parquet"
    pd.DataFrame([registro_test]).to_parquet(ruta_parquet)

    metadata_cols, row_count, file_schema = get_structural_schema(ruta_parquet)

    assert metadata_cols["warn"] == [{"id": "S-03", "reason": "unknown_column", "column": "extra_col"}]

def test_reject_ratio_reject(tmp_path):
    filas = [REGISTRO_VALIDO.copy() for _ in range(100)]
    for i in range(6):
        filas[i]["fare_amount"] = - 5.00

    ruta_parquet = tmp_path / f"reject_ratio.parquet"
    pd.DataFrame(filas).to_parquet(ruta_parquet)

    transformed = col_transformations(ruta_parquet, SCHEMA_COL_DTYPE, "abc123", 2026, 9)
    validated = validate_row_quality(transformed)
    meta_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, \
    reasons_rejected_count, reasons_warning_count = batch_gate(validated, 100)

    assert meta_batch["block"] == [{"id": "B-01", "reason": "reject_ratio_exceeded", "reject_ratio": 0.0600, "threshold": 0.05}]


def test_reject_ratio_pass(tmp_path):
    filas = [REGISTRO_VALIDO.copy() for _ in range(100)]
    for i in range(5):
        filas[i]["fare_amount"] = - 5.00

    ruta_parquet = tmp_path / f"reject_ratio.parquet"
    pd.DataFrame(filas).to_parquet(ruta_parquet)

    transformed = col_transformations(ruta_parquet, SCHEMA_COL_DTYPE, "abc123", 2026, 9)
    validated = validate_row_quality(transformed)
    meta_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, \
    reasons_rejected_count, reasons_warning_count = batch_gate(validated, 100)

    assert meta_batch["block"] == []

def test_manifest_idempotency(tmp_path):
    manifest_path = tmp_path / f"manifest.db"

    register(manifest_path, 2024, 1, "abc123", 1, 4, 5, 6, "2024")
    sha = lookup_sha(manifest_path, 2024, 1)
    sha2 = lookup_sha(manifest_path, 2024, 2)

    assert sha == "abc123"
    assert sha2 == None