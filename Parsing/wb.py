import datetime
from sqlalchemy import column, select, update
from database.engine import session_maker
from database.orm_query import orm_get_brands_all, orm_get_categories, orm_get_products, orm_update_categorytwb, \
    orm_update_productwb
from database.models import BrandWB, Category, Category11


async def add_productwb():
    count = 0

    while count < 15_000:
        products = await orm_get_products()
        for product in products:
            obj = ProductWB(
                wb_id=product.id,
                name=product.name,
                price=product.price,
                quantity=product.quantity,
                brand=product.brand,
                category=product.category,
                root=product.root,
                subjectId=product.subjectId,
                rating=product.rating,
                pics=product.pics,
                price_history=product.price_history,
            )
            product.updated = datetime.datetime.now()
            await orm_update_productwb(obj, product)

        count += 1


async def add_brandwb():
    brands = await orm_get_brands_all()
    for brand in brands:
        #print(category.parent, category.seo)

        obj = BrandWB(
            wb_id=brand.id,
            name=brand.name,
        )

        brand.updated = datetime.datetime.now()
        await orm_update_categorytwb(obj)


# async def add_categorywb():
#     count = 0
#     categories = await orm_get_categories()
#     for category in categories:
#         #print(category.parent, category.seo)
#
#         obj = CategoryWB(
#             wb_id=category.id,
#             parent=category.parent,
#             name=category.name,
#             seo=category.seo,
#             url=category.url,
#             shard=category.shard,
#             query=category.query,
#             childs=category.childs,
#             published=category.published,
#             sub_category=category.sub_category,
#             filter_category=category.filter_category)
#
#         category.updated = datetime.datetime.now()
#         await orm_update_categorytwb(obj)


async def add_category_tree():
    async with session_maker(expire_on_commit=False) as session:

        # #2 этап
        # level = 3
        # query = select(Category).where(Category.level == level)
        # result = await session.execute(query)
        # categories = result.scalars().all()
        # for category in categories:
        #     query = select(Category11).where(category.id == Category11.parent)
        #     result = await session.execute(query)
        #     for r in result.scalars().all():
        #         #print(r.name, r.id, r.parent, f'{category.level=}, {category.tree_id=}')
        #         obj = Category(
        #             id=r.id,
        #             parent=r.parent,
        #             name=r.name,
        #             seo=r.seo,
        #             url=r.url,
        #             shard=r.shard,
        #             query=r.query,
        #             childs=r.childs,
        #             published=r.published,
        #             sub_category=r.sub_category,
        #             filter_category=r.filter_category,
        #             lft=3,
        #             rght=3,
        #             tree_id=category.tree_id,
        #             level=level + 1)
        #         session.add(obj)
        #         await session.commit()
        #         await session.delete(r)
        #         await session.commit()

        #1 этап
        #count = 0
        # перенести последние три счетчик с 25
        count = 25
        query = select(Category11)
        result = await session.execute(query)
        categories = result.scalars().all()
        for category in categories:
            if category.parent is None: # and category.childs is True:
                count += 1
                obj = Category(
                    id=category.id,
                    name=category.name,
                    seo=category.seo,
                    url=category.url,
                    shard=category.shard,
                    query=category.query,
                    childs=category.childs,
                    published=category.published,
                    sub_category=category.sub_category,
                    filter_category=category.filter_category,
                    lft=3,
                    rght=3,
                    tree_id=count,
                    level=0)
                session.add(obj)
                await session.commit()
                await session.delete(category)
                await session.commit()


        # # Удалить данные с categories начиная с уровня 4
        # level = 4
        # query = select(Category).where(Category.level == level)
        # result = await session.execute(query)
        # categories = result.scalars().all()
        # for category in categories:
        #     await session.delete(category)
        #     await session.commit()
        # print(len(categories))
        # print(count)
