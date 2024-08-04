import asyncio
import datetime
import logging
import os
import time

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv

if not load_dotenv(find_dotenv('.env.dev')):
    load_dotenv(dotenv_path='docker/.env.prod')

token = os.getenv('TOKEN')
url = f'https://api.telegram.org/bot{token}/sendMessage'


async def send_tg_message(m):
    print(f"Отправка сообщения в телегу {datetime.datetime.now()}")
    data = {
            'chat_id': 699474992,
            'text': m,
        }
    async with aiohttp.ClientSession() as session:
        await session.post(url=url, data=data)



