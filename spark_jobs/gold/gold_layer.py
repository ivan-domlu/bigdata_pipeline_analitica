import sys
import yaml

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    sum,
    avg,
    when
)

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def main(config_path):

    config = load_config(config_path)

    bucket = config["gcp"]["bucket_name"]

    silver_path = f"gs://{bucket}/{config['layers']['silver']}"
    gold_path = f"gs://{bucket}/{config['layers']['gold']}"

    spark = SparkSession.builder \
        .appName("fraud-gold-layer") \
        .getOrCreate()

    print("Reading Silver data from:", silver_path)

    df = spark.read.parquet(silver_path)

    # --------------------------------------------------
    # Fraud Rate by Category
    # --------------------------------------------------

    fraud_by_category = df.groupBy("category").agg(
        count("*").alias("total_transactions"),
        sum("is_fraud").alias("fraud_transactions"),
        avg("amt").alias("avg_amount")
    )

    fraud_by_category = fraud_by_category.withColumn(
        "fraud_rate",
        col("fraud_transactions") / col("total_transactions")
    )

    # --------------------------------------------------
    # Fraud Rate by State
    # --------------------------------------------------

    fraud_by_state = df.groupBy("state").agg(
        count("*").alias("total_transactions"),
        sum("is_fraud").alias("fraud_transactions")
    )

    fraud_by_state = fraud_by_state.withColumn(
        "fraud_rate",
        col("fraud_transactions") / col("total_transactions")
    )

    # --------------------------------------------------
    # Fraud by Hour
    # --------------------------------------------------

    fraud_by_hour = df.groupBy("transaction_hour").agg(
        count("*").alias("total_transactions"),
        sum("is_fraud").alias("fraud_transactions")
    )

    fraud_by_hour = fraud_by_hour.withColumn(
        "fraud_rate",
        col("fraud_transactions") / col("total_transactions")
    )

    # --------------------------------------------------
    # Fraud by Age Group
    # --------------------------------------------------

    df_age = df.withColumn(
        "age_group",
        when(col("customer_age") < 25, "18-24")
        .when(col("customer_age") < 35, "25-34")
        .when(col("customer_age") < 50, "35-49")
        .otherwise("50+")
    )

    fraud_by_age_group = df_age.groupBy("age_group").agg(
        count("*").alias("total_transactions"),
        sum("is_fraud").alias("fraud_transactions")
    )

    fraud_by_age_group = fraud_by_age_group.withColumn(
        "fraud_rate",
        col("fraud_transactions") / col("total_transactions")
    )

    # --------------------------------------------------
    # Fraud vs Distance
    # --------------------------------------------------

    df_distance = df.withColumn(
        "distance_bucket",
        when(col("distance_customer_merchant") < 10, "<10km")
        .when(col("distance_customer_merchant") < 50, "10-50km")
        .when(col("distance_customer_merchant") < 200, "50-200km")
        .otherwise(">200km")
    )

    fraud_by_distance = df_distance.groupBy("distance_bucket").agg(
        count("*").alias("total_transactions"),
        sum("is_fraud").alias("fraud_transactions")
    )

    fraud_by_distance = fraud_by_distance.withColumn(
        "fraud_rate",
        col("fraud_transactions") / col("total_transactions")
    )

    # --------------------------------------------------
    # Write outputs
    # --------------------------------------------------

    fraud_by_category.write.mode("overwrite").parquet(
        f"{gold_path}/fraud_by_category"
    )

    fraud_by_state.write.mode("overwrite").parquet(
        f"{gold_path}/fraud_by_state"
    )

    fraud_by_hour.write.mode("overwrite").parquet(
        f"{gold_path}/fraud_by_hour"
    )

    fraud_by_age_group.write.mode("overwrite").parquet(
        f"{gold_path}/fraud_by_age_group"
    )

    fraud_by_distance.write.mode("overwrite").parquet(
        f"{gold_path}/fraud_by_distance"
    )

    spark.stop()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: gold_layer.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]

    main(config_path)