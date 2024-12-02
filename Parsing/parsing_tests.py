import asyncio
import math
from datetime import datetime, timedelta

from BOT_TG.app import send_tg_message
from database.orm_query import (
    orm_delete_product,
    orm_get_categories, orm_get_products,
    orm_update_product,
)
from Parsing.utils import check_discount_and_send_tg, get_response, get_url_price_history, price_history_wb_convert

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TASKS = []
COUNT_ALL = 0
COUNT_TASK = 0


async def convert_product_price_history():
    global TASKS, COUNT_ALL, COUNT_TASK
    work_time = datetime.strptime("2024-11-26 02:08:00", "%Y-%m-%d %H:%M:%S")
    tasks = []
    count = 0
    while work_time > datetime.now():
        # await asyncio.sleep(3)
        products = await orm_get_products()
        for product in products:
            count += 1
            task = asyncio.create_task(update_product(product))
            tasks.append(task)
        if count > 30:
            COUNT_ALL += count
            COUNT_TASK = count
            print(f"{count} задач запущенно. Всего {COUNT_ALL=}")
            await asyncio.gather(*tasks)
            tasks = []
            count = 0

        if len(TASKS) != 0:
            print(f"{len(TASKS)} задач не выполненно. Запускаем после сна 5 сек.")
            # await asyncio.sleep(3)
            await asyncio.gather(*TASKS)
            TASKS = []


# async def get_one_in_url_product(product):
#     try:
#         url_price = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-3917721&spp=30&ab_testing=false&nm={product.id}"
#         response_product = await get_response(url_price)
#         url_history = await get_url_price_history(product.id)
#         response_history = await get_response(url_history)
#     except Exception as e:
#         task = asyncio.create_task(get_one_in_url_product(product))
#         TASKS.append(task)
#         print(str(e))
#
#     await update_product(
#         product, response_product, response_history, url_price, url_history
#     )


async def update_product(product):
    try:
        price_history_my = product.price_history['price_history_my'][0]
    except:
        print(product.id)
    if not price_history_my.get('dt', None):
        for i in price_history_my:
            price_history_my = [{'dt': int(i), 'price': price_history_my[str(i)]}]
    product.price_history['price_history_my'] = price_history_my
    product.price_history = product.price_history
    product.updated = datetime.now()
    await orm_update_product(product)





async def test_test():

    await send_tg_message("https://www.wildberries.ru/catalog/213497976/detail.aspx", 'https://www.wildberries.ru/catalog/213497976/detail.aspx')
    # categories = await orm_get_categories()
    # count = 0
    # for category in categories:
    #     print(category.updated)
    #     if category.query is None or category.shard is None or category.childs:
    #         continue
    #     if category.sub_category:
    #         for item in category.sub_category:
    #             item_count = math.ceil(item["count"] / 100)
    #             pages = item_count if item_count < 5 else 5
    #             for page in range(1, pages + 1):
    #                 count += 1
    # print(count * 100)

    # products = await orm_get_products()
    # for product in products:
    #     # await check_discount_and_send_tg(product)
    #     price_history_wb: list = product.price_history.get('price_history_wb', None)
    #     if price_history_wb:
    #         print(price_history_wb)
    #         min_wb_history: int = min(price_history_wb, key=lambda x: x['price'])
    #         min_wb_price: int = min_wb_history['price']
    #         min_wb_date = min_wb_history['dt']
    #         print(min_wb_price, datetime.fromtimestamp(min_wb_date))


        # price_history_last = int((datetime.now().timestamp() - price_history_last['dt']) / 86400)
        # print(product.updated.replace(tzinfo=None))
        # product_date = (datetime.now() - product.updated).days
        # print(product_date)
        # date_string = "2024-11-26 23:01:00.774296"
        # product_in_bd.updated.replace(tzinfo=None) + timedelta(hours=3) > category_date:

        # price_history_my = product.price_history.get('price_history_my', None)
        # if type(price_history_my) == dict:
        #     print(product.id)
        #     await orm_delete_product(product.id)






