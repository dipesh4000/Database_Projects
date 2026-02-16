# FastAPI CRUD App Flow Guide

## 📊 Project Architecture Overview

Your project is a **FastAPI Social Media App** with:
- **Authentication**: User login/signup with JWT tokens
- **Users**: Create user accounts with hashed passwords
- **Posts**: Create, read, update, delete posts (CRUD operations)
- **Votes**: Like/upvote system for posts

---

## 🗂️ Project Structure

```
app/
├── main.py           → App entry point, routes initialization
├── database.py       → PostgreSQL connection setup with SQLAlchemy
├── models.py         → Database models (User, Post, Vote)
├── schemas.py        → Pydantic models (data validation)
├── oauth2.py         → JWT token creation & verification
├── utils.py          → Password hashing functions
└── routers/
    ├── auth.py       → Login endpoint
    ├── user.py       → User creation & retrieval
    └── post.py       → Post CRUD & voting
```

---

## 🔐 Authentication Flow

```
1. USER SIGNUP
   └─→ POST /users/
       ├─ Receive: email, password (plain)
       ├─ Hash password using bcrypt
       ├─ Save to database
       └─ Return: user id, email, created_at

2. USER LOGIN
   └─→ POST /login
       ├─ Receive: email (as username), password
       ├─ Query DB for user by email
       ├─ Verify plain password against hashed password
       ├─ Create JWT token with user_id
       └─ Return: access_token, token_type: "bearer"

3. PROTECTED ENDPOINT ACCESS
   └─→ GET /posts/ (with Authorization header "Bearer TOKEN")
       ├─ Extract token from header
       ├─ Decode JWT to get user_id
       ├─ Query DB to fetch User object
       ├─ Allow access if user exists
       └─ Return: posts data
```

---

## 🚀 Complete Request-Response Flow

### **SIGNUP FLOW**
```
Client Request:
POST /users/
{
  "email": "john@example.com",
  "password": "mypassword123"
}
    ↓
app/routers/user.py → create_user()
    ├─ utils.hash() → bcrypt hashes password
    ├─ models.User() → creates User instance
    ├─ db.add() & db.commit() → saves to PostgreSQL
    └─ db.refresh() → retrieves created user
    ↓
Response:
{
  "id": 1,
  "email": "john@example.com",
  "created_at": "2026-02-16T22:52:03.074476+05:30"
}
```

### **LOGIN FLOW**
```
Client Request:
POST /login
(form-data: username=john@example.com, password=mypassword123)
    ↓
app/routers/auth.py → login()
    ├─ OAuth2PasswordRequestForm captures username & password
    ├─ models.User query by email
    ├─ utils.verify() checks: plain password vs stored hashed password
    ├─ oauth2.create_access_token() creates JWT with user_id
    └─ Token expires in 30 minutes
    ↓
Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### **PROTECTED ENDPOINT FLOW (Create Post)**
```
Client Request:
POST /posts/
Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Body: {
  "title": "My First Post",
  "content": "This is awesome",
  "published": true
}
    ↓
app/routers/post.py → create_posts()
    ├─ oauth2.get_current_user() dependency is triggered
    │   ├─ Extracts token from Authorization header
    │   ├─ jwt.decode() verifies token signature
    │   ├─ Extracts user_id from token payload
    │   ├─ Queries database for User by id
    │   └─ Returns User object if valid
    │
    ├─ current_user = User(id=1, email="john@example.com")
    ├─ models.Post(owner_id=current_user.id, title=..., content=...)
    ├─ db.add() & db.commit()
    └─ db.refresh() to get created post with id
    ↓
Response:
{
  "id": 5,
  "title": "My First Post",
  "content": "This is awesome",
  "published": true,
  "created_at": "2026-02-16T23:00:00.000000+05:30",
  "owner_id": 1,
  "owner": {
    "id": 1,
    "email": "john@example.com",
    "created_at": "2026-02-16T22:52:03.074476+05:30"
  }
}
```

### **GET POSTS WITH VOTES**
```
Client Request:
GET /posts/?limit=10&skip=0&search=""
Headers: Authorization: Bearer token...
    ↓
