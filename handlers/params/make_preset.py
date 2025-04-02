from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from datetime import date
import config
import database.requests as rq
from database.db import async_session, User, Preset

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


@router.callback_query(F.data == 'my_presets')
async def presets_main_menu(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    async with async_session() as session:
        result = await session.execute(
            select(Preset).where(Preset.tg_id == callback.from_user.id)
        )
        presets = result.scalars().all()

    for preset in presets:
        builder.button(
            text=preset.name,
            callback_data=f"preset_{preset.id}"
        )

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="➕ Добавить пресет", callback_data="add_preset"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="params"))

    await callback.message.edit_caption(
        caption="<b>Пресеты:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


class AddPresetState(StatesGroup):
    waiting_for_name = State()
    waiting_for_min_reg_day = State()
    waiting_for_max_reg_day = State()
    waiting_for_price_diapazone = State()
    waiting_for_max_posts = State()
    waiting_for_max_views = State()
    waiting_for_max_sold = State()
    waiting_for_max_bought = State()


@router.callback_query(F.data == 'add_preset')
async def start_add_preset(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_caption(
        caption="✍️ <b>Введите название пресета:</b>",
        parse_mode='HTML'
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AddPresetState.waiting_for_name)


@router.message(AddPresetState.waiting_for_name)
async def preset_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_min_reg")]
    ])

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption="🕒 <b>Введите минимальную дату регистрации продавца:\n\n"
                "Пример: <code>2022-01-31</code></b>\n",
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_min_reg_day)


@router.message(AddPresetState.waiting_for_min_reg_day)
async def preset_min_reg(message: Message, state: FSMContext):
    await state.update_data(min_reg_day=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']
    today = date.today().strftime("%Y-%m-%d")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_max_reg")]
    ])

    text = (f"🕒 <b>Введите максимальную дату регистрации продавца:\n\n"
            f"Пример: <code>{today}</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_max_reg_day)


@router.message(AddPresetState.waiting_for_max_reg_day)
async def preset_max_reg(message: Message, state: FSMContext):
    await state.update_data(max_reg_day=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_price")]
    ])

    text = ("<b>💶 Введите диапазон цен на товары:\n"
            "Примеры:\n"
            "- <code>1-9999999</code>\n"
            "- <code>Не использовать фильтр</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_price_diapazone)


@router.message(AddPresetState.waiting_for_price_diapazone)
async def preset_price(message: Message, state: FSMContext):
    await state.update_data(price_diapazone=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_posts")]
    ])

    text = ("🗂️ <b>Введите максимальное кол-во объявлений у продавца:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_max_posts)


@router.message(AddPresetState.waiting_for_max_posts)
async def preset_max_posts(message: Message, state: FSMContext):
    await state.update_data(max_posts=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_views")]
    ])

    text = ("<b>👀 Введите максимальное кол-во просмотров на сайте:\n"
            "Примеры:\n"
            "- <code>100</code>\n"
            "- <code>Не использовать фильтр</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_max_views)


@router.message(AddPresetState.waiting_for_max_views)
async def preset_max_views(message: Message, state: FSMContext):
    await state.update_data(max_views=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_sold")]
    ])

    text = ("<b>🗂 Введите максимальное кол-во проданных товаров продавцом:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_max_sold)


@router.message(AddPresetState.waiting_for_max_sold)
async def preset_max_sold(message: Message, state: FSMContext):
    await state.update_data(max_sold=message.text)
    await message.delete()

    data = await state.get_data()
    bot_msg_id = data['bot_message_id']

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_bought")]
    ])

    text = ("<b>🗂 Введите максимальное кол-во купленных товаров продавцом:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=markup
    )
    await state.set_state(AddPresetState.waiting_for_max_bought)


