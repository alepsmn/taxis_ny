COMO CAMBIAR EXPRESIONES DE DUCKDB A SQL "PURO":
- En rows.py: validated_rows - list_filter([{', '.join(a)}], x->x IS NOT NULL)
- En batch.py: batch_gate - UNNEST

**APP INGEST**

Toma desde consola los argumentos necesarios para recorrer el pipeline. Se informa del resultado unico de cada ingesta
y de sus excepciones en caso de fallo.

***Pipeline.py***
*run_ingest*
Parametros
date: str - la fecha de un archivo (YYYY-MM)
source_path: Path - ruta del archivo
reprocess: bool = False - ignora o no la comprobacion de la existencia del archivo (por su SHA256)
db_path: Path = Path('data/control/manifest.db) - ruta default del manifest (metadatos de un archivo escrito)
Devuelve:
metadatos recopilados (dict: date, file_sha, row_count, metadata_cols, tota_curated, total_quarantine, reasons_rejected_count, reasons_warning_count)

Se obtienen year,month por split de date, el sha y la ruta donde se encuentra el archivo identificado (sha.parquet) *get_file()*
Si reprocess no esta activo, se busca si el archivo esta registrado por su sha *lookup()*.
Comprobacion secuencial (if, if):
- si esta y coincide con el recien calculado, se avisa para que la funcion que encapsula decida
- si no es None: se avisa de que se intenta una revision (existe un sha para esa fecha pero no coinciden)

Mediante la ruta del archivo identificado (raw_file_path), con *get_structural_schema* se obtienen: metadatos respecto a cada
columna del esquema, el conteo total de filas y el propio esquema (dict[str, str]) al comprobar si las columnas pasan los
requerimientos estructuales. Si se da alguna razon de bloqueo, se levanta *FileBlocked* como excepcion, para su captura en niveles superiores.

El esquema obtenido, sirve de partida para hacer las transformaciones necesarias de dominio *col_transformations*, y a partir de este objeto
DuckDBPyRelation, se pasa a *validate_row_quality*  para validar la calidad de la estructura obtenida y dar otro objeto DuckDB.

Las filas validadas y el conteo total, sirven para verificar la puerta batch *batch_gate*, de donde se obtendran finalmente los datos necesarios para
la observabilidad y los datos divididos en curated y quarantine (objetos que cumplen ciertas condiciones). Si de los metadatos de esta puerte se obtienen bloqueos, se llama a *FileBlocked* para su captura posterior.

Los objetos obtenidos, se encolan para ir publicandolos, y obtener sus rutas formadas desde *publish*, las cuales serviran como comprobacion
de que no hubo problemas al escribirlos, y asi, proceder con la escritura de sus metadatos, los cuales se accederan para realizar comprobaciones de existencia
mas rapida sin recurrir a los propios datos

***acquire.py***
*get_file*
Parametros:
source_path: str - ruta del archivo origen
raw_base_path: str - ruta base donde se esrcibria el sha.parquet
year: ano del archivo
month: mes del archivo
Devuelve:
file_sha, raw_file_path

Se calcula el file_sha del archivo actual para renombrar el original e identificarlo por este. Se crea la ruta final (raw_file_path) para materializar
la ruta padre que albergara el archivo por reemplazo (shutil.copy2)

***manifest.py***
*ensure_schema*
Parametros:
db_path: str - ruta del manifest.db

CREATE TABLE IF NOT EXISTS tabla - para ser usada en las funciones que puedan ir antes de crear la tabla de metadatos del fichero
mediante conexiones sqlite3.connect()

*lookup*
Parametros:
db_path: Path
year: int
month: int

Devuelve sha[0]: str contiene el sha del archivo ya publicado en la bbdd

*lookup_published*
Parametros
db_path: Path
year: int
month: int

Devuelve todas las filas y sus valores para el ano y mes dados.
se usa conn.row_factory = sqlite3.Row para devolver los resultados en objeto Row (acceso por claves / indices)

*register*
Parametros:
db_path: Path
year: int
month: int
sha: str
contract_version: int
row_count: int - Filas totales encontradas
curated_count: int
quarantine_count: int
published_at: str - timestamp tomada justo antes de publicar los metadatos pasados como parametros

INSERT OR REPLACE tabla (valores,....) publica en manifest.db los metadatos para el fichero indicado

***structural.py***
*get_structural_schema*
Parametros:
raw_file_path: Path

Devuelve:
metadata_cols: dict[str, str] - contiene avisos de block o warn para su posterior comprobacion
row_count: int - numero de filas en el fichero
file_schema: dict[str, str] - esquema de datos del fichero {columna_minusculas:tipo dato}

Comprueba y registra en metadata_cols, las razones para bloquear o avisar del avance del proceso del esquema
de las columnas. Por simplicidad (desde duckdb):
- Se verifica S-04: si el archivo esta vacio por conteo de sus filas - empty_file
- Se verifica S-01: si una columna obligatoria por el contrato, esta ausente (contract - esquema)
- Se verifica S-02: si los tipos del fichero son compatibles con los indicados para su conversion por el contrato
- Se verifica S-03: si alguna columna extra del esquema no se encuentra en el contrato (esquema - contract)

***transforms.py***
*col_transformations*
Parametros:
raw_file_path: str - 
file_schema: dict[str, str] - esquema en forma de dict columna-datatype
file_sha: str
year: int
month: int

Devuelve:
Objeto DuckDB conteniendo las columnas modificadas

Aplica la serie de transformaciones T-01 a T-04: renombrado, casteo al tipo correcto, si alguna columna no existente
en el contrato es encontrada, se agrega como NULL, linaje (datediff('minute', pickup_at, dropoff_at)), sha, year, month,
contract_version, CURRENT_TIMESTAMP

***rows.py***
*validate_row_quality*
Parametros: 
transformed_cols: DuckDBPyRelation

Devuelve
validated_rows: DuckDBPyRelation

Aplica las 19 reglas a cada fila, dividiendo las tareas entre la severidad (block, warn). Si alguna se incumple, 
se agrega a la lista de su columna correspondiente mediante. list_filter([{', '.join(clauses)}], x -> x IS NOT NULL)

***batch.py***
*batch_gate*
Parametros:
validated_rows: DuckDB
row_count: int

Devuelve:
meta_batch: dict[str, str] - dict con las razones de warn y blocked
curated_rows: DuckDB
quarantine_rows: DuckDB
total_curated: int
total_quarantine: int
reasons_rejected_count: dict[str, str] - cada razon de block o warning y su conteo
reasons_warning_count: dict[str, str]

Se aplican las comprobaciones de lote B-01 y B-02.
Para B-01 es necesario obtener el numero de filas en los datos en quarantine *curated_quarantine*, tal que si el ratio respecto al total de filas es superior al 5%,
el lote deja de ser valido y se notifica para su observacion.
Para B-02 es necesario comparar el numero de filas exactamente duplicadas (group by por todas las columnas a comparar y todas ellas en select) Si es mayor al 0.1%,
se emite un aviso no bloqueante.

*curated_quarantine*
Parametros:
validated_rows: DuckDB

Devuelve:

curated_rows: Duck
quarantine_rows: Duck
total_curated: int
total_quarantine: int

Para curated y quarantine rows, se hacen dos queries donde se evalua la len de la columna que contiene las razones de reject
Si es = 0 (curated), si es > 0 (quarantine) El total de cada una se hace por un count

*reasons_count*
Parametros:

Devuelve:
reasons_rejected_count: dict[str str] - razones reject y su conteo total
reasons_warning_count: dict[str, str] - razones warning y su conteo

Mediante UNNEST de las listas en las columnas reasons_rejected y reasons_warning, se desempaqueta para dar lugar 
a tuplas de (razon, conteo), las cuales se pasan a formato dict con un list_comprehension

***publish.py***
*publish*
Parametros:
rows: Duck - contiene las filas curated/quarantine/... 
type_rows: str - indica el tipo de filas (rows)
year: int
month: int

Devuelve:
final_path: Path - donde se ha escrito las el grupo de filas

Se crea un path temporal donde se escribira el contenido de rows, una vez completado, se hara replace del dir temporal,
con el final formado a partir de type_rows y las fechas (type_rows.parquet) Si el archivo existe, se devuelve su ruta entera,
si no False. Puede ocurrir algun error al escribir, por loque se captura con ParquetNoEscrito, y si el dir temporal se llego a formar,
se borra.

***plan.py***
*missing_processed_files*
Parametros
date_from: str - fecha de inicio de la comprobacion de metadatos
date_to: str - fecha fin
db_path: Path - dir del archivo manifest.db que sera consultado

Devuelve:
Dict con los metadatos extraidos

A partir de las fechas indicadas, se consultara la existencia de metadatos de los ficheros que deberian existir entre este
intervalo de tiempo. Por cada paso en el intervalo (1 mes) se ira contando para tener track. Si el fichero devuelve metadatos vacio,
es porq esta pendiente de ser publicado. Este filtro se da gracias a las propias fechas (WHERE year=? AND month=?)

Para facilitar el manejo de fechas se usa datetime.strptime(date_from, "%Y-%m")
Para cada iteracion se usa actual_date += relativedelta(months=1) pasando asi cada mes mientras actual_date < end_date

Se llama desde cli mediante la funcion decorada plan