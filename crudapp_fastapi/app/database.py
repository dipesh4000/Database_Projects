from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# import psycopg2
# import time
# from psycopg2.extras import RealDictCursor

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:PostgreSQL%401@localhost:5432/crud"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autoflush=False, autocommit= False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# # database credentials

# DB_NAME = "crud"
# DB_USER = "postgres"
# DB_PASS = "PostgreSQL@1"
# DB_HOST = "localhost"
# DB_PORT = "5432"

# #database connection 
# try:
#     conn = psycopg2.connect(
#                     host=DB_HOST,
#                     database=DB_NAME,
#                     user=DB_USER,
#                     password=DB_PASS,
#                     port=DB_PORT,
#                     cursor_factory=RealDictCursor)
#     cursor = conn.cursor()
#     print("Database connected successfully")
# except Exception as error:
#     print("Database not connected")
#     print("Error: ", error)
#     time.sleep(2)