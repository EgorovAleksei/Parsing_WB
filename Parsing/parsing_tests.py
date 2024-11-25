import asyncio
import aiohttp
from datetime import datetime
from aiohttp.client_exceptions import ContentTypeError

from database.orm_query import (
    orm_delete_product,
    orm_get_categories,
    orm_get_one_product_join_category,
    orm_get_product,
    orm_get_products,
    orm_update_product,
)
from Parsing.utils import get_response, get_url_price_history, price_history_wb_convert

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TASKS = []
COUNT_ALL = 0
COUNT_TASK = 0


async def convert_product_price_history():
    global TASKS, COUNT_ALL, COUNT_TASK
    work_time = datetime.strptime("2024-11-25 02:08:00", "%Y-%m-%d %H:%M:%S")
    tasks = []
    count = 0
    while work_time > datetime.now():
        await asyncio.sleep(3)
        products = await orm_get_products()
        for product in products:
            count += 1
            task = asyncio.create_task(get_one_in_url_product(product))
            tasks.append(task)
        if count > 20:
            COUNT_ALL += count
            COUNT_TASK = count
            print(f"{count} задач запущенно. Всего {COUNT_ALL=}")
            await asyncio.gather(*tasks)
            tasks = []
            count = 0

        if len(TASKS) != 0:
            print(f"{len(TASKS)} задач не выполненно. Запускаем после сна 5 сек.")
            await asyncio.sleep(3)
            await asyncio.gather(*TASKS)
            TASKS = []


async def get_one_in_url_product(product):
    try:
        url_price = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-3917721&spp=30&ab_testing=false&nm={product.id}"
        response_product = await get_response(url_price)
        url_history = await get_url_price_history(product.id)
        response_history = await get_response(url_history)
    except Exception as e:
        task = asyncio.create_task(get_one_in_url_product(product))
        TASKS.append(task)
        print(str(e))

    await update_product(
        product, response_product, response_history, url_price, url_history
    )


async def update_product(
    product, response_product, response_history, url_price, url_history
):
    price_history = {"price_history_wb": [], "price_history_my": []}
    try:
        response_product = response_product.get("data", None).get("products", None)
        if response_product[0].get("sizes", None)[0].get("price", None):
            new_price = int(
                response_product[0].get("sizes", None)[0].get("price").get("product")
                / 100
            )
            price_history["price_history_my"].append(
                {str(int(datetime.now().timestamp())): new_price}
            )
        else:
            await orm_delete_product(product.id)
            return

        if response_history:
            price_history_wb = await price_history_wb_convert(response_history)
            price_history["price_history_wb"] = price_history_wb

        product.price_history = price_history
        product.updated = datetime.now()
        product.price_history_check = True
        await orm_update_product(product)
    except AttributeError:
        print(product.id)
    except Exception as e:
        print(f"Удален продукт {product.id}")
        await orm_delete_product(product.id)
