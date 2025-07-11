import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.account import Account

async def create_test_account():
    async with async_session() as session:
        # Test hesabı oluştur
        test_account = Account(
            udid="test-udid-123",
            platform="IOS",
            credit=1000,
            level=4
        )
        
        session.add(test_account)
        await session.commit()
        print("✅ Test hesabı oluşturuldu: test-udid-123")

if __name__ == "__main__":
    asyncio.run(create_test_account()) 