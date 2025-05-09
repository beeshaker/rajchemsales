import streamlit as st
from conn import DatabaseConnection
import pandas as pd
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

db = DatabaseConnection()
db.connect()

# Fetch only orders with Pending status from accounts
pending_orders = db.fetch_orders_by_accounts_status("Pending")

st.title("💰 Accounts Approval – Sales Orders")

if not pending_orders:
    st.success("✅ No orders pending accounts approval.")
else:
    # Build the selectbox options with full customer labels
    order_options = []
    for o in pending_orders:
        customer = db.get_customer_by_id(o["customer_id"])
        customer_label = (
            f"{customer['customer_name']} ({customer['contact_person_name']})"
            if customer else "Unknown Customer"
        )
        order_options.append(f"{o['order_id']} - {customer_label}")

    selected_order_id = st.selectbox("Select Order to Review", order_options)
    order_id = selected_order_id.split(" - ")[0]
    order = next(o for o in pending_orders if o["order_id"] == order_id)

    order_id = selected_order_id.split(" - ")[0]
    order = next(o for o in pending_orders if o["order_id"] == order_id)

    st.markdown(f"### 🧾 Order `{order['order_id']}`")
    customer = db.get_customer_by_id(order["customer_id"])
    st.write(f"**Customer:** {customer['customer_name']} ({customer['contact_person_name']})" if customer else "Unknown Customer")
    st.write(f"**Order Created By:** {order['salesperson_name']}")
    st.write(f"**Payment Terms:** {order['payment_terms']}")
    st.write(f"**Order Date:** {order['order_date']}")

    # Display items
    item_df = pd.DataFrame([{
        "Product": i["product_name"],
        "Qty": i["quantity_ordered"],
        "Unit Price": i["unit_price"],
        "Total": i["quantity_ordered"] * i["unit_price"]
    } for i in order["items"]])
    item_df.index = range(1, len(item_df) + 1)
    st.dataframe(item_df, use_container_width=True)

    # Approval Section
    st.markdown("### 💬 Remarks from Accounts")
    remarks = st.text_area("Enter your remarks")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Recommend for Processing"):
            if db.update_accounts_approval(order_id, "Recommend for Processing", remarks):
                st.success("Order approved.")
                st.rerun()

    with col2:
        if st.button("❌ Do Not Recommend"):
            if db.update_accounts_approval(order_id, "Do Not Recommend", remarks):
                st.warning("Order rejected.")
                st.rerun()
