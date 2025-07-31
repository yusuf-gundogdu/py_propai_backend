from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

# Production için pool ayarları - SQLite için düzeltildi
if DATABASE_URL and "sqlite" in DATABASE_URL:
    # SQLite için basit ayarlar
    engine = create_async_engine(
        DATABASE_URL,
        echo=bool(os.getenv("DEBUG", False))
    )
else:
    # PostgreSQL/MySQL için pool ayarları
    engine = create_async_engine(
        DATABASE_URL,
        echo=bool(os.getenv("DEBUG", False)),
        poolclass=NullPool if os.getenv("TESTING") else None,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()