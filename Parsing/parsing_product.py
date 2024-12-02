import asyncio
import math
import time
from datetime import datetime, timezone, timedelta

import aiohttp
from aiohttp import ClientConnectorError, ContentTypeError

from BOT_TG.app import send_tg_message
from database.models import Brand, Category, Product
from database.orm_query import (
    orm_add_brand,
    orm_add_product,
    orm_get_brands,
    orm_get_categories,
    orm_get_product,
    orm_update_categories,
    orm_update_product,
)
from Parsing.utils import check_discount_and_send_tg, create_product, get_price_history_wb, get_response, \
    get_url_price_history, \
    price_history_wb_convert

TASKS = []
COUNT_ALL = 0
COUNT_TASK = 0
ALL_BRANDS = []

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


async def get_brand(url_brand):
    try:
        response_brand = await get_response(url_brand)
        brands = response_brand.get("data", None).get("filters", None)
        for brand in brands[0].get("items"):
            id = brand.get("id")
            if id not in ALL_BRANDS:
                await orm_add_brand(Brand(wb_id=id, name=brand.get("name")))
                print(f"Добавили {id=}")
    except:
        print(f"Нет response {response_brand=} \n {url_brand=}")
        return


async def get_brands():
    global COUNT_TASK, ALL_BRANDS
    categories = await orm_get_categories()
    ALL_BRANDS = await orm_get_brands()
    tasks = []
    count = 0
    for category in categories:
        count += 1
        category.updated = datetime.now()
        await orm_update_categories(category)
        if category.query is None or category.shard is None or category.childs:
            continue
        url_brand = f"https://catalog.wb.ru/catalog/{category.shard}/v4/filters?appType=1&{category.query}&dest=-1257786&filters=fbrand"
        task = asyncio.create_task(get_brand(url_brand=url_brand))
        tasks.append(task)
        # if count > 1000:
        #     print('начинаем выполнять задачи')
        #     COUNT_TASK += count
        #     await asyncio.gather(*tasks)
        #     print(f"{COUNT_TASK=}")
        #     await asyncio.sleep(20)
        #     print(f"Сон прошел")
        #     tasks = []
        #     count = 0
    await asyncio.gather(*tasks)


async def get_products(url: str, category_id: int, subjectId: int | None, count: int):
    global COUNT_TASK, TASKS

    try:
        response_products = await get_response(url)
    except:
        task = asyncio.create_task(
            get_products(
                url=url,
                category_id=category_id,
                subjectId=subjectId,
                count=count,
            )
        )
        TASKS.append(task)
        COUNT_TASK -= 1
        # print(f"{len(TASKS)=}, {COUNT_TASK=}")
        return
    if response_products:
        response_products = response_products.get("data", None).get("products", None)
        await update_products(response_products, category_id, subjectId)
    print(f"Задача {count} выполнена, из {COUNT_ALL} осталось {COUNT_TASK}")


async def update_products(response_products, category_id: int, subjectId: int | None):
    global COUNT_TASK
    for product in response_products:
        await orm_add_brand(
            Brand(
                wb_id=int(product.get("brandId")), name=product.get("brand")
            )
        )
        product_id = product.get("id")
        product_in_bd = await orm_get_product(product_id)
        if not product_in_bd:
            price_history_wb = await get_price_history_wb(product_id)
            obj = await create_product(product, price_history_wb, category_id, subjectId)
            await orm_add_product(obj)
            await check_discount_and_send_tg(obj)

            return

        new_price = int(product.get("sizes")[0].get("price").get("product") / 100)
        if product_in_bd.price_history["price_history_my"][-1]['price'] != new_price:
            product_in_bd.price = new_price
            try:
                product_in_bd.price_history["price_history_my"].append(
                    {'dt': int(datetime.now().timestamp()), 'price': new_price}
                )
            except AttributeError as e:
                print(product_in_bd.id, 'Не удалось добавить AttributeError: dict object has no attribute append')

            new_discount = 100 - int(new_price * 100 / product_in_bd.price)
            product_in_bd.discount = new_discount
            if (datetime.now() - product_in_bd.updated).days > 7:
                price_history_wb = await get_price_history_wb(product_id)
                product_in_bd.price_history['price_history_wb'] = price_history_wb
            await orm_update_product(product_in_bd)
            await check_discount_and_send_tg(product_in_bd)
    COUNT_TASK -= 1


async def get_url_product():
    print('Начало')
    global TASKS, COUNT_ALL, COUNT_TASK
    """Получение всех ссылок на списки продуктов в категориях."""

    categories = await orm_get_categories()
    tasks = []
    count = 0
    work_time = datetime.strptime("2024-12-02 12:42:00", "%Y-%m-%d %H:%M:%S")
    for category in categories:
        await asyncio.sleep(0.002)
        if datetime.now() > work_time:
            break

        category.updated = datetime.now()
        await orm_update_categories(category)
        if category.query is None or category.shard is None or category.childs:
            continue
        url = f"https://catalog.wb.ru/catalog/{category.shard}/v2/catalog?appType=1&{category.query}&dest=-3917721"
        if category.sub_category:
            for item in category.sub_category:
                item_count = math.ceil(item["count"] / 100)
                pages = item_count if item_count < 3 else 3

                if "id" in item:
                    url = (
                        f"https://catalog.wb.ru/catalog/{category.shard}/v2/catalog?appType=1"
                        f"&{category.query}&dest=-3917721&xsubject={item.get('id')}"
                    )

                for page in range(1, pages + 1):
                    count += 1
                    task = asyncio.create_task(
                        get_products(
                            url=url + "&page=" + str(page),
                            category_id=category.id,
                            subjectId=item.get("id"),
                            count=count,
                        )
                    )

                    tasks.append(task)
                if count > 50:
                    COUNT_ALL += count
                    COUNT_TASK = count
                    print(f"{count} задач запущенно. Всего {COUNT_ALL=}")
                    await asyncio.gather(*tasks)

                    # Если что-то не обработалось из-за Cannot connect to host catalog.wb.ru:443 ssl:default [Превышен таймаут семафора]
                    # собираем эти задачи в TASKS и снова пытаемся выполнять несколько раз.
                    print('while len(TASKS) != 0:', len(TASKS))
                    x = 0
                    while len(TASKS) != 0 and x < 2:
                        x = x + 1
                        await asyncio.sleep(5)
                        print(f"не выполнено {len(TASKS)} задач. из {count}")
                        count = len(TASKS)
                        COUNT_TASK = count
                        print(f"Осталось {count} задач")
                        tasks = TASKS[:]
                        print(f"TASKS {len(TASKS)=}, {x}, {len(tasks)=}")
                        TASKS = []
                        await asyncio.gather(*tasks)
                    TASKS, tasks = [], []
                    print(
                        f"Запущен сон 5 секунд, {count=}, {COUNT_TASK=}, {COUNT_ALL=} {datetime.now()}"
                    )
                    await asyncio.sleep(3)
                    print(f"Сон закончился")
                    count = 0
                    COUNT_TASK = 0
        COUNT_TASK = 0
        print(f"Выполнено {COUNT_ALL} задач")
