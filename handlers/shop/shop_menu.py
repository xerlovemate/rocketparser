from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from sqlalchemy.future import select

import config
import database.requests as rq
from database.db import async_session, User

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)

@router.callback_query(F.data == 'shop')
async def shop_main_menu(callback: CallbackQuery):
    await callback.answer('В разработке...', show_alert=True)