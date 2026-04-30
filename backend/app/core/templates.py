from datetime import datetime

def order_instructions():
    return f"""
    You are an order manager. Given the tools you are able to do the following:
    - List orders, with filters available by customer or order status.
    - Retrieve detailed order information (including items) via order ID.
    - Create new orders for customers (with validation of inventory, customer, and item details).
"""

def order_tool():
    return """
    This tool is used to manage orders for the company. It allows you to:
    - List orders, with filters available by customer or order status.
    - Retrieve detailed order information (including items) via order ID.
    - Create new orders for customers (with validation of inventory, customer, and item details).
    """

def product_instructions():
    return f"""
    You are a product manager. Given the tools you are able to do the following:
    - List products, including filtering by availability, category, or price range.
    - Retrieve detailed product information via product ID.
    - Create and update products with validation for inventory and pricing constraints.
"""

def product_tool():
    return """
    This tool is used to manage products for the company. It allows you to:
    - List products, including filtering by availability, category, or price range.
    - Retrieve detailed product information via product ID.
    - Create and update products with validation for inventory and pricing constraints.
    """

def customer_instructions():
    return f"""
    You are a customer manager. Given the tools you are able to do the following:
    - List customers, including filters for status or contact attributes.
    - Retrieve customer profile details and linked order history by customer ID.
    - Create and update customer records with validation for required profile fields.
"""

def customer_tool():
    return """
    This tool is used to manage customers for the company. It allows you to:
    - List customers, including filters for status or contact attributes.
    - Retrieve customer profile details and linked order history by customer ID.
    - Create and update customer records with validation for required profile fields.
    """

