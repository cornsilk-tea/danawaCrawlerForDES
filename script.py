from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import csv
import re
import oracledb
import math
import logging
from tqdm import tqdm
from crawler_config import DATABASE_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OracleDB:
    def __init__(self):
        self._conn = None

    def start(self):
        # Oracle 데이터베이스에 연결합니다.
        db_config = DATABASE_CONFIG  # config.py에서 데이터베이스 연결 정보 가져오기
        self._conn = oracledb.connect(
            user=db_config["user"],
            password=db_config["password"],
            dsn=db_config["dsn"]
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
        # self._conn.commit()
    
    def commit(self):
        self._conn.commit()
    

    # def execute_insert_many(self, query, values_list):
    #     # 여러 개의 데이터를 한 번에 삽입합니다.
    #     cursor = self._conn.cursor()
    #     cursor.executemany(query, values_list)
    #     # self._conn.commit()
    #     # print(cursor.rowcount, "개의 데이터가 삽입되었습니다.")
    #     return cursor.rowcount
    
    def execute_many(self, query, values_list):
        cursor = self._conn.cursor()
        cursor.executemany(query, values_list)
        # self._conn.commit()
        # print(cursor.rowcount, "개의 데이터가 삽입되었습니다.")
        return cursor.rowcount

    def begin_transaction(self):
        # 새로운 데이터베이스 트랜잭션을 시작합니다.
        self._conn.begin()

    def commit_transaction(self):
        # 현재의 데이터베이스 트랜잭션을 커밋합니다.
        self.commit()

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
    
    def __str__(self):
        return f"제품명: {self.name}\n가격: {self.price}\n링크: {self.link}\n"


def get_webdriver():
    options = Options()
    options.add_argument('--disable-extensions')  # 브라우저 확장 프로그램 비활성화
    options.add_argument('--disable-infobars')  # 인포바 비활성화
    options.add_argument('--disable-dev-shm-usage')  # /dev/shm 사용 비활성화
    options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    options.add_argument('--headless')  # 헤드리스 모드 사용
    options.add_argument('--log-level=3')  # 로그 레벨 설정 (3: 경고 메시지만 표시)
    options.add_argument('--disable-gpu')  # GPU 사용 비활성화
    return webdriver.Chrome("driver/chromedriver.exe", options=options)
    # return webdriver.Chrome("driver/chromedriver.exe")


def get_product_info(product):
    name = product.select_one('p.prod_name > a').text.strip()
    price_element = product.select_one('p.price_sect > a > strong')
    price_text = price_element.text.strip()
    price_text = remove_comma(price_text)
    price = int(price_text) if price_text.isdigit() else 0
    link = product.select_one('p.prod_name > a')['href'].strip()
    return Product(name, price, link)

def remove_comma(price_text):
    return re.sub(r"[^\d]", "", price_text)


def write_product_info(cat, file, products):
    try:
        values = [
        {
            'equip_cate_no': int(cat),
            'equip_nm': product.name,
            'equip_price': int(product.price),
            'equip_link': product.link
        } for product in products]
        logging.info(f"{len(values)}개의 데이터를 삽입합니다.")
        query = """
            MERGE INTO EQUIPMENTS t
            USING (SELECT :EQUIP_CATE_NO AS EQUIP_CATE_NO, :EQUIP_NM AS EQUIP_NM, :EQUIP_PRICE AS EQUIP_PRICE, :EQUIP_LINK AS EQUIP_LINK FROM dual) s
            ON (t.EQUIP_NM = s.EQUIP_NM)
            WHEN MATCHED THEN 
                UPDATE SET 
                EQUIP_PRICE = s.EQUIP_PRICE,
                EQUIP_LINK = s.EQUIP_LINK
            WHEN NOT MATCHED THEN 
                INSERT (EQUIP_CATE_NO, EQUIP_NM, EQUIP_PRICE, EQUIP_LINK) 
                VALUES (s.EQUIP_CATE_NO, s.EQUIP_NM, s.EQUIP_PRICE, s.EQUIP_LINK)
        """
        result = oracle_db.execute_many(query, values)
        oracle_db.commit_transaction()
        logging.info(f"{result}개의 데이터가 삽입되었습니다.")

    except Exception as e:
        logging.error(str(e))
        logging.info("롤백")
        oracle_db.rollback_transaction()
    
    for product in products:
        file.write(f"{product.name},")
        file.write(f"{product.price},")
        file.write(f"{product.link}\n")


def crawl_products(driver, products, url):
    page = 1
    total_products = 0
    start_with_slash = 0
    duplicate = 0
    pbar = None

    while True:
        try:
            wait = WebDriverWait(driver, 100)
            wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, '#danawa_container > div.product_list_cover > div > img')))
            new_html = driver.page_source
            new_soup = BeautifulSoup(new_html, 'html.parser')
            if total_products == 0:
                total_products = int(remove_comma(new_soup.select_one(
                    '#danawa_content > div.product_list_wrap > div.product_list_area > div.prod_list_tab > ul > li.tab_item.selected > a > strong.list_num').text.strip()))
                logging.info(f"총 상품 개수는 {total_products}개 입니다.")
            # logging.info(f"현재 페이지: {page}")
            select_elements = new_soup.select('div.main_prodlist > ul.product_list > li.prod_item > div.prod_main_info')
            # next_page_link = new_soup.select_one('a.edge_nav.nav_next')
            if math.ceil(total_products / 90) == page:
                break
            if pbar is None:
                pbar = tqdm(total=total_products, desc="Processing", unit="product")
            for product_element in select_elements:
                product = get_product_info(product_element)
                size_before = len(products)
                if product.link.startswith('/'):
                    start_with_slash += 1
                    continue
                products.add(product)
                size_after = len(products)
                if size_before == size_after:
                    duplicate += 1
                logging.debug(f"size_before: {size_before}, size_after: {size_after}")
                pbar.update(1)
            page += 1
            driver.execute_script(f"javascript:movePage({page});")
        except Exception as e:
            logging.error(str(e))
            # 오류가 발생한 url 표시
            logging.error(f"오류가 발생한 url: {url}")
            logging.error("크롤링 중 비정상적인 오류로 인한 종료")
            return
    if pbar is not None:
        pbar.close()
    logging.info(f"현재까지 {len(products)}개의 데이터 수집 완료, {start_with_slash}개의 데이터는 제외, {duplicate}개의 중복 데이터는 제외")


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

    def __str__(self):
        return f"제품명: {self.name}\n가격: {self.price}\n링크: {self.link}\n"


