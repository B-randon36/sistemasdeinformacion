import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

logger = logging.getLogger("bsc.database")
logging.basicConfig(level=logging.INFO)

db_url = DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(db_url, connect_args=connect_args)
    # Quick probe to test connection
    with engine.connect() as conn:
        pass
    logger.info(f"Conexión exitosa a la base de datos: {db_url}")
except Exception as e:
    logger.warning(f"Error conectando a {db_url}: {e}. Conmutando a SQLite local...")
    db_url = "sqlite:///./agroperuvian_bsc.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
