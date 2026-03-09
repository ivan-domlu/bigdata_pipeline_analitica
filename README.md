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

## Estructura del Data Lake

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

# Paso 3 — Crear el Cluster de Procesamiento (Dataproc)

Para procesar los datos de forma distribuida, este proyecto utiliza **Apache Spark ejecutándose en un cluster de Google Dataproc**.

Dataproc permite crear clusters administrados de **Spark y Hadoop**, facilitando la ejecución de jobs de procesamiento a gran escala sin necesidad de gestionar manualmente la infraestructura.

En este proyecto se utilizará un **cluster de 3 nodos**:

* 1 nodo **Master**
* 2 nodos **Worker**

Esto permite ejecutar **procesamiento distribuido real con Spark**.

---

## Habilitar la API de Dataproc

Primero habilita el servicio de Dataproc en tu proyecto de GCP.

Ejecuta en **Cloud Shell**:

```bash
gcloud services enable dataproc.googleapis.com
```

---

## Crear el Cluster

Ejecuta el siguiente comando:

```bash
gcloud dataproc clusters create <CLUSTER_NAME> \
--region=<REGION> \
--zone=<ZONE> \
--master-machine-type=e2-standard-2 \
--worker-machine-type=e2-standard-2 \
--num-workers=2 \
--master-boot-disk-size=50GB \
--worker-boot-disk-size=50GB \
--image-version=2.1-debian11
```

---

### Ejemplo

```bash
gcloud dataproc clusters create fraud-dataproc-cluster \
--region=us-central1 \
--zone=us-central1-a \
--master-machine-type=e2-standard-2 \
--worker-machine-type=e2-standard-2 \
--num-workers=2 \
--master-boot-disk-size=50GB \
--worker-boot-disk-size=50GB \
--image-version=2.1-debian11
```

---

## Configuración del Cluster

La configuración utilizada busca un balance entre **capacidad de procesamiento y costo**.

| Componente   | Configuración                   |
| ------------ | ------------------------------- |
| Master Node  | e2-standard-2 (2 vCPU, 8GB RAM) |
| Worker Nodes | 2 × e2-standard-2               |
| Disco        | 50GB por nodo                   |
| Región       | us-central1                     |

Esto permite ejecutar **Spark distribuido en 3 nodos** sin requerir recursos excesivos.

---

## Verificar el Cluster

Una vez creado el cluster, puedes verificar su estado ejecutando:

```bash
gcloud dataproc clusters list --region=<REGION>
```

Salida esperada:

```text
NAME                    REGION       STATUS
fraud-dataproc-cluster  us-central1  RUNNING
```

---

# Paso 4 — Preparar los Scripts del Pipeline

El pipeline utiliza **Apache Spark (PySpark)** para procesar los datos almacenados en el Data Lake.

Antes de ejecutar el procesamiento, es necesario subir al bucket:

* El script de Spark
* El archivo de configuración del pipeline

Es necesario configurar algunos parámetros del proyecto.

Estos parámetros se encuentran en el archivo:

```id="cfg_path"
config/pipeline_config.yaml
```

Este archivo permite que el pipeline funcione en **cualquier proyecto de Google Cloud**, evitando rutas o valores hardcodeados.

---

## Editar el Archivo de Configuración

Abre el archivo:

```bash id="open_config"
nano config/pipeline_config.yaml
```

El archivo tendrá una estructura similar a la siguiente:

```yaml id="cfg_example"
gcp:
  project_id: "YOUR_PROJECT_ID"
  bucket_name: "YOUR_BUCKET_NAME"
  region: "us-central1"

data_paths:
  dataset_train: "datasets/fraudTrain.csv"
  dataset_test: "datasets/fraudTest.csv"

layers:
  bronze: "bronze/transactions"
  silver: "silver/transactions_clean"
  gold: "gold/fraud_analytics"
```

---

### Configuración Necesaria

Debes modificar los siguientes valores:

#### project_id

El ID de tu proyecto de Google Cloud.

Ejemplo:

```yaml id="cfg_project"
project_id: "fraud-detection-pipeline-2026"
```

---

#### bucket_name

El nombre del bucket de Cloud Storage creado en el paso anterior.

Ejemplo:

```yaml id="cfg_bucket"
bucket_name: "fraud-detection-data-2026"
```

---

#### region

La región donde se ejecutará el cluster de Dataproc.

Ejemplo:

```yaml id="cfg_region"
region: "us-central1"
```

---

### Ejemplo Completo

