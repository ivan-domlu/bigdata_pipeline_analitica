import os
import yaml
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator


def get_config_path():
    """
    Detect config path automatically depending on environment.
    """

    airflow_home = os.environ.get("AIRFLOW_HOME", os.path.expanduser("~/airflow"))

    possible_paths = [
        f"{airflow_home}/dags/config/airflow_config.yaml",  # Airflow local
        "/home/airflow/gcs/dags/config/airflow_config.yaml",  # Cloud Composer
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("airflow_config.yaml not found in expected locations")


CONFIG_PATH = get_config_path()


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

    def dataproc_command(script):
        return f"""
        gcloud dataproc jobs submit pyspark \
        {script} \
        --cluster={CLUSTER_NAME} \
        --region={REGION} \
        --files={CONFIG_FILE} \
        -- pipeline_config.yaml
        """

    bronze_task = BashOperator(
        task_id="bronze_layer",
        bash_command=dataproc_command(BRONZE_SCRIPT)
    )

    silver_task = BashOperator(
        task_id="silver_layer",
        bash_command=dataproc_command(SILVER_SCRIPT)
    )

    gold_task = BashOperator(
        task_id="gold_layer",
        bash_command=dataproc_command(GOLD_SCRIPT)
    )

    bigquery_task = BashOperator(
        task_id="load_bigquery",
        bash_command=dataproc_command(BIGQUERY_SCRIPT)
    )

    bronze_task >> silver_task >> gold_task >> bigquery_task