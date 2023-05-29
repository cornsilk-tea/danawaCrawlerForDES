from bs4 import BeautifulSoup
import uvicorn
import time
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import csv

app = FastAPI()

class Product:
    def __init__(self, name, price, link):
        self.name = name
        self.price = price
        self.link = link
    def __hash__(self):
        return hash((self.name, self.price, self.link))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.name, self.price, self.link) == (other.name, other.price, other.link)

@app.on_event("startup")
async def startup_event():
    # 파일을 쓰기 모드로 열기
    f = open("products.csv", "w", encoding="utf-8-sig", newline="")
    # csv.writer는 파일 객체를 매개변수로 지정합니다.
    writer = csv.writer(f)
    # 첫 번째 줄에는 헤더를 작성합니다.
    writer.writerow(["제품명", "가격", "링크"])

    # Selenium 웹드라이버 설정
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome("driver\\chromedriver.exe", options=options)

    # 웹사이트 크롤링
    # url = "https://prod.danawa.com/list/?cate=112757&15main_11_02&_gl=1*1amflb0*_ga*MjAyMjcyMDI4NS4xNjg0OTA5OTYw*_ga_L8D5P2KD8Z*MTY4NTM1MDA4OC43LjEuMTY4NTM1NDM5MC42MC4wLjA.#"
    url = "https://prod.danawa.com/list/?cate="
    driver.get(url)
    # 여기서 현재 페이지에서 보이는 전체 물품들의 리스트를 가져온다.
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # 신상품순 링크를 클릭
    element = driver.find_element(By.LINK_TEXT, "신상품순")
    driver.execute_script("arguments[0].click();", element)

    # 화면에 표시하는 목록의 개수를 설정하는 select 요소를 찾음
    select_element = driver.find_element(By.CLASS_NAME, "qnt_selector")
    # Select 객체를 생성
    select = Select(select_element)
    # 값을 선택
    select.select_by_value("90")

    page = 1
    products = set()
    flag = True
    while True:
        print(f"현재 페이지: {page}")
        # 링크 클릭 후 새로운 페이지 로드될 때까지 기다림
        wait = WebDriverWait(driver, 100)
        wait.until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, 'div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change')))
        # 이동 후의 HTML 구조 확인
        new_html = driver.page_source
        new_soup = BeautifulSoup(new_html, 'html.parser')
        # 새로운 페이지에서 보이는 전체 물품들의 리스트를 가져온다.
        # 제품 명, 가격, 링크를 가져온다.
        # 파일에 제품 정보를 저장한다.
        for product in new_soup.select('div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change'):
            # 제품명, 가격, 링크를 가지고 있는 Pruduct 객체를 생성한 후 리스트에 추가한다.
            name = product.select_one('p.prod_name > a').text.strip()
            price = product.select_one('p.price_sect > a > strong').text.strip()
            if price == "가격비교예정":
                price = "0"
            link = product.select_one('p.prod_name > a')['href'].strip()
            product_obj = Product(name, price, link)
            size_before = len(products)
            products.add(product_obj)
            size_after = len(products)
            # size_before와 size_after가 같은지 출력
            print(f"size_before: {size_before}, size_after: {size_after}")
            if size_before == size_after:
                flag = False
                break
            # 제품 정보를 파일에 쓰고 출력
            f.write(f"{name},")
            f.write(f"{price},")
            f.write(f"{link}\n")
            print(f"제품명: {name}")
            print(f"가격: {price}")
            print(f"링크: {link}")
            print()
        # break
        if flag == False:
            break
        # 다음 페이지로 이동
        page += 1
        try:
            driver.execute_script(f"javascript:movePage({page}); return false;")
            # false가 반환되면 멈춰주기
        except:
            break
    driver.quit()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
