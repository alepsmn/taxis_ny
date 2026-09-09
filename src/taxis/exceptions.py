class ParquetNoEscrito(Exception):
    def __init__(self, year, month, type_parquet):
        self.year = year
        self.month = month
        self.type_parquet = type_parquet
        mensaje = f"""El archivo {type_parquet} - con fecha {year}-{month}, no ha podido ser escrito"""
        super().__init__(mensaje)