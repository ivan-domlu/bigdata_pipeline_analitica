# Pipeline de Detección de Fraude

Este proyecto implementa un **pipeline de datos de Big Data** para la detección de transacciones financieras fraudulentas utilizando procesamiento distribuido con **Apache Spark**, orquestación con **Apache Airflow**, y servicios en **Google Cloud Platform (GCP)**.

El objetivo es construir una **arquitectura escalable de ingeniería de datos** que permita:

* Ingestar datos de transacciones
* Procesarlos con **Spark**
* Organizar los datos en capas **Bronze, Silver y Gold**
* Prepararlos para análisis y modelos de machine learning

---

# Arquitectura del Proyecto (Nivel General)

El pipeline sigue el patrón de **Medallion Architecture**, ampliamente utilizado en proyectos de ingeniería de datos.

Dataset (Kaggle)
↓
Google Cloud Storage (Data Lake)
↓
Procesamiento con Spark (Dataproc)
↓
Capas Bronze → Silver → Gold
↓
BigQuery (Capa Analítica)
↓
Airflow (Orquestación del Pipeline)

---

# Dataset

El dataset utilizado proviene de Kaggle:

Fraud Detection Dataset
https://www.kaggle.com/datasets/kartik2112/fraud-detection

Este dataset contiene **transacciones simuladas de tarjetas de crédito**, incluyendo una variable que indica si la transacción fue fraudulenta.

### Principales Variables

* `trans_date_trans_time` – fecha y hora de la transacción
* `cc_num` – número de tarjeta de crédito
* `merchant` – nombre del comercio
* `category` – categoría del comercio
* `amt` – monto de la transacción
* `city`, `state`, `zip` – información de ubicación
* `lat`, `long` – coordenadas del cliente
* `merch_lat`, `merch_long` – coordenadas del comercio
* `unix_time` – timestamp en formato Unix
* `is_fraud` – indicador de fraude (variable objetivo)

---

# Estructura del Proyecto

```id="4s06iz"
bigdata_pipeline_analitica
│
├── infrastructure
│     setup_gcs.sh
│
├── spark_jobs
│
├── airflow
│
├── config
│
├── requirements.txt
│
└── README.md
```

---

# Prerrequisitos

Antes de ejecutar el script de infraestructura, asegúrate de contar con lo siguiente:

* Una **cuenta de Google Cloud Platform**
* Un **proyecto creado en GCP**
* **Cloud Shell habilitado**
* La herramienta **gcloud CLI** disponible (ya incluida en Cloud Shell)

También necesitarás:

* Un **nombre único para tu bucket de Cloud Storage**

---

# Paso 1 — Crear el Data Lake (Cloud Storage)

Este proyecto utiliza **Google Cloud Storage como Data Lake**, siguiendo una arquitectura de capas tipo **Medallion**.

El script incluido en este repositorio se encarga de:

* Configurar el proyecto de GCP
* Crear el bucket de almacenamiento
* Inicializar las capas Bronze, Silver y Gold
* Crear directorios para datasets y scripts del pipeline

---

## Ejecutar el Script de Configuración

Primero clona el repositorio:

```bash id="lwh8uc"
git clone https://github.com/ivan-domlu/bigdata_pipeline_analitica.git
cd bigdata_pipeline_analitica
```

Dar permisos de ejecución al script:

```bash id="v6znbp"
chmod +x infrastructure/setup_gcs.sh
```

Ejecutar el script:

```bash id="gcofkk"
./infrastructure/setup_gcs.sh <PROJECT_ID> <BUCKET_NAME> [REGION]
```

Ejemplo:

```bash id="uwl7q6"
./infrastructure/setup_gcs.sh fraud-detection-pipeline-2026 fraud-detection-data-2026 us-central1
```

---

# Estructura del Data Lake

Después de ejecutar el script, se creará la siguiente estructura en **Google Cloud Storage**:

```id="2i0lfl"
gs://BUCKET_NAME/

bronze/
silver/
gold/
datasets/
scripts/
temp/
```

### Descripción de las Capas

**Bronze Layer**
Contiene los datos crudos recién ingeridos, con mínimo procesamiento.

**Silver Layer**
Contiene datos limpios, validados y preparados para transformaciones.

**Gold Layer**
Contiene datasets agregados y optimizados para análisis y consumo analítico.

---

# Paso 2 — Subir el Dataset

Descarga el dataset desde Kaggle:

https://www.kaggle.com/datasets/kartik2112/fraud-detection

Obtendrás dos archivos:

```id="9yfn6k"
fraudTrain.csv
fraudTest.csv
```

Sube estos archivos a **Cloud Shell** y luego ejecuta:

```bash id="wkvqoq"
gsutil cp fraudTrain.csv gs://<BUCKET_NAME>/datasets/
gsutil cp fraudTest.csv gs://<BUCKET_NAME>/datasets/
```

Verifica que los archivos se hayan subido correctamente:

```bash id="6ri9xf"
gsutil ls gs://<BUCKET_NAME>/datasets/
```

Salida esperada:

```id="5o5ukr"
fraudTrain.csv
fraudTest.csv
```

---

# Autores

- Ana Teresa Vega
- Cristian Rangel
- Juan José Tinajero
- Iván Domínguez

Proyecto de la clase de Análisis de Grandes Volúmenes de Datos
