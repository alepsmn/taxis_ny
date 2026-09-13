class ParquetNoEscrito(Exception):
    def __init__(self, year, month, type_parquet):
        self.year = year
        self.month = month
        self.type_parquet = type_parquet
        mensaje = f"El archivo {type_parquet} - con fecha {year}-{month}, no ha podido ser escrito"
        super().__init__(mensaje)

class FileBlocked(Exception):
    def __init__(self, metadata_cols, type_block, year, month):
        self.metadata_cols = metadata_cols
        self.type_block = type_block
        self.year = year
        self.year = month
        mensaje = f"Status: blocked. Type: {type_block}. Cause: {metadata_cols['block']}. Date: {year}-{month}"
        super().__init__(mensaje)