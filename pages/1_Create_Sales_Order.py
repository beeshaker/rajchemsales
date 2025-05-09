import streamlit as st
from conn import DatabaseConnection
from datetime import datetime
import pandas as pd
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()



# Initialize the database connection
db = DatabaseConnection()
db.connect()

# Check if the connection was successful
if not db.connection or not db.connection.is_connected():
    st.error("Failed to connect to the database. Please check your credentials and try again.")
else:
    # Title of the application
    st.title("Sales Order Tracker")
    st.subheader("Step 1: Create an Order")
    
   

   
    


    # Initialize session state for items if not already set
    if "items" not in st.session_state:
        st.session_state["items"] = [{"product_name": "", "quantity_ordered": 0.01, "unit_price": 0.0}]
        
    st.write("Enter the details of the order:")

    # Customer Information
    customers = db.get_all_customers()
    if customers:
        customer_options = {
            f"{c['customer_name']} ({c['contact_person_name']}) - ID {c['id']}": c for c in customers
        }
        selected_customer_label = st.selectbox("Select Customer", list(customer_options.keys()))
        selected_customer = customer_options[selected_customer_label]

        customer_id = selected_customer["id"]
        customer_name = selected_customer["customer_name"]
        customer_contact = selected_customer.get("contact", "")  # optional, for display or logging
    else:
        st.warning("⚠️ No customers found. Please create one first.")
        customer_id = None
        customer_name = ""
        customer_contact = ""

    


    # Allow the user to specify the number of items outside the form
    st.write("Set the number of items:")
    num_items = st.number_input(
        "Number of Items",
        min_value=1,
        value=len(st.session_state["items"]),
        key="num_items_input"
    )
    
    payment_terms = st.text_input("Payment Terms (Optional)", placeholder="e.g. 30 days credit")

    if st.button("Apply Item Count"):
        current_count = len(st.session_state["items"])
        if current_count < num_items:
            for _ in range(num_items - current_count):
                st.session_state["items"].append({"product_name": "", "quantity_ordered": 1, "unit_price": 0.0})
        elif current_count > num_items:
            st.session_state["items"] = st.session_state["items"][:num_items]
        st.rerun()

    # Input fields for order creation
    with st.form("order_creation_form"):
        products = db.fetch_all_products()
        product_options = [f"{p['product_id']} - {p['product_name']}" for p in products]


        
        # Items Section
        st.write("Add Items to the Order:")
        total_amount = 0.0
        
        

        # Render rows for each item
        for i, item in enumerate(st.session_state["items"]):
            st.write(f"Item {i + 1}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                

                selected_product = st.selectbox(
                    "Select Product",
                    options=product_options,
                    key=f"product_select_{i}"
                )

                # Extract and store only product name
                product_id, product_name = selected_product.split(" - ", 1)
                item["product_id"] = int(product_id.strip())
                item["product_name"] = product_name.strip()
                        
            with col2:
                item["quantity_ordered"] = st.number_input(
                    "Quantity", 
                    min_value=0.0, 
                    step=0.01,
                    value=float(item["quantity_ordered"]), 
                    key=f"quantity_{i}"
                )
            
            with col3:
                item["unit_price"] = st.number_input(
                    "Unit Price", 
                    min_value=0.0, 
                    value=item["unit_price"], 
                    step=0.01, 
                    key=f"unit_price_{i}"
                )
            
            # Calculate total price for the item
            item_total = item["quantity_ordered"] * item["unit_price"]
            total_amount += item_total

        # Display total amount
        st.write(f"Total Amount: Ksh{total_amount:.2f}")

        # Submit button
        submitted =  st.form_submit_button("Create Order")

    # Handle form submission
    if submitted:
        # Validate inputs
        if not customer_name or not customer_contact or not any(item["product_name"] for item in st.session_state["items"]):
            st.error("Please fill in all required fields.")
        else:
            # Generate a unique Order ID
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order_status = "Pending"
            
            created = db.create_order(
            order_id=order_id,
            customer_id=customer_id,
            user=st.session_state["username"],
            total_amount=total_amount,
            order_date=order_date,
            accounts_approval_status=order_status,
            items=st.session_state["items"],
            payment_terms=payment_terms  # <-- add this line
        )



            # Create the order in the database
            if created:
                st.success(f"Order {order_id} created successfully!")
                st.session_state["items"] = [{"product_name": "", "quantity_ordered": 1, "unit_price": 0.0}]  # Reset items
            else:
                st.error("Failed to create the order.")

    # Display the list of created orders
    
# Disconnect from the database when done
db.disconnect()