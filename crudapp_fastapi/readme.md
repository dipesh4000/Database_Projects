# FastAPI CRUD App

A RESTful API built with FastAPI for managing posts with user authentication and authorization.

## Features

- ✅ User registration and authentication (JWT)
- ✅ CRUD operations for posts
- ✅ Post voting system
- ✅ User ownership validation
- ✅ PostgreSQL database integration
- ✅ SQLAlchemy ORM
- ✅ Password hashing

## Tech Stack

- **FastAPI** - Modern web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **OAuth2** - Authentication
- **JWT** - Token-based auth

## Project Structure

```
crudapp_fastapi/
├── app/
│   ├── routers/
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── post.py      # Post CRUD endpoints
│   │   └── user.py      # User endpoints
│   ├── __init__.py
│   ├── database.py      # Database connection
│   ├── main.py          # App entry point
│   ├── models.py        # SQLAlchemy models
│   ├── oauth2.py        # JWT authentication
│   ├── schemas.py       # Pydantic schemas
│   └── utils.py         # Helper functions
└── requirements.txt
```

## Prerequisites

- Python 3.7+
- PostgreSQL

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crudapp_fastapi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```sql
CREATE DATABASE crud;
```

4. Update database credentials in `app/database.py`:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://<user>:<password>@localhost:5432/crud"
```

## Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /login` - User login (returns JWT token)

### Users
- `POST /users/` - Create new user
- `GET /users/{id}` - Get user by ID

### Posts
- `GET /posts/` - Get all posts (with pagination & search)
- `POST /posts/` - Create new post (requires auth)
- `GET /posts/{id}` - Get post by ID
- `PUT /posts/{id}` - Update post (requires auth & ownership)
- `DELETE /posts/{id}` - Delete post (requires auth & ownership)

## Authentication

The API uses JWT tokens for authentication. To access protected endpoints:

1. Register a user via `POST /users/`
2. Login via `POST /login` to get access token
3. Include token in requests: `Authorization: Bearer <token>`

## Database Models

### User
- id (Primary Key)
- email (Unique)
- password (Hashed)
- created_at

### Post
- id (Primary Key)
- title
- content
- published
- created_at
- owner_id (Foreign Key)

### Vote
- user_id (Foreign Key)
- post_id (Foreign Key)

## License

MIT
