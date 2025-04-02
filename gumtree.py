import asyncio
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import GUMTREE, async_session
from webdriver_manager.chrome import ChromeDriverManager



def convert_to_int(value):
    if 'K' in value:
        return int(float(value.replace('K', '').strip()) * 1000)
    elif 'M' in value:
        return int(float(value.replace('M', '').strip()) * 1000000)
    else:
        return int(value.replace(',', '').strip())


def calculate_registration_date(selling_time):
    current_date = datetime.today()
    if "year" in selling_time:
        years = int(re.search(r'\d+', selling_time).group())
        registration_date = current_date - timedelta(days=years * 365)
    elif "month" in selling_time:
        months = int(re.search(r'\d+', selling_time).group())
        registration_date = current_date - timedelta(days=months * 30)
    else:
        registration_date = current_date
    return registration_date.strftime("%Y-%m-%d")


def extract_number_from_text(text):
    number = re.search(r'\d+', text)
    return int(number.group()) if number else 0


async def save_ad_to_db(session: AsyncSession, ad_data):
    result = await session.execute(select(GUMTREE).filter_by(seller_name=ad_data['seller_name']))
    existing_ad = result.scalars().first()

    if existing_ad is None:
        gumtree_ad = GUMTREE(
            is_phone_number=ad_data['is_phone_number'],
            delivery=ad_data.get('delivery', False),
            has_rating=ad_data.get('has_rating', False),
            price=ad_data['price'],
            views=ad_data['views'],
            link=ad_data['link'],
            seller_name=ad_data['seller_name'],
            phone_number=ad_data.get('phone_number'),
            seller_direct=ad_data['seller_direct'],
            reg_date=ad_data['reg_date'],
            items_count=ad_data['items_count'],
            items_sold=ad_data.get('items_sold', 0),
            items_bought=ad_data.get('items_bought', 0),
            parse_date=ad_data.get('parse_date')
        )
        session.add(gumtree_ad)
        await session.commit()
    else:
        print(f"Объявление с seller_name '{ad_data['seller_name']}' уже существует в базе данных.")


async def process_data():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--incognito")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    category_urls = [
        'https://www.gumtree.co.za/s-cars-bakkies/v1c9077p1',
        'https://www.gumtree.co.za/s-cell-phones-accessories/v1c9198p1',
        'https://www.gumtree.co.za/s-furniture/v1c9181p1',
        'https://www.gumtree.co.za/s-houses-flats-for-rent/v1c9078p1',
        'https://www.gumtree.co.za/s-auto-parts-accessories/v1c9026p1',
        'https://www.gumtree.co.za/s-boats-jet-skis/v1c9102p1',
        'https://www.gumtree.co.za/s-toys/v1c9192p1',
        'https://www.gumtree.co.za/s-clothing/v1c9193p1',
        'https://www.gumtree.co.za/s-sports-fitness-gear/v1c9204p1',
        'https://www.gumtree.co.za/s-dogs-puppies/v1c9123p1'
    ]

    async with async_session() as session:
        while True:
            for url in category_urls:
                driver.get(url)

                try:
                    WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.CLASS_NAME, 'related-content')))
                    print("Страница загружена.")
                except Exception as e:
                    print(f"Ошибка загрузки страницы: {e}")

                html = driver.page_source
                bs = BeautifulSoup(html, 'html.parser')

                all_links = bs.find_all('a', class_='related-ad-title')

                for link in all_links:
                    ad_link = 'https://www.gumtree.co.za' + link['href']
                    print(f'Открываем ссылку: {ad_link}')

                    driver.execute_script(f"window.open('{ad_link}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.CLASS_NAME, 'seller-stats')))
                        print("Страница объявления загружена.")
                    except Exception as e:
                        print(f"Ошибка при загрузке страницы объявления: {e}")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                    ad_html = driver.page_source
                    ad_bs = BeautifulSoup(ad_html, 'html.parser')

                    # Извлекаем данные
                    seller_name = ad_bs.find('div', class_='seller-name').get_text(strip=True) if ad_bs.find('div',
                                                                                                             class_='seller-name') else "Неизвестно"
                    try:
                        total_ads = driver.find_element(By.XPATH,
                                                        '//*[@id="wrapper"]/div[1]/div[3]/div[2]/div[1]/div[2]/div[2]/div[2]/span[2]').text
                        total_views = driver.find_element(By.XPATH,
                                                          '//*[@id="wrapper"]/div[1]/div[3]/div[1]/div/div[3]/div[1]/span[4]/span').text
                        total_ads = extract_number_from_text(total_ads)
                        total_views = extract_number_from_text(total_views)
                    except Exception as e:
                        total_ads, total_views = 0, 0
                        print(f"Ошибка извлечения статистики: {e}")

                    try:
                        seller_time = driver.find_element(By.XPATH,
                                                          '//*[@id="wrapper"]/div[1]/div[3]/div[2]/div[1]/div[1]/div[2]/div[2]/span').text
                        registration_date = calculate_registration_date(seller_time)
                    except NoSuchElementException:
                        registration_date = "Неизвестно"

                    try:
                        phone_link = driver.find_element(By.CLASS_NAME, 'phoneclick-increment')
                        phone_number = phone_link.get_attribute('href').replace('tel:', '').strip()
                    except NoSuchElementException:
                        phone_number = None

                    ad_price = ad_bs.find('span', class_='ad-price')
                    if ad_price:
                        price_text = ad_price.get_text(strip=True)
                        try:
                            price = int(re.sub(r'\D', '', price_text)) if price_text else 0
                        except ValueError:
                            price = 0
                    else:
                        price = 0

                    ad_data = {
                        'is_phone_number': True if phone_number != None else False,
                        'delivery': False,
                        'has_rating': False,
                        'price': price,
                        'views': total_views,
                        'link': ad_link,
                        'seller_name': seller_name,
                        'phone_number': phone_number,
                        'seller_direct': ad_link,
                        'reg_date': registration_date,
                        'items_count': total_ads,
                        'items_sold': 0,
                        'items_bought': 0,
                        'parse_date': datetime.today().strftime("%Y-%m-%d")
                    }

                    await save_ad_to_db(session, ad_data)

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
    driver.quit()


if __name__ == "__main__":
    asyncio.run(process_data())
