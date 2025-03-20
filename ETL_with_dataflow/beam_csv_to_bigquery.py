import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, WorkerOptions
from apache_beam.io import ReadFromText
import logging
import csv
import io
from datetime import datetime

# Configuration - Replace with your own values
PROJECT_ID = 'ninth-tensor-453515-n3'
BUCKET = 'fake-data-1'
DATASET = 'fake_dataset'
TABLE = 'fake_table'
REGION = 'us-east1'
INPUT_FILE = f'gs://{BUCKET}/structured/top_it_companies_stock_data.csv'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidateDataTypesDoFn(beam.DoFn):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, record):
        """Validate and convert data types for BigQuery."""
        if record is None:
            return []
        
        try:
            from datetime import datetime
            
            # Extract values
            company_name = record.get('company_name', '')
            date_str = record.get('date', '')
            open_price_str = record.get('open_price', '')
            close_price_str = record.get('close_price', '')
            
            # Validate and convert date (YYYY-MM-DD format)
            try:
                # Validate date format
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date = date_obj.strftime('%Y-%m-%d')  # Format for BigQuery
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid date format: {date_str}. Record: {record}")
                return []
            
            # Validate and convert prices to float
            try:
                open_price = float(open_price_str) if open_price_str else None
                close_price = float(close_price_str) if close_price_str else None
            except ValueError:
                self.logger.warning(f"Invalid price values. Record: {record}")
                return []
            
            # Return the validated record
            return [{
                'company_name': company_name,
                'date': date,
                'open_price': open_price,
                'close_price': close_price
            }]
            
        except Exception as e:
            self.logger.error(f"Error validating record {record}: {str(e)}")
            return []

class ParseCsvDoFn(beam.DoFn):
    def __init__(self):
        # Create a logger inside the class so it's available everywhere
        self.logger = logging.getLogger(__name__)
    
    def process(self, element, header_row):
        try:
            # Import modules inside the process method
            import csv
            import io
            
            # Parse the CSV line
            reader = csv.reader(io.StringIO(element))
            row = next(reader)
            
            # Skip the header row
            if element == header_row:
                self.logger.info("Skipping header row")
                return []
            
            # Create a dictionary with the correct field names
            field_dict = {
                'company_name': row[0].strip() if len(row) > 0 else '',
                'date': row[1].strip() if len(row) > 1 else '',
                'open_price': row[2].strip() if len(row) > 2 else '',
                'close_price': row[3].strip() if len(row) > 3 else ''
            }
            
            return [field_dict]
        except Exception as e:
            self.logger.error(f"Error parsing CSV line: {element}. Exception: {str(e)}")
            return []

def run():
    """Main entry point; defines and runs the pipeline."""
    logger.info("Starting CSV to BigQuery pipeline")
    
    # Set up pipeline options
    pipeline_options = PipelineOptions()
    google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
    google_cloud_options.project = PROJECT_ID
    google_cloud_options.job_name = f'csv-to-bq-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    google_cloud_options.temp_location = f'gs://{BUCKET}/temp'
    google_cloud_options.region = REGION
    
    # Specify worker options to avoid zone resource issues
    worker_options = pipeline_options.view_as(WorkerOptions)
    worker_options.zone = 'us-east1-b'  # Change to a zone within us-east1 region
    
    pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'
    
    # Define the BigQuery schema as a string
    schema = 'company_name:STRING, date:DATE, open_price:FLOAT, close_price:FLOAT'
    
    # Run the pipeline
    with beam.Pipeline(options=pipeline_options) as p:
        # Read the file
        logger.info(f"Reading from GCS: {INPUT_FILE}")
        lines = p | 'ReadFromGCS' >> ReadFromText(INPUT_FILE)
        
        # Extract the header row (first row)
        logger.info("Extracting header row")
        header = (
            lines 
            | 'GetFirst' >> beam.transforms.combiners.Sample.FixedSizeGlobally(1)
            | 'ExtractHeader' >> beam.FlatMap(lambda x: x)
        )
        
        header_value = beam.pvalue.AsSingleton(header)
        
        # Process the CSV data
        logger.info("Processing CSV data")
        processed_data = (
            lines
            | 'ParseCSV' >> beam.ParDo(ParseCsvDoFn(), header_value)
            | 'FilterNoneAfterParse' >> beam.Filter(lambda x: x is not None)
            | 'ValidateDataTypes' >> beam.ParDo(ValidateDataTypesDoFn())
            | 'FilterNoneAfterValidate' >> beam.Filter(lambda x: x is not None)
        )
        
        # Write to BigQuery
        logger.info(f"Writing to BigQuery table: {PROJECT_ID}:{DATASET}.{TABLE}")
        processed_data | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
            f'{PROJECT_ID}:{DATASET}.{TABLE}',
            schema=schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,  # Table must already exist
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND    # Append to existing data
        )
    
    logger.info("Pipeline definition complete")

if __name__ == '__main__':
    logger.info("Script started")
    try:
        run()
        logger.info("Pipeline launched successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise 