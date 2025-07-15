# src/yolo_detector.py

import os
import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime
import glob
from ultralytics import YOLO
import logging
import cv2  # For dummy image creation
import numpy as np  # For dummy image creation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Database connection details
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")  # Changed default to 'localhost' for local dev
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# Path to your raw images data lake
RAW_IMAGES_PATH = "scripts/data/raw/telegram_media"  # Corrected based on your input

# Path to store YOLO results temporarily (not directly used for DB load, but for reference)
YOLO_OUTPUT_PATH = "scripts/data/processed/yolo_detections"
os.makedirs(YOLO_OUTPUT_PATH, exist_ok=True)


def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logging.info("Successfully connected to the database for YOLO processing.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Error connecting to database for YOLO: {e}")
        raise


def create_yolo_raw_table(conn):
    """
    Creates a temporary raw table for YOLO detection results.
    This table will be consumed by dbt to create fct_image_detections.
    """
    cur = conn.cursor()
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.image_detections (
                id SERIAL PRIMARY KEY,
                image_path VARCHAR(512) NOT NULL,
                message_id BIGINT,
                channel_name VARCHAR(255),
                detected_class VARCHAR(255) NOT NULL,
                confidence_score REAL NOT NULL,
                detection_bbox JSONB,
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_image_class UNIQUE (image_path, detected_class)
            );
        """)
        conn.commit()
        logging.info("Ensured raw.image_detections table exists with unique constraint.")
    except psycopg2.Error as e:
        if "already exists" in str(e) and "unique_image_class" in str(e):
            logging.warning("Unique constraint 'unique_image_class' already exists. Skipping creation.")
        else:
            logging.error(f"Error creating raw.image_detections table: {e}")
            conn.rollback()
            raise
    finally:
        cur.close()


def get_processed_images(conn):
    """Retrieves a set of image paths that have already been processed."""
    cur = conn.cursor()
    processed_images = set()
    try:
        cur.execute("SELECT DISTINCT image_path FROM raw.image_detections;")
        for row in cur.fetchall():
            processed_images.add(row[0])
        logging.info(f"Found {len(processed_images)} images already processed in raw.image_detections.")
    except psycopg2.Error as e:
        logging.error(f"Error retrieving processed images: {e}")
    finally:
        cur.close()
    return processed_images


def detect_objects_and_load(conn):
    """
    Scans for new images, runs YOLO detection, and loads results to PostgreSQL.
    """
    try:
        model = YOLO("yolov8n.pt")  # Load a pre-trained YOLOv8n model
        logging.info("YOLOv8 model loaded.")
    except Exception as e:
        logging.error(f"Failed to load YOLO model: {e}")
        logging.error("Ensure you have an internet connection for initial model download (yolov8n.pt).")
        return

    processed_images = get_processed_images(conn)

    logging.info(f"Current working directory: {os.getcwd()}")  # NEW: Log CWD
    logging.info(
        f"Absolute path being searched: {os.path.abspath(RAW_IMAGES_PATH)}")  # NEW: Log absolute path being searched
    # Revert to os.path.join, as this is correct for local Windows environment
    image_extensions = ('*.jpg', '*.jpeg', '*.png')
    all_image_files = []

    for ext in image_extensions:
        all_image_files.extend(glob.glob(os.path.join(RAW_IMAGES_PATH, '**', ext), recursive=True))

    logging.info(f"Found {len(all_image_files)} total image files matching extensions {image_extensions}.")

    new_image_files = [f for f in all_image_files if f not in processed_images]

    if not new_image_files:
        logging.info("No new images found for object detection based on previous processing records.")
        return

    logging.info(f"Processing {len(new_image_files)} new images.")

    cur = conn.cursor()
    insert_query = sql.SQL("""
        INSERT INTO raw.image_detections (image_path, message_id, channel_name, detected_class, confidence_score, detection_bbox)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (image_path, detected_class) DO UPDATE
        SET confidence_score = EXCLUDED.confidence_score,
            detection_bbox = EXCLUDED.detection_bbox,
            processed_at = EXCLUDED.processed_at;
    """)

    for image_path in new_image_files:
        logging.info(f"Attempting to process image: {image_path}")
        try:
            # Extract message_id and channel_name from the file path
            relative_path = os.path.relpath(image_path, RAW_IMAGES_PATH)
            path_components = relative_path.split(os.sep)

            inferred_channel_name = None
            inferred_message_id = None

            if len(path_components) >= 2:
                inferred_channel_name = path_components[-2]
                filename = path_components[-1]
                inferred_message_id_str = os.path.splitext(filename)[0]
                if inferred_message_id_str.isdigit():
                    inferred_message_id = int(inferred_message_id_str)
                else:
                    logging.warning(f"Could not infer numeric message_id from filename '{filename}'.")
            else:
                logging.warning(
                    f"Image path '{image_path}' does not fit expected structure to infer channel/message ID.")

            logging.debug(
                f"Inferred channel_name: {inferred_channel_name}, message_id: {inferred_message_id} for {image_path}")

            results = model(image_path, verbose=False)

            detections_for_image = []
            for r in results:
                logging.debug(f"YOLO results for {image_path}: {r.boxes.data.tolist()}")
                for box in r.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    detected_class_name = model.names[class_id]
                    bbox = box.xyxy[0].tolist()

                    detections_for_image.append({
                        "image_path": image_path,
                        "message_id": inferred_message_id,
                        "channel_name": inferred_channel_name,
                        "detected_class": detected_class_name,
                        "confidence_score": confidence,
                        "detection_bbox": bbox
                    })

            if detections_for_image:
                for det in detections_for_image:
                    cur.execute(insert_query, (
                        det["image_path"],
                        det["message_id"],
                        det["channel_name"],
                        det["detected_class"],
                        det["confidence_score"],
                        json.dumps(det["detection_bbox"])
                    ))
                conn.commit()
                logging.info(f"Loaded {len(detections_for_image)} detections for {image_path}")
            else:
                logging.info(f"No objects detected in {image_path}. Marking as processed.")
                cur.execute(insert_query,
                            (image_path, inferred_message_id, inferred_channel_name, 'NO_DETECTIONS', 0.0, None))
                conn.commit()
                logging.info(f"Marked {image_path} as processed (no detections).")

        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}", exc_info=True)
            conn.rollback()
    cur.close()


if __name__ == "__main__":
    # --- Run the detection process ---
    conn_yolo = None
    try:
        conn_yolo = connect_db()
        create_yolo_raw_table(conn_yolo)
        detect_objects_and_load(conn_yolo)
    except Exception as e:
        logging.critical(f"YOLO processing failed: {e}", exc_info=True)
    finally:
        if conn_yolo:
            conn_yolo.close()
            logging.info("YOLO database connection closed.")