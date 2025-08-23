import os
import json
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta, date, time
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import pytz
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Logging Setup ---
LOG_DIR = '/var/log/mcp-server-gemini-cli'
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        app.logger.error(f"Error creating log directory {LOG_DIR}: {e}")

log_file = os.path.join(LOG_DIR, 'app.log')
file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5) # 1 MB per file, 5 backups
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
# --- End Logging Setup ---

# SQLAlchemy Setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://your_user:your_password@localhost/stock_app_db')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define the ORM model for the snapshots table
class Snapshot(Base):
    __tablename__ = 'snapshots'

    id = Column(Integer, primary_key=True)
    snapshot_timestamp = Column(DateTime, nullable=False)
    ingestion_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    symbol = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    price = Column(String(20), nullable=False)
    change = Column(String(20), nullable=False)
    changes_percentage = Column(String(20), nullable=False)
    launch_link = Column(String, nullable=False)
    is_gainer = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Snapshot(id='{self.id}', symbol='{self.symbol}', snapshot_timestamp='{self.snapshot_timestamp}')>"

def get_color(percentage, max_percentage, is_gainer):
    """
    Calculates the color shade based on the percentage change relative to the max change.
    """
    try:
        percentage = float(percentage)
        max_percentage = float(max_percentage)
    except (ValueError, TypeError):
        return "rgba(255, 255, 255, 0.1)" # Default color for invalid data

    if max_percentage == 0:
        normalized_percentage = 0
    else:
        normalized_percentage = abs(percentage) / max_percentage

    if is_gainer:
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(0, 255, 0, {alpha})"
    else:
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(255, 0, 0, {alpha})"

@app.route('/')
def index():
    session = Session()
    try:
        # Check if we need to fetch new snapshots
        check_and_fetch_snapshots()

        # Query for distinct snapshot dates
        snapshot_dates = session.query(func.date(Snapshot.snapshot_timestamp)).distinct().order_by(func.date(Snapshot.snapshot_timestamp).desc()).all()
        # Extract date objects from the result
        snapshot_dates = [d[0] for d in snapshot_dates]
        return render_template('index.html', snapshot_dates=snapshot_dates)
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in index route: {e}")
        return "An unexpected error occurred.", 500
    finally:
        session.close()

@app.route('/snapshots/<snapshot_date>')
def snapshot_details(snapshot_date):
    session = Session()
    try:
        # Convert string date to datetime object
        snapshot_date_obj = datetime.strptime(snapshot_date, '%Y-%m-%d').date()
        
        # Query for snapshots on the given date
        snapshots = session.query(Snapshot).filter(func.date(Snapshot.snapshot_timestamp) == snapshot_date_obj).all()
        
        gainers = [s for s in snapshots if s.is_gainer]
        losers = [s for s in snapshots if not s.is_gainer]

        if gainers:
            max_gain = max(float(stock.changes_percentage) for stock in gainers)
            for stock in gainers:
                stock.color = get_color(stock.changes_percentage, max_gain, is_gainer=True)
        
        if losers:
            max_loss = max(abs(float(stock.changes_percentage)) for stock in losers)
            for stock in losers:
                stock.color = get_color(stock.changes_percentage, max_loss, is_gainer=False)

        return render_template('snapshot_details.html', gainers=gainers, losers=losers, snapshot_date=snapshot_date)
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in snapshot_details route: {e}")
        return "An unexpected error occurred.", 500
    finally:
        session.close()

def check_and_fetch_snapshots():
    """Checks if a snapshot for the current day has been taken and fetches it if not."""
    session = Session()
    try:
        today = date.today()
        now_utc = datetime.now(pytz.utc)
        us_est = pytz.timezone('America/New_York')
        current_est_time = now_utc.astimezone(us_est)
        refresh_hour = 15 # 3 PM
        refresh_minute = 0
        refresh_time_today_est = us_est.localize(datetime.combine(today, time(refresh_hour, refresh_minute)))

        # Check if a snapshot for today has already been taken
        snapshot_for_today_exists = session.query(Snapshot).filter(func.date(Snapshot.snapshot_timestamp) == today).first() is not None

        if not snapshot_for_today_exists and current_est_time >= refresh_time_today_est:
            app.logger.info(f"It's after 3 PM EST and no snapshot for {today} exists. Fetching new data...")
            fetch_and_store_snapshots()
        else:
            app.logger.info("Snapshot for today already exists or it's not yet 3 PM EST.")

    except Exception as e:
        app.logger.error(f"An error occurred in check_and_fetch_snapshots: {e}")
    finally:
        session.close()

def fetch_and_store_snapshots():
    """Fetches snapshot data from the API and stores it in the database."""
    api_key = os.environ.get('FMP_API_KEY', 'YOUR_API_KEY')
    session = Session()
    try:
        now_utc = datetime.now(pytz.utc)
        us_est = pytz.timezone('America/New_York')
        current_est_time = now_utc.astimezone(us_est)
        snapshot_time = current_est_time

        # Fetch gainers
        gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
        gainers_response = requests.get(gainers_url)
        gainers_response.raise_for_status()
        top_25_gainers = gainers_response.json()[:100]

        # Fetch losers
        losers_url = f"https://financialmodelingprep.com/api/v3/stock_market/losers?apikey={api_key}"
        losers_response = requests.get(losers_url)
        losers_response.raise_for_status()
        top_25_losers = losers_response.json()[:100]

        # Store fetched data
        for stock in top_25_gainers:
            new_snapshot = Snapshot(
                snapshot_timestamp=snapshot_time,
                symbol=stock['symbol'],
                name=stock['name'],
                price=str(stock['price']),
                change=str(stock['change']),
                changes_percentage=str(stock['changesPercentage']),
                launch_link=f"https://finance.yahoo.com/quote/{stock['symbol']}",
                is_gainer=True
            )
            session.add(new_snapshot)

        for stock in top_25_losers:
            new_snapshot = Snapshot(
                snapshot_timestamp=snapshot_time,
                symbol=stock['symbol'],
                name=stock['name'],
                price=str(stock['price']),
                change=str(stock['change']),
                changes_percentage=str(stock['changesPercentage']),
                launch_link=f"https://finance.yahoo.com/quote/{stock['symbol']}",
                is_gainer=False
            )
            session.add(new_snapshot)

        session.commit()
        app.logger.info(f"Successfully fetched and stored snapshots for {snapshot_time}")

    except requests.exceptions.RequestException as e:
        session.rollback()
        app.logger.error(f"Error fetching data from FMP API: {e}")
    except IntegrityError:
        session.rollback()
        app.logger.warning("IntegrityError: Data likely already exists for this timestamp.")
    except Exception as e:
        session.rollback()
        app.logger.error(f"An unexpected error occurred during snapshot fetching: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Flask Snapshot App')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The hostname to listen on.')
    parser.add_argument('--port', type=int, default=5000, help='The port of the webserver.')
    args = parser.parse_args()

    # Create database tables if they don't exist
    if not inspect(engine).has_table('snapshots'):
        app.logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        app.logger.info("Database tables created.")

    app.run(host=args.host, port=args.port, debug=True)