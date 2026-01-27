from shopify.connection_adapter.adapter import ShopifyEngine
from utils.response_formatter import format_product_data, format_single_product_data

if __name__ == "__main__":
    shopify_engine = ShopifyEngine("12345")
    # products = shopify_engine.list_products()
    products = shopify_engine.get_product(7530792648779) 
    # format_product_data(products)
    format_single_product_data(products)
