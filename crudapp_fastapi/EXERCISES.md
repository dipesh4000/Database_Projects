# Practice Exercises - Build on Your Project

## Level 1: Understanding Existing Code

### Exercise 1.1: Add Logging
**Goal**: Understand the flow by adding print statements

```python
# In routers/auth.py, modify login():
@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    print(f"[LOG] Login attempt with email: {user_credentials.username}")
    
    user = db.query(models.User).filter(
        models.User.email == user_credentials.username).first()
    print(f"[LOG] User found: {user.email if user else 'None'}")
    
    if not user:
        print(f"[LOG] User not found, raising 403")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        print(f"[LOG] Password verification failed")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    print(f"[LOG] Password verified, creating token")
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    print(f"[LOG] Token created: {access_token[:30]}...")
    
    return {"access_token": access_token, "token_type": "bearer"}
```

**What You'll Learn**: 
- See requests flowing through the system
- Understand the order of operations
- Debug by checking console output

### Exercise 1.2: Add Request Timing
**Goal**: Measure endpoint performance

```python
import time

@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    start_time = time.time()
    
    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    
    elapsed = time.time() - start_time
    print(f"Query took {elapsed:.3f} seconds, returned {len(posts)} posts")
    
    return posts
```

**What You'll Learn**: Performance metrics, database query speed

---

## Level 2: Add New Features (Modify Existing Models)

### Exercise 2.1: Add User Profile Picture
**Goal**: Add a new field to User model

1. **Modify models.py**:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    profile_picture_url = Column(String, nullable=True)  # NEW LINE
```

2. **Update schemas.py**:
```python
class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    profile_picture_url: Optional[str] = None  # NEW
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    profile_picture_url: Optional[str] = None  # NEW
```

3. **Test**:
```bash
# Create user with picture
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"pic@test.com","password":"test","profile_picture_url":"https://..."}'
```

4. **Database migration** (manual):
```sql
ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR(255);
```

**What You'll Learn**: Schema evolution, database migrations, optional fields

### Exercise 2.2: Add Post Update Counter
**Goal**: Track how many times a post was edited

1. **Modify models.py**:
```python
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)  # NEW
    update_count = Column(Integer, server_default='0', nullable=False)  # NEW
    
    owner = relationship("User")
```

2. **Modify routers/post.py** - Update endpoint:
```python
@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    post_query.update(
        {
            **updated_post.dict(),
            models.Post.updated_at: datetime.now(timezone.utc),  # NEW
            models.Post.update_count: models.Post.update_count + 1  # NEW
        },
        synchronize_session=False
    )
    db.commit()
    return post_query.first()
```

**What You'll Learn**: Timestamps, update tracking, database math operations

---

## Level 3: Add New Relationships (New Models)

### Exercise 3.1: Add Comments
**Goal**: Users can comment on posts

1. **Add Comment Model** in models.py:
```python
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    
    user = relationship("User")
    post = relationship("Post")
```

2. **Add Schemas** in schemas.py:
```python
class CommentCreate(BaseModel):
    content: str

class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    post_id: int
    
    class Config:
        from_attributes = True
```

3. **Create New Router** - routers/comment.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/{post_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentOut)
def create_comment(post_id: int, comment: schemas.CommentCreate, 
                   db: Session = Depends(get_db), 
                   current_user: models.User = Depends(oauth2.get_current_user)):
    
    # Check if post exists
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Create comment
    new_comment = models.Comment(
        content=comment.content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment

@router.get("/{post_id}")
def get_post_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
    return comments
```

4. **Register in main.py**:
```python
from .routers import post, user, auth, comment  # ADD comment

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(comment.router)  # ADD THIS
```

5. **Test**:
```bash
# Create comment on post 1
curl -X POST http://localhost:8000/comments/1 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Great post!"}'

# Get all comments on post 1
curl -X GET http://localhost:8000/comments/1 \
  -H "Authorization: Bearer TOKEN"
```

**What You'll Learn**: New models, relationships, cascading deletes, router isolation

### Exercise 3.2: Add Follow System
**Goal**: Users can follow other users

1. **Add Follow Model**:
```python
class Follow(Base):
    __tablename__ = "follows"
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
```

2. **Create routers/follow.py**:
```python
@router.post("/{user_id}/follow")
def follow_user(user_id: int, db: Session = Depends(get_db), 
                current_user: models.User = Depends(oauth2.get_current_user)):
    
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    
    # Check if user exists
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if already following
    already_follows = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == user_id
    ).first()
    
    if already_follows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already following")
    
    # Create follow
    new_follow = models.Follow(follower_id=current_user.id, following_id=user_id)
    db.add(new_follow)
    db.commit()
    
    return {"message": f"Now following user {user_id}"}
```

**What You'll Learn**: Self-referential relationships, composite keys, business logic validation

---

## Level 4: Advanced Queries

### Exercise 4.1: Pagination
**Goal**: Return paginated results

```python
from typing import Optional

@router.get("/", response_model=Dict)
def get_posts_paginated(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = ""
):
    skip = (page - 1) * per_page
    
    # Query with count
    query = db.query(models.Post).filter(models.Post.title.contains(search))
    total_count = query.count()
    
    posts = query.limit(per_page).offset(skip).all()
    
    return {
        "data": posts,
        "page": page,
        "per_page": per_page,
        "total": total_count,
        "pages": (total_count + per_page - 1) // per_page
    }
```

**Test**:
```bash
curl "http://localhost:8000/posts/?page=1&per_page=5" \
  -H "Authorization: Bearer TOKEN"
```

### Exercise 4.2: Search and Filter
**Goal**: Search across multiple fields

```python
@router.get("/search/")
def search_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    q: str = "",  # Query string
    published: Optional[bool] = None,
    owner_id: Optional[int] = None
):
    query = db.query(models.Post)
    
    if q:
        query = query.filter(
            or_(
                models.Post.title.ilike(f"%{q}%"),
                models.Post.content.ilike(f"%{q}%")
            )
        )
    
    if published is not None:
        query = query.filter(models.Post.published == published)
    
    if owner_id:
        query = query.filter(models.Post.owner_id == owner_id)
    
    return query.limit(10).all()
```

**Test**:
```bash
curl "http://localhost:8000/posts/search/?q=python&published=true&owner_id=1" \
  -H "Authorization: Bearer TOKEN"
```

**What You'll Learn**: Complex queries, OR conditions, ILIKE for case-insensitive search

### Exercise 4.3: User Feed (Posts from Followed Users)
**Goal**: Show feed of only posts from users you follow

```python
@router.get("/feed/")
def get_user_feed(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    limit: int = 10
):
    # Get list of users current_user is following
    following = db.query(models.Follow.following_id).filter(
        models.Follow.follower_id == current_user.id
    ).all()
    
    following_ids = [f[0] for f in following]
    
    if not following_ids:
        return []
    
    # Get posts from those users
    posts = db.query(models.Post).filter(
        models.Post.owner_id.in_(following_ids)
    ).order_by(models.Post.created_at.desc()).limit(limit).all()
    
    return posts
```

**What You'll Learn**: Subqueries, IN operator, relationships in filtering

---

## Level 5: Error Handling & Validation

### Exercise 5.1: Custom Exception Handler
**Goal**: Better error messages

```python
# In main.py, add to app:
from fastapi import Request
from fastapi.responses import JSONResponse

class PostNotFoundError(Exception):
    def __init__(self, post_id: int):
        self.post_id = post_id

@app.exception_handler(PostNotFoundError)
async def post_not_found_handler(request: Request, exc: PostNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "post_not_found",
            "message": f"Post with id {exc.post_id} does not exist",
            "post_id": exc.post_id
        }
    )

# Usage in routers:
@router.get("/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise PostNotFoundError(id)
    return post
```

### Exercise 5.2: Input Validation
**Goal**: Better Pydantic schemas

```python
from pydantic import validator, constr

class PostCreate(BaseModel):
    title: constr(min_length=5, max_length=200)  # 5-200 chars
    content: constr(min_length=10)  # At least 10 chars
    published: bool = True
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)  # At least 8 chars
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

**What You'll Learn**: Input validation, proper error messages, security

---

## Progressive Testing Checklist

```
Level 1: ✅ Logging & Timing
  ├─ Add print statements to all routers
  └─ Measure query performance

Level 2: ✅ Extend Existing Models  
  ├─ Add profile_picture_url to User
  ├─ Add updated_at, update_count to Post
  └─ Test with curl

Level 3: ✅ Add New Models
  ├─ Comments system
  ├─ Follow system
  └─ Update Post model to show comment count

Level 4: ✅ Advanced Queries
  ├─ Pagination working
  ├─ Search and filter working
  ├─ User feed showing only followed users' posts
  └─ All with proper type hints

Level 5: ✅ Production Ready
  ├─ Custom error handlers
  ├─ Input validation with good UX
  ├─ Permission checks on all endpoints
  └─ Test coverage > 80%
```

---

## Testing Commands for Each Exercise

```bash
# 1.1 Check logs in terminal while running
python -m uvicorn app.main:app --reload
# Send requests and watch terminal output

# 2.1 Test user with picture
curl -X POST http://localhost:8000/users/ -H "Content-Type: application/json" \
  -d '{"email":"pic@test.com","password":"test123","profile_picture_url":"https://..."}'

# 3.1 Create comment
curl -X POST http://localhost:8000/comments/1 -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" -d '{"content":"Great!"}'

# 3.2 Follow user
curl -X POST http://localhost:8000/users/2/follow -H "Authorization: Bearer TOKEN"

# 4.1 Paginated posts
curl "http://localhost:8000/posts/?page=2&per_page=5" -H "Authorization: Bearer TOKEN"

# 4.2 Search
curl "http://localhost:8000/posts/search/?q=python" -H "Authorization: Bearer TOKEN"

# 4.3 User feed
curl http://localhost:8000/posts/feed/ -H "Authorization: Bearer TOKEN"
```

Good luck! Try one exercise per day 🚀
