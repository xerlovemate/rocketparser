from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from sqlalchemy.future import select

import config
import database.requests as rq
from database.db import async_session, User
from aiogram.fsm.state import StatesGroup, State


router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


class WhatsAppTextState(StatesGroup):
    waiting_for_text = State()


@router.callback_query(F.data == 'text_whatsapp')
async def edit_text_whatsapp(callback: CallbackQuery, state: FSMContext):
    text = (f'<b>Для вставки названия в текст @title\n'
            f'Для вставки ссылки в текст @link\n'
            f'Для вставки цены в текст @price\n\n'
            f'Пример: Здравствуйте. @title за @price ещё актуально?\n'
            f'На выходе получаем: Здравствуйте. Кроссовки за 7000 RUB ещё актуально?</b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='params')]
    ])

    await callback.message.edit_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )

    await state.set_state(WhatsAppTextState.waiting_for_text)
    await state.update_data(bot_message_id=callback.message.message_id)


@router.message(WhatsAppTextState.waiting_for_text)
async def save_whatsapp_text(message: Message, state: FSMContext):
    user_text = message.text

    # Удаляем сообщение пользователя
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            user.whatsapp_text = user_text
            await session.commit()

            data = await state.get_data()
            bot_msg_id = data.get("bot_message_id")

            # Обновляем предыдущее сообщение бота
            if bot_msg_id:
                await message.bot.edit_message_caption(
                    chat_id=message.chat.id,
                    message_id=bot_msg_id,
                    caption="✅ <b>Текст успешно сохранён!</b>",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='◀️ Назад', callback_data='params')]
                    ])
                )

    await state.clear()

