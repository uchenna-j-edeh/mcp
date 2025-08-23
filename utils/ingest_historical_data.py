import sys
import os

# Add the parent directory to the sys.path to allow imports from the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from datetime import datetime, time
from sqlalchemy.exc import IntegrityError
import requests

from database import Session, Snapshot, create_tables, func
import fmp_api

# --- Logging Setup ---
LOG_DIR = '/var/log/mcp-server-gemini-cli'
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        print(f"Error creating log directory {LOG_DIR}: {e}")

log_file = os.path.join(LOG_DIR, 'ingestion.log')
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
# --- End Logging Setup ---

def fetch_and_store_snapshots(specific_date):
    """Fetches snapshot data for a specific date from the API and stores it in the database."""
    session = Session()
    try:
        # Check if the table exists
        if not inspect(engine).has_table('snapshots'):
            logger.error("Table 'snapshots' does not exist. Please run the main app to create it.")
            print("Table 'snapshots' does not exist. Please run the main app to create it.")
            return

if __name__ == "__main__":
    create_tables()
    if len(sys.argv) != 2:
        print("Usage: python ingest_historical_data.py YYYY/MM/DD")
        sys.exit(1)
    
    date_str = sys.argv[1]
    try:
        specific_date = datetime.strptime(date_str, '%Y/%m/%d').date()
        fetch_and_store_snapshots(specific_date)
    except ValueError:
        print("Invalid date format. Please use YYYY/MM/DD.")