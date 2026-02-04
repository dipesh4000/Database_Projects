from pydantic import BaseModel

class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True





class Post(BaseModel):
  title: str
  content: str
  published: bool = True

  class Config:
    orm_mode = True


