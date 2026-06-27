import asyncio
import sys
import os

# Add src to python path so imports work without installing as a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from models.database import engine, Base
import uvicorn
from api.main import app

async def init_db():
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await init_db()
    
    # Run FastAPI server
    config = uvicorn.Config("app:app", host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
