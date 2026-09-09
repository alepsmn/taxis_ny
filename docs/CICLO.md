El pipeline se basa en los taxis de NY (yellow), su finalidad es la infraestructura, el analisis es secundario.

Se parten de argumentos por consola, capturados por typer, del cual se crea el objeto Typer, y mediante typehints,
convierte los argumentos pasados en el tipo de dato indicados por estos.

taxis.acquire (def acquire)
A partir de date, se extraen el ano y mes correspondientes al archivo, y desde el path indicado (localizacion del archivo
descargado) se llevan para crear un nuevo archivo identificable como unico, mediante una clave SHA256 por idempotencia,
al basarse en el numero de bytes del archivo (como un dni mientras no cambie su contenido/bytes)

taxis.gates.estructural (def comparing_schemas)
Mediante este SHA y la localizacion del fichero creado, se compara incialmente los esquemas para obtener las filas leidas,
y las medidas de puerta estructural inicial (S-01 a S-04) crear un dict informativo que se pasa a json para ser imprimido.

taxis.transforms (def transform)
Si la funcion anterior no levanta SystemExist(2) por los resultados, se obtiene el esquema encontrado para el fichero,
del cual se comparara con CONTRACT_V1, dataclass que contiene el nombre inicial de cada columna del fichero, su proximo nombre
normalizado, el tipo de dato esperado, y si es obligatoria o no.
Para ello se comparan los valores presentes en esta lista de objetos dataclass, con el esquema obtenido,  para resolver las
transformaciones T-01 a T-05 (anteriores y: duration_min, linaje). Se devuelve el objeto duckdb.DuckDBPyRelation para continuar
con la referencia en memoria y poder crear vistas desde la que realizar las comprobaciones finales

taxis.gates.rows (def row_rule)
Esta funcion toma el objeto anterior, para crear una vista y aplicar las reglas de negocio/semantica, a cada columna de cada fila presente.
Mediante la acumulacion de sentencias CASE WHEN sql THEN reason END para cada caso de severidad (rejected o warning), cada fila contara con dos cols nuevas
reasons (razones por las que se considra invalida) y warnings(avisos a tener en cuenta por fallos en las cols de la fila) - cada una esta una lista de str
con la informacion
