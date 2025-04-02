from sqlalchemy import BigInteger, String, DateTime, Integer, Column, Boolean, ForeignKey, Text, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """Класс пользователей"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    tg_username: Mapped[str] = mapped_column(String, nullable=False)

    balance: Mapped[float] = mapped_column(Float, default=0.00)
    all_deps: Mapped[float] = mapped_column(Float, default=0.00)

    promocode: Mapped[str] = mapped_column(String, nullable=True)
    refferal_count: Mapped[int] = mapped_column(Integer, default=0)

    only_with_numbers: Mapped[bool] = mapped_column(Boolean, default=False)
    only_with_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    find_without_rating: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_text: Mapped[str] = mapped_column(String, nullable=True)

    preset_id: Mapped[int] = mapped_column(Integer, nullable=True)


class Preset(Base):
    """Класс пресетов"""
    __tablename__ = 'presets'

    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    min_reg_day: Mapped[str] = mapped_column(String, nullable=True)
    max_reg_day: Mapped[str] = mapped_column(String, nullable=True)
    price_diapazone: Mapped[str] = mapped_column(String, nullable=True)
    max_posts: Mapped[int] = mapped_column(Integer, nullable=True)
    max_views: Mapped[int] = mapped_column(Integer, nullable=True)
    max_sold: Mapped[int] = mapped_column(Integer, nullable=True)
    max_bought: Mapped[int] = mapped_column(Integer, nullable=True)


class GUMTREE(Base):
    """Класс gumtree.co.za"""
    __tablename__ = 'gumtree'

    id: Mapped[int] = mapped_column(primary_key=True)

    is_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delivery: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_rating: Mapped[bool] = mapped_column(Boolean, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)

    seller_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    seller_direct: Mapped[str] = mapped_column(String, nullable=False)
    reg_date: Mapped[str] = mapped_column(String, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    items_sold: Mapped[int] = mapped_column(Integer, nullable=True)
    items_bought: Mapped[int] = mapped_column(Integer, nullable=True)

    parse_date: Mapped[str] = mapped_column(String, nullable=False)


class POSHMARK_COM(Base):
    """Класс POSHMARK COM"""
    __tablename__ = 'poshmark_com'

    id: Mapped[int] = mapped_column(primary_key=True)

    is_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=True)
    delivery: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_rating: Mapped[bool] = mapped_column(Boolean, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=False)

    seller_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    seller_direct: Mapped[str] = mapped_column(String, nullable=True)
    reg_date: Mapped[str] = mapped_column(String, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    items_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    items_bought: Mapped[int] = mapped_column(Integer, nullable=True)

    parse_date: Mapped[str] = mapped_column(String, nullable=False)


class POSHMARK_CA(Base):
    """Класс POSHMARK CA"""
    __tablename__ = 'poshmark_ca'

    id: Mapped[int] = mapped_column(primary_key=True)

    is_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=True)
    delivery: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_rating: Mapped[bool] = mapped_column(Boolean, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=False)

    seller_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    seller_direct: Mapped[str] = mapped_column(String, nullable=True)
    reg_date: Mapped[str] = mapped_column(String, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    items_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    items_bought: Mapped[int] = mapped_column(Integer, nullable=True)

    parse_date: Mapped[str] = mapped_column(String, nullable=False)


class LALAFO_RS(Base):
    """Класс LALAFO_RS"""
    __tablename__ = 'lalafo_rs'

    id: Mapped[int] = mapped_column(primary_key=True)

    is_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delivery: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_rating: Mapped[bool] = mapped_column(Boolean, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=True)
    views: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=True)

    seller_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    seller_direct: Mapped[str] = mapped_column(String, nullable=True)
    reg_date: Mapped[str] = mapped_column(String, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, nullable=True)
    items_sold: Mapped[int] = mapped_column(Integer, nullable=True)
    items_bought: Mapped[int] = mapped_column(Integer, nullable=True)

    parse_date: Mapped[str] = mapped_column(String, nullable=False)


class LALAFO_KG(Base):
    """Класс LALAFO_KG"""
    __tablename__ = 'lalafo_kg'

    id: Mapped[int] = mapped_column(primary_key=True)

    is_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delivery: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_rating: Mapped[bool] = mapped_column(Boolean, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=True)
    views: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=True)

    seller_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    seller_direct: Mapped[str] = mapped_column(String, nullable=True)
    reg_date: Mapped[str] = mapped_column(String, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, nullable=True)
    items_sold: Mapped[int] = mapped_column(Integer, nullable=True)
    items_bought: Mapped[int] = mapped_column(Integer, nullable=True)

    parse_date: Mapped[str] = mapped_column(String, nullable=False)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
