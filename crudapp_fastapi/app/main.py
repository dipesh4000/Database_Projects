from fastapi import FastAPI
from .database import engine
from .routers import post, user, auth
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(post.router)
app.include_router(user.router) 
app.include_router(auth.router)

#Routing

@app.get("/")
def root():
    return {"message":"Hii World, how are you"}


