import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    url = "postgresql+asyncpg://cliniscribe:cliniscribe@localhost:5432/cliniscribe"
    engine = create_async_engine(url)
    try:
        async with engine.connect():
            print("EXPLICIT URL CONNECTION: SUCCESS")
    finally:
        await engine.dispose()

asyncio.run(main())
