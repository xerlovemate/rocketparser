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


@router.callback_query(F.data.in_(['help', 'back_to_help_menu']))
async def help_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Рефералка', callback_data='referal'),
         InlineKeyboardButton(text='Новостной канал', url='https://t.me/rocketparsernews')],
        [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
    ])
    await callback.message.edit_caption(
        caption='<b>Помощь</b>',
        parse_mode='HTML',
        reply_markup=kb
    )


