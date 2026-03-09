#!/bin/bash

# ==========================================
# Fraud Detection Pipeline
# GCS Data Lake Setup Script
# ==========================================

set -e

# Check arguments
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <PROJECT_ID> <BUCKET_NAME> [REGION]"
  echo ""
  echo "Example:"
  echo "./setup_gcs.sh fraud-detection-pipeline-2026 fraud-detection-data-2026 us-central1"
  exit 1
fi

PROJECT_ID=$1
BUCKET_NAME=$2
REGION=${3:-us-central1}

echo "----------------------------------------"
echo "Fraud Detection Data Lake Setup"
echo "----------------------------------------"
echo "Project ID: $PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo ""

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Create bucket
echo "Creating bucket..."
gsutil mb -l $REGION gs://$BUCKET_NAME || echo "Bucket already exists"

# Create Medallion architecture folders
echo "Creating data lake structure..."

gsutil cp /dev/null gs://$BUCKET_NAME/bronze/
gsutil cp /dev/null gs://$BUCKET_NAME/silver/
gsutil cp /dev/null gs://$BUCKET_NAME/gold/
gsutil cp /dev/null gs://$BUCKET_NAME/datasets/
gsutil cp /dev/null gs://$BUCKET_NAME/scripts/
gsutil cp /dev/null gs://$BUCKET_NAME/temp/

echo ""
echo "----------------------------------------"
echo "Data Lake successfully created"
echo "----------------------------------------"

echo ""
echo "Bucket structure:"
gsutil ls gs://$BUCKET_NAME/

echo ""
echo "Next step:"
echo "Upload datasets to:"
echo "gs://$BUCKET_NAME/datasets/"