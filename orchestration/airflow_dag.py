import yaml
from airflow import DAG
from datetime import datetime
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator

CONFIG_PATH = "/home/airflow/gcs/dags/config/airflow_config.yaml"


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


config = load_config()

PROJECT_ID = config["gcp"]["project_id"]
REGION = config["gcp"]["region"]
CLUSTER_NAME = config["dataproc"]["cluster_name"]

CONFIG_FILE = config["paths"]["config_file"]

BRONZE_SCRIPT = config["scripts"]["bronze"]
SILVER_SCRIPT = config["scripts"]["silver"]
GOLD_SCRIPT = config["scripts"]["gold"]
BIGQUERY_SCRIPT = config["scripts"]["bigquery"]


default_args = {
    "start_date": datetime(2024, 1, 1),
    "retries": 1
}


with DAG(
    dag_id="fraud_detection_pipeline",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    tags=["fraud", "data_pipeline"]
) as dag:

    def dataproc_job(script):

        return {
            "reference": {"project_id": PROJECT_ID},
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": script,
                "args": [CONFIG_FILE]
            }
        }

    bronze_task = DataprocSubmitJobOperator(
        task_id="bronze_layer",
        job=dataproc_job(BRONZE_SCRIPT),
        region=REGION,
        project_id=PROJECT_ID
    )

    silver_task = DataprocSubmitJobOperator(
        task_id="silver_layer",
        job=dataproc_job(SILVER_SCRIPT),
        region=REGION,
        project_id=PROJECT_ID
    )

    gold_task = DataprocSubmitJobOperator(
        task_id="gold_layer",
        job=dataproc_job(GOLD_SCRIPT),
        region=REGION,
        project_id=PROJECT_ID
    )

    bigquery_task = DataprocSubmitJobOperator(
        task_id="load_bigquery",
        job=dataproc_job(BIGQUERY_SCRIPT),
        region=REGION,
        project_id=PROJECT_ID
    )

    bronze_task >> silver_task >> gold_task >> bigquery_task