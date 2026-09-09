from dataclasses import dataclass

@dataclass
class Column:
    canonical: str
    source: str
    type: str
    required: bool

CONTRACT_V1 = [
    Column(canonical='vendor_id', source='VendorID', type='INTEGER', required=True),
    Column(canonical='pickup_at', source='tpep_pickup_datetime', type='TIMESTAMP', required=True),
    Column(canonical='dropoff_at', source='tpep_dropoff_datetime', type='TIMESTAMP', required=True),
    Column(canonical='passenger_count', source='passenger_count', type='INTEGER', required=False),
    Column(canonical='trip_distance', source='trip_distance', type='DOUBLE', required=True),
    Column(canonical='ratecode_id', source='RatecodeID', type='INTEGER', required=False),
    Column(canonical='store_and_fwd_flag', source='store_and_fwd_flag', type='VARCHAR', required=False),
    Column(canonical='pu_location_id', source='PULocationID', type='INTEGER', required=True),
    Column(canonical='do_location_id', source='DOLocationID', type='INTEGER', required=True),
    Column(canonical='payment_type', source='payment_type', type='INTEGER', required=True),
    Column(canonical='fare_amount', source='fare_amount', type='DECIMAL(10,2)', required=True),
    Column(canonical='extra', source='extra', type='DECIMAL(10,2)', required=True),
    Column(canonical='mta_tax', source='mta_tax', type='DECIMAL(10,2)', required=True),
    Column(canonical='tip_amount', source='tip_amount', type='DECIMAL(10,2)', required=True),
    Column(canonical='tolls_amount', source='tolls_amount', type='DECIMAL(10,2)', required=True),
    Column(canonical='improvement_surcharge', source='improvement_surcharge', type='DECIMAL(10,2)', required=True),
    Column(canonical='total_amount', source='total_amount', type='DECIMAL(10,2)', required=True),
    Column(canonical='congestion_surcharge', source='congestion_surcharge', type='DECIMAL(10,2)', required=False),
    Column(canonical='airport_fee', source='airport_fee', type='DECIMAL(10,2)', required=False),
    Column(canonical='cbd_congestion_fee', source='cbd_congestion_fee', type='DECIMAL(10,2)', required=False),
]

COMPATIBLE_TYPES = {
    ("BIGINT", "INTEGER"),
    ("INTEGER", "INTEGER"),
    ("DOUBLE", "DOUBLE"),
    ("DOUBLE", "DECIMAL(10,2)"),
    ("TIMESTAMP", "TIMESTAMP"),
    ("VARCHAR", "VARCHAR")
}

RULES = [
    {"id": "R-01", "severity": "reject", "reason": "missing_timestamp", "sql": "pickup_at IS NULL OR dropoff_at IS NULL"},
    {"id": "R-02", "severity": "reject", "reason": "negative_duration", "sql": "dropoff_at < pickup_at"},
    {"id": "R-03", "severity": "reject", "reason": "duration_over_24h", "sql": "duration_min > 1440"},
    # verifica que el mes de pickup, pertenece al mes del propio fichero: ej pickup_at = 2026-10-12 se trunca a 2026-10-1
    # el fichero recibe col 2026, y 9, hace fecha 2026-09-1; <> verifica si son distintos, lo son, se selecciona la col para avisar
    {"id": "R-04", "severity": "reject", "reason": "pickup_outside_partition", "sql": "date_trunc('month', pickup_at) <> make_date(source_year, source_month, 1)"},
    {"id": "R-05", "severity": "reject", "reason": "negative_distance", "sql": "trip_distance < 0"},
    {"id": "R-06", "severity": "reject", "reason": "implausible_distance", "sql": "trip_distance > 200"},
    {"id": "R-07", "severity": "reject", "reason": "negative_amount", "sql": "fare_amount < 0 OR total_amount < 0"},
    {"id": "R-08", "severity": "reject", "reason": "missing_amount", "sql": "fare_amount IS NULL OR total_amount IS NULL"},
    {"id": "R-09", "severity": "reject", "reason": "unknown_zone", 
    "sql": "pu_location_id NOT BETWEEN 1 AND 265 OR do_location_id NOT BETWEEN 1 AND 265 OR pu_location_id IS NULL OR do_location_id IS NULL"},

    {"id": "R-10", "severity": "warn", "reason": "long_duration", "sql": "duration_min > 180 AND duration_min <= 1440"},
    {"id": "R-11", "severity": "warn", "reason": "zero_distance", "sql": "trip_distance = 0"},
    {"id": "R-12", "severity": "warn", "reason": "zero_amount", "sql": "total_amount = 0"},
    {"id": "R-13", "severity": "warn", "reason": "unresolved_zone", "sql": "pu_location_id IN (264, 265) OR do_location_id IN (264, 265)"},
    {"id": "R-14", "severity": "warn", "reason": "passenger_count_unknown", "sql": "passenger_count IS NULL OR passenger_count = 0"},
    {"id": "R-15", "severity": "warn", "reason": "passenger_count_high", "sql": "passenger_count > 6"},
    {"id": "R-16", "severity": "warn", "reason": "undocumented_ratecode", "sql": "ratecode_id NOT IN (1,2,3,4,5,6) AND ratecode_id IS NOT NULL"},
    {"id": "R-17", "severity": "warn", "reason": "undocumented_payment_type", "sql": "payment_type NOT IN (1,2,3,4,5,6)"},
    {"id": "R-18", "severity": "warn", "reason": "undocumented_vendor", "sql": "vendor_id NOT IN (1,2,6,7)"},
    {"id": "R-19", "severity": "warn", "reason": "invalid_sf_flag", "sql": "store_and_fwd_flag NOT IN ('Y','N') AND store_and_fwd_flag IS NOT NULL"},
]