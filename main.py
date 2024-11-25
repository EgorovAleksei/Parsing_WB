import asyncio
from datetime import datetime, timedelta

from BOT_TG.app import send_tg_message
from database.engine import create_db, drop_db
from database.orm_query import orm_add_product, orm_get_product, orm_update_product
from Parsing.parsing_catalog import get_all_category, get_sub_category
from Parsing.parsing_image import get_url_image
from Parsing.parsing_options import get_options
from Parsing.parsing_product import get_brands, get_url_product
from Parsing.parsing_tests import convert_product_price_history, get_one_in_url_product
from Parsing.utils import get_basket


# from Parsing.wb import (
#     add_brandwb,
#     add_category_tree,
# )  # , #add_categorywb, add_productwb


async def main():
    # await drop_db()
    # await create_db()

    # получение всех категорий WB

    # await get_all_category()

    # получение всех подкатегорий которые в фильтрах.
    # await get_sub_category()

    # получение продуктов
    # await get_url_product()

    # получение брендов
    # await get_brands()

    # получение картинок
    # await get_url_image()

    # получение Options
    # await get_options()

    # await add_productwb()
    # await add_categorywb()
    # await add_brandwb()
    # await add_category_tree()

    # product = orm_get_product(200417135)
    await convert_product_price_history()


if __name__ == "__main__":

    asyncio.run(main())
