from datetime import datetime

import aiohttp
from aiohttp.client_exceptions import ContentTypeError

from BOT_TG.app import send_tg_message
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


async def create_product(product, price_history_wb, category_id: int, subjectId: int | None):
    product_id = product.get("id")
    price = int(product.get("sizes")[0].get("price").get("product") / 100)
    price_history = {"price_history_wb": price_history_wb, "price_history_my": []}
    price_history["price_history_my"].append(
        {'dt': int(datetime.now().timestamp()), 'price': price}
    )
    pics = await get_url_pics(product_id=product_id, pic_count=int(product.get("pics")))

    obj = Product(
        id=product_id,
        name=product.get("name"),
        price=price,
        quantity=3,
        brand=product.get("brandId"),
        category=category_id,
        root=product.get("root"),
        subjectId=subjectId,
        rating=product.get("rating"),
        pics=pics,
        price_history=price_history,
        price_history_check=True,
    )
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


async def price_history_wb_convert(response_history):
    try:
        for i in response_history:
            price = int(i["price"]["RUB"] / 100)
            i["price"] = price
            # print(i)
        return response_history
    except ContentTypeError as e:
        print(response_history)
        print(str(e))


async def get_price_history_wb(product_id):
    url_history = await get_url_price_history(product_id)
    try:
        response_history = await get_response(url_history)
    except:
        print(f"{url_history} нет истории")
        return None
    if response_history:
        price_history_wb = await price_history_wb_convert(response_history)
        return price_history_wb


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


async def check_discount_and_send_tg(product_in_bd):
    price_history_wb: list = product_in_bd.price_history.get('price_history_wb', None)
    price_history_my: list = product_in_bd.price_history.get('price_history_my', None)

    if price_history_wb:
        price_wb_last: int = price_history_wb[-1]['price']
        date_wb_last = price_history_wb[-1]['dt']
        min_wb_history: int = min(price_history_wb, key=lambda x: x['price'])
        min_wb_price: int = min_wb_history['price']
        min_wb_date = min_wb_history['dt']
        discount_last: int = 100 - int(product_in_bd.price * 100 / price_wb_last)
        discount_min: int = 100 - int(product_in_bd.price * 100 / min_wb_price)
        if discount_last > 30 and discount_min > 20:
            m_url: str = (
                f"Скидка: <strong>{discount_last}%</strong> \n"
                f"Старая цена: <strong>{price_wb_last}</strong> руб.\n"
                f"Цена сейчас: <strong>{product_in_bd.price}</strong> руб.\n"
                f"Минимальная цена была {datetime.fromtimestamp(min_wb_date).strftime('%Y-%m-%d')} "
                f"<strong>{min_wb_price}</strong> руб. \n"
            )
            url_photo = f"https://www.wildberries.ru/catalog/{product_in_bd.id}/detail.aspx"
            await send_tg_message(m_url, url_photo)
            return

        # print(f"{price_wb_last=}, {date_wb_last=}, {min_wb_price=}, {product_in_bd.id}")
    if len(price_history_my) < 2:
        return
    if price_history_my and len(price_history_my) > 1:
        price_my_last = price_history_my[-2]['price']
        date_my_last = price_history_my[-2]['dt']
        min_my_history: int = min(price_history_my, key=lambda x: x['price'])
        discount = 100 - int(product_in_bd.price * 100 / price_my_last)
        if discount > 30:
            m_url: str = (
                f"Скидка: <strong>{discount}%</strong> \n"
                f"Старая цена: <strong>{price_my_last}</strong> руб.\n"
                f"Цена сейчас: <strong>{product_in_bd.price}</strong> руб.\n"
            )
            url_photo = f"https://www.wildberries.ru/catalog/{product_in_bd.id}/detail.aspx"
            # print(m_url)
            await send_tg_message(m_url, url_photo)
            return


        # print('my', product_in_bd.price, price_my_last, datetime.fromtimestamp(date_my_last), product_in_bd.id)
