from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
import time
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, SessionLocal, get_db

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


#Routing

@app.get("/")
def root():
    return {"message":"Hii World, how are you"}


@app.get("/posts", response_model= schemas.Post)
def get_posts(db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * FROM posts""")
    posts = db.query(models.Post).all()
    return posts


# @app.get("/posts/latest")
# def get_latest():
#     post = my_posts[len(my_posts)-1]
#     return {"detail": post}


@app.get("/posts/{id}")
def get_post(id:int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail = f"post with id: {id} was not found")
    return post

@app.post("/posts", status_code=status.HTTP_201_CREATED)
def createpost(post: schemas.PostBase, db: Session = Depends(get_db)):
    # cursor.execute("""INSERT INTO public.posts(title, content, published)
	# VALUES (%s, %s, %s) RETURNING * ;""",(post.title, post.content, post.published))
    # new_post = cursor.fetchone()

    # conn.commit()
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.delete("/posts/{id}", status_code=status.HTTP_404_NOT_FOUND)
def delete_post(id: int, db: Session = Depends(get_db)):
    # cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    # deleted_post = cursor.fetchone()
    # conn.commit()
    post = db.query(models.Post).filter(models.Post.id == id)

    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    post.delete(synchronize_session=False)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: schemas.PostBase, db: Session = Depends(get_db)):
    # cursor.execute("""UPDATE posts SET title = %s, content = %s, 
    # published = %s WHERE id = %s RETURNING *;""", (post.title, post.content, post.published, str(id)))

    # updated_post = cursor.fetchone()

    # conn.commit()

    post_query = db.query(models.Post).filter(models.Post.id == id)

    updated_post = post_query.first()

    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    post_query.update(post.dict(), synchronize_session=False)

    db.commit()

    return updated_post

