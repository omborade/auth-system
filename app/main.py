from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.core.redis_client import get_redis, close_redis
from app.utils.seeder import seed_roles_and_permissions
from app.routes import auth, users, roles


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀  Starting {settings.APP_NAME} [{settings.APP_ENV}]")
    await init_db()                      # create tables
    # await seed_roles_and_permissions()   # seed default roles/permissions
    await get_redis()                    # warm Redis connection
    print("✅  Database, Redis ready")
    yield
    # Shutdown
    await close_redis()
    print("🛑  Shutdown complete")


# ─── App Instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## 🔐 Authentication & Authorization System

A production-grade auth backend built with:
- **FastAPI** (async)
- **PostgreSQL** + **SQLAlchemy** (ORM)
- **JWT** (stateless tokens)
- **Redis** (caching + blacklist)
- **bcrypt** (password hashing)
- **RBAC** (Role-Based Access Control)

### Roles
| Role  | Permissions         |
|-------|---------------------|
| admin | read, write, delete |
| user  | read                |

### Quick Start
1. `POST /auth/register` → create account
2. `POST /auth/login` → get JWT token
3. Use `Authorization: Bearer <token>` on protected routes
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse({"status": "ok", "app": settings.APP_NAME})


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "redoc": "/redoc",
    }
