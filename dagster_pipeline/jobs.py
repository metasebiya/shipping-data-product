# dagster_pipeline/jobs.py

from dagster import define_asset_job, ScheduleDefinition
from .assets import raw_telegram_messages, raw_image_detections, dbt_models

# Define a job that materializes all our assets
telegram_data_pipeline_job = define_asset_job(
    name="telegram_data_pipeline_job",
    selection=[raw_telegram_messages, raw_image_detections, dbt_models]
)

# Define a daily schedule for the job
daily_telegram_pipeline_schedule = ScheduleDefinition(
    job=telegram_data_pipeline_job,
    cron_schedule="0 0 * * *",  # Run daily at midnight UTC
    execution_timezone="UTC",
)