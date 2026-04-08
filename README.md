## Why I Built This

I built this project to deeply understand how real-world authentication systems work beyond basic login/signup features.

Instead of just implementing JWT, I focused on:
- Secure password storage using bcrypt
- Role-Based Access Control (RBAC) with permissions
- Token invalidation using Redis (logout handling)
- Async backend architecture using FastAPI

During development, I faced real-world issues like:
- Python version compatibility (3.13 → fixed using 3.11)
- Async SQLAlchemy errors (MissingGreenlet)
- Database connection failures and debugging

This project helped me understand how production-level backend systems are designed and debugged.


# Authentication & Authorization System

A production-grade backend auth system built with **FastAPI**, **PostgreSQL**, **Redis**, and **JWT**.

---

## 🏗️ Tech Stack

| Layer          | Technology              |
|----------------|-------------------------|
| Language       | Python 3.10+            |
| Framework      | FastAPI                 |
| Database       | PostgreSQL              |
| ORM            | SQLAlchemy (async)      |
| Auth           | JWT (python-jose)       |
| Cache/Session  | Redis                   |
| Hashing        | bcrypt (passlib)        |
| Server         | Uvicorn                 |
| Config         | python-dotenv           |

---

## 📦 Project Structure

```
auth-system/
├── app/
│   ├── main.py            # FastAPI app, routers, lifespan
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py        # Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py        # User model
│   │   └── role.py        # Role, Permission, M:N tables
│   ├── schemas/
│   │   ├── user.py        # Pydantic request/response schemas
│   │   └── role.py        # Role schemas
│   ├── routes/
│   │   ├── auth.py        # /auth/register, /auth/login, /auth/logout
│   │   ├── users.py       # /users/me, /users/
│   │   └── roles.py       # /roles/, /roles/assign
│   ├── services/
│   │   ├── user_service.py
│   │   └── role_service.py
│   ├── core/
│   │   ├── security.py    # bcrypt + JWT logic
│   │   ├── redis_client.py# Redis helpers (cache, blacklist)
│   │   └── dependencies.py# FastAPI DI: get_current_user, require_role
│   └── utils/
│       └── seeder.py      # Seed default roles + permissions
├── requirements.txt
├── .env
└── README.md
```

---

## 🚀 Setup & Run

### 1. Clone and install

```bash
git clone <repo>
cd auth-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env .env.local
# Edit .env with your DB + Redis credentials
```

### 3. Start PostgreSQL + Redis

```bash
# Using Docker (recommended)
docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
docker run -d --name redis -p 6379:6379 redis:7
```

### 4. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

---

## 🔌 API Endpoints

### Auth
| Method | Endpoint         | Auth     | Description             |
|--------|-----------------|----------|-------------------------|
| POST   | /auth/register  | Public   | Register new user       |
| POST   | /auth/login     | Public   | Login, returns JWT      |
| POST   | /auth/logout    | Bearer   | Blacklist token         |

### Users
| Method | Endpoint  | Auth          | Description             |
|--------|-----------|---------------|-------------------------|
| GET    | /users/me | Bearer        | Get own profile         |
| GET    | /users/   | Bearer(admin) | List all users          |

### Roles
| Method | Endpoint       | Auth          | Description             |
|--------|----------------|---------------|-------------------------|
| POST   | /roles/        | Bearer(admin) | Create role             |
| POST   | /roles/assign  | Bearer(admin) | Assign role to user     |

---

## 🗄️ Database Schema

```
users              roles              permissions
─────────          ─────────          ───────────────
id (PK)            id (PK)            id (PK)
email (unique)     name (unique)      name (unique)
password_hash
is_active          user_roles (M:N)   role_permissions (M:N)
created_at         ───────────────    ─────────────────────
                   user_id (FK)       role_id (FK)
                   role_id (FK)       permission_id (FK)
```

---

## 🔑 JWT Structure

```json
{
  "user_id": 1,
  "role": "admin",
  "exp": 1712345678
}
```

---

## ⚡ Redis Keys

| Key Pattern             | Purpose                        | TTL         |
|------------------------|--------------------------------|-------------|
| `token:user:{id}`      | Cached JWT per user            | 30 min      |
| `blacklist:{token}`    | Invalidated tokens (logout)    | Token expiry|

---

## 🛡️ Security Features

- ✅ bcrypt password hashing (cost factor 12)
- ✅ JWT with expiry
- ✅ Token blacklisting on logout
- ✅ Pydantic input validation
- ✅ Role-Based Access Control (RBAC)
- ✅ Permission-Based checks
- ✅ Async DB (no blocking I/O)
- ✅ DB connection pooling

---

## ❗ Edge Cases Handled

| Case                       | Handling                                      |
|---------------------------|-----------------------------------------------|
| Token expired             | JWTError → 401 Unauthorized                   |
| Invalid token             | JWTError → 401 Unauthorized                   |
| Token blacklisted         | Redis check → 401 Unauthorized                |
| User deleted after login  | DB lookup returns None → 404                  |
| Role changed after login  | Fresh DB lookup on every request              |
| Duplicate email signup    | 409 Conflict                                  |
| Inactive account          | 403 Forbidden                                 |
| Wrong role for endpoint   | 403 Forbidden                                 |

---

## 📈 Performance Optimizations

- Async FastAPI endpoints (non-blocking)
- Redis caches tokens → avoids repeated DB reads
- `email` column indexed in PostgreSQL
- DB connection pooling (pool_size=10, max_overflow=20)
- `selectinload` for eager loading roles/permissions (avoids N+1)
