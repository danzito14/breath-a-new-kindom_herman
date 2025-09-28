from sqlalchemy import  create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session



DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "db_Breath_of_a_New_Kingdom"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Motor de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)
meta_data = MetaData()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# conn = engine.connect()
