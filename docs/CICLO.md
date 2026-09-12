El pipeline comienza desde cli.py. Se espera la ruta de un .parquet, descargado manualmente, con fecha 2024-01, tal que, mediante un Typer() se obtengan sus tipos para su
procesamiento.

acquire.py
La ruta y de los elementos de la fecha (year, month) se pasan a la funcion acquire, del modulo indicado, junto con la ruta base del destino donde se colocara el archivo.
Para ello, se calcula el hash sha256, y mediante esta serie de elementos se formara la ruta final, cuyo archivo/s seran nombrados mediante su sha256, pasandolo de la ruta
donde se descargo a esta (shutil.copy2). La clave sha256 y la ruta creada, se devolveran para el futuro

structural.py
Este archivo contiene la funcion **comparing_schemas**, para comprobar si:
- S-04 el Fichero tiene alguna fila (COUNT(*)), si esta vacio, se descarta - block. Para comparar los esquemas, se extraen mediante consultas SQL-duckdb (DESCRIBE) y se procesan para compararlas con el conjunto de esquemas que contienen los objetos dataclass para cada columna. 
- Se comprueba la pertenencia de estos objetos en el esquema obtenido, si no existen y se comprueba su obligatoriedad, se bloquean. S-01 - block
- Se comprueba la compatibilidad de los tipos existentes en el esquema (con una estructura que almacena tipos compatibles entre
    ficheros y el motor duckdb/sql) y los esperados por los objetos. Fallo, S-02 - block.
- Se comprueba columnas existentes en el esquema obtenido pero no en los objetos CONTRATO, si no existen - warn - para valorar si anadirlas

Los avisos se guardan en un dict: **meta(data)_cols**, se envian el **numero de filas** y el **esquema del documento** para su posteior procesamiento

Desde cli.py, si existen razones para **block** (S-01, S-02 o S-03) se detiene el programa avisando por consola de los fallos encontrados en esta primera puerta de inspeccion

transform.py
La ruta final creada desde acquire.py, el sha, el ano, mes y schema obtenidos, son usados por la **funcion transform** para realizar las siguientes transformaciones a dicho esquema / columnas
Se recorren las columnas de los objetos del contrato, si estas, pertenecen al contrato, se CASTEA mediante tipos equivalentes (indicada por la estructura correspondiente)
y se les asigna un nombre canonico (cambiando el nombre source). Si la columna no  pertenece al objeto contrato, se indica como NULL::(AS type) AS nombre.
Este recorrido almacena las sentencias select como f str donde se incluyen los elementos individuales para cada columna y posteriormente se unen mendiante un join, tal que se forme una unica sentencia select de elementos str y se pase como f str al select de la query. (T-01 a T-03)
En dicha query se anadiran tambien: duration_min - como datediff de los dos eventos pick_up y drop_off(T-04 ), y los columnas de linaje para cada fila(T-05):
    - source_sha256 como sha, source_year/month, contract-version, y ingested_at como  CURRENT TIMESTAMP 

Al ejecutarse como duckdb.sql, se obtiene un objeto DuckDBPyRelation que contendra estas transformaciones.

rows.py
A partir del dict que contiene todas las reglas que se aplicaran a todas las filas, se filtraran para dividirse posteriormente entre curated/quarantine. Esta estructura
contiene la condicion sql, la razon de para rechazar la fila o avisar y la senal de rejected/warn
La funcion itera sobre la estructura de reglas, y comprueba si la severidad es reject/warn para anadir la sentencia como f-str de CASE  WHEN {relga.sql} THEN {regla.reason} END
Para juntarlas y hacer dos listas de reglas para cada tipo de severidad. Mediante list_filter([(', ').join(a)], x->x IS NOT NULL) AS reject/warn, cada regla
que la fila supere, se anadira como un NULL, si supera todas, se eliminan los nulls y la lista de razones queda vacia. Se terminan anadiendo dos listas de razones r/w
y se obtiene otro objeto DuckDBPyRelation que manipular posteriormente.

batch.py
La funcion batch_gate obtiene el objeto duckdb anterior, para realizar la puerta de validacion para el lote. 
- B-01: Comenzara comprobando el ratio de filas rechazadas(aquellas cuyas razones de block no sean nulas) 
    Obtiene todas las filas rechazadas y las compara con el total de filas del fichero. Si se supera el 5%, el FICHERO se descarta.
- B-02: las filas exactamente duplicadas se obtienen al agrupar a todos las columnas que se quieran verificar que no repiten valor (al agrupar por todos los campos posibles,
para que una fila sea exactamente duplicada, debe compartir los valores de todos esos campos, por lo que solo habria que verificar si el COUNT(*) de los grupos es mayor a 1 HAVING) - subquery
A la query superior le llega este conteo por con los grupos duplicados y cuantas filas duplicadas por grupo, para saber el valor exacto, es necesario restar: TOTAL FILA DUPLICADAS (sum del count) - COUNT() de los grupos actuales (count en la query superior) COALESCE 0 para evitar error por NULLS si no hubiera duplicados
Si estas filas duplicadas superan al 0.1%, se avisa con un warn (no impide el avance)

Los fallos se registran en meta(data)_batch como block/warn

------- Otras cosas que hace la f. - separar
Obtiene los objetos para curated, quarantine, junto con la cantidad de filas de ambos.
Curated contiene todas las  filas donde NO HAY avisos por rejected provenientes de las reglas de rows.py
Quarantine tiene al menos UNA RAZON por rejected

Se obtienen el conteo de cada razon (rejected/warning) a partir de rows_ruled (aplicadas las reglas)
Se hace UNNEST (cols) AS t(col) y se agrupa por col (asi cada razon agrupa a las filas que la contengan) y se
procede a su conteo.
Esto servira para metadata para **OBSERVABILIDAD** 

Si tras la puerta, se cumple alguna condicion block, el proceso se detiene y avisa por consola de los fallos encontrados

publish.py
Los objetos curated, quarantine se guardan en un dict junto a otros datos para ser publicados.
La funcion publish, crea una ruta temporal y escribe el parquet, si el proceso termina, inmediatamente se hace replace de la
ruta temporal con la ruta final (donde realmente viviran los datos procesados) todo esto en un proceso try, que captura
fallo de escritura - ParquetNoEscrito, lacual avisa por mensaje el bloque qno se ha escrito (curated o quarantine y su fecha) 
podria enviarse a una Deadletterqueue - fallo de infra, ha pasado ya toda validacion hasta corte 1. Si el temp se creo, se borra en la excepcion
para evitar mas fallos.

Si el proceso funciona, se comprueba medianta la existencia del archivo,el cual se devuelve (ahora devolvere True si acierta,)

Finalmente se informa de la metadata creada en el proceso:
    Fecha
    sha256
    total filas
    meta_cols
    total curadas
    total cuarentena
    rechazadas
    con aviso

COMO CAMBIAR EXPRESIONES DE DUCKDB A SQL "PURO":
- En rows.py: validated_rows - list_filter([{', '.join(a)}], x->x IS NOT NULL)
- En batch.py: batch_gate - UNNEST
