import re
import asyncio
from datetime import datetime
from lxml import html
from bs4 import BeautifulSoup
import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import async_session, POSHMARK_COM

BASE_URL = "https://poshmark.com/"

def clean_post_url(post_url):
    match = re.search(r"(listing/).*?-([a-f0-9]+)$", post_url)
    return match.group(1) + match.group(2) if match else post_url

def format_sold_count(sold_text):
    if sold_text == "--":
        return 0
    sold_text = sold_text.replace("+", "").replace(",", "").strip()
    sold_text_lower = sold_text.lower()
    if "k" in sold_text_lower:
        return int(float(sold_text_lower.replace("k", "")) * 1000)
    return int(sold_text)

async def add_data_to_db(session: AsyncSession, link, seller_name, price, items_count, items_sold):
    result = await session.execute(select(POSHMARK_COM).filter_by(seller_name=seller_name))
    existing_entry = result.scalars().first()

    if existing_entry is None:
        poshmark_entry = POSHMARK_COM(
            price=price,
            link=link,
            seller_name=seller_name,
            items_count=items_count,
            items_sold=items_sold,
            parse_date=datetime.now().strftime('%Y-%m-%d')
        )
        session.add(poshmark_entry)
        await session.commit()
        print(f"Товар {link} добавлен в POSHMARK_COM.")
    else:
        print(f"Объявление с seller_name '{seller_name}' уже существует в базе данных.")

async def parse_poshmark():
    urls = [
        "https://poshmark.com/category/Men?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Women?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Kids?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Home?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Electronics?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Women-Makeup?availability=available&sort_by=added_desc&all_size=true&my_size=false",
        "https://poshmark.com/category/Women-Jewelry?availability=available&sort_by=added_desc&all_size=true&my_size=false"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    async with aiohttp.ClientSession(headers=headers) as http_session:
        while True:
            for url in urls:
                try:
                    async with http_session.get(url) as response:
                        if response.status != 200:
                            print(f"Ошибка загрузки {url} | Статус: {response.status}")
                            continue

                        text = await response.text()

                    bs = BeautifulSoup(text, "html.parser")
                    all_items = bs.find_all("div", class_="card")

                    print(f"Найдено товаров на странице {url}: {len(all_items)}")

                    for item in all_items:
                        link_tag = item.find("a", class_="tile__covershot")
                        href = link_tag["href"].lstrip("/") if link_tag else None
                        post_url = BASE_URL + href if href else None

                        seller_tag = item.find("span", class_="tc--g")
                        seller_name = seller_tag.text.strip().lower() if seller_tag else None

                        if not post_url or not seller_name:
                            continue

                        async with http_session.get(post_url) as post_response:
                            if post_response.status != 200:
                                print(f"Ошибка загрузки поста {post_url} | Статус: {post_response.status}")
                                continue

                            post_text = await post_response.text()

                        post_bs = BeautifulSoup(post_text, "html.parser")

                        likes_block = post_bs.find("div", class_="p--l--3 p--r--2")
                        if likes_block:
                            print(f"Пропущен {seller_name}, т.к. есть лайки.")
                            continue

                        sold_listings_block = post_bs.find("div", class_="tc--g m--l--1 as--fs")
                        if not sold_listings_block:
                            print(f"{BASE_URL + clean_post_url(post_url)} | {seller_name} | Продано: не найдено (блок отсутствует)")
                            continue

                        sold_count_tag = sold_listings_block.find("h4", class_="fw--med tc--b")
                        if not sold_count_tag:
                            print(f"{BASE_URL + clean_post_url(post_url)} | {seller_name} | Продано: не найдено (нет числа)")
                            continue

                        sold_text = sold_count_tag.text.strip()
                        sold_count = format_sold_count(sold_text)

                        all_listings_block = post_bs.find('div', class_='tc--g as--fs')
                        all_count_tag = all_listings_block.find("h4", class_="fw--med tc--b")
                        if not all_count_tag:
                            print(f"{BASE_URL + clean_post_url(post_url)} | {seller_name} | Всего: не найдено (нет числа)")
                            continue

                        all_count_text = all_count_tag.text.strip()
                        try:
                            items_count = int(all_count_text.replace(",", "").strip())
                        except ValueError:
                            items_count = 0

                        tree = html.fromstring(post_text)
                        price_text = tree.xpath('//*[@id="content"]/div/div/div[3]/div[2]/div[3]/p/text()')

                        if price_text:
                            price = float(price_text[0].strip().replace('$', '').replace(',', ''))
                        else:
                            price = 0.0

                        link = f"{BASE_URL + clean_post_url(post_url)}"

                        async with async_session() as session:
                            await add_data_to_db(session, link, seller_name, price, items_count, sold_count)

                        print(f"Проверка завершена: {link} | Продано: {sold_count} | Всего: {items_count}")

                except Exception as e:
                    print(f"Ошибка при обработке URL {url}: {e}")



if __name__ == "__main__":
    asyncio.run(parse_poshmark())
