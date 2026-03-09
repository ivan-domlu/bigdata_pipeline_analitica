import sys
import yaml
from pyspark.sql import SparkSession


def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def main(config_path):

    config = load_config(config_path)

    bucket = config["gcp"]["bucket_name"]

    dataset_path = f"gs://{bucket}/{config['data_paths']['dataset_train']}"
    bronze_path = f"gs://{bucket}/{config['layers']['bronze']}"

    spark = SparkSession.builder \
        .appName("fraud-bronze-layer") \
        .getOrCreate()

    print("Reading dataset from:", dataset_path)

    df = spark.read.csv(
        dataset_path,
        header=True,
        inferSchema=True
    )

    print("Writing Bronze layer to:", bronze_path)

    df.write \
        .mode("overwrite") \
        .parquet(bronze_path)

    spark.stop()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: bronze_layer.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]

    main(config_path)