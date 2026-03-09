import sys
import yaml
from pyspark.sql import SparkSession


def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def main(config_path):

    config = load_config(config_path)

    project_id = config["gcp"]["project_id"]
    bucket = config["gcp"]["bucket_name"]

    gold_path = f"gs://{bucket}/{config['layers']['gold']}"
    dataset = f"{project_id}.fraud_detection_analytics"

    spark = SparkSession.builder \
        .appName("load-gold-to-bigquery") \
        .getOrCreate()

    tables = [
        "fraud_by_category",
        "fraud_by_state",
        "fraud_by_hour",
        "fraud_by_age_group",
        "fraud_by_distance"
    ]

    for table in tables:

        path = f"{gold_path}/{table}"

        print(f"Reading {table} from {path}")

        df = spark.read.parquet(path)

        print(f"Loading {table} to BigQuery")

        df.write \
            .format("bigquery") \
            .option("table", f"{dataset}.{table}") \
            .mode("overwrite") \
            .save()

    spark.stop()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: load_to_bigquery.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]

    main(config_path)