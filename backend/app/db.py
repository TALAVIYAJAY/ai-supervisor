from sqlmodel import SQLModel, create_engine, Session
from .config import settings
from .models import Supervisor, OrderRun, ActivityLog

db_url = settings.get_database_url()

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    echo=(settings.ENVIRONMENT == "development_debug"),
    connect_args=connect_args,
    pool_pre_ping=True
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
