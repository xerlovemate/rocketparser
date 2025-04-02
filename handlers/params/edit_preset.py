from aiogram import Router, Bot, F, types
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

@router.callback_query(F.data.startswith("preset_"))
async def show_preset(callback: CallbackQuery):
    preset_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()

    if not preset:
        await callback.answer("Пресет не найден", show_alert=True)
        return

    # Формируем описание
    def f(value): return value if value else "Не использовать фильтр"

    caption = (
        f"<b>🏷 Название пресета: {preset.name}\n"
        f"💶 Диапазон цен на товары: {f(preset.price_diapazone)}\n"
        f"🕒 Мин дата рег. продавца: {f(preset.min_reg_day)}\n"
        f"🕒 Макс дата рег. продавца:  {f(preset.max_reg_day)}\n"
        f"👀️ Максимальное кол-во просмотров на сайте: {f(preset.max_views)}\n"
        f"🗂️ Максимальное кол-во объявлений продавца: {f(preset.max_posts)}\n"
        f"🗂️ Максимальное кол-во проданных товаров продавцом:  {f(preset.max_sold)}\n"
        f"🗂️ Максимальное кол-во купленных товаров продавцом: {f(preset.max_bought)}</b>"
    )

    # Клавиатура
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💶 Диапазон цен на товары", callback_data=f"edit_price_{preset.id}"),
        InlineKeyboardButton(text="👀️ Просмотров на сайте", callback_data=f"edit_views_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🕓 Мин. дата рег. продавца", callback_data=f"edit_minreg_{preset.id}"),
        InlineKeyboardButton(text="🕓 Макс дата рег. продавца", callback_data=f"edit_maxreg_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗂️ Объявлений продавца", callback_data=f"edit_posts_{preset.id}"),
        InlineKeyboardButton(text="🗂️ Кол-во проданных", callback_data=f"edit_sold_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗂️ Кол-во купленных", callback_data=f"edit_bought_{preset.id}"),
        InlineKeyboardButton(text="🗑️ Удалить пресет", callback_data=f"delete_preset_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="my_presets")
    )
    await callback.message.edit_caption(
        caption=caption,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("delete_preset_"))
async def delete_preset(callback: CallbackQuery):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()

        if not preset:
            await callback.answer("Пресет не найден", show_alert=True)
            return

        await session.delete(preset)
        await session.commit()

    await callback.message.edit_caption(
        caption="🗑️ <b>Пресет успешно удалён.</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="my_presets")]
        ])
    )


class EditPresetState(StatesGroup):
    editing_price = State()
    editing_views = State()
    editing_minreg = State()
    editing_maxreg = State()
    editing_posts = State()
    editing_sold = State()
    editing_bought = State()


async def show_preset_by_id(preset_id: int, callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()

    if not preset:
        await callback.answer("Пресет не найден", show_alert=True)
        return

    def f(value): return value if value else "Не использовать фильтр"

    caption = (
        f"<b>🏷 Название пресета: {preset.name}\n"
        f"💶 Диапазон цен на товары: {f(preset.price_diapazone)}\n"
        f"🕒 Мин дата рег. продавца: {f(preset.min_reg_day)}\n"
        f"🕒 Макс дата рег. продавца:  {f(preset.max_reg_day)}\n"
        f"👀️ Максимальное кол-во просмотров на сайте: {f(preset.max_views)}\n"
        f"🗂️ Максимальное кол-во объявлений продавца: {f(preset.max_posts)}\n"
        f"🗂️ Максимальное кол-во проданных товаров продавцом:  {f(preset.max_sold)}\n"
        f"🗂️ Максимальное кол-во купленных товаров продавцом: {f(preset.max_bought)}</b>"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💶 Диапазон цен на товары", callback_data=f"edit_price_{preset.id}"),
        InlineKeyboardButton(text="👀️ Просмотров на сайте", callback_data=f"edit_views_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🕓 Мин. дата рег. продавца", callback_data=f"edit_minreg_{preset.id}"),
        InlineKeyboardButton(text="🕓 Макс дата рег. продавца", callback_data=f"edit_maxreg_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗂️ Объявлений продавца", callback_data=f"edit_posts_{preset.id}"),
        InlineKeyboardButton(text="🗂️ Кол-во проданных", callback_data=f"edit_sold_{preset.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗂️ Кол-во купленных", callback_data=f"edit_bought_{preset.id}"),
        InlineKeyboardButton(text="🗑️ Удалить пресет", callback_data=f"delete_preset_{preset.id}")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="my_presets"))

    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("edit_price_"))
