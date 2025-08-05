from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

# Production için pool ayarları
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQLAlchemy loglarını tamamen kapat - performans için
    poolclass=NullPool if os.getenv("TESTING") else None,  # Testler için pool kapatma
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  # Bağlantıların sağlığını kontrol et
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