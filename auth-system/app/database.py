from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# ─── Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,          # auto-reconnect on stale connections
)

# ─── Session Factory ─────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ─── Base Model ──────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Dependency ──────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Startup: create all tables ──────────────────────────────────────────────
async def init_db():
    from app.models import user, role  # noqa: F401 — ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
