from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
import time
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, SessionLocal, get_db
from .routers import post, user

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

#database credentials

DB_NAME = "crud"
DB_USER = "postgres"
DB_PASS = "PostgreSQL@1"
DB_HOST = "localhost"
DB_PORT = "5432"

#database connection 
try:
    conn = psycopg2.connect(
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASS,
                    port=DB_PORT,
                    cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("Database connected successfully")
except Exception as error:
    print("Database not connected")
    print("Error: ", error)
    time.sleep(2)

app.include_router(post.router)
app.include_router(user.router) 
app.include_router(auth.router)

#Routing

@app.get("/")
def root():
    return {"message":"Hii World, how are you"}


