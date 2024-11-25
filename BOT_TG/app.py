import asyncio
import datetime
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


async def send_tg_message(m):
    print(f"Отправка сообщения в телегу {datetime.datetime.now()}")
    #
    # m = (
    #     f"https://www.wildberries.ru/catalog/111111/detail.aspx \n"
    #     f"старая цена: <strong>1000</strong> \n"
    #     f"новая цена: 100 \n"
    #     f"<b>RED</b>"
    # )
    # 865805900 Dima chat_id
    data = {
        "chat_id": 699474992,
        "parse_mode": "HTML",
        "text": m,
    }
    async with aiohttp.ClientSession() as session:
        await session.post(url=url, data=data)
        print("сообщение отправлено Алексею")

    data = {
        "chat_id": 865805900,
        "parse_mode": "HTML",
        "text": m,
    }
    async with aiohttp.ClientSession() as session:
        await session.post(url=url, data=data)
        print("сообщение отправлено Диме")

    # data = {
    #     "chat_id": 1784880332,
    #     "parse_mode": "HTML",
    #     "text": m,
    # }
    # async with aiohttp.ClientSession() as session:
    #     await session.post(url=url, data=data)
    #     print("сообщение отправлено Лене")
