import asyncio
from app.database import get_db
from app.models.generatemodelitem import GenerateModelItem

async def create_test_model():
    async for db in get_db():
        # Test model oluştur
        test_model = GenerateModelItem(
            name="pixarStyleModel_v10.safetensors",
            credit=10,  # 10 kredi
            level=0,    # Seviye 0 (ücretsiz)
            priority=1  # Öncelik 1
        )
        
        db.add(test_model)
        await db.commit()
        print(f"Test model created: Name={test_model.name}, Credit={test_model.credit}, Level={test_model.level}")
        break

if __name__ == "__main__":
    asyncio.run(create_test_model()) 