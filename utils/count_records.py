import sys
import os

# Add the parent directory to the sys.path to allow imports from the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Session, Snapshot, func

def count_records():
    """Counts the number of records in the snapshots table."""
    session = Session()
    
    try:
        # Check if the table exists
        if not inspect(engine).has_table('snapshots'):
            print("Table 'snapshots' does not exist.")
            return
    
    try:
        count = session.query(func.count(Snapshot.id)).scalar()
        print(f"Total records in snapshots table: {count}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    count_records()
