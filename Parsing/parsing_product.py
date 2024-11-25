import asyncio
import math
import time
from datetime import datetime, timezone

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
from Parsing.utils import get_product

TASKS = []
COUNT_ALL = 0
COUNT_TASK = 0
ALL_BRANDS = []

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


async def get_brand(url_brand):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url_brand, headers=HEADERS) as response:
                try:
                    response = await response.json(encoding="utf-8")
                except ContentTypeError as e:
                    print(f"Content type error, адрес {url_brand} не работает!")
                try:
                    brands = response.get("data", None).get("filters", None)
                    for brand in brands[0].get("items"):
                        id = brand.get("id")
                        if id not in ALL_BRANDS:
                            await orm_add_brand(Brand(wb_id=id, name=brand.get("name")))
                            print(f"Добавили {id=}")
                except AttributeError as e:
                    print(f"Нет response {response=} \n {url_brand=}")
                    return

        except ClientConnectorError as e:
            # Ошибка семафора возникает. Эти задачи в новую задачу.
            print(f"Ошибка семафора {e}  {url_brand} ")
        except ConnectionError as e:
            print(f"Ошибка ConnectionError {e} {url_brand}")
        except TimeoutError as e:
            print(f"Ошибка TimeoutError  {e} {url_brand}")


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
    global COUNT_TASK
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                try:
                    response = await response.json(encoding="utf-8")
                except ContentTypeError as e:
                    print(
                        f"Content type error, адрес {url} не работает, {count=}, {COUNT_TASK=}"
                    )
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
                    print(f"{len(TASKS)=}, {COUNT_TASK=}")
                    return
                try:
                    products = response.get("data", None).get("products", None)
                except AttributeError as e:
                    print(f"Нет response {response=} \n {url=}")
                    return
                for product in products:

                    await orm_add_brand(
                        Brand(
                            wb_id=int(product.get("brandId")), name=product.get("brand")
                        )
                    )
                    product_in_bd = await orm_get_product(product.get("id"))
                    if product_in_bd:
                        new_price = int(
                            product.get("sizes")[0].get("price").get("product") / 100
                        )
                        new_discount = int(new_price * 100 / product_in_bd.price)
                        if 100 - new_discount > 40:
                            product_in_bd.discount = new_discount
                            m_url = (
                                f"https://www.wildberries.ru/catalog/{product_in_bd.id}/detail.aspx \n"
                                f"старая цена: <strong>{product_in_bd.price}</strong> \n"
                                f"новая цена: <strong>{new_price}</strong> \n "
                            )
                            await send_tg_message(m_url)
                        product_in_bd.price = new_price
                        product_in_bd.price_history[0][
                            int(datetime.now().timestamp())
                        ] = new_price
                        await orm_update_product(product_in_bd)
                    else:
                        obj = await get_product(product, category_id, subjectId)
                        await orm_add_product(obj)
                COUNT_TASK -= 1

        except ClientConnectorError as e:
            # Ошибка семафора возникает. Эти задачи в новую задачу.
            task = asyncio.create_task(
                get_products(
                    url=url,
                    category_id=category_id,
                    subjectId=subjectId,
                    count=count,
                )
            )
            TASKS.append(task)
            print(f"Ошибка семафора {e}  {count}, {COUNT_TASK} {url} ")
            COUNT_TASK -= 1
            return
        except Exception as e:
            print(f"Exception {e} ошибка!!!!!")

        # COUNT_TASK -= 1
        print(f"Задача {count} выполнена, осталось {COUNT_TASK}")


async def get_url_product(product_id):
    global TASKS, COUNT_ALL, COUNT_TASK
    """Получение всех ссылок на списки продуктов в категориях."""
    categories = await orm_get_categories()
    tasks = []
    count = 0
    work_time = datetime.strptime("2024-11-04 23:01:00", "%Y-%m-%d %H:%M:%S")

    for category in categories:
        if datetime.now() > work_time:
            break

        past_hours = (
            (datetime.now() - category.updated.replace(tzinfo=None)).total_seconds()
            / 60
            / 60
        )

        if past_hours < 24:
            continue
        category.updated = datetime.now()
        await orm_update_categories(category)
        if category.query is None or category.shard is None or category.childs:
            continue
        url = f"https://catalog.wb.ru/catalog/{category.shard}/v2/catalog?appType=1&{category.query}&dest=-3917721"
        if category.sub_category:
            for item in category.sub_category:
                item_count = math.ceil(item["count"] / 100)
                pages = item_count if item_count < 50 else 50

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
                if count > 100:
                    COUNT_ALL += count
                    COUNT_TASK = count
                    print(f"{count} задач запущенно. Всего {COUNT_ALL=}")
                    await asyncio.gather(*tasks)

                    # Если что-то не обработалось из-за Cannot connect to host catalog.wb.ru:443 ssl:default [Превышен таймаут семафора]
                    # собираем эти задачи в TASKS и снова пытаемся выполнять несколько раз.
                    x = 0  # количество попыток. пока 10.
                    while len(TASKS) != 0 and x <= 10:
                        await asyncio.sleep(10)
                        x += 1
                        print(f"не выполнено {len(TASKS)} задач. из {count}")
                        count = len(TASKS)
                        COUNT_TASK = count
                        print(f"Осталось {count} задач")
                        tasks = TASKS[:]
                        print(f"TASKS {len(TASKS)=}, {x}, {len(tasks)=}")
                        TASKS = []
                        await asyncio.gather(*tasks)
                    tasks = []
                    print(
                        f"Запущен сон 5 секунд, {count=}, {COUNT_TASK=}, {COUNT_ALL=} {datetime.now()}"
                    )
                    await asyncio.sleep(5)
                    print(f"Сон закончился")
                    count = 0
                    COUNT_TASK = 0
        COUNT_TASK = 0
        print(f"Выполнено {COUNT_ALL} задач")


# async with session.get(BASE_URL, headers=HEADERS) as response:


# asyncio.run(get_product())
