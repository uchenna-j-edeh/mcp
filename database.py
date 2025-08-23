import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# SQLAlchemy Setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://your_user:your_password@localhost/stock_app_db')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Snapshot(Base):
    __tablename__ = 'snapshots'

    def __init__(self, tablename=None, **kw):
        if tablename:
            self.__tablename__ = tablename
        super().__init__(**kw)

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

def create_tables():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(engine)