def remove_comma(price_text):
    return re.sub(r"[^\d]", "", price_text)


def get_product_info(product):
    name = product.select_one('p.prod_name > a').text.strip()
    price_element = product.select_one('p.price_sect > a > strong')
    price_text = price_element.text.strip()
    price_text = remove_comma(price_text)
    price = int(price_text) if price_text.isdigit() else 0
    link = product.select_one('p.prod_name > a')['href'].strip()
    return Product(name, price, link)


def write_product_info(cat, file, products):
    try:
        values = [
            {
                'equip_cate_no': int(cat),
                'equip_nm': product.name,
                'equip_price': int(product.price),
                'equip_link': product.link
            } for product in products]
        logging.info(f"{len(values)}개의 데이터를 삽입합니다.")
        query = """
            MERGE INTO EQUIPMENTS t
            USING (SELECT :EQUIP_CATE_NO AS EQUIP_CATE_NO, :EQUIP_NM AS EQUIP_NM, :EQUIP_PRICE AS EQUIP_PRICE, :EQUIP_LINK AS EQUIP_LINK FROM dual) s
            ON (t.EQUIP_NM = s.EQUIP_NM)
            WHEN MATCHED THEN 
                UPDATE SET 
                EQUIP_PRICE = s.EQUIP_PRICE,
                EQUIP_LINK = s.EQUIP_LINK
            WHEN NOT MATCHED THEN 
                INSERT (EQUIP_CATE_NO, EQUIP_NM, EQUIP_PRICE, EQUIP_LINK) 
                VALUES (s.EQUIP_CATE_NO, s.EQUIP_NM, s.EQUIP_PRICE, s.EQUIP_LINK)
        """
        result = oracle_db.execute_many(query, values)
        oracle_db.commit_transaction()
        logging.info(f"{result}개의 데이터가 삽입되었습니다.")

    except Exception as e:
        logging.error(str(e))
        logging.info("롤백")
        oracle_db.rollback_transaction()

    for product in products:
        file.write(f"{product.name},")
        file.write(f"{product.price},")
        file.write(f"{product.link}\n")


def start_crawl():
    # categories = {
    #     "monitor": [112757, 11248106, 11230049, 11230059, 11230081, 11230076],
    #     "keyboard": [11335184, 1131635, 1139922, 11317385, 11341565, 11347372, 11342148, 11342291, 11344629],
    #     "mouse": [11310719, 11317389, 11312617, 1131804],
    #     "desk": [15335915, 15343651, 15344971, 15335908, 15344981],
    #     "chair": [15345047, 15345042, 15345043, 15346299, 15345045],
    # }
    categories = {
        "monitor": [112757, 11248106, 11230049, 11230059, 11230081, 11230076],
        "keyboard": [112782],
        "mouse": [112787],
        "desk": [15240504, 15235876, 15243650, 15235873, 15235874, 15235877, 15243647],
        "chair": [1523647, 15221463, 15240090, 15235834],
    }

    try:
        driver = get_webdriver()
        oracle_db.start()
        data = oracle_db.execute_query("select * from EQUIPMENTS_CATE")
        logging.info(data)
        cat_num = 1
        for cate_name, category in categories.items():
            products = set()
            with open(f"{cate_name}.csv", "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["제품명", "가격", "링크"])

                for cat in category:
                    url = "https://prod.danawa.com/list/?cate=" + str(cat)
                    driver.get(url)

                    element = driver.find_element(By.LINK_TEXT, "신상품순")
                    driver.execute_script("arguments[0].click();", element)

                    select_element = driver.find_element(By.CLASS_NAME, "qnt_selector")
                    select = Select(select_element)
                    select.select_by_value("90")
                    logging.info(f"{cate_name}카테고리의 데이터 크롤링 시작")
                    crawl_products(driver, products, url)

                sorted_products = sorted(products, key=lambda x: x.name)
                logging.info("현재까지 크롤링한 데이터의 개수: " + str(len(sorted_products)))
                write_product_info(cat_num, f, sorted_products)
                cat_num += 1
                logging.info(f"{cate_name} 크롤링 종료")
    except Exception as e:
        logging.error(f"오류가 발생한 url: {url}")
        logging.error(str(e))
        return
    finally:
        driver.quit()
        oracle_db.stop()
        logging.info("드라이버 종료")


if __name__ == "__main__":
    logging.info("크롤링 스크립트를 실행합니다.")
    start_crawl()
    logging.info("크롤링 스크립트가 종료되었습니다.")