import asyncio
import datetime
from datetime import timedelta, date

import aiohttp
import aiofiles
from pathlib import Path

from aiohttp import ClientConnectorError, ContentTypeError

from BOT_TG.app import send_tg_message
from database.models import Product
from database.orm_query import orm_get_products, orm_update_product

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

DOWNLOAD_DIR = Path('./Parsing/Media/products_images')
TASKS = []

#print(DOWNLOAD_DIR)


async def save_image(url_image, filename, dir_image):
    global TASKS
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url_image, headers=HEADERS) as response:
                try:
                    r = await response.content.read()
                except ContentTypeError:
                    print(f'Content type error, адрес {url_image} попробуем еще позже!')
                    task = asyncio.create_task(save_image(
                        url_image=url_image,
                        filename=filename,
                        dir_image=dir_image,
                    ))
                    TASKS.append(task)
                    print(f"{url_image} задача не выполнена")
                    return

                dir_image.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(r)
                    print(f"{filename} записан")

        except ClientConnectorError as e:
            task = asyncio.create_task(save_image(
                url_image=url_image,
                filename=filename,
                dir_image=dir_image,
            ))
            TASKS.append(task)
            print(f"Ошибка семафора {e}  {url_image}")
            return


async def get_url_image():
    global TASKS
    count = 0
    tasks = []
    print(datetime.datetime.now())
    products = await orm_get_products()
    for product in products:
        print(product.id, product.name)

    # while count < 100:
    #     products = await orm_get_products()
    #     for product in products:
    #         product.pics.pop('3', None)
    #         product.pics.pop('4', None)
    #         count += 1
    #         part = product.id // 1000
    #         vol = product.id // 100_000
    #         data = {
    #             'id': product.id,
    #             'updated': datetime.datetime.now(),
    #             'pics': product.pics
    #         }
    #         await orm_update_product(data)
    #
    #         for j in product.pics.values():
    #             url_image = j
    #             dir_image = DOWNLOAD_DIR / f"{j[8:17]}/vol{vol}/part{part}/{product.id}"
    #             filename = dir_image / f'{j[-6:]}'
    #             task = asyncio.create_task(save_image(
    #                 url_image=url_image,
    #                 filename=filename,
    #                 dir_image=dir_image,
    #                 ))
    #             tasks.append(task)
    #         if len(tasks) > 120:
    #             print(f"Запущенно {count} задач")
    #             await asyncio.gather(*tasks)
    #             tasks = []
    #             x = 0
    #             while len(TASKS) > 0 or x > 10:
    #                 print(f"Запущенны не выполненные задачи {len(TASKS)} штук")
    #                 x += 1
    #                 tasks = TASKS[:]
    #                 TASKS = []
    #                 await asyncio.gather(*TASKS)
    #             print(f"Пауза 5 сек, {x=}, {len(tasks)=}")
    #             await asyncio.sleep(5)
    #             print(f"Не выполненные задачи, что смогли выполнились. осталось {len(tasks)}")
    # m = 'Закончилось выполнение'
    await send_tg_message(m)

