import pytest, duckdb
import pandas as pd

from taxis.transforms import transform
from taxis.cli import ingest


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

SCHEMA = {
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

def test_transform(tmp_path):
    ruta_parquet = tmp_path / f"test.parquet"
    df = pd.DataFrame([REGISTRO_VALIDO])
    df.to_parquet(ruta_parquet, index=False)

    result = transform(ruta_parquet, "3232232", 2024, 1, SCHEMA)

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


# @pytest.mark.parametrize("modificacionm regla_id, severidad_esperada", [
#     # --- REGLAS DE RECHAZO (REJECT) ---
#     ({"tpep_pickup_datetime": None}, "R-01", "reject"),
#     ({"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 09:00:00")}, "R-02", "reject"), # dropoff < pickup
#     (
#         {"tpep_dropoff_datetime": pd.Timestamp("2026-09-11 12:00:00")}, 
#         "R-03", "reject"
#     ), # > 24 horas (1440 min)
#     (
#         {"tpep_pickup_datetime": pd.Timestamp("2026-10-01 00:00:00")}, 
#         "R-04", "reject"
#     ), # Fuera de partición (asumiendo fichero de Septiembre 2026)
#     ({"trip_distance": -1.0}, "R-05", "reject"),
#     ({"trip_distance": 250.0}, "R-06", "reject"),
#     ({"fare_amount": -5.00}, "R-07", "reject"),
#     ({"fare_amount": None}, "R-08", "reject"),
#     ({"PULocationID": 999}, "R-09", "reject"), # Zona inválida

#     # --- REGLAS DE ADVERTENCIA (WARN) ---
#     (
#         {"tpep_dropoff_datetime": pd.Timestamp("2026-09-10 14:00:00")}, 
#         "R-10", "warn"
#     ), # 4 horas duracion (entre 180 y 1440 min)
#     ({"trip_distance": 0.0}, "R-11", "warn"),
#     ({"total_amount": 0.0}, "R-12", "warn"),
#     ({"PULocationID": 264}, "R-13", "warn"), # Zona desconocida/unresolved
#     ({"passenger_count": 0}, "R-14", "warn"),
#     ({"passenger_count": 7}, "R-15", "warn"),
#     ({"RatecodeID": 9}, "R-16", "warn"),
#     ({"payment_type": 9}, "R-17", "warn"),
#     ({"VendorID": 9}, "R-18", "warn"),
#     ({"store_and_fwd_flag": "X"}, "R-19", "warn"),
# ])
# def test_regla_calidad_datos(tmp_path, modificaciones, regla_id, severidad_esperada):
#     registro_test = REGISTRO_VALIDO.copy()
#     registro_test.update(modificaciones)

#     ruta_parquet = tmp_path / f"test_{regla_id}.parquet"