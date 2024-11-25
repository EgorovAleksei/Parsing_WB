import aiohttp
from aiohttp.client_exceptions import ContentTypeError

from database.models import Category, Product
from database.orm_query import orm_add_categories

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


async def get_basket(product_id: int) -> str:
    """
    в этом файле смотреть новые basket если вдруг появятся.
    https://static-basket-01.wbbasket.ru/vol2/site/j/spa/index.bf38c4a54122121cff83.js
    initiator fetch @ index.bf38c4a.js
    column 57300
    """
    part: int = product_id // 1000
    vol: int = product_id // 100_000

    if 0 <= vol <= 143:
        basket = "01"
    elif vol <= 287:
        basket = "02"
    elif vol <= 431:
        basket = "03"
    elif vol <= 719:
        basket = "04"
    elif vol <= 1007:
        basket = "05"
    elif vol <= 1061:
        basket = "06"
    elif vol <= 1115:
        basket = "07"
    elif vol <= 1169:
        basket = "08"
    elif vol <= 1313:
        basket = "09"
    elif vol <= 1601:
        basket = "10"
    elif vol <= 1655:
        basket = "11"
    elif vol <= 1919:
        basket = "12"
    elif vol <= 2045:
        basket = "13"
    elif vol <= 2189:
        basket = "14"
    elif vol <= 2405:
        basket = "15"
    elif vol <= 2621:
        basket = "16"
    elif vol <= 2837:
        basket = "17"
    elif vol <= 3053:
        basket = "18"
    return basket, part, vol


async def get_url_pics(product_id: int, pic_count: int = 4) -> dict:
    basket, part, vol = await get_basket(product_id)
    url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/"
    return {i: f"{url}{i}.webp" for i in range(1, pic_count + 1)}


async def get_url_options(product_id: int) -> str:
    basket, part, vol = await get_basket(product_id)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"


async def get_url_price_history(product_id: int) -> str:
    basket, part, vol = await get_basket(product_id)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/price-history.json"


async def get_product(product, category_id: int, subjectId: int | None):
    product_id = product.get("id")
    pics = (
        await get_url_pics(product_id=product_id)
        if int(product.get("pics")) >= 4
        else await get_url_pics(
            product_id=product_id, pic_count=int(product.get("pics"))
        )
    )

    obj = Product(
        id=product_id,
        name=product.get("name"),
        price=int(product.get("sizes")[0].get("price").get("product") / 100),
        quantity=3,
        brand=product.get("brandId"),
        category=category_id,
        root=product.get("root"),
        subjectId=subjectId,
        rating=product.get("rating"),
        pics=pics,
        price_history=[{}],
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
    """Обработка json категорий и добавлений всех категорий и их childs в базу данных"""
    for r in response:
        obj = Category(
            id=r.get("id", None),
            parent=r.get("parent", None),
            name=r.get("name", None),
            seo=r.get("seo", None),
            url=r.get("url", None),
            shard=r.get("shard", None),
            query=r.get("query", None),
            childs=True if r.get("childs") else False,
        )
        if "childs" in r:
            await orm_add_categories(obj)
            await add_category(r["childs"])
        if "childs" not in r:
            await orm_add_categories(obj)


async def price_history_wb_convert(price_history_wb):
    try:
        for i in price_history_wb:
            i["price"] = i["price"]["RUB"]
            # print(i)
        return price_history_wb
    except ContentTypeError as e:
        print(price_history_wb)
        print(str(e))


async def get_response(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                try:
                    response = await response.json(encoding="utf-8")
                except ContentTypeError as e:
                    print(f"Content type error, адрес {url} не работает, ")
                    return None
        except:
            return None

    return response
