import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime

class DatabaseConnection:
    def __init__(self, host="localhost", user="root", password="pass", database="rajchemsales"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connected to the database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    def disconnect(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")

    def create_order(self, order_id, customer_id, user, total_amount, order_date, accounts_approval_status, items, payment_terms):
        """
        Create an order and its associated items.
        :param order_id: Unique order ID.
        :param customer_id: Foreign key to customer table.
        :param user: Salesperson name.
        :param total_amount: Total amount of the order.
        :param order_date: Date and time of the order.
        :param accounts_approval_status: Status of the order.
        :param items: List of dictionaries containing item details (including product_id).
        :param payment_terms: Optional payment terms.
        :return: True if successful, False otherwise.
        """
        if not self.connection or not self.connection.is_connected():
            print("Error: No active database connection.")
            return False

        try:
            cursor = self.connection.cursor()

            # Insert into the 'orders' table using customer_id
            order_query = """
            INSERT INTO orders (
                order_id, customer_id, salesperson_name, total_amount, 
                order_date, accounts_approval_status, payment_terms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            order_values = (
                order_id, customer_id, user, total_amount, 
                order_date, accounts_approval_status, payment_terms
            )
            cursor.execute(order_query, order_values)

            # Insert into the 'order_items' table
            item_query = """
            INSERT INTO order_items (
                order_id, product_id, product_name, quantity_ordered, unit_price, total_price
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in items:
                item_values = (
                    order_id,
                    item["product_id"],
                    item["product_name"],
                    item["quantity_ordered"],
                    item["unit_price"],
                    item["quantity_ordered"] * item["unit_price"]
                )
                cursor.execute(item_query, item_values)

            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error creating order: {e}")
            self.connection.rollback()
            return False



    def fetch_orders(self):
        """
        Fetch all orders along with their items.
        :return: List of orders with associated items.
        """
        if not self.connection or not self.connection.is_connected():
            print("Error: No active database connection.")
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)

            # Fetch orders
            order_query = "SELECT * FROM orders"
            cursor.execute(order_query)
            orders = cursor.fetchall()

            # Fetch items for each order
            for order in orders:
                item_query = "SELECT * FROM order_items WHERE order_id = %s"
                cursor.execute(item_query, (order['order_id'],))
                order['items'] = cursor.fetchall()

            cursor.close()
            return orders
        except Error as e:
            print(f"Error fetching orders: {e}")
            return []
        
        
    def fetch_pending_orders(self):
        if not self.connection or not self.connection.is_connected():
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders WHERE accounts_approval_status = 'Pending'")
            orders = cursor.fetchall()

            # Optional: fetch items for each order too
            for order in orders:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order["order_id"],))
                order["items"] = cursor.fetchall()

            return orders
        except Error as e:
            print(f"Error fetching pending orders: {e}")
            return []

    
    def add_product(self, name, barcode, uom, opening_qty, batch_number=None, expiration_date=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO products 
                (product_name, barcode, unit_of_measure, opening_qty, batch_number, expiration_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, barcode, uom, opening_qty, batch_number, expiration_date))
            self.connection.commit()
            return True
        except Exception as e:
            print("Add product error:", e)
            return False
        
        
    def fetch_director_pending_orders(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM orders 
                WHERE director_approval_status = 'Pending'
                ORDER BY order_date DESC
            """)
            orders = cursor.fetchall()

            for order in orders:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
                order['items'] = cursor.fetchall()

            return orders
        except Exception as e:
            print("Error fetching director pending orders:", e)
            return []


    def update_accounts_approval(self, order_id, status, remarks):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE orders
                SET accounts_approval_status = %s, accounts_remarks = %s
                WHERE order_id = %s
            """, (status, remarks, order_id))
            self.connection.commit()
            return True
        except Exception as e:
            print("Approval update error:", e)
            return False
        
        
    def fetch_all_products(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT product_id, product_name FROM products")
            return cursor.fetchall()
        except Exception as e:
            print("Error fetching products:", e)
            return []
        
    
    def update_director_approval(self, order_id, status, remarks):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE orders
                SET director_approval_status = %s, director_remarks = %s
                WHERE order_id = %s
            """, (status, remarks, order_id))
            self.connection.commit()
            return True
        except Exception as e:
            print("Director approval error:", e)
            return False

    def fetch_reviewed_orders(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM orders 
                WHERE accounts_approval_status IN ('Approved', 'Rejected')
                OR director_approval_status != 'Pending'
                ORDER BY order_date DESC
            """)
            orders = cursor.fetchall()

            for order in orders:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
                order['items'] = cursor.fetchall()

            return orders
        except Exception as e:
            print("Error fetching reviewed orders:", e)
            return []
        
        
    def fetch_director_approved_orders(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM orders 
                WHERE director_approval_status = 'Approved'
                AND loading_status = 'Pending Loading'
                ORDER BY order_date DESC
            """)
            orders = cursor.fetchall()

            for order in orders:
                cursor.execute("""
                    SELECT 
                        oi.id AS id,
                        oi.product_id,
                        p.product_name,
                        oi.quantity_ordered,
                        oi.loaded_quantity
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.product_id
                    WHERE oi.order_id = %s
                """, (order['order_id'],))
                order['items'] = cursor.fetchall()

            return orders
        except Exception as e:
            print("Error fetching approved orders for loading:", e)
            return []


    def update_loading_status(self, order_id, status, remarks, item_updates):
        try:
            cursor = self.connection.cursor()

            # Update order-level loading status
            cursor.execute("""
                UPDATE orders
                SET loading_status = %s, loading_remarks = %s
                WHERE order_id = %s
            """, (status, remarks, order_id))

            # Update each item's loaded quantity and remarks
            for item in item_updates:
                cursor.execute("""
                    UPDATE order_items
                    SET loaded_quantity = %s, loading_remarks = %s
                    WHERE id = %s
                """, (item['loaded_quantity'], item['loading_remarks'], item['item_id']))

            self.connection.commit()
            return True
        except Exception as e:
            print("Error updating loading status:", e)
            return False
        
        
    def fetch_orders_by_accounts_status(self, status):
        """
        Fetch orders filtered by accounts approval status, including their items.
        :param status: 'Approved', 'Rejected', or 'Pending'
        :return: List of orders with item details
        """
        if not self.connection or not self.connection.is_connected():
            print("Error: No active database connection.")
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)

            # Fetch orders matching the accounts approval status
            cursor.execute("""
                SELECT * FROM orders 
                WHERE accounts_approval_status = %s 
                ORDER BY order_date DESC
            """, (status,))
            orders = cursor.fetchall()

            # For each order, fetch its items
            for order in orders:
                cursor.execute("""
                    SELECT * FROM order_items WHERE order_id = %s
                """, (order['order_id'],))
                order['items'] = cursor.fetchall()

            cursor.close()
            return orders

        except Exception as e:
            print(f"Error fetching orders by accounts status: {e}")
            return []
        
        
    def fetch_loading_history(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM orders 
                WHERE loading_status IN ('Loaded', 'Cancelled')
                ORDER BY order_date DESC
            """)
            orders = cursor.fetchall()

            for order in orders:
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
                order['items'] = cursor.fetchall()

            return orders
        except Exception as e:
            print("Error fetching loading history:", e)
            return []
        
    
    def get_user_by_username(self, username):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    def verify_password(self, plain_password, hashed_password):
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception as e:
            print(f"Password verification failed: {e}")
            return False
        
        
    def fetch_one(self, query, params):
        if not self.connection or not self.connection.is_connected():
            self.connect()
            if not self.connection:
                raise ConnectionError("Database connection failed.")
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def authenticate_user(self, username, password):
        query = "SELECT * FROM users WHERE username = %s"
        user = self.fetch_one(query, (username,))
        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None
    
    
    def count_pending_approvals_for_accounts(self):
        query = "SELECT COUNT(*) AS count FROM orders WHERE accounts_approval_status = 'Pending'"
        return self.fetch_one(query, ())["count"]

    def count_pending_approvals_for_director(self):
        query = "SELECT COUNT(*) AS count FROM orders WHERE accounts_approval_status = 'Approved' AND director_approval_status = 'Pending'"
        return self.fetch_one(query, ())["count"]

    def count_pending_for_loading(self):
        query = "SELECT COUNT(*) AS count FROM orders WHERE director_approval_status = 'Approved' AND loading_status = 'Pending Loading'"
        return self.fetch_one(query, ())["count"]
    
    
    def insert_grn_item(self, grn_id, product_id, ordered_qty, received_qty):
        """Insert a GRN item into the database."""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO grn_items (grn_id, product_id, ordered_qty, received_qty, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (grn_id, product_id, ordered_qty, received_qty, datetime.now()))
            self.connection.commit()
        except Error as e:
            print(f"Error inserting GRN item: {e}")

    def get_grn_items(self, grn_id):
        """Fetch GRN items for a given GRN ID."""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM grn_items WHERE grn_id = %s"
            cursor.execute(query, (grn_id,))
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"Error fetching GRN items: {e}")
            return []

    def update_grn_verification(self, grn_item_id, verified_qty, discrepancy):
        """Update verified quantity and discrepancy for a GRN item."""
        try:
            cursor = self.connection.cursor()
            query = """
                UPDATE grn_items
                SET verified_qty = %s, discrepancy = %s
                WHERE id = %s
            """
            cursor.execute(query, (verified_qty, discrepancy, grn_item_id))
            self.connection.commit()
        except Error as e:
            print(f"Error updating GRN item: {e}")
            
            
    def get_grn_items(self, grn_id):
        """Fetch all GRN items for a given GRN ID."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM grn_items WHERE grn_id = %s"
            cursor.execute(query, (grn_id,))
            results = cursor.fetchall()
            return results

        except Error as e:
            print(f"Error fetching GRN items: {e}")
        return []


    def decrease_product_quantity(self, product_id, qty_to_subtract):
        """Decrease the quantity of a product when loading is done."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            query = """
                UPDATE products
                SET qty = qty - %s
                WHERE product_id = %s
            """
            cursor.execute(query, (qty_to_subtract, product_id))
            self.connection.commit()

        except Exception as e:
            print(f"Error decreasing product quantity: {e}")
            
            
    def log_stock_movement(self, product_id, movement_type, quantity, reference=None, remarks=None):
        """Log stock movements for audit."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            query = """
                INSERT INTO stock_movements (product_id, movement_type, quantity, reference, remarks)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (product_id, movement_type, quantity, reference, remarks))
            self.connection.commit()

        except Exception as e:
            print(f"Error logging stock movement: {e}")
            
            
    def increase_product_quantity(self, product_id, qty_to_add):
        """Increase the quantity of a product in inventory."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            query = """
                UPDATE products
                SET qty = qty + %s
                WHERE product_id = %s
            """
            cursor.execute(query, (qty_to_add, product_id))
            self.connection.commit()

        except Exception as e:
            print(f"Error increasing product quantity: {e}")
            
            
    def get_product_details(self, product_id):
        """Fetch product name and unit of measure from products table."""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT product_name, unit_of_measure 
                FROM products 
                WHERE product_id = %s
            """
            cursor.execute(query, (product_id,))
            result = cursor.fetchone()
            return result if result else {}
        except Error as e:
            print(f"Error fetching product details: {e}")
            return {}


    def get_product_opening_info(self, product_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT opening_qty, unit_of_measure FROM products WHERE product_id = %s
            """
            cursor.execute(query, (product_id,))
            result = cursor.fetchone()
            return result if result else {'opening_qty': 0.0, 'unit_of_measure': ''}
        except Error as e:
            print(f"Error fetching product details: {e}")
            return {'opening_qty': 0.0, 'unit_of_measure': ''}
        
        
    
        
        
        
    def insert_customer(self, name, contact, address=None, contact_person_name=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO customers (customer_name, contact, address, contact_person_name)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (name, contact, address, contact_person_name))
            self.connection.commit()
            return True
        except Exception as e:
            print("Error inserting customer:", e)
            return False
        
        
    def customer_exists(self, name, contact):
        """Check if a customer with the same name and contact already exists."""
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT COUNT(*) FROM customers 
                WHERE customer_name = %s AND contact = %s
            """
            cursor.execute(query, (name, contact))
            result = cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            print("Error checking for duplicate customer:", e)
            return False
        
        
        
    def get_all_customers(self):
        """Fetch all customer names for use in dropdowns or templates."""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, customer_name, contact_person_name, contact FROM customers"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print("Error fetching customers:", e)
            return []

    def get_customer_by_id(self, customer_id):
        """Fetch full customer info by ID."""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT customer_name, contact_person_name, contact 
                FROM customers 
                WHERE id = %s
            """
            cursor.execute(query, (customer_id,))  # Wrap in tuple!
            return cursor.fetchone()  # This returns a dict like {'customer_name': ..., ...}
        except Exception as e:
            print("Error fetching customer by ID:", e)
            return None

    def fetch_all_orders(self):
        """
        Fetch all orders with their related customer info and order items.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Get all orders with customer details
            cursor.execute("""
                SELECT o.order_id, o.customer_id, c.customer_name, o.salesperson_name, o.total_amount, o.order_date, o.accounts_approval_status, o.director_approval_status,
                o.loading_status FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.order_date DESC
            """)
            orders = cursor.fetchall()

            # Fetch and attach order items
            for order in orders:
                cursor.execute("""
                    SELECT 
                        id, product_id, product_name, quantity_ordered, 
                        unit_price, total_price, loaded_quantity, loading_remarks
                    FROM order_items
                    WHERE order_id = %s
                """, (order["order_id"],))
                order["items"] = cursor.fetchall()

            return orders
        except Exception as e:
            print("Error fetching all orders:", e)
            return []
        
        
        
      
  # ✅ Sample `log_stock_adjustment` method in conn.py
  
    def log_stock_adjustment(self, product_id, adjustment_type, quantity, reason, adjusted_by, previous_quantity, new_quantity):
        try:
            cursor = self.connection.cursor()
            
            # Insert into the log table with previous and new quantity
            query = """
                INSERT INTO stock_adjustments (
                    product_id, adjustment_type, quantity, reason, adjusted_by, previous_quantity, new_quantity, adjusted_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (
                product_id, adjustment_type, quantity, reason,
                adjusted_by, previous_quantity, new_quantity
            ))

            # Update the stock to match the new quantity
            update_query = "UPDATE products SET qty = %s WHERE product_id = %s"
            cursor.execute(update_query, (new_quantity, product_id))

            self.connection.commit()
            return True
        except Exception as e:
            print("Error logging stock adjustment:", e)
            self.connection.rollback()
            return False

        
    def get_product_stock(self, product_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT qty FROM products WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except Exception as e:
            print("Error fetching product stock:", e)
            return 0.0
        
        
        
    def fetch_stock_adjustments(self, product_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT adjustment_type, quantity, reason, adjusted_by, created_at
                FROM stock_adjustments
                WHERE product_id = %s
                ORDER BY created_at ASC
            """
            cursor.execute(query, (product_id,))
            return cursor.fetchall()
        except Exception as e:
            print("Error fetching stock adjustments:", e)
            return []




        
        










