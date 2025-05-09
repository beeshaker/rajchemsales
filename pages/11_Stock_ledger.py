import streamlit as st
import pandas as pd
from conn import DatabaseConnection
from menu import menu

# Page protection
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()

st.title("📋📦 Stock Ledger (Product-wise Movement)")

db = DatabaseConnection()
db.connect()

# Fetch all products
def get_all_products():
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()

        cursor = db.connection.cursor(dictionary=True)
        query = "SELECT product_id, product_name FROM products"
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

# Fetch movements for a product
def get_product_movements(product_id):
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()

        cursor = db.connection.cursor(dictionary=True)
        query = """
            SELECT 
                movement_type,
                quantity,
                reference,
                remarks,
                created_at
            FROM stock_movements
            WHERE product_id = %s
            ORDER BY created_at ASC
        """
        cursor.execute(query, (product_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching stock movements: {e}")
        return []

# Select Product
products = get_all_products()

if products:
    product_options = {f"{p['product_name']} (ID: {p['product_id']})": p['product_id'] for p in products}
    selected_product_label = st.selectbox("Select Product:", list(product_options.keys()))
    selected_product_id = product_options[selected_product_label]

    # Load stock movements
    movements = get_product_movements(selected_product_id)

    # Load adjustments and merge into movements
    adjustments = db.fetch_stock_adjustments(selected_product_id)
    for adj in adjustments:
        movements.append({
            "movement_type": "ADJ",
            "quantity": adj["quantity"] if adj["adjustment_type"] == "Increase" else -adj["quantity"],
            "reference": f"Adjusted by {adj['adjusted_by']}",
            "remarks": adj["reason"],
            "created_at": adj["created_at"]
        })

    if movements:
        ledger = pd.DataFrame(movements)
        ledger['Date'] = pd.to_datetime(ledger['created_at'])

        # Adjust quantity signs
        ledger['Quantity'] = ledger.apply(
            lambda row: row['quantity'] if row['movement_type'] in ['IN', 'ADJ'] else -row['quantity'],
            axis=1
        )

        # Get product info
        product_info = db.get_product_opening_info(selected_product_id)
        opening_qty = float(product_info['opening_qty'])
        unit = product_info['unit_of_measure']

        # Opening row
        opening_row = {
            'Date': pd.to_datetime("1970-01-01"),
            'Movement': 'Opening Stock',
            'Quantity': opening_qty,
            'Running Balance': opening_qty,
            'Reference': '',
            'Remarks': '',
            'Unit': unit
        }

        # Format ledger
        ledger.rename(columns={
            'movement_type': 'Movement',
            'reference': 'Reference',
            'remarks': 'Remarks'
        }, inplace=True)

        # Replace movement type labels for clarity
        ledger['Movement'] = ledger['Movement'].replace({
            "IN": "Stock In",
            "OUT": "Stock Out",
            "ADJ": "Adjustment"
        })

        ledger['Unit'] = unit

        # Sort by date
        ledger.sort_values(by="Date", inplace=True)
        ledger.reset_index(drop=True, inplace=True)

        # Add running balance
        ledger['Running Balance'] = opening_qty + ledger['Quantity'].cumsum()

        # Append opening row
        ledger = pd.concat([pd.DataFrame([opening_row]), ledger], ignore_index=True)
        ledger['Running Balance'] = ledger['Quantity'].cumsum()

        # Final column order
        ledger['Date'] = ledger['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        ledger = ledger[['Date', 'Movement', 'Quantity', 'Unit', 'Running Balance', 'Reference', 'Remarks']]

        st.subheader("📋 Stock Ledger")
        st.dataframe(ledger, use_container_width=True)

        # Summary Section
        st.subheader("📊 Summary:")
        st.write(f"**Opening Stock:** {opening_qty} {unit}")
        st.write(f"**Total IN:** {ledger[ledger['Movement'] == 'Stock In']['Quantity'].sum()} {unit}")
        st.write(f"**Total OUT:** {ledger[ledger['Movement'] == 'Stock Out']['Quantity'].sum()} {unit}")
        st.write(f"**Total Adjustments:** {ledger[ledger['Movement'] == 'Adjustment']['Quantity'].sum()} {unit}")
        st.write(f"**Final Running Balance:** {ledger['Running Balance'].iloc[-1]} {unit}")

    else:
        st.info("ℹ️ No stock movement records found for this product.")
else:
    st.warning("⚠️ No products available.")
