import os

from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery, InputFile
from sqlalchemy import delete
from sqlalchemy.future import select
from datetime import datetime, timedelta
import config
import database.requests as rq
import handlers.utils
from database.db import async_session, User, Preset, GUMTREE, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


@router.callback_query(F.data == 'parse_gumtree')
async def parse_gumtree(callback: CallbackQuery):
    # Получаем tg_id пользователя
    tg_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if user and user.preset_id:
            preset_result = await session.execute(select(Preset).filter_by(id=user.preset_id))
            preset = preset_result.scalars().first()

            if preset:
                def f(value):
                    return value if value is not None else "Не использовать фильтр"

                caption = (
                    f"<b>🇿🇦 GUMTREE.CO.ZA\n"
                    f"Используемый пресет:\n\n"
                    f"🏷 Название пресета: {preset.name}\n"
                    f"💶 Диапазон цен на товары: {f(preset.price_diapazone)}\n"
                    f"🕒 Мин дата рег. продавца: {f(preset.min_reg_day)}\n"
                    f"🕒 Макс дата рег. продавца: {f(preset.max_reg_day)}\n"
                    f"👀️ Максимальное кол-во просмотров на сайте: {f(preset.max_views)}\n"
                    f"🗂️ Максимальное кол-во объявлений продавца: {f(preset.max_posts)}\n"
                    f"🗂️ Максимальное кол-во проданных товаров продавцом: {f(preset.max_sold)}\n"
                    f"🗂️ Максимальное кол-во купленных товаров продавцом: {f(preset.max_bought)}\n\n"
                    f"Выберите дату парсинга:</b>"
                )

                today = datetime.today()
                yesterday = today - timedelta(days=1)
                two_days_ago = today - timedelta(days=2)
                three_days_ago = today - timedelta(days=3)

                today_str = today.strftime("%Y-%m-%d")
                yesterday_str = yesterday.strftime("%Y-%m-%d")
                two_days_ago_str = two_days_ago.strftime("%Y-%m-%d")
                three_days_ago_str = three_days_ago.strftime("%Y-%m-%d")

                choosed_preset = f'💾 Пресет: {preset.name}'

                date_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=today_str, callback_data=f"gumtree_parse_date_{today_str}"),
                     InlineKeyboardButton(text=yesterday_str, callback_data=f"gumtree_parse_date_{yesterday_str}")],
                    [InlineKeyboardButton(text=two_days_ago_str, callback_data=f"gumtree_parse_date_{two_days_ago_str}"),
                     InlineKeyboardButton(text=three_days_ago_str, callback_data=f"gumtree_parse_date_{three_days_ago_str}")],
                    [InlineKeyboardButton(text=choosed_preset, callback_data='choose_another_preset')],
                    [InlineKeyboardButton(text='◀️ Назад', callback_data='parse_menu')]
                ])

                await callback.message.edit_caption(
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=date_kb
                )
            else:
                await callback.answer("Пресет не найден.")
        else:
            await callback.answer("Вы не выбрали пресет или произошла ошибка.")


