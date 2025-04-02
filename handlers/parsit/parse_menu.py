from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from sqlalchemy.future import select

import config
import database.requests as rq
from database.db import async_session, User, Preset

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


@router.callback_query(F.data == 'parse_menu')
async def parse_main_menu(callback: CallbackQuery):
    tg_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

    if user:
        presets_kb = InlineKeyboardMarkup(inline_keyboard=[])

        if user.preset_id is None:
            async with async_session() as session:
                presets_result = await session.execute(select(Preset).filter_by(tg_id=tg_id))
                presets = presets_result.scalars().all()

                if presets:
                    for preset in presets:
                        presets_kb.inline_keyboard.append(
                            [InlineKeyboardButton(text=preset.name, callback_data=f"choose_preset_{preset.id}")])

            presets_kb.inline_keyboard.append(
                [InlineKeyboardButton(text="➕ Добавить пресет", callback_data="add_preset")]
            )
            presets_kb.inline_keyboard.append(
                [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_main_menu')]
            )

            await callback.message.edit_caption(
                caption="<b>Для начала выберите или создайте пресет:</b>",
                parse_mode='HTML',
                reply_markup=presets_kb
            )
        else:
            parse_services_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🌎 POSHMARK', callback_data='choose_poshmark'),
                 InlineKeyboardButton(text='🌎 LALAFO', callback_data='choose_lalafo')],
                [InlineKeyboardButton(text='🇿🇦 GUMTREE.CO.ZA', callback_data='parse_gumtree')],
                [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
            ])

            await callback.message.edit_caption(
                caption='<b>Выберите сервис:</b>',
                parse_mode='HTML',
                reply_markup=parse_services_kb
            )
    else:
        await callback.message.answer("Ошибка! Пользователь не найден.")



@router.callback_query(F.data.startswith("choose_preset_"))
async def choose_preset(callback: CallbackQuery):
    preset_id = int(callback.data.split("_")[2])

    tg_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if user:
            user.preset_id = preset_id
            await session.commit()

            parse_services_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🌎 POSHMARK', callback_data='choose_poshmark'),
                 InlineKeyboardButton(text='🌎 LALAFO', callback_data='choose_lalafo')],
                [InlineKeyboardButton(text='🇿🇦 GUMTREE.CO.ZA', callback_data='parse_gumtree')],
                [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
            ])

            await callback.message.edit_caption(
                caption='<b>Выберите сервис:</b>',
                parse_mode='HTML',
                reply_markup=parse_services_kb
            )
        else:
            await callback.answer("Пользователь не найден.")


@router.callback_query(F.data == 'choose_another_preset')
async def choose_another_preset(callback: CallbackQuery):
    tg_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

    if user:
        presets_kb = InlineKeyboardMarkup(inline_keyboard=[])

        async with async_session() as session:
            presets_result = await session.execute(select(Preset).filter_by(tg_id=tg_id))
            presets = presets_result.scalars().all()

            if presets:
                for preset in presets:
                    presets_kb.inline_keyboard.append(
                        [InlineKeyboardButton(text=preset.name, callback_data=f"choose_preset_{preset.id}")])

        presets_kb.inline_keyboard.append(
            [InlineKeyboardButton(text="➕ Добавить пресет", callback_data="add_preset")]
        )
        presets_kb.inline_keyboard.append(
            [InlineKeyboardButton(text='◀️ Назад', callback_data='parse_menu')]
        )

        await callback.message.edit_caption(
            caption="<b>Выберите пресет:</b>",
            parse_mode='HTML',
            reply_markup=presets_kb
        )