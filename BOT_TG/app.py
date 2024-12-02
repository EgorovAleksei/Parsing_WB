import asyncio
import datetime
import json
import logging
import os
import time

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv("../.env"))
token = os.getenv("TOKEN")
url = f"https://api.telegram.org/bot{token}/sendMessage"
url_send_photo = f"https://api.telegram.org/bot{token}/sendPhoto"


async def send_tg_message(m, url_photo):
    print(f"Отправка сообщения в телегу {datetime.datetime.now()}")
    # m = (
    #     f"старая цена: <strong>1000</strong> \n"
    #     f"новая цена: 100 \n"
    # )
    # chat_id = # -1002318082434  f"https://www.wildberries.ru/catalog/213497976/detail.aspx"
    data = {
        "chat_id": '@wb_sales_wb',
        "parse_mode": "HTML",
        "text": m,
        'link_preview_options': {
            'url': url_photo,
            'prefer_large_media': True
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url=url, json=data)
            print("сообщение отправлено Алексею")
    except:
        await send_tg_message(m, url_photo)
    #

    # 865805900 Dima chat_id
    data = {
        "chat_id": 699474992,
        "parse_mode": "HTML",
        "text": m,
        'link_preview_options': {
            'url': url_photo,
            'prefer_large_media': True
        },
    }
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url=url, data=data)
            await session.post(url=url, json=data)
            print("сообщение отправлено Алексею")
    except:
        await send_tg_message(m, url_photo)

    # data = {
    #     "chat_id": 865805900,
    #     "parse_mode": "HTML",
    #     "text": m,
    # }
    # async with aiohttp.ClientSession() as session:
    #     await session.post(url=url, data=data)
    #     print("сообщение отправлено Диме")

    # data = {
    #     "chat_id": 1784880332,
    #     "parse_mode": "HTML",
    #     "text": m,
    # }
    # async with aiohttp.ClientSession() as session:
    #     await session.post(url=url, data=data)
    #     print("сообщение отправлено Лене")


