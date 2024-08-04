import asyncio
import datetime
import json
import time

import aiohttp
from aiohttp import ClientConnectorError, ContentTypeError

from database.models import Category
from database.orm_query import orm_add_categories, orm_get_categories, orm_update_categories
from Parsing.utils import add_category

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
BASE_URL = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v2.json'
TASKS = []
COUNT_ALL = 0


async def get_all_category():
    """ Получение json всех категорий """
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, headers=HEADERS) as response:
            try:
                response = await response.json()
            except ContentTypeError as e:
                print(f'Content type error, адрес {BASE_URL} больше не работает')
                return
            await add_category(response)


async def get_items_for_sub_category(cat: Category, url, count: int):
    global COUNT_ALL
    if count % 10 == 0:
        await asyncio.sleep(20)
    if count % 2 == 0:
        await asyncio.sleep(50)
    if count % 3 == 0:
        await asyncio.sleep(30)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                try:
                    response = await response.json(encoding='utf-8')
                except ContentTypeError as e:
                    print(f'Content type error, {cat.name} адрес {url} не работает')
                    cat.filter_category = False
                    COUNT_ALL -= 1
                    await orm_update_categories(cat)
                    return
                total = response.get('data').get('total')
                items = response.get('data').get('filters')[0].get('items')
                if items:
                    cat.sub_category = items
                    await orm_update_categories(cat)
                else:
                    cat.sub_category = [{'count': total}]
                    await orm_update_categories(cat)
                    COUNT_ALL -= 1
                print(f"Задача {count} выполнена, осталось {COUNT_ALL}")

        except ClientConnectorError as e:
            # Ошибка семафора возникает. Эти задачи в новую задачу.
            task = asyncio.create_task(
                get_items_for_sub_category(
                    cat=cat,
                    url=url,
                    count=count,
                )
            )
            TASKS.append(task)
            print(f"{e}  {count}, {cat.url}, {cat.name}")
            COUNT_ALL -= 1
            return


async def get_sub_category():
    global TASKS, COUNT_ALL
    """ получение всех фильтров по категориям внутри категорий. если они есть """
    categories = await orm_get_categories()
    tasks = []
    count = 0
    for cat in categories:
        if (cat.query is not None
                and cat.shard is not None
                and cat.filter_category
                and cat.sub_category is None
                #and (datetime.datetime.now() - cat.updated).days > 10
        ):
            count += 1
            url = f'https://catalog.wb.ru/catalog/{cat.shard}/v4/filters?appType=1&{cat.query}&dest=-3917721'

            task = asyncio.create_task(
                get_items_for_sub_category(
                    cat=cat,
                    url=url,
                    count=count,
                )
            )
            tasks.append(task)
            # if count == 20:
            #     break
    COUNT_ALL = count
    print(f"{count} задач")
    await asyncio.gather(*tasks)

    # Если что-то не обработалось из-за Cannot connect to host catalog.wb.ru:443 ssl:default [Превышен таймаут семафора]
    # собираем эти задачи в TASKS и снова пытаемся выполнять несколько раз.
    x = 0  # количество попыток. пока 10.
    while len(TASKS) != 0 and x <= 10:
        x += 1
        time.sleep(10)
        print(f"не выполнено {len(TASKS)} задач. из {count}")
        count = len(TASKS)
        COUNT_ALL = count
        print(f"Осталось {count} задач")
        tasks = TASKS[:]
        TASKS = []
        print(f"TASKS {TASKS}, {x}")
        await asyncio.gather(*tasks)
