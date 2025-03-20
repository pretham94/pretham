import datetime
from airflow import models
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.operators.dataflow import DataflowCreatePythonJobOperator
from airflow.utils.trigger_rule import TriggerRule

# Default arguments for the DAG
default_dag_args = {
    "start_date": datetime.datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Define the DAG
with models.DAG(
    "csv_to_bq_beam_pipeline",
    schedule_interval="@daily",
    default_args=default_dag_args,
    catchup=False,
    description="DAG to run Apache Beam pipeline for CSV to BigQuery data loading",
) as dag:
    start = DummyOperator(task_id="start")

    # Execute Apache Beam Pipeline using Dataflow
    # This directly runs your Python Beam file instead of using a template
    run_beam_dataflow = DataflowCreatePythonJobOperator(
        task_id="run_beam_pipeline",
        py_file="gs://fake-data-1/beam_scripts/beam_csv_to_bigquery.py",  # Location of your Beam Python file in GCS
        job_name="csv-to-bq-{{ ds_nodash }}",  # Adds date to job name for tracking
        options={
            "project": "ninth-tensor-453515-n3",
            "region": "us-east1",
            "zone": "us-east1-b",
            "temp_location": "gs://fake-data-1/temp/",
        },
        py_options=[],
        py_requirements=["apache-beam[gcp]==2.49.0"],  # Specifying dependencies
        py_interpreter="python3",
        location="us-east1",  # Directly passed as a parameter
        wait_until_finished=True,  # Directly passed as a parameter
    )

    end = DummyOperator(
        task_id="end", 
        trigger_rule=TriggerRule.ALL_DONE  # Will run even if upstream tasks failed
    )

    # Set task dependencies
    start >> run_beam_dataflow >> end 