async def calculate_available_items(preset, user, selected_date=None):
    filters = []

    if preset.min_reg_day:
        filters.append(GUMTREE.reg_date >= preset.min_reg_day)
    if preset.max_reg_day:
        filters.append(GUMTREE.reg_date <= preset.max_reg_day)

    if preset.price_diapazone:
        price_min, price_max = map(int, preset.price_diapazone.split('-'))
        filters.append(GUMTREE.price >= price_min)
        filters.append(GUMTREE.price <= price_max)

    if preset.max_views is not None:
        filters.append(GUMTREE.views <= preset.max_views)
    if preset.max_posts is not None:
        filters.append(GUMTREE.items_count <= preset.max_posts)
    if preset.max_sold is not None:
        filters.append(GUMTREE.items_sold <= preset.max_sold)
    if preset.max_bought is not None:
        filters.append(GUMTREE.items_bought <= preset.max_bought)

    if user.only_with_numbers:
        filters.append(GUMTREE.is_phone_number == True)
    if user.only_with_delivery:
        filters.append(GUMTREE.delivery == True)
    if user.find_without_rating:
        filters.append(GUMTREE.has_rating == False)

    if selected_date:
        filters.append(GUMTREE.parse_date == selected_date)

    print(f"Filters applied: {filters}")

    if filters:
        async with async_session() as session:
            query = select(GUMTREE).filter(*filters)
            result = await session.execute(query)
            ads = result.scalars().all()

            print(f"Filtered ads count: {len(ads)}")
            for ad in ads:
                print(f"Ad ID: {ad.id}, items_count: {ad.items_count}, items_sold: {ad.items_sold}, items_bought: {ad.items_bought}, price: {ad.price}")

            available_items = len(ads)

            print(f"Available items count: {available_items}")
            return available_items
    else:
        print("No filters applied, returning all items.")
        async with async_session() as session:
            result = await session.execute(select(GUMTREE))
            ads = result.scalars().all()

            available_items = len(ads)

            return available_items



class Form(StatesGroup):
    waiting_for_quantity = State()


@router.callback_query(F.data.startswith("gumtree_parse_date_"))
async def parse_date_gumtree(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id

    selected_date = callback.data.split("_")[3]

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if user and user.preset_id:
            preset_result = await session.execute(select(Preset).filter_by(id=user.preset_id))
            preset = preset_result.scalars().first()

            if preset:
                await state.update_data(selected_date=selected_date)

                if selected_date == datetime.today().strftime("%Y-%m-%d"):
                    base_price = 0.003
                elif selected_date == (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"):
                    base_price = 0.002
                elif selected_date == (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"):
                    base_price = 0.001
                elif selected_date == (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"):
                    base_price = 0
                else:
                    base_price = 0

                price_per_ad = round(base_price, 3)

                available_items = await calculate_available_items(preset, user, selected_date)

                caption = (
                    f"<b>Цена за одно объявление: {price_per_ad} USDT\n"
                    f"Доступно к покупке: {available_items}\n"
                    f"Выбранная дата: {selected_date}\n"
                    f"Ваш баланс: {await rq.get_balance_by_tg_id(callback.from_user.id)}</b>\n"
                    f"*Цена зависит от настроек пресета\n\n"
                    f"<b>Отправьте числом необходимое количество объявлений для покупки:</b>"
                )

                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='◀️ Назад', callback_data='parse_gumtree')]
                ])

                sent_message = await callback.message.edit_caption(
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=markup
                )

                await state.update_data(message_id=sent_message.message_id)
                await state.update_data(price_per_ad=price_per_ad)
                await state.update_data(selected_date=selected_date)
                await state.set_state(Form.waiting_for_quantity)

            else:
                await callback.answer("Пресет не найден.")
        else:
            await callback.answer("Вы не выбрали пресет или произошла ошибка.")



@router.message(Form.waiting_for_quantity)
async def handle_quantity_input(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)

        await state.update_data(quantity=quantity)

        tg_id = message.from_user.id

        async with async_session() as session:
            result = await session.execute(select(User).filter_by(tg_id=tg_id))
            user = result.scalars().first()
            if user and user.preset_id:
                preset_result = await session.execute(select(Preset).filter_by(id=user.preset_id))
                preset = preset_result.scalars().first()

                if preset:
                    available_items = await calculate_available_items(preset, user)
                    if quantity <= available_items:
                        user_data = await state.get_data()
                        message_id = user_data.get('message_id')
                        price_per_ad = user_data.get('price_per_ad')
                        total_price = quantity * price_per_ad

                        await state.update_data(total_price=total_price)

                        caption = (
                            f"<b>К оплате: {total_price} USDT</b>\n"
                            f"<b>Нажмите на кнопку, чтобы оплатить.</b>"
                        )

                        markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f'Оплатить {total_price} USDT', callback_data='gumtree_pay')],
                            [InlineKeyboardButton(text='Отмена', callback_data='parse_gumtree')]
                        ])

                        if message_id:
                            await message.bot.edit_message_caption(
                                chat_id=message.chat.id,
                                message_id=message_id,
                                caption=caption,
                                parse_mode='HTML',
                                reply_markup=markup
                            )

                            await message.delete()

                    else:
                        await message.answer(f"Недоступное количество товаров. В наличии только {available_items} товаров.")
                else:
                    await message.answer("Пресет не найден.")
            else:
                await message.answer("Вы не выбрали пресет или произошла ошибка.")

    except ValueError:
        await message.answer("Пожалуйста, введите число.")


