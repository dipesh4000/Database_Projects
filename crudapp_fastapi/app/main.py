from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2


app = FastAPI()

class Post(BaseModel):
  title: str
  content: str
  published: bool = True

DB_NAME = "tkgafrwp"
DB_USER = "tkgafrwp"
DB_PASS = "iYYtLAXVbid-i6MV3NO1EnU-_9SW2uEi"
DB_HOST = "tyke.db.elephantsql.com"
DB_PORT = "5432"

try:
    conn = psycopg2.connect(database=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS,
                            host=DB_HOST,
                            port=DB_PORT)
    print("Database connected successfully")
except:
    print("Database not connected successfully")

my_posts = [
  {"title":"title of post1", "content":"content of post1", "id":1},
  {"title":"title of post2", "content":"content of post2", "id":2}
  ]

def find_post(id: int):
    for p in my_posts:
      if p["id"] == id:
        return p

def find_index_post(id):
    for i,p in enumerate(my_posts):
      if p["id"] == id:
        return i



@app.get("/")
def root():
    return {"message":"Hii World, how are you"}


@app.get("/posts")
def get_posts():
    return {"data":my_posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def createpost(new_post: Post):
    my_posts.append(new_post.dict())
    return {"data": new_post}


@app.get("/posts/latest")
def get_latest():
    post = my_posts[len(my_posts)-1]
    return {"detail": post}



@app.get("/posts/{id}")
def get_post(id:int, response: Response):
    post = find_post(id)
    if not post:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail = f"post with id: {id} was not found")
    return {"post_detail": post}

@app.delete("/posts/{id}", status_code=status.HTTP_404_NOT_FOUND)
def delete_post(id: int):
    index = find_index_post(id)

    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    
    my_posts.pop(index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post):

    index = find_index_post(id)

    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    post_dict = post.dict()
    post_dict['id'] = id
    my_posts[index] = post_dict
    return {"data": post_dict}