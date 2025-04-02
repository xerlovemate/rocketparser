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


# ================== /start handler ==================
@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (f'<b>🥷 ID: <code>{message.from_user.id}</code></b>\n\n'
            f'<b>Баланс: {await rq.get_balance_by_tg_id(message.from_user.id)} USDT</b>\n'
            f'<b>Рефералов: {await rq.get_refferal_count_by_tg_id(message.from_user.id)}</b>\n\n'
            f'<b>Бот находится в разработке, но вы можете в ней <a href="https://t.me/rocketparsernews">поучаствовать</a></b>')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪐 Парсить", callback_data="parse_menu")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data='depozit')],
        [InlineKeyboardButton(text='Настройки', callback_data="params")],
        [InlineKeyboardButton(text='Помощь', callback_data='help')]
    ])

    home_photo = FSInputFile(path='media/main_photo.jpg')

    promo_code = None
    if message.text and len(message.text.split()) > 1:
        promo_code = message.text.split()[1]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()

        is_self_ref = promo_code == str(message.from_user.id)

        if user:
            # Если промокод есть, пользователь сам себе не реферал, и промо ещё не записан
            if promo_code and not is_self_ref and not user.promocode:
                user.promocode = promo_code

                # Увеличим счётчик у пригласившего
                result_ref = await session.execute(select(User).where(User.tg_id == int(promo_code)))
                ref_user = result_ref.scalar_one_or_none()
                if ref_user:
                    ref_user.refferal_count += 1

                await session.commit()
        else:
            new_user = User(
                tg_id=message.from_user.id,
                tg_username=message.from_user.username or "Unknown",
                promocode=None if is_self_ref else promo_code
            )
            session.add(new_user)

            if promo_code and not is_self_ref:
                result_ref = await session.execute(select(User).where(User.tg_id == int(promo_code)))
                ref_user = result_ref.scalar_one_or_none()
                if ref_user:
                    ref_user.refferal_count += 1

            await session.commit()

    await message.answer_photo(photo=home_photo,
                               caption=text,
                               reply_markup=markup,
                               parse_mode="HTML")


@router.callback_query(F.data == 'back_to_main_menu')
async def back_to_main_menu(callback: CallbackQuery):
    text = (f'<b>🥷 ID: <code>{callback.from_user.id}</code></b>\n\n'
            f'<b>Баланс: {await rq.get_balance_by_tg_id(callback.from_user.id)} USDT</b>\n'
            f'<b>Рефералов: {await rq.get_refferal_count_by_tg_id(callback.from_user.id)}</b>\n\n'
            f'<b>Бот находится в разработке, но вы можете в ней <a href="https://t.me/rocketparsernews">поучаствовать</a></b>')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪐 Парсить", callback_data="parse_menu")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data='depozit')],
        [InlineKeyboardButton(text='Настройки', callback_data="params")],
        [InlineKeyboardButton(text='Помощь', callback_data='help')]
    ])

    await callback.message.edit_caption(
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )