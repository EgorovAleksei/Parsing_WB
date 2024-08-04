import aiohttp

from database.models import Category, Product
from database.orm_query import orm_add_categories


async def get_url_pics(product_id: int, pic_count: int = 4) -> dict:
    part = product_id // 1000
    vol = product_id // 100_000
    if 0 <= vol <= 143:
        basket = '01'
    elif 143 <= vol <= 287:
        basket = '02'
    elif 288 <= vol <= 431:
        basket = '03'
    elif 432 <= vol <= 719:
        basket = '04'
    elif 720 <= vol <= 1007:
        basket = '05'
    elif 1008 <= vol <= 1061:
        basket = '06'
    elif 1062 <= vol <= 1115:
        basket = '07'
    elif 1116 <= vol <= 1169:
        basket = '08'
    elif 1170 <= vol <= 1313:
        basket = '09'
    elif 1314 <= vol <= 1601:
        basket = '10'
    elif 1602 <= vol <= 1655:
        basket = '11'
    elif 1656 <= vol <= 1919:
        basket = '12'
    elif 1920 <= vol <= 2045:
        basket = '13'
    elif 2046 <= vol <= 2189:
        basket = '14'
    elif 2190 <= vol <= 2405:
        basket = '15'
    elif 2406 <= vol <= 2621:
        basket = '16'
    elif 2622 <= vol <= 2870:
        basket = '17'
    url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/"
    return {i: f"{url}{i}.webp" for i in range(1, pic_count + 1)}


async def get_product(product, category_id: int, subjectId: int | None):
    product_id = product.get('id')
    pics = (await get_url_pics(product_id=product_id) if int(product.get('pics')) >= 4
            else await get_url_pics(product_id=product_id, pic_count=int(product.get('pics'))))

    obj = Product(
        id=product_id,
        name=product.get('name'),
        price=int(product.get('sizes')[0].get('price').get('product') / 100),
        quantity=3,
        brand=product.get('brandId'),
        category=category_id,
        root=product.get('root'),
        subjectId=subjectId,
        rating=product.get('rating'),
        pics=pics,
        price_history=[{}]
    )
    # print(
    #     f"{product_id=}, "
    #     f"{product.get('name')=}, "
    #     f"{product.get('sizes')[0].get('price').get('product')=}, "
    #     f"{product.get('brandId')=}, {category_id=}, {product.get('root')=},"
    #     f"{subjectId=}, {product.get('rating')=}, {pics=}"
    # )
    return obj


async def add_category(response):
    """ Обработка json категорий и добавлений всех категорий и их childs в базу данных"""
    for r in response:
        obj = Category(
            id=r.get('id', None),
            parent=r.get('parent', None),
            name=r.get('name', None),
            seo=r.get('seo', None),
            url=r.get('url', None),
            shard=r.get('shard', None),
            query=r.get('query', None),
            childs=True if r.get('childs') else False,
        )
        if 'childs' in r:
            await orm_add_categories(obj)
            await add_category(r['childs'])
        if 'childs' not in r:
            await orm_add_categories(obj)


async def get_url_options(product_id: int) -> str:
    part = product_id // 1000
    vol = product_id // 100_000
    if 0 <= vol <= 143:
        basket = '01'
    elif 143 <= vol <= 287:
        basket = '02'
    elif 288 <= vol <= 431:
        basket = '03'
    elif 432 <= vol <= 719:
        basket = '04'
    elif 720 <= vol <= 1007:
        basket = '05'
    elif 1008 <= vol <= 1061:
        basket = '06'
    elif 1062 <= vol <= 1115:
        basket = '07'
    elif 1116 <= vol <= 1169:
        basket = '08'
    elif 1170 <= vol <= 1313:
        basket = '09'
    elif 1314 <= vol <= 1601:
        basket = '10'
    elif 1602 <= vol <= 1655:
        basket = '11'
    elif 1656 <= vol <= 1919:
        basket = '12'
    elif 1920 <= vol <= 2045:
        basket = '13'
    elif 2046 <= vol <= 2189:
        basket = '14'
    elif 2190 <= vol <= 2405:
        basket = '15'
    elif 2406 <= vol <= 2621:
        basket = '16'
    elif 2622 <= vol <= 2870:
        basket = '17'

    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"
