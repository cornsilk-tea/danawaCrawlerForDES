from bs4 import BeautifulSoup
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import uvicorn
import csv
import re
import oracledb
import time


app = FastAPI()


class OracleDB:
    def __init__(self):
        self._conn = None

    def start(self):
        # Oracle 데이터베이스에 연결합니다.
        self._conn = oracledb.connect(
            user="DEVENVSHARE",
            password="DEVENVSHARE",
            dsn="localhost:1521/xe"
        )

    def stop(self):
        # 연결을 닫습니다.
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute_query(self, query):
        # 쿼리를 실행하고 결과를 반환합니다.
        cursor = self._conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    def execute_insert(self, query, values):
        # INSERT 쿼리를 실행하고 커밋합니다.
        cursor = self._conn.cursor()
        cursor.execute(query, values)
        self._conn.commit()

    def execute_insert_many(self, query, values_list):
        # 여러 개의 데이터를 한 번에 삽입합니다.
        cursor = self._conn.cursor()
        cursor.executemany(query, values_list)
        self._conn.commit()
        print(cursor.rowcount, "개의 데이터가 삽입되었습니다.")

    def begin_transaction(self):
        # 새로운 데이터베이스 트랜잭션을 시작합니다.
        self._conn.begin()

    def commit_transaction(self):
        # 현재의 데이터베이스 트랜잭션을 커밋합니다.
        self._conn.commit()

    def rollback_transaction(self):
        # 현재의 데이터베이스 트랜잭션을 롤백합니다.
        self._conn.rollback()

    def execute_query_with_params(self, query, params=None):
        # 파라미터를 사용하여 쿼리를 실행합니다.
        # 쿼리 문자열에는 파라미터를 나타내는 플레이스홀더를 포함해야 합니다.
        # params 매개변수에는 파라미터 값을 담은 딕셔너리를 전달해야 합니다.
        # 결과를 반환합니다.
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows


oracle_db = OracleDB()


class Product:
    def __init__(self, name, price, link):
        self.name = name
        self.price = price
        self.link = link

    def __hash__(self):
        return hash((self.name))

    def __eq__(self, other):
        if isinstance(other, Product):
            return self.name == other.name
        return False


def get_webdriver():
    options = Options()
    options.add_argument('--headless')

    return webdriver.Chrome("driver\\chromedriver.exe", options=options)


def get_product_info(product):
    name = product.select_one('p.prod_name > a').text.strip()
    price_element = product.select_one('p.price_sect > a > strong')
    price_text = price_element.text.strip()
    price_text = re.sub(r"[^\d]", "", price_text)
    price = int(price_text) if price_text.isdigit() else 0
    link = product.select_one('p.prod_name > a')['href'].strip()
    return Product(name, price, link)


def write_product_info(CAT, file, products):
    # db에 저장
    try:
        # oracle_db.begin_transaction()
        values = [
        {
            'equip_cate_no': int(CAT),
            'equip_nm': product.name,
            'equip_price': int(product.price),
            'equip_link': product.link
        } for product in products]
        print(str(len(values)) + "개의 데이터를 삽입합니다.")
        query = "INSERT INTO EQUIPMENTS (EQUIP_CATE_NO, EQUIP_NM, EQUIP_PRICE, EQUIP_LINK) VALUES (:equip_cate_no, :equip_nm, :equip_price, :equip_link)"
        oracle_db.execute_insert_many(query, values)
        # oracle_db.commit_transaction()

    except Exception as e:
        print(e)
        print("롤백")
        # oracle_db.rollback_transaction()
    
    for product in products:
        file.write(f"{product.name},")
        file.write(f"{product.price},")
        file.write(f"{product.link}\n")
        # print(f"제품명: {product.name}")
        # print(f"가격: {product.price}")
        # print(f"링크: {product.link}\n")


def crawl_products(driver, products):
    page = 1
    while True:
        print(f"현재 페이지: {page}")
        try:
            wait = WebDriverWait(driver, 100)
            # wait.until(EC.element_to_be_clickable(driver.find_element(By.CSS_SELECTOR, 'div.main_prodlist > ul.product_list > li.prod_item')))
            wait.until(EC.element_to_be_clickable(driver.find_element(By.CSS_SELECTOR, '#productListArea > div.main_prodlist.main_prodlist_list > ul')))
            # time.sleep(3)
            new_html = driver.page_source
            new_soup = BeautifulSoup(new_html, 'html.parser')
            for product_element in new_soup.select('div.main_prodlist > ul.product_list > li.prod_item > div.prod_main_info'):
                product = get_product_info(product_element)
                size_before = len(products)
                # 만약 link의 시작이 /로 시작한다면 종료(잘못된 데이터를 가져오는 것을 방지)
                if product.link.startswith('/'):
                    # print(product_element)
                    # print("link가 /로 시작합니다.")
                    continue
                products.add(product)
                size_after = len(products)
                # print(f"size_before: {size_before}, size_after: {size_after}")
            print(f"size: {len(products)}")

            # 페이지에 '다음 페이지' 링크가 없으면 크롤링 종료
            next_page_link = new_soup.select_one('a.edge_nav.nav_next')
            if next_page_link is None:
                break
            page += 1

            driver.execute_script(f"javascript:movePage({page}); return false;")
        except:
            break


@app.on_event("startup")
async def startup_event():
    categories = {
        "monitor_cate": [112757, 11248106, 11230049, 11230059, 11230081, 11230076],
        "keyboard_cate": [11335184, 1131635, 1139922, 11317385, 11341565, 11347372, 11342148, 11342291, 11344629],
        "mouse_cate": [11310719, 11317389, 11312617, 1131804],
        "desk_cate": [15335915, 15343651, 15344971, 15335908, 15344981],
        "chair_cate": [15345047, 15345042, 15345043, 15346299, 15345045],
    }

    try:
        driver = get_webdriver()    
        oracle_db.start()
        data = oracle_db.execute_query("select * from EQUIPMENTS_CATE")
        # [(1, 'Monitor'), (2, 'Keyboard'), (3, 'Mouse'), (4, 'Desk'), (5, 'Chair')]
        print(data)
        cat_num = 1
        for filename, category in categories.items():
            products = set()
            with open(f"{filename}.csv", "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["제품명", "가격", "링크"])

                for CAT in category:
                    url = "https://prod.danawa.com/list/?cate=" + str(CAT)
                    driver.get(url)

                    element = driver.find_element(By.LINK_TEXT, "신상품순")
                    driver.execute_script("arguments[0].click();", element)

                    select_element = driver.find_element(By.CLASS_NAME, "qnt_selector")
                    select = Select(select_element)
                    select.select_by_value("90")

                    crawl_products(driver, products)

                sorted_products = sorted(products, key=lambda x: x.name)
                write_product_info(cat_num, f, sorted_products)
                cat_num += 1
                print(f"{filename} 크롤링 종료")
    except Exception as e:
        print(e)
        return    
    finally:
        driver.quit()
        oracle_db.stop()
        print("드라이버 종료")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
