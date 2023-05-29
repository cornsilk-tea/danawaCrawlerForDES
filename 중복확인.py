import csv


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
    
# Product 객체를 만드는 함수
def make_product(row):
    name = row['name']
    price = float(row['price'])  # 가정: price는 실수 형태
    link = row['link']
    return Product(name, price, link)

# CSV 파일에서 데이터를 읽어 Product 객체의 리스트를 만드는 함수
def read_products_from_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        return [make_product(row) for row in reader]

# Product 객체의 리스트를 가격(price) 기준으로 정렬하는 함수
def sort_products_by_price(products):
    return sorted(products, key=lambda product: product.price)

# 메인 함수
def main():
    filename = 'products.csv'  # 파일명을 필요에 따라 변경
    products = read_products_from_csv(filename)
    sorted_products = sort_products_by_price(products)
    for product in sorted_products:
        print(product.name, product.price, product.link)

if __name__ == '__main__':
    main()
