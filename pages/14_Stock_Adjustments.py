import streamlit as st
from datetime import datetime
from conn import DatabaseConnection
from menu import menu

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()

st.title("🔧 Stock Adjustment")

db = DatabaseConnection()
db.connect()

products = db.fetch_all_products()
product_options = {f"{p['product_id']} - {p['product_name']}": p['product_id'] for p in products}

with st.form("stock_adjustment_form"):
    product_label = st.selectbox("Select Product", list(product_options.keys()))
    product_id = product_options[product_label]

    # Fetch and display current stock
    current_stock = db.get_product_stock(product_id)  # Assume this method returns current quantity
    st.markdown(f"**Current Stock:** `{current_stock}` units")

    # Let user input new desired quantity
    new_quantity = st.number_input("New Quantity", min_value=0.0, step=0.01)

    # Show system-calculated adjustment
    adjustment_value = round(new_quantity - current_stock, 2)
    adjustment_type = "Increase" if adjustment_value > 0 else "Decrease" if adjustment_value < 0 else "No Change"

    if adjustment_type == "No Change":
        st.info("No stock change detected.")
    else:
        st.markdown(f"**Adjustment Type:** `{adjustment_type}` by `{abs(adjustment_value)}` units")

    reason = st.text_area("Reason for Adjustment")
    submitted = st.form_submit_button("Submit Adjustment")

    

if submitted:
    if adjustment_value == 0:
        st.warning("No adjustment needed.")
    else:
        adjusted_by = st.session_state["username"]
        success = db.log_stock_adjustment(
            product_id=product_id,
            adjustment_type=adjustment_type,
            quantity=abs(adjustment_value),
            reason=reason,
            adjusted_by=adjusted_by,
            previous_quantity=current_stock,
            new_quantity=new_quantity
        )
        if success:
            st.success("Stock adjustment recorded.")
            st.rerun()
        else:
            st.error("Failed to record stock adjustment.")


db.disconnect()
