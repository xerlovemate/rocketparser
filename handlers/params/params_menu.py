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


@router.callback_query(F.data == 'params')
async def params_main_menu(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            await update_settings_message(
                callback,
                only_with_numbers=user.only_with_numbers,
                only_with_delivery=user.only_with_delivery,
                find_without_rating=user.find_without_rating
            )

        else:
            await callback.answer("Перезапустите бота через /start", show_alert=True)



@router.callback_query(F.data.in_([
    'edit_only_with_numbers',
    'edit_only_with_delivery',
    'edit_find_without_rating'
]))
async def toggle_user_setting(callback: CallbackQuery):
    field_map = {
        'edit_only_with_numbers': 'only_with_numbers',
        'edit_only_with_delivery': 'only_with_delivery',
        'edit_find_without_rating': 'find_without_rating'
    }

    field = field_map[callback.data]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            current_value = getattr(user, field)
            setattr(user, field, not current_value)

            # Читаем значения ДО выхода из контекста
            only_with_numbers = user.only_with_numbers
            only_with_delivery = user.only_with_delivery
            find_without_rating = user.find_without_rating

            await session.commit()

            await update_settings_message(callback,
                                          only_with_numbers=only_with_numbers,
                                          only_with_delivery=only_with_delivery,
                                          find_without_rating=find_without_rating)
        else:
            await callback.answer("Перезапустите бота через /start", show_alert=True)


async def update_settings_message(callback: CallbackQuery,
                                  only_with_numbers: bool,
                                  only_with_delivery: bool,
                                  find_without_rating: bool):
    def get_symbol(value: bool) -> str:
        return '✅' if value else '❌'

    text = (f'<b>Настройки:</b>\n'
            f'<b>🗂️ Пресеты: {await rq.get_preset_count_by_tg_id(callback.from_user.id)} шт.</b>\n'
            f'<b>⚙️ Текст WhatsApp: {await rq.get_WA_text_by_tg_id(callback.from_user.id)}</b>')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙️ Пресеты', callback_data='my_presets'),
         InlineKeyboardButton(text='⚙️ Текст WhatsApp', callback_data='text_whatsapp')],
        [InlineKeyboardButton(text='⚙️ Доп. настройки площадок', callback_data='dop_params')],
        [InlineKeyboardButton(text=f'{get_symbol(only_with_numbers)} Только с номерами', callback_data='edit_only_with_numbers'),
         InlineKeyboardButton(text=f'{get_symbol(only_with_delivery)} Только с доставкой', callback_data='edit_only_with_delivery')],
        [InlineKeyboardButton(text=f'{get_symbol(find_without_rating)} Искать без рейтинга', callback_data='edit_find_without_rating')],
        [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
    ])

    await callback.message.edit_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )


@router.callback_query(F.data == 'dop_params')
async def dop_params(callback: CallbackQuery):
    await callback.answer()

