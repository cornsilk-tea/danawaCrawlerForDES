from bs4 import BeautifulSoup
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import uvicorn
import csv, time

app = FastAPI()

class Product:
    def __init__(self, name, price, link):
        self.name = name
        self.price = price
        self.link = link

    def __hash__(self):
        return hash((self.name, self.price, self.link))

    def __eq__(self, other):
        if isinstance(other, Product):
            return self.name == other.name
        return False


def get_webdriver():
    options = Options()
    options.add_argument('--headless')
    return webdriver.Chrome("driver\\chromedriver.exe")


def get_product_info(product):
    name = product.select_one('p.prod_name > a').text.strip()
    price = product.select_one('p.price_sect > a > strong').text.strip()
    if price == "가격비교예정":
        price = "0"
    link = product.select_one('p.prod_name > a')['href'].strip()
    return Product(name, price, link)


def write_product_info(file, products):
    for product in products:
        file.write(f"{product.name},")
        file.write(f"{product.price},")
        file.write(f"{product.link}\n")
        print(f"제품명: {product.name}")
        print(f"가격: {product.price}")
        print(f"링크: {product.link}\n")


def crawl_products(file, driver, products):
    
    page = 1
    while True:
        print(f"현재 페이지: {page}")
        try:
            wait = WebDriverWait(driver, 100)
            wait.until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, 'div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change')))
        except:
            break
        new_html = driver.page_source
        new_soup = BeautifulSoup(new_html, 'html.parser')
        for product_element in new_soup.select('div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change'):
            product = get_product_info(product_element)
            size_before = len(products)
            products.add(product)
            size_after = len(products)
            print(f"size_before: {size_before}, size_after: {size_after}")
            if size_before == size_after:
                return

        page += 1
        try:
            driver.execute_script(f"javascript:movePage({page}); return false;")
        except:
            break


@app.on_event("startup")
async def startup_event():
    # 크롤링 할 카테고리를 선택합니다.
    # monitor_category = ["112757", "11248106", "11230049", "11230059", "11230081", "11230076"]
    monitor_category = ["11248106", "11230049", "11230059", "11230081", "11230076"]
    products = set()
    with open("products.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["제품명", "가격", "링크"])

        driver = get_webdriver()
        for CAT in monitor_category:
            url = "https://prod.danawa.com/list/?cate="+CAT
            driver.get(url)

            element = driver.find_element(By.LINK_TEXT, "신상품순")
            driver.execute_script("arguments[0].click();", element)

            select_element = driver.find_element(By.CLASS_NAME, "qnt_selector")
            select = Select(select_element)
            select.select_by_value("90")

            crawl_products(f, driver, products)
        
        sorted_products = sorted(products, key=lambda x: x.name)
        write_product_info(f, sorted_products)
        print("크롤링 종료")
        driver.quit()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
