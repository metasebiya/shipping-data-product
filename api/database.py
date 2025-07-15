# my_project/database.py

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Database connection details from environment variables
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost") # Default to localhost for local dev
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_db_connection():
    """
    Establishes and returns a new PostgreSQL database connection.
    This function is intended to be used directly by CRUD operations,
    or as a dependency in FastAPI.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logging.info("Database connection established.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

# Dependency for FastAPI to manage database sessions
def get_db():
    """
    FastAPI dependency that provides a database connection and ensures it's closed.
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")