# Stock Data Pipeline with Apache Beam and Cloud Composer

This project demonstrates how to build a data pipeline that processes CSV stock data files from Google Cloud Storage and loads them into BigQuery using Apache Beam (Dataflow) and orchestrates the pipeline with Cloud Composer (Airflow).

## Project Files

- `beam_csv_to_bigquery.py` - The original Apache Beam pipeline for processing CSV stock data
- `beam_csv_to_bigquery_composer.py` - A parameterized version of the Beam pipeline designed to work with Cloud Composer
- `stock_data_pipeline_dag.py` - The Airflow DAG definition for Cloud Composer
- `deploy_to_composer.sh` - A deployment script to upload files to GCS and Cloud Composer

## Prerequisites

1. A Google Cloud Platform account with billing enabled
2. The following APIs enabled:
   - Dataflow API
   - Cloud Composer API
   - BigQuery API
   - Cloud Storage API
3. A Cloud Composer environment
4. A Cloud Storage bucket for input data, temporary files, and staging
5. The `gcloud` CLI installed and configured
6. Python 3.9 or higher

## Configuration

Before running the pipeline, you need to:

1. Edit the deployment script `deploy_to_composer.sh` to set your:
   - `PROJECT_ID`
   - `BUCKET`
   - `REGION`
   - `COMPOSER_ENVIRONMENT`

2. Upload your stock data CSV file to GCS:
   ```bash
   gsutil cp your-stock-data.csv gs://your-bucket/structured/top_it_companies_stock_data.csv
   ```

3. Make sure the CSV has the expected format with columns:
   - company_name
   - date (in YYYY-MM-DD format)
   - open_price
   - close_price

## Deployment

1. Make the deployment script executable:
   ```bash
   chmod +x deploy_to_composer.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy_to_composer.sh
   ```

3. This will:
   - Create necessary directories in your GCS bucket
   - Upload the Beam pipeline script to GCS
   - Upload the Airflow DAG to your Cloud Composer environment

## Airflow Variables

You can customize the pipeline by setting the following Airflow variables in the Cloud Composer UI:

- `gcp_project_id`: Your GCP project ID
- `gcs_bucket`: GCS bucket for input data
- `dataflow_bucket`: GCS bucket for Dataflow temporary and staging files
- `bigquery_dataset`: BigQuery dataset to store the stock data
- `bigquery_table`: BigQuery table name
- `region`: GCP region for running Dataflow jobs
- `zone`: GCP zone for Dataflow workers

## Pipeline Workflow

1. Checks if the input CSV file exists in GCS
2. Creates the BigQuery dataset if it doesn't exist
3. Creates the BigQuery table with the proper schema if it doesn't exist
4. Launches a Dataflow job to process the CSV file
5. The Dataflow job:
   - Reads the CSV file from GCS
   - Parses and validates the data
   - Loads the data into BigQuery

## Troubleshooting

- Check the Airflow UI logs for any errors in the DAG execution
- Check the Dataflow job logs for errors in data processing
- Ensure your service accounts have the necessary permissions:
  - Cloud Composer service account needs Dataflow Admin and Storage Admin roles
  - Dataflow service account needs BigQuery Data Editor and Storage Object Admin roles

## Customizing the Pipeline

To modify the pipeline for different data formats:

1. Update the schema in both the Beam pipeline and the DAG file
2. Modify the `ParseCsvDoFn` and `ValidateDataTypesDoFn` classes in the Beam pipeline
3. Redeploy using the deployment script 