```yaml id="cfg_complete"
gcp:
  project_id: "fraud-detection-pipeline-2026"
  bucket_name: "fraud-detection-data-2026"
  region: "us-central1"

data_paths:
  dataset_train: "datasets/fraudTrain.csv"
  dataset_test: "datasets/fraudTest.csv"

layers:
  bronze: "bronze/transactions"
  silver: "silver/transactions_clean"
  gold: "gold/fraud_analytics"
```

---

## Guardar el Archivo

Si estás usando **nano**, presiona:

```
CTRL + X
Y
ENTER
```

---

## Subir los Scripts al Bucket

Desde **Cloud Shell**, ejecuta:

```bash
gsutil cp spark_jobs/bronze_layer.py gs://<BUCKET_NAME>/scripts/
gsutil cp config/pipeline_config.yaml gs://<BUCKET_NAME>/config/
```

Verifica que los archivos se hayan subido correctamente:

```bash
gsutil ls gs://<BUCKET_NAME>/scripts/
gsutil ls gs://<BUCKET_NAME>/config/
```

Salida esperada:

```
gs://<BUCKET_NAME>/scripts/bronze_layer.py
gs://<BUCKET_NAME>/config/pipeline_config.yaml
```

---

# Paso 5 — Ejecutar el Bronze Layer (Spark)

El **Bronze Layer** representa la primera capa del pipeline de datos.

En esta etapa:

* Se leen los archivos CSV del dataset
* Se cargan en un **DataFrame de Spark**
* Se almacenan en formato **Parquet** dentro del Data Lake

El formato Parquet se utiliza porque es **columnar, comprimido y optimizado para análisis con Spark**.

---

## Ejecutar el Job de Spark

Ejecuta el siguiente comando desde **Cloud Shell**:

```bash
gcloud dataproc jobs submit pyspark \
gs://<BUCKET_NAME>/scripts/bronze_layer.py \
--cluster=<CLUSTER_NAME> \
--region=<REGION> \
-- gs://<BUCKET_NAME>/config/pipeline_config.yaml
```

Ejemplo:

```bash
gcloud dataproc jobs submit pyspark \
gs://fraud-detection-data-2026/scripts/bronze_layer.py \
--cluster=fraud-dataproc-cluster \
--region=us-central1 \
-- gs://fraud-detection-data-2026/config/pipeline_config.yaml
```

---

## Resultado Esperado

Después de ejecutar el job, los datos procesados se almacenarán en la capa **Bronze** del Data Lake.

Puedes verificarlo con:

```bash
gsutil ls gs://<BUCKET_NAME>/bronze/
```

Salida esperada:

```
gs://<BUCKET_NAME>/bronze/transactions/
```

Dentro de esta carpeta encontrarás múltiples archivos **Parquet**, que corresponden a las particiones generadas por Spark.

---

# Paso 6 — Procesamiento de Datos (Silver Layer)

La **Silver Layer** corresponde a la segunda etapa del pipeline de datos.

En esta etapa se realiza:

* limpieza de datos
* estandarización de tipos
* creación de nuevas variables (feature engineering)

El objetivo es transformar los datos crudos de la capa **Bronze** en un dataset limpio y enriquecido que pueda utilizarse para análisis y modelado.

---

## Entrada y Salida de Datos

Entrada (Bronze):

```
gs://<BUCKET_NAME>/bronze/transactions/
```

Salida (Silver):

```
gs://<BUCKET_NAME>/silver/transactions_clean/
```

---

## Transformaciones Aplicadas

Durante esta etapa se generan nuevas variables relevantes para la detección de fraude.

| Feature                    | Descripción                                                   |
| -------------------------- | ------------------------------------------------------------- |
| transaction_timestamp      | Conversión del campo de fecha a formato timestamp             |
| transaction_hour           | Hora en la que ocurrió la transacción                         |
| customer_age               | Edad del cliente calculada a partir de la fecha de nacimiento |
| is_night_transaction       | Indicador de transacción nocturna                             |
| distance_customer_merchant | Distancia geográfica entre cliente y comercio                 |

Estas transformaciones permiten identificar patrones sospechosos como:

* transacciones nocturnas
* montos inusuales
* compras en ubicaciones lejanas al cliente

---

## Subir el Script al Bucket

Primero sube el script de Spark al bucket de Cloud Storage.

```bash
gsutil cp spark_jobs/silver/silver_layer.py gs://<BUCKET_NAME>/scripts/
```

Verifica que el archivo se haya subido correctamente:

```bash
gsutil ls gs://<BUCKET_NAME>/scripts/
```

Salida esperada:

```
silver_layer.py
```

---

## Ejecutar el Job de Spark

Para ejecutar el procesamiento de la Silver Layer utiliza el siguiente comando:

```bash
gcloud dataproc jobs submit pyspark \
gs://<BUCKET_NAME>/scripts/silver_layer.py \
--cluster=<CLUSTER_NAME> \
--region=<REGION> \
--files=gs://<BUCKET_NAME>/config/pipeline_config.yaml \
-- pipeline_config.yaml
```

Ejemplo:

```bash
gcloud dataproc jobs submit pyspark \
gs://fraud-detection-data-2026/scripts/silver_layer.py \
--cluster=fraud-dataproc-cluster \
--region=us-central1 \
--files=gs://fraud-detection-data-2026/config/pipeline_config.yaml \
-- pipeline_config.yaml
```

---

## Verificar Resultados

Una vez finalizado el job, los datos procesados estarán disponibles en la capa **Silver**.

Verifica con:

```bash
gsutil ls gs://<BUCKET_NAME>/silver/
```

Salida esperada:

```
gs://<BUCKET_NAME>/silver/transactions_clean/
```

Dentro de esta carpeta se generarán múltiples archivos **Parquet**, producidos por Spark.

---

# Paso 7 — Analítica de Datos (Gold Layer)

La **Gold Layer** representa la etapa final del pipeline de datos y está diseñada para generar **datasets agregados optimizados para análisis y reporting**.

En esta capa se construyen **tablas analíticas derivadas** a partir de los datos limpios de la Silver Layer.

Estas tablas permiten analizar patrones de fraude desde diferentes perspectivas:

* categoría de comercio
* ubicación geográfica
* comportamiento temporal
* características demográficas
* distancia entre cliente y comercio

---

## Entrada y Salida de Datos

Entrada (Silver Layer):

```text
gs://<BUCKET_NAME>/silver/transactions_clean/
```

Salida (Gold Layer):

```text
gs://<BUCKET_NAME>/gold/fraud_analytics/
```

---

## Datasets Analíticos Generados

La Gold Layer genera múltiples datasets agregados que permiten realizar análisis exploratorio de fraude.

---

### Fraud Rate by Category

Analiza la tasa de fraude por tipo de comercio.

Columnas:

| columna            | descripción                          |
| ------------------ | ------------------------------------ |
| category           | categoría del comercio               |
| total_transactions | número total de transacciones        |
| fraud_transactions | número de transacciones fraudulentas |
| fraud_rate         | tasa de fraude                       |
| avg_amount         | monto promedio                       |

---

### Fraud Rate by State

Permite identificar estados con mayor actividad fraudulenta.

Columnas:

| columna            | descripción                |
| ------------------ | -------------------------- |
| state              | estado                     |
| total_transactions | total de transacciones     |
| fraud_transactions | transacciones fraudulentas |
| fraud_rate         | tasa de fraude             |

---

### Fraud by Hour

Analiza patrones temporales de fraude durante el día.

Columnas:

| columna            | descripción                |
| ------------------ | -------------------------- |
| transaction_hour   | hora del día               |
| total_transactions | total de transacciones     |
| fraud_transactions | transacciones fraudulentas |
| fraud_rate         | tasa de fraude             |

---

### Fraud by Age Group

Evalúa la distribución de fraude según grupos de edad de los clientes.

Columnas:

| columna            | descripción            |
| ------------------ | ---------------------- |
| age_group          | grupo de edad          |
| total_transactions | total de transacciones |
| fraud_transactions | número de fraudes      |
| fraud_rate         | tasa de fraude         |

---

### Fraud by Distance

Analiza la relación entre la distancia cliente-comercio y el fraude.

Columnas:

| columna            | descripción            |
| ------------------ | ---------------------- |
| distance_bucket    | rango de distancia     |
| total_transactions | total de transacciones |
| fraud_transactions | número de fraudes      |
| fraud_rate         | tasa de fraude         |

---

## Subir el Script al Bucket

```bash
gsutil cp spark_jobs/gold/gold_layer.py gs://<BUCKET_NAME>/scripts/
```

---

## Ejecutar el Job de Spark

```bash
gcloud dataproc jobs submit pyspark \
gs://<BUCKET_NAME>/scripts/gold_layer.py \
--cluster=<CLUSTER_NAME> \
--region=<REGION> \
--files=gs://<BUCKET_NAME>/config/pipeline_config.yaml \
-- pipeline_config.yaml
```

---

## Verificar Resultados

```bash
gsutil ls gs://<BUCKET_NAME>/gold/fraud_analytics/
```

Salida esperada:

```text
fraud_by_category/
fraud_by_state/
fraud_by_hour/
fraud_by_age_group/
fraud_by_distance/
```

---

# Autores

- Ana Teresa Vega
- Cristian Rangel
- Juan José Tinajero
- Iván Domínguez

Proyecto de la clase de Análisis de Grandes Volúmenes de Datos
