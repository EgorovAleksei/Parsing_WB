import asyncio
import datetime
from datetime import timedelta, date

import aiohttp
import aiofiles
from pathlib import Path

from aiohttp import ClientConnectorError, ContentTypeError

from BOT_TG.app import send_tg_message
from database.models import Options, Product
from database.orm_query import orm_add_options, orm_get_products, orm_update_product
from Parsing.utils import get_url_options

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

DOWNLOAD_DIR = Path("./Parsing/Media/products_images")
TASKS = []

# print(DOWNLOAD_DIR)


async def get_json_options(url, product_id):
    global TASKS
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                try:
                    r = await response.json(encoding="utf-8")
                    print(f"{url=}  {r=}")
                except ContentTypeError:
                    print(f"Content type error, адрес {url} попробуем еще позже!")
                    task = asyncio.create_task(get_json_options(url=url))
                    TASKS.append(task)
                    print(f"{url} задача не выполнена")
                    return
                if r:
                    obj = Options(
                        nm_id=product_id,
                        card=r,
                    )
                    await orm_add_options(obj)

        except ClientConnectorError as e:
            task = asyncio.create_task(get_json_options(url=url))
            TASKS.append(task)
            print(f"Ошибка семафора {e}  {url}")
            return


async def get_options():
    global TASKS
    count = 0
    tasks = []
    # print(datetime.datetime.now())
    # products = await orm_get_products()
    # for product in products:
    #     print(product.id, product.name)

    while count < 100:
        products = await orm_get_products()
        for product in products:
            count += 1
            url = await get_url_options(product.id)

            data = {
                "id": product.id,
                "updated": datetime.datetime.now(),
            }
            # await orm_update_product(data)

            task = asyncio.create_task(get_json_options(url=url, product_id=product.id))
            tasks.append(task)
            if len(tasks) > 100:
                print(f"Запущенно {count} задач")
                await asyncio.gather(*tasks)
                tasks = []
                x = 0
                while len(TASKS) > 0 or x > 10:
                    print(f"Запущенны не выполненные задачи {len(TASKS)} штук")
                    x += 1
                    tasks = TASKS[:]
                    TASKS = []
                    await asyncio.gather(*TASKS)
                print(f"Пауза 5 сек, {x=}, {len(tasks)=}")
                await asyncio.sleep(5)
                print(
                    f"Не выполненные задачи, что смогли выполнились. осталось {len(tasks)}"
                )
    m = "Закончилось выполнение"
    await send_tg_message(m)
