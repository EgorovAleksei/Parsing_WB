import datetime
import json
import asyncio
from datetime import date, timedelta

from sqlalchemy import column, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from database.engine import session_maker, engine
from database.models import Brand, Category, Options, Product


async def orm_add_categories(obj: Category):
    async with session_maker() as session:
        query = select(Category).where(Category.id == obj.id)
        result = await session.execute(query)
        if result.first() is None:
            session.add(obj)
            await session.commit()


async def orm_update_categories(obj: Category):
    async with session_maker(expire_on_commit=False) as session:
        session.add(obj)
        await session.commit()


async def orm_get_categories(cat):
    async with session_maker(expire_on_commit=False) as session:
        query = select(cat)
        result = await session.execute(query)
        return result.scalars().all()


async def orm_get_brands():
    async with session_maker(expire_on_commit=False) as session:
        query = select(Brand.id)
        result = await session.execute(query)
        return result.scalars().all()


async def orm_add_brand(obj: Brand):
    async with session_maker() as session:
        query = select(Brand).where(Brand.id == obj.id)
        result = await session.execute(query)
        if result.first() is None:
            try:
                session.add(obj)
                session.expire_all()
                await session.commit()
            except AttributeError as e:
                print(f"{e} ошибка. такой {obj.id}, {obj.name} уже существует")


async def orm_add_product(obj: Product):
    async with session_maker() as session:
        query = select(Product).where(Product.id == obj.id)
        result = await session.execute(query)
        if result.first() is None:
            session.add(obj)
            await session.commit()


async def orm_get_products():
    async with session_maker() as session:
        # query = select(Product).where(Product.updated < date.today() - timedelta(days=3)).limit(10)
        product_date = datetime.datetime.strptime("2024-07-20", "%Y-%m-%d")
        query = select(Product).filter(Product.updated < product_date).limit(100)

        result = await session.execute(query)
        return result.scalars()


async def orm_update_product(data):
    async with session_maker(expire_on_commit=False) as session:
        query = (
            update(Product)
            .where(Product.id == data["id"])
            .values(
                updated=data["updated"],
                pics=data["pics"],
            )
        )
        await session.execute(query)
        await session.commit()


async def orm_update_productwb(obj, product):
    async with session_maker(expire_on_commit=False) as session:
        session.add(obj)
        session.add(product)
        await session.commit()


async def orm_update_categorytwb(obj):
    async with session_maker(expire_on_commit=False) as session:
        session.add(obj)
        await session.commit()


async def orm_get_brands_all():
    async with session_maker(expire_on_commit=False) as session:
        query = select(Brand)
        result = await session.execute(query)
        return result.scalars().all()


async def orm_add_options(obj: Options):
    async with session_maker() as session:
        session.add(obj)
        await session.commit()


# async def proba():
#     categories = await orm_get_categories()
#     for cat in categories:
#         if cat.id == 1:
#             print(cat.id)
#             await orm_update_categories(cat)
#             break
#
# asyncio.run(proba())
