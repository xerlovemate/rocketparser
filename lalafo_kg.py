import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from sqlalchemy import select
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from bs4 import BeautifulSoup
import re
from datetime import datetime

from database.db import async_session, LALAFO_KG


async def save_to_db(seller_name, phone_number, price, views_count, reg_date, link):
    async with async_session() as session:
        result = await session.execute(select(LALAFO_KG).filter_by(seller_name=seller_name))
        existing_entry = result.scalars().first()
        if not seller_name:
            return
        if existing_entry is None:
            new_record = LALAFO_KG(
                is_phone_number=True if phone_number else False,
                seller_name=seller_name,
                phone_number=phone_number,
                price=price,
                views=views_count,
                reg_date=reg_date,
                link=link,
                parse_date=datetime.now().strftime('%Y-%m-%d')
            )

            session.add(new_record)
            await session.commit()
        else:
            print(f"Объявление с seller_name '{seller_name}' уже существует в базе данных.")


BASE_URL = 'https://lalafo.kg'
url_list = ['https://lalafo.kg/kyrgyzstan',
            'https://lalafo.kg/kyrgyzstan/transport?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/detskii-mir-2?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/zhivotnye-2?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/sport-i-khobbi?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/lichnye-veshchi?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/elektronika?sort_by=newest',
            'https://lalafo.kg/kyrgyzstan/dom-i-sad?sort_by=newest'
            ]


def clean_post_url(post_url):
    match = re.search(r"(https://lalafo.kg/[a-z-]+)/ads/.*?-(\d+)$", post_url)
    return match.group(1) + '/ads/' + match.group(2) if match else post_url


def extract_number(text):
    return int(re.sub(r'\D', '', text))


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str.split("с ")[1], '%d.%m.%Y')
        return date_obj.strftime('%Y-%m-%d')
    except Exception as e:
        return None


async def parse_lalafo_rs():
    while True:
        for url in url_list:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--headless")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)

            sleep(1)
            page_source = driver.page_source

            bs = BeautifulSoup(page_source, 'html.parser')

            all_links = bs.find_all('a', class_='ad-tile-horizontal-link')

            for link in all_links:
                href = link.get('href')
                if href:
                    full_url = BASE_URL + href
                    driver.execute_script(f"window.open('{full_url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])
                    sleep(3)

                    page_source = driver.page_source
                    bs_ad = BeautifulSoup(page_source, 'html.parser')

                    try:
                        views = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[1]/div[2]/div[1]/div/span').text
                        views_count = extract_number(views)
                    except Exception as e:
                        views_count = None

                    try:
                        seller_name = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[2]/div/div[1]/div[3]/div/div/div/span/span').text
                    except Exception as e:
                        seller_name = None

                    try:
                        price = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[2]/div/div[1]/div[1]/div/p').text
                        price_value = extract_number(price)
                    except Exception as e:
                        price_value = None

                    try:
                        phone_button = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[2]/div/div[1]/div[4]/div[2]/div/button')
                        phone_button.click()
                        sleep(1)

                        phone_number = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[2]/div/div[1]/div[4]/div[2]/div/div/div/div/a').text.replace(" ", "")
                    except Exception as e:
                        phone_number = None

                    try:
                        seller_profile_link = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/div[2]/div/div[1]/div[3]/div/div/div/span/span')
                        seller_profile_link.click()
                        sleep(1)

                        registration_date = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div/div/div/div/div[1]/div/div/div/div/div/div[2]/div[3]/p').text
                        formatted_date = format_date(registration_date)
                    except Exception as e:
                        formatted_date = None

                    # Выводим данные
                    print(f"Ссылка: {clean_post_url(full_url)}")
                    print(f"Количество просмотров: {views_count}")
                    print(f"Имя продавца: {seller_name}")
                    print(f"Цена товара: {price_value}")
                    print(f"Номер телефона: {phone_number}")
                    print(f"Дата регистрации продавца: {formatted_date}")
                    print("-" * 40)

                    await save_to_db(seller_name,
                                     phone_number,
                                     price_value,
                                     views_count,
                                     formatted_date,
                                     clean_post_url(full_url))

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

    driver.quit()


if __name__ == '__main__':
    asyncio.run(parse_lalafo_rs())