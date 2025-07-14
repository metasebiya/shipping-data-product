# src/load_json.py

import os
import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime
import glob

# Load environment variables from .env file
load_dotenv()

# Database connection details from environment variables
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # 'db' is the service name in docker-compose
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

RAW_DATA_PATH = "data/raw/telegram_messages"  # This path is relative to /app in Docker container


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
        print("Successfully connected to the database.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def create_raw_table(conn):
    """Creates the raw.telegram_messages table if it doesn't exist."""
    cur = conn.cursor()
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                id SERIAL PRIMARY KEY,
                channel_name VARCHAR(255) NOT NULL,
                message_date DATE NOT NULL,
                message_json JSONB NOT NULL,
                loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_channel_date UNIQUE (channel_name, message_date)
            );
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_telegram_messages_channel_date ON raw.telegram_messages (channel_name, message_date);")
        conn.commit()
        print("Ensured raw.telegram_messages table exists.")
    except psycopg2.Error as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()


def load_json_to_postgres(conn, file_path):
    """
    Loads a single JSON file into the raw.telegram_messages table.
    Assumes file path structure: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
    """
    cur = conn.cursor()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)

        # Extract channel_name and date from the file path
        # Example path: data/raw/telegram_messages/2024-07-14/chemed_channel.json
        parts = file_path.split(os.sep)
        date_str = parts[-2]  # YYYY-MM-DD
        channel_name_raw = parts[-1].replace('.json', '')  # channel_name

        message_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Assuming 'messages' is a list of dictionaries, each representing a message
        # We'll insert each message as a separate row, or you might choose to insert
        # the entire file content as one JSONB object if the file represents a single 'batch'.
        # For this project, let's assume each item in the JSON file's list is a message.
        # If the JSON file contains a single JSON object with many messages, adjust accordingly.

        # Let's adjust this to load the *entire file content* as a single JSONB blob per channel/date file.
        # This keeps the raw structure truly raw. dbt will then extract individual messages.

        # Prepare the insert statement
        insert_query = sql.SQL("""
            INSERT INTO raw.telegram_messages (channel_name, message_date, message_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (channel_name, message_date) DO UPDATE
            SET message_json = EXCLUDED.message_json,
                loaded_at = EXCLUDED.loaded_at;
        """)

        # Execute the insert
        cur.execute(insert_query, (channel_name_raw, message_date, json.dumps(messages)))
        print(f"Loaded/Updated {file_path} into raw.telegram_messages.")
        conn.commit()

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        conn.rollback()
    finally:
        cur.close()


def process_raw_data_lake():
    """
    Scans the raw data lake directory and loads new/updated JSON files into PostgreSQL.
    """
    conn = None
    try:
        conn = connect_db()
        create_raw_table(conn)

        # Find all JSON files in the raw data lake
        json_files = glob.glob(os.path.join(RAW_DATA_PATH, '**', '*.json'), recursive=True)

        if not json_files:
            print(f"No JSON files found in {RAW_DATA_PATH}. Ensure Task 1 is complete.")
            return

        for file_path in json_files:
            load_json_to_postgres(conn, file_path)

    except Exception as e:
        print(f"An error occurred during raw data processing: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":

    process_raw_data_lake()