@router.message(AddPresetState.waiting_for_max_bought)
async def preset_max_bought(message: Message, state: FSMContext):
    await message.delete()
    await state.update_data(max_bought=message.text)
    data = await state.get_data()

    async with async_session() as session:
        preset = Preset(
            tg_id=message.from_user.id,
            name=data['name'],
            min_reg_day=None if "не использовать" in data['min_reg_day'].lower() else data['min_reg_day'],
            max_reg_day=None if "не использовать" in data['max_reg_day'].lower() else data['max_reg_day'],
            price_diapazone=None if "не использовать" in data['price_diapazone'].lower() else data['price_diapazone'],
            max_posts=None if "не использовать" in data['max_posts'].lower() else int(data['max_posts']),
            max_views=None if "не использовать" in data['max_views'].lower() else int(data['max_views']),
            max_sold=None if "не использовать" in data['max_sold'].lower() else int(data['max_sold']),
            max_bought=None if "не использовать" in data['max_bought'].lower() else int(data['max_bought']),
        )
        session.add(preset)
        await session.commit()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='params')]
    ])

    await message.bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=data['bot_message_id'],
        caption=f"✅ Пресет <b>{data['name']}</b> успешно создан!",
        parse_mode='HTML',
        reply_markup=markup
    )

    await state.clear()


@router.callback_query(F.data == 'skip_min_reg')
async def skip_min_reg(callback: CallbackQuery, state: FSMContext):
    await state.update_data(min_reg_day="Не использовать фильтр")
    today = date.today().strftime("%Y-%m-%d")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_max_reg")]
    ])
    text = (f"🕒 <b>Введите максимальную дату регистрации продавца:\n\n"
            f"Пример: <code>{today}</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_max_reg_day)


@router.callback_query(F.data == 'skip_max_reg')
async def skip_max_reg(callback: CallbackQuery, state: FSMContext):
    await state.update_data(max_reg_day="Не использовать фильтр")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_price")]
    ])
    text = ("<b>💶 Введите диапазон цен на товары:\n"
            "Примеры:\n"
            "- <code>1-9999999</code>\n"
            "- <code>Не использовать фильтр</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_price_diapazone)


@router.callback_query(F.data == 'skip_price')
async def skip_price(callback: CallbackQuery, state: FSMContext):
    await state.update_data(price_diapazone="Не использовать фильтр")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_posts")]
    ])
    text = ("🗂️ <b>Введите максимальное кол-во объявлений у продавца:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_max_posts)


@router.callback_query(F.data == 'skip_posts')
async def skip_posts(callback: CallbackQuery, state: FSMContext):
    await state.update_data(max_posts="Не использовать фильтр")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_views")]
    ])
    text = ("<b>👀 Введите максимальное кол-во просмотров на сайте:\n"
            "Примеры:\n"
            "- <code>100</code>\n"
            "- <code>Не использовать фильтр</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_max_views)


@router.callback_query(F.data == 'skip_views')
async def skip_views(callback: CallbackQuery, state: FSMContext):
    await state.update_data(max_views="Не использовать фильтр")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_sold")]
    ])
    text = ("<b>🗂 Введите максимальное кол-во проданных товаров продавцом:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_max_sold)


@router.callback_query(F.data == 'skip_sold')
async def skip_sold(callback: CallbackQuery, state: FSMContext):
    await state.update_data(max_sold="Не использовать фильтр")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data="skip_bought")]
    ])
    text = ("<b>🗂 Введите максимальное кол-во купленных товаров продавцом:\n"
            "Примеры:\n"
            "- <code>2</code>\n"
            "- <code>Не использовать фильтр</code></b>")
    await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=markup)
    await state.set_state(AddPresetState.waiting_for_max_bought)


@router.callback_query(F.data == 'skip_bought')
async def skip_bought(callback: CallbackQuery, state: FSMContext):
    await state.update_data(max_bought="Не использовать фильтр")
    data = await state.get_data()

    async with async_session() as session:
        preset = Preset(
            tg_id=callback.from_user.id,
            name=data['name'],
            min_reg_day=None if "не использовать" in data['min_reg_day'].lower() else data['min_reg_day'],
            max_reg_day=None if "не использовать" in data['max_reg_day'].lower() else data['max_reg_day'],
            price_diapazone=None if "не использовать" in data['price_diapazone'].lower() else data['price_diapazone'],
            max_posts=None if "не использовать" in data['max_posts'].lower() else int(data['max_posts']),
            max_views=None if "не использовать" in data['max_views'].lower() else int(data['max_views']),
            max_sold=None if "не использовать" in data['max_sold'].lower() else int(data['max_sold']),
            max_bought=None if "не использовать" in data['max_bought'].lower() else int(data['max_bought']),
        )
        session.add(preset)
        await session.commit()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data='params')]
    ])

    await callback.message.edit_caption(
        caption=f"✅ Пресет <b>{data['name']}</b> успешно создан!",
        parse_mode='HTML',
        reply_markup=markup
    )

    await state.clear()
