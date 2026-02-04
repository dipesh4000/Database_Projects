from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
import time
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models
from .database import engine, SessionLocal, get_db


models.Base.metadata.create_all(bind=engine)

app = FastAPI()



class Post(BaseModel):
  title: str
  content: str
  published: bool = True

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


#Routing

def find_post(id: int):
    cursor.execute("""SELECT * FROM posts WHERE id = %s;""", (str(id),))

    p = cursor.fetchone()

    return p

def find_index_post(id):
    for i,p in enumerate(my_posts):
      if p["id"] == id:
        return i

@app.get("/")
def root():
    return {"message":"Hii World, how are you"}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * FROM posts""")
    posts = db.query(models.Post).all()
    return {"data":posts}


@app.get("/posts/latest")
def get_latest():
    post = my_posts[len(my_posts)-1]
    return {"detail": post}


@app.get("/posts/{id}")
def get_post(id:int, db: Session = Depends(get_db)):
    post = find_post(id)
    if not post:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail = f"post with id: {id} was not found")
    return {"post_detail": post}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def createpost(post: Post, db: Session = Depends(get_db)):
    # cursor.execute("""INSERT INTO public.posts(title, content, published)
	# VALUES (%s, %s, %s) RETURNING * ;""",(post.title, post.content, post.published))
    # new_post = cursor.fetchone()

    # conn.commit()
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {"data": new_post}


@app.delete("/posts/{id}", status_code=status.HTTP_404_NOT_FOUND)
def delete_post(id: int):
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    cursor.execute("""UPDATE posts SET title = %s, content = %s, 
    published = %s WHERE id = %s RETURNING *;""", (post.title, post.content, post.published, str(id)))

    updated_post = cursor.fetchone()

    conn.commit()

    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    return {"data": updated_post}

