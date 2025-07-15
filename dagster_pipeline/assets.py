# dagster_pipeline/assets.py

import os
import subprocess
from dagster import asset, OpExecutionContext
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Assuming your scripts are in the 'scripts/' directory relative to the project root
# And your dbt project is in 'telegram_data_dbt/' relative to the project root

@asset(compute_kind="python")
def raw_telegram_messages(context: OpExecutionContext):
    """
    Runs the Telegram data loader script to ingest raw messages.
    This asset represents the raw.telegram_messages table in PostgreSQL.
    """
    context.log.info("Starting raw_telegram_messages ingestion...")
    try:
        # Assuming data_loader.py is in the 'scripts' directory
        # And the script is designed to load data into raw.telegram_messages
        # We need to run this from the project root for relative paths to work
        # (e.g., for .env, or data/raw/telegram_messages if it writes files)
        project_root = os.getenv("PROJECT_ROOT_PATH", ".")  # Get project root from env or assume CWD

        # Construct the command to run the data_loader.py script
        # Ensure data_loader.py handles its own environment variables (e.g., via python-dotenv)
        command = ["python", os.path.join(project_root, "scripts", "load_json.py")]

        context.log.info(f"Executing command: {' '.join(command)}")
        # Use subprocess.run to execute the script
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=project_root)
        context.log.info(f"load_json.py stdout:\n{result.stdout}")
        if result.stderr:
            context.log.error(f"load_json.py stderr:\n{result.stderr}")
        context.log.info("raw_telegram_messages ingestion completed.")
    except subprocess.CalledProcessError as e:
        context.log.error(f"Error running load_json.py: {e}")
        context.log.error(f"Stdout: {e.stdout}")
        context.log.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        context.log.error("load_json.py not found. Ensure 'scripts/load_json.py' exists and is executable.")
        raise


@asset(compute_kind="python", deps=[raw_telegram_messages])  # Depends on raw_telegram_messages
def raw_image_detections(context: OpExecutionContext):
    """
    Runs the YOLO object detection script to process images and load results.
    This asset represents the raw.image_detections table in PostgreSQL.
    """
    context.log.info("Starting raw_image_detections processing...")
    try:
        # Assuming yolo_detector.py is in the 'scripts' directory
        project_root = os.getenv("PROJECT_ROOT_PATH", ".")
        command = ["python", os.path.join(project_root, "scripts", "yolo_detector.py")]

        context.log.info(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=project_root)
        context.log.info(f"yolo_detector.py stdout:\n{result.stdout}")
        if result.stderr:
            context.log.error(f"yolo_detector.py stderr:\n{result.stderr}")
        context.log.info("raw_image_detections processing completed.")
    except subprocess.CalledProcessError as e:
        context.log.error(f"Error running yolo_detector.py: {e}")
        context.log.error(f"Stdout: {e.stdout}")
        context.log.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        context.log.error("yolo_detector.py not found. Ensure 'scripts/yolo_detector.py' exists and is executable.")
        raise


@asset(compute_kind="dbt")
def dbt_models(context: OpExecutionContext, deps=[raw_telegram_messages, raw_image_detections]):
    """
    Runs dbt build to transform raw data into staging and mart models.
    This asset represents all dbt models in your telegram_data_dbt project.
    """
    context.log.info("Starting dbt build...")
    try:
        # Assuming dbt project is in 'telegram_data_dbt' directory
        # And dbt is installed and in PATH within the container/environment
        project_dir = os.path.join(os.getenv("PROJECT_ROOT_PATH", "."), "telegram_data_dbt")

        # Ensure dbt dependencies are installed (run dbt deps once or include in Dockerfile)
        # command_deps = ["dbt", "deps", "--project-dir", project_dir]
        # context.log.info(f"Running dbt deps: {' '.join(command_deps)}")
        # subprocess.run(command_deps, capture_output=True, text=True, check=True)

        command_build = ["dbt", "build", "--project-dir", project_dir]
        context.log.info(f"Running dbt build: {' '.join(command_build)}")

        # Pass environment variables to the dbt subprocess
        # This is crucial for dbt to pick up POSTGRES_DB, USER, etc.
        dbt_env = os.environ.copy()

        result = subprocess.run(command_build, env=dbt_env, capture_output=True, text=True, check=True)
        context.log.info(f"dbt build stdout:\n{result.stdout}")
        if result.stderr:
            context.log.error(f"dbt build stderr:\n{result.stderr}")
        context.log.info("dbt build completed successfully.")
    except subprocess.CalledProcessError as e:
        context.log.error(f"Error running dbt build: {e}")
        context.log.error(f"Stdout: {e.stdout}")
        context.log.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        context.log.error("dbt command not found. Ensure dbt is installed and in your PATH.")
        raise