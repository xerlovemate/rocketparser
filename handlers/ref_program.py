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

@router.callback_query(F.data == 'referal')
async def referal(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_help_menu')],
        [InlineKeyboardButton(text='⏪ Главное меню', callback_data='back_to_main_menu')]
    ])

    text = (f'<b>За каждое пополнение вашего реферала вы получаете 15% на свой баланс</b>\n\n'
            f'<b>Ваша реферальная ссылка: https://t.me/rocketparserbot?start={callback.from_user.id}</b>\n\n'
            f'<b>Количество рефералов: {await rq.get_refferal_count_by_tg_id(callback.from_user.id)}</b>')

    await callback.message.edit_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=kb
    )