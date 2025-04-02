import asyncio
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN
from database.db import async_main
from handlers import (
    start,
    help,
    ref_program,
    pay,
    utils,
    admin_commands
)
from handlers.parsit import parse_menu, gumtree, poshmark, poshmark_ca, lalafo, lalafo_kg
from handlers.params import params_menu, edit_whatsapp, make_preset, edit_preset
from handlers.shop import shop_menu


# Создаем планировщик
scheduler = AsyncIOScheduler()


async def send_file_to_user(bot: Bot, user_id: int):
    file_path = 'db.sqlite3'

    if os.path.exists(file_path):
        moscow_time = datetime.now(pytz.timezone('Europe/Moscow'))
        formatted_time = moscow_time.strftime("%Y-%m-%d %H:%M:%S")

        message_text = f"База данных на {formatted_time}."

        document = FSInputFile(file_path)

        await bot.send_document(user_id, document=document, caption=message_text)
    else:
        print(f"Файл {file_path} не найден.")



async def send_database_file():
    user_id = 6389394798
    bot = Bot(token=TOKEN)
    await send_file_to_user(bot, user_id)


scheduler.add_job(send_database_file, 'interval', hours=2)


async def start_scheduler():
    scheduler.start()

async def main():
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_routers(
        start.router,
        help.router,
        ref_program.router,
        pay.router,
        utils.router,
        admin_commands.router,

        parse_menu.router,
        gumtree.router,
        poshmark.router,
        poshmark_ca.router,
        lalafo.router,
        lalafo_kg.router,

        params_menu.router,
        make_preset.router,
        edit_preset.router,
        edit_whatsapp.router,

        shop_menu.router
    )

    task_polling = dp.start_polling(bot)

    task_scheduler = start_scheduler()

    await asyncio.gather(task_polling, task_scheduler)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('иди нахуй')
