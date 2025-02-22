from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load variabel lingkungan dari .env
load_dotenv()

# Ambil informasi database dari environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.cisbbvivvrvlzvcxwysz:Siji2telu@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")

# Buat engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Buat session untuk database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Buat base untuk model ORM
Base = declarative_base()

# Dependency untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
