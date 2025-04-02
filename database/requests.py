from database.db import async_session, User, Preset, GUMTREE
from sqlalchemy import select, func, delete
from aiogram import Bot
from config import TOKEN

bot = Bot(token=TOKEN)


async def set_user(tg_id: int, username: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.tg_id == tg_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.tg_username = username
            else:
                user = User(
                    tg_id=tg_id,
                    tg_username=username
                )
                session.add(user)

            await session.commit()


async def get_balance_by_tg_id(tg_id: int) -> float:
    async with async_session() as session:
        result = await session.execute(select(User.balance).filter(User.tg_id == tg_id))
        balance = result.scalars().first()

        if balance is None:
            return 0.00

        return round(balance, 3)


async def get_refferal_count_by_tg_id(tg_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(select(User.refferal_count).filter(User.tg_id == tg_id))
        count = result.scalars().first()

        if count is None:
            return 0

        return count


async def add_balance_to_user(tg_id: int, amount: float):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.balance = amount
            await session.commit()
            return True
        else:
            return False


async def get_WA_text_by_tg_id(tg_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(select(User.whatsapp_text).filter(User.tg_id == tg_id))
        text = result.scalars().first()
        if text is None:
            return ''

        return text


async def get_preset_count_by_tg_id(tg_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(Preset).where(Preset.tg_id == tg_id)
        )
        count = result.scalar_one()
        return count or 0


async def get_preset_id_by_tg_id(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if user:
            return user.preset_id
        else:
            return None


async def minus_balik(tg_id: int, total_price: float):
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if not user:
            raise ValueError("User not found")

        new_balance = user.balance - total_price
        if new_balance < 0:
            raise ValueError("Insufficient funds")

        user.balance = new_balance
        session.add(user)

        await session.commit()