async def save_ads_to_txt_and_remove(preset, user, selected_date=None, num_to_write=10):
    filters = []

    if preset.min_reg_day:
        filters.append(GUMTREE.reg_date >= preset.min_reg_day)
    if preset.max_reg_day:
        filters.append(GUMTREE.reg_date <= preset.max_reg_day)

    if preset.price_diapazone:
        price_min, price_max = map(int, preset.price_diapazone.split('-'))
        filters.append(GUMTREE.price >= price_min)
        filters.append(GUMTREE.price <= price_max)

    if preset.max_views is not None:
        filters.append(GUMTREE.views <= preset.max_views)
    if preset.max_posts is not None:
        filters.append(GUMTREE.items_count <= preset.max_posts)
    if preset.max_sold is not None:
        filters.append(GUMTREE.items_sold <= preset.max_sold)
    if preset.max_bought is not None:
        filters.append(GUMTREE.items_bought <= preset.max_bought)

    if user.only_with_numbers:
        filters.append(GUMTREE.is_phone_number == True)
    if user.only_with_delivery:
        filters.append(GUMTREE.delivery == True)
    if user.find_without_rating:
        filters.append(GUMTREE.has_rating == False)

    if selected_date:
        filters.append(GUMTREE.parse_date == selected_date)

    print(f"Filters applied: {filters}")

    async with async_session() as session:
        query = select(GUMTREE).filter(*filters)
        result = await session.execute(query)
        ads = result.scalars().all()

        print(f"Filtered ads count: {len(ads)}")

        ads_to_write = ads[:num_to_write]

        with open("объявления.txt", "a") as file:
            for ad in ads_to_write:
                if ad.phone_number:
                    phone_number = ad.phone_number.replace(" ", "")
                    line = f"{ad.link}, +27{phone_number}\n"
                else:
                    line = f"{ad.link}\n"

                file.write(line)

                await session.execute(delete(GUMTREE).where(GUMTREE.id == ad.id))
            await session.commit()

        print(f"Written {len(ads_to_write)} ads to file and removed from DB.")


@router.callback_query(F.data == 'gumtree_pay')
async def handle_payment(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    user_data = await state.get_data()
    selected_date = user_data.get('selected_date')
    quantity = user_data.get('quantity')
    total_price = user_data.get('total_price')

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if user and user.preset_id:
            preset_result = await session.execute(select(Preset).filter_by(id=user.preset_id))
            preset = preset_result.scalars().first()

            new_balance = user.balance - total_price
            if new_balance < 0:
                await callback.answer("У вас недостаточно средств для этой операции.")
                return

            await rq.minus_balik(tg_id, total_price)

        await save_ads_to_txt_and_remove(preset, user, selected_date, num_to_write=quantity)

        text = f"<b>Оплата произведена успешно!\nВаш новый баланс: {round(new_balance, 3)} USDT.</b>"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
        ])

        await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode='HTML')

        file_path = "объявления.txt"

        input_file = FSInputFile(file_path)

        with open(file_path, 'rb') as file:
            await callback.message.answer_document(input_file, reply_markup=handlers.utils.delete_kb)

        os.remove(file_path)