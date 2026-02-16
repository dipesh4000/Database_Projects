# Quick Reference: File Interactions

## How Files Talk to Each Other

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│        (App Entry Point - Includes all routers)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌────────┐         ┌────────┐        ┌────────┐
   │routers/│         │routers/│        │routers/│
   │auth.py │         │user.py │        │post.py │
   └───┬────┘         └───┬────┘        └───┬────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ┌────────┐    ┌──────────┐    ┌─────────────┐
    │oauth2  │    │database  │    │models       │
    │(tokens)│◄───┤(sessions)│◄───┤(ORM models) │
    └────────┘    └──────────┘    └─────┬───────┘
        │              │                  │
        │              ▼                  │
        │         ┌──────────┐           │
        │         │PostgreSQL│◄──────────┘
        │         │ Database │
        │         └──────────┘
        │
        ▼
    ┌──────────┐
    │schemas   │
    │(validation)
    └──────────┘
        │
        ▼
    ┌──────────┐
    │utils     │
    │(bcrypt)  │
    └──────────┘
```

---

## File-by-File Dependencies

### **main.py**
```
Imports: models, schemas, routers
Does: Initializes app, creates DB tables, registers routers
Used by: uvicorn when server starts
```

### **routers/auth.py**
```
Imports: models, schemas, oauth2, utils, database
Does: Handles login (POST /login)
Process: 
  1. Get username/password from form
  2. Query DB for user
  3. Verify password with utils.verify()
  4. Create JWT with oauth2.create_access_token()
  5. Return token
```

### **routers/user.py**
```
Imports: models, schemas, utils, database
Does: Handles signup and get user
Process (Signup):
  1. Get email/password from request
  2. Hash password with utils.hash()
  3. Create User model instance
  4. Save to DB
  5. Return user (no password)
```

### **routers/post.py**
```
Imports: models, schemas, oauth2, database
Does: CRUD operations on posts
Process (Create Post):
  1. oauth2.get_current_user() validates token, returns User
  2. Create Post model with owner_id from current_user
  3. Save to DB
Process (Get Posts):
  1. oauth2.get_current_user() validates token
  2. Complex SQL: SELECT posts with vote counts
  3. Return posts sorted by votes
Usage: All endpoints require oauth2.get_current_user dependency
```

### **oauth2.py**
```
Imports: schemas, models, database
Provides: 
  - create_access_token(user_id) → JWT string
  - verify_access_token(token) → TokenData
  - get_current_user(token, db) → User object
Usage: Dependency for all protected endpoints
Key: get_current_user validates token + queries DB for current user
```

### **models.py**
```
Imports: sqlalchemy, database.Base
Models:
  - User: id, email, password, created_at
  - Post: id, title, content, owner_id (FK), published, created_at
  - Vote: user_id (FK), post_id (FK)
Relationships: User → Post (one-to-many), Post → Vote
Used by: ORM queries in routers
```

### **schemas.py**
```
Imports: pydantic, EmailStr
Schemas:
  - UserCreate: input validation (email, password)
  - UserOut: output only (id, email, created_at) - no password!
  - PostCreate, Post, PostOut: post validation
  - Token: login response (token, token_type)
  - TokenData: internal (id extracted from JWT)
Usage: @router.post(response_model=schemas.UserOut)
Benefit: Automatic validation + hides sensitive data
```

### **database.py**
```
Imports: sqlalchemy, Base from models
Does:
  - Creates PostgreSQL connection string
  - Creates SQLAlchemy engine
  - Creates SessionLocal (session factory)
  - Provides get_db() dependency
get_db() function: yields session for query, closes after request
Used by: Every endpoint that needs DB access
```

### **utils.py**
```
Imports: passlib/CryptContext
Functions:
  - hash(password: str) → hashed string
  - verify(plain_password, hashed_password) → bool
Used by: 
  - user.py: hash during signup
  - auth.py: verify during login
Benefit: Passwords never stored as plain text
```

---

## Request Flow (Example: Create Post)

```
1. Client sends POST /posts/
   Headers: Authorization: Bearer eyJhb...
   Body: {"title": "test", "content": "content", "published": true}

2. post.py: create_posts() is called
   
3. FastAPI resolves dependencies:
   a) Depends(get_db) → database.py:get_db() 
      → Creates SessionLocal() → PostgreSQL connection
      → Returns 'db' session
   
   b) Depends(oauth2.get_current_user) → oauth2.py:get_current_user()
      → Extracts token from header
      → oauth2_scheme (OAuth2PasswordBearer) extracts token string
      → Calls verify_access_token(token, db)
      → jwt.decode() verifies signature
      → Extracts user_id = 5 from token payload
      → db.query(models.User).filter(id == 5).first()
      → Queries DB → returns User object
      → Returns User(id=5, email="john@example.com", ...)

4. post.py: create_posts() executes with:
   - post = PostCreate(title="test", content="content", published=true)
   - db = Session object connected to PostgreSQL
   - current_user = User(id=5, email="john@example.com", ...)

5. creates: models.Post(owner_id=5, title="test", ...)
   → db.add() → db.commit() → db.refresh()
   → INSERT INTO posts VALUES (...)

6. Returns: Post(id=1, owner_id=5, title="test", ...)
   → Response follows schemas.Post format
   → Automatic validation before returning

7. Client receives JSON response with post data
```

---

## Circular Import Prevention

Why we don't import like this:
```
# ❌ BAD - Circular import
main.py imports routers/post.py
routers/post.py imports models
models imports schemas
schemas imports models ← CIRCULAR!
```

How it's organized instead:
```
# ✅ GOOD - No circular imports
models.py imports: database.Base (just ORM)
schemas.py imports: pydantic (just validation)
oauth2.py imports: schemas (schemas doesn't import oauth2)
routers/post.py imports: models, schemas, oauth2 (no back edges)
main.py imports: everything (at the top)
```

---

## Key Concepts

### **Dependency Injection**
```python
# Instead of:
def get_posts():
    db = get_db()
    user = get_current_user()
    # do something

# FastAPI does this: (much cleaner)
def get_posts(db = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # FastAPI automatically calls dependencies
    # and passes results to function
```

### **Response Models**
```python
@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(email=user.email, password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user  # FastAPI formats this as UserOut schema
    # → Always returns: id, email, created_at
    # → Never returns: password
```

### **Relationship Queries**
```python
# One-to-many: User has many Posts
user = db.query(models.User).first()
user.posts  # All posts by this user (because relationship defined)

# Foreign keys: Post belongs to User
post = db.query(models.Post).first()
post.owner  # The User object who owns this post
```

### **JOIN Queries**
```python
# Get posts with vote counts
posts = db.query(
    models.Post,
    func.count(models.Vote.post_id).label("votes")
).join(
    models.Vote,
    models.Vote.post_id == models.Post.id,
    isouter=True  # LEFT JOIN
).group_by(
    models.Post.id
).all()

# Returns: [(Post object, 3), (Post object, 0), ...]
```

---

## Testing Each Component Independently

```bash
# 1. Test database connection (models.py + database.py)
python -c "from app.database import SessionLocal; db = SessionLocal(); print('DB OK')"

# 2. Test password hashing (utils.py)
python -c "from app.utils import hash, verify; h = hash('test'); print(verify('test', h))"

# 3. Test JWT (oauth2.py)
python -c "from app.oauth2 import create_access_token; t = create_access_token({'user_id': 1}); print(t)"

# 4. Test endpoint with curl/httpie (all files together)
python test_auth_detailed.py
```