async def edit_price(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_price)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = (f'<b>Введите диапазон цен на товары:\n'
            f'Пример: <code>1-9999999</code></b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_price_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_price_'))
async def skip_price_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.price_diapazone = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_price)
async def save_price_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.price_diapazone = message.text
            await session.commit()

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_views_"))
async def edit_views(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_views)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = (f'<b>Введите максимальное кол-во просмотров на сайте:\n'
            f'Пример: <code>100</code></b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_views_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_views_'))
async def skip_views_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_views = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_views)
async def save_views_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_views = int(message.text)
            await session.commit()

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_minreg_"))
async def edit_minreg(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_minreg)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = (f'<b>Введите минимальную дату регистрации продавца:\n'
            f'Пример: <code>2023-01-01</code></b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_minreg_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_minreg_'))
async def skip_minreg_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.min_reg_day = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_minreg)
async def save_minreg_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.min_reg_day = message.text
            await session.commit()

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_maxreg_"))
async def edit_maxreg(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_maxreg)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = (f'<b>Введите максимальную дату регистрации продавца:\n'
            f'Пример: <code>2025-12-31</code></b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_maxreg_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_maxreg_'))
async def skip_maxreg_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_reg_day = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_maxreg)
async def save_maxreg_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_reg_day = message.text
            await session.commit()

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_posts_"))
async def edit_posts(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_posts)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = "<b>Введите максимальное количество объявлений продавца:\nПример: <code>5</code></b>"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_posts_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_posts_'))
async def skip_posts_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_posts = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_posts)
async def save_posts_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            try:
                preset.max_posts = int(message.text)
                await session.commit()
            except ValueError:
                await message.answer("❌ Введите число.")
                return

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_sold_"))
async def edit_sold(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_sold)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = "<b>Введите максимальное количество проданных товаров продавцом:\nПример: <code>3</code></b>"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_sold_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_sold_'))
async def skip_sold_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_sold = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_sold)
async def save_sold_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            try:
                preset.max_sold = int(message.text)
                await session.commit()
            except ValueError:
                await message.answer("❌ Введите число.")
                return

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)


@router.callback_query(F.data.startswith("edit_bought_"))
async def edit_bought(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])
    await state.set_state(EditPresetState.editing_bought)
    await state.update_data(preset_id=preset_id, message_id=callback.message.message_id)

    text = (f'<b>Введите макс. кол-во купленных товаров продавцом:\n'
            f'Пример: <code>5</code></b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не использовать фильтр", callback_data=f'skip_bought_{preset_id}')]
    ])
    await callback.message.edit_caption(caption=text, parse_mode='HTML', reply_markup=markup)


@router.callback_query(F.data.startswith('skip_bought_'))
async def skip_bought_filter(callback: CallbackQuery, state: FSMContext):
    preset_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_bought = None
            await session.commit()

    await state.clear()
    await show_preset_by_id(preset_id, callback)


@router.message(EditPresetState.editing_bought)
async def save_bought_value(message: Message, state: FSMContext):
    data = await state.get_data()
    preset_id = data.get("preset_id")
    message_id = data.get("message_id")
    await message.delete()

    async with async_session() as session:
        result = await session.execute(select(Preset).where(Preset.id == preset_id))
        preset = result.scalar_one_or_none()
        if preset:
            preset.max_bought = int(message.text)
            await session.commit()

    await state.clear()

    class DummyCallback:
        def __init__(self, message, from_user):
            self.message = message
            self.from_user = from_user
        async def answer(self, *args, **kwargs):
            pass

    dummy_callback = DummyCallback(
        message=types.Message(
            message_id=message_id,
            chat=message.chat,
            date=message.date,
        ),
        from_user=message.from_user
    )
    await show_preset_by_id(preset_id, dummy_callback)
