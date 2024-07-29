from dataclay import DataClayObject, activemethod


class Product(DataClayObject):
    name: str
    price: float
    stock: int

    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

    @activemethod
    def purchase(self, quantity: int):
        """Simulate a purchase of the product, reducing the stock."""
        if quantity <= self.stock:
            self.stock -= quantity
            return True
        else:
            print("Not enough stock available")
            return False

    @activemethod
    def restock(self, quantity: int, jocker: str):
        """Restock the product by adding to the stock."""
        self.stock += quantity


class Box(DataClayObject):
    product: Product

    def __init__(self, product: Product):
        self.product = product

    @activemethod
    def change_product(self, new_product: Product):
        self.product = new_product


class Shop(DataClayObject):
    name: str
    products: list[Product]

    def __init__(self, name):
        self.name = name
        self.products = []

    @activemethod
    def add_product(self, product: Product):
        self.products.append(product)

    @activemethod
    def remove_product(self, product: Product):
        self.products.remove(product)

    @activemethod
    def get_product(self, product_name: str):
        for product in self.products:
            if product.name == product_name:
                return product
        return None

    @activemethod
    def purchase_product(self, product_name: str, quantity: int):
        product = self.get_product(product_name)
        if product is not None:
            return product.purchase(quantity)
        else:
            print("Product not found")
            return False

    @activemethod
    def restock_product(self, product_name: str, quantity: int):
        product = self.get_product(product_name)
        if product is not None:
            product.restock(quantity)
        else:
            print("Product not found")
            return False

    @activemethod
    def get_total_stock(self):
        total = 0
        for product in self.products:
            total += product.stock
        return total
