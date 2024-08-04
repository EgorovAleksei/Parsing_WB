import asyncio
import os


from dotenv import find_dotenv, load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from database.models import Base, Product

load_dotenv(find_dotenv('../.env'))

engine = create_async_engine(os.getenv('DB_URL'), echo=False)

#session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
session_maker = async_sessionmaker(bind=engine)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        ...
        #await conn.run_sync(Base.metadata.drop_all)
        #await conn.run_sync(Base.metadata.tables['options'].drop)
        #await conn.run_sync(Base.metadata.tables['product'].drop)
        #await conn.run_sync(Base.metadata.tables['brand'].drop)