app/routers/post.py → get_posts()
    ├─ oauth2.get_current_user() validates token
    ├─ Complex SQL Query:
    │   ├─ Query all Posts
    │   ├─ LEFT JOIN with Votes table (counts votes per post)
    │   ├─ GROUP BY post.id
    │   ├─ FILTER by title search
    │   ├─ LIMIT 10, SKIP 0
    │   └─ Return: [(Post, votes_count), ...]
    │
    └─ Map to PostOut schema with vote counts
    ↓
Response: Array of Posts with vote counts
[
  {
    "Post": { ...post details... },
    "votes": 3
  }
]
```

---

## 🔑 Key Components Explained

### **1. main.py** - Entry Point
- Initializes FastAPI app
- Creates all database tables: `models.Base.metadata.create_all()`
- Includes routers (auth, user, post)

### **2. database.py** - Database Connection
- PostgreSQL connection string
- SQLAlchemy engine and session
- `get_db()` dependency provides DB session to endpoints

### **3. models.py** - ORM Models
```python
User: id, email, password, created_at
Post: id, title, content, published, created_at, owner_id (FK → User)
Vote: user_id (FK), post_id (FK) - composite primary key
```

### **4. schemas.py** - Data Validation
- Pydantic models for request/response validation
- `UserCreate`: email + password (input only, no id)
- `UserOut`: id + email + created_at (output only, no password)
- `TokenData`: id extracted from JWT token

### **5. oauth2.py** - JWT Authentication
- `create_access_token()`: Signs user_id into JWT token
- `verify_access_token()`: Decodes JWT and validates signature
- `get_current_user()`: FastAPI dependency that protects endpoints

### **6. utils.py** - Password Security
- `hash()`: Converts plain password to bcrypt hash
- `verify()`: Compares plain password with stored hash (returns True/False)

### **7. routers/** - Endpoints

**auth.py**: 
- POST /login → returns JWT token

**user.py**:
- POST /users/ → create user (signup)
- GET /users/{id} → get user details

**post.py**:
- GET /posts/ → list all posts (protected)
- POST /posts/ → create post (protected)
- GET /posts/{id} → get single post (protected)
- PUT /posts/{id} → update post (protected)
- DELETE /posts/{id} → delete post (protected)

---

## 💡 How Dependency Injection Works

```python
# Without CURRENT_USER dependency:
@router.post("/")
def create_post(post: PostCreate, db: Session):
    # Would need to manually handle auth in function body
    pass

# With oauth2.get_current_user dependency (BETTER):
@router.post("/")
def create_post(
    post: PostCreate, 
    db: Session = Depends(get_db),                      # Gets DB session
    current_user: User = Depends(oauth2.get_current_user) # Validates token
):
    # FastAPI automatically:
    # 1. Calls get_db() → returns DB session
    # 2. Calls get_current_user(token, db) → validates token
    # 3. Returns User object if valid
    # 4. Calls create_post() with all dependencies resolved
```

---

## 🎯 Where to Learn & Practice

### **Learn FastAPI**
1. **Official Docs** (Best): https://fastapi.tiangolo.com/
2. **Video Tutorials**:
   - Mosh Hamedani on YouTube (2-4 hours)
   - Tech with Tim FastAPI Series
3. **Interactive Learning**:
   - https://github.com/tiangolo/full-stack-fastapi-postgresql (Official full project template)
   - https://github.com/tiangolo/fastapi/tree/master/docs/en/docs (Learn from examples)

### **Learn SQLAlchemy (ORM)**
1. **Official Docs**: https://docs.sqlalchemy.org/
2. **Key Concepts**:
   - Models (declare_base, Column, relationships)
   - Relationships (ForeignKey, relationship())
   - Sessions (query, add, commit, filter)
3. **Practice**: Create relationships (one-to-many, many-to-many)

### **Learn JWT & Security**
1. **JWT Basics**: https://jwt.io/introduction
2. **FastAPI Security**: https://fastapi.tiangolo.com/advanced/security/
3. **Topics to Study**:
   - CORS (cross-origin requests)
   - API Key authentication
   - OAuth2 flows
   - Password reset tokens

### **Learn PostgreSQL**
1. **SQL Practice**: https://www.codecademy.com/learn/learn-sql
2. **PostgreSQL Specific**: https://www.postgresql.org/docs/
3. **Key Topics**:
   - JOINs (INNER, LEFT, RIGHT)
   - Aggregations (COUNT, SUM, GROUP BY)
   - Indexes for performance
   - Transactions & ACID

### **Practice Projects (Difficulty Order)**

**Beginner:**
1. ✅ Your current project (CRUD Blog) 
2. Todo App with users
3. Simple Chat API

**Intermediate:**
4. **Twitter Clone** (Posts, Likes, Follows, Feed)
   - Add Follow system (many-to-many relationships)
   - Create your own feed algorithm
   - Add notifications
   
5. **E-commerce API** (Products, Orders, Payments)
   - Shopping cart
   - Order processing
   - Integration with payment API (Stripe)

6. **Social Media** (Instagram-like)
   - Comments on posts
   - Direct messaging
   - Search functionality

**Advanced:**
7. **Real-time Chat** (WebSockets)
8. **Full Search System** (Elasticsearch)
9. **Batch Processing** (Celery + Redis)

---

## 🧪 Practice Exercises for Your Project

### Exercise 1: Add Commenting
- Create Comment model (user_id, post_id, content, created_at)
- Add endpoints: POST /posts/{id}/comments, GET /posts/{id}/comments
- Model relationships: User → Comments, Post → Comments

### Exercise 2: Add Following System
- Create Follow model (follower_id, following_id)
- Endpoint: POST /users/{id}/follow
- Endpoint: GET /users/{id}/followers
- Show only posts from followed users in feed

### Exercise 3: Add Search & Filter
- GET /posts/?search=python&published=true&limit=10
- GET /users/?search=john&limit=20

### Exercise 4: Add Pagination
- Implement cursor-based pagination for large datasets
- Add total_count in response

### Exercise 5: Add Error Handling
- Custom exception classes
- Better error messages
- Request validation error handling

---

## 📚 Recommended Learning Path

```
Week 1: Master Your Current Project
├─ Understand every line of code
├─ Add logging to see execution flow
├─ Write tests for each endpoint
└─ Try API requests in different ways (curl, httpie, Python)

Week 2: Add Features
├─ Add comments feature (Exercise 1)
├─ Add search/filter (Exercise 3)
└─ Deploy to Heroku/Railway

Week 3: Master Relationships
├─ Study SQLAlchemy relationships
├─ Create Follow system (Exercise 2)
└─ Understand query optimization

Week 4: Advanced Topics
├─ Pagination & filtering
├─ Caching (Redis)
├─ Background tasks (Celery)
└─ Full-text search

Week 5: Build New Project
├─ Start Twitter clone
├─ Apply everything learned
└─ Deploy to production
```

---

## 🚀 Quick Commands to Test

```bash
# Signup new user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"

# Create post (replace TOKEN with your access_token)
curl -X POST http://localhost:8000/posts/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Post","content":"Content","published":true}'

# Get all posts
curl -X GET http://localhost:8000/posts/ \
  -H "Authorization: Bearer TOKEN"
```

---

## 💻 IDE Tips

In VS Code:
- Use FastAPI extension for better IntelliSense
- Use SQLAlchemy extension
- Use REST Client extension to make HTTP requests in editor

Files to explore:
- [app/oauth2.py](app/oauth2.py) - Authorization logic
- [app/routers/post.py](app/routers/post.py) - Complex queries with JOINs
- [app/models.py](app/models.py) - Database relationships

Good luck! 🚀
