from bs4 import BeautifulSoup
import uvicorn, time
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()

class Product:
    def __init__(self, name, price, link):
        self.name = name
        self.price = price
        self.link = link

@app.on_event("startup")
async def startup_event():
    # Selenium 웹드라이버 설정
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome("driver\\chromedriver.exe", options=options)

    # 웹사이트 크롤링
    url = "https://prod.danawa.com/list/?cate=112757&15main_11_02&_gl=1*1amflb0*_ga*MjAyMjcyMDI4NS4xNjg0OTA5OTYw*_ga_L8D5P2KD8Z*MTY4NTM1MDA4OC43LjEuMTY4NTM1NDM5MC42MC4wLjA.#"
    driver.get(url)
    # 여기서 현재 페이지에서 보이는 전체 물품들의 리스트를 가져온다.
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # 신상품순 링크를 클릭
    element = driver.find_element(By.LINK_TEXT, "신상품순")
    driver.execute_script("arguments[0].click();", element)

    # 링크 클릭 후 새로운 페이지 로드될 때까지 기다림
    wait = WebDriverWait(driver, 10)
    wait.until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, 'div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change')))

    # 이동 후의 HTML 구조 확인
    new_html = driver.page_source
    new_soup = BeautifulSoup(new_html, 'html.parser')

    # 링크 이동 전과 후의 HTML 구조 비교
    if html == new_html:
        print("링크 이동 후 HTML 구조가 동일합니다.")
    else:
        print("링크 이동 후 HTML 구조가 다릅니다.")

    # 제품 명, 가격, 링크를 가져온다.
    product_list = []
    for product in new_soup.select('div.main_prodlist > ul.product_list > li.prod_item.prod_layer.width_change'):
        # 제품명, 가격, 링크를 가지고 있는 Pruduct 객체를 생성한 후 리스트에 추가한다.
        name = product.select_one('p.prod_name > a').text.strip()
        price = product.select_one('p.price_sect > a > strong').text.strip()
        if(price == "가격비교예정"):
            price = "0"
        link = product.select_one('p.prod_name > a')['href'].strip()
        product_obj = Product(name, price, link)
        product_list.append(product_obj)
    # 출력
    for product in product_list:
        # 보기좋게 출력
        print(product.name)
        print(product.price)
        print(product.link)
        print()
        # 만약 마지막 출력이면,마지막으로 알려준다.
        if product == product_list[-1]:
            print("마지막 제품입니다.")
    # 현재 상태에서 20초간 기다리기
    time.sleep(20)
    driver.quit()  # Selenium 웹드라이버 종료

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)