import sys
import yaml

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    hour,
    to_timestamp,
    year,
    current_date,
    floor,
    when,
    radians,
    sin,
    cos,
    sqrt,
    atan2
)

# ----------------------------
# Load configuration
# ----------------------------

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

# ----------------------------
# Haversine distance function
# ----------------------------

def haversine(lat1, lon1, lat2, lon2):

    R = 6371  # Earth radius km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2) * sin(dlat/2) + \
        cos(radians(lat1)) * cos(radians(lat2)) * \
        sin(dlon/2) * sin(dlon/2)

    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c

# ----------------------------
# Main
# ----------------------------

def main(config_path):

    config = load_config(config_path)

    bucket = config["gcp"]["bucket_name"]

    bronze_path = f"gs://{bucket}/{config['layers']['bronze']}"
    silver_path = f"gs://{bucket}/{config['layers']['silver']}"

    spark = SparkSession.builder \
        .appName("fraud-silver-layer") \
        .getOrCreate()

    print("Reading Bronze data from:", bronze_path)

    df = spark.read.parquet(bronze_path)

    # ----------------------------
    # Transformations
    # ----------------------------

    df = df.withColumn(
        "transaction_timestamp",
        to_timestamp(col("trans_date_trans_time"))
    )

    df = df.withColumn(
        "transaction_hour",
        hour(col("transaction_timestamp"))
    )

    # customer age
    df = df.withColumn(
        "customer_age",
        year(current_date()) - year(col("dob"))
    )

    # night transaction
    df = df.withColumn(
        "is_night_transaction",
        when((col("transaction_hour") >= 22) | (col("transaction_hour") <= 5), 1).otherwise(0)
    )

    # distance customer ↔ merchant
    df = df.withColumn(
        "distance_customer_merchant",
        haversine(
            col("lat"),
            col("long"),
            col("merch_lat"),
            col("merch_long")
        )
    )

    # ----------------------------
    # Write Silver layer
    # ----------------------------

    print("Writing Silver data to:", silver_path)

    df.write \
        .mode("overwrite") \
        .parquet(silver_path)

    spark.stop()

# ----------------------------
# Entry point
# ----------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: silver_layer.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]

    main(config_path)