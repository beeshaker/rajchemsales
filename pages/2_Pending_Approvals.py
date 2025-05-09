import streamlit as st
import pandas as pd
from conn import DatabaseConnection
from menu import menu

# Auth check
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()

# DB connection
db = DatabaseConnection()
db.connect()

# Fetch pending orders
orders = db.fetch_pending_orders()
order_summary_rows = []
for order in orders:
    customer_info = db.get_customer_by_id(order['customer_id'])
    customer_label = (
        f"{customer_info['customer_name']} ({customer_info['contact_person_name']})"
        if customer_info else "Unknown"
    )

if not orders:
    st.info("No pending orders to approve.")
else:
    st.markdown("## 🕓 Pending Approval Orders")

    # --- Build order-level summary table (not items) ---
    order_summary_rows = []
    for order in orders:
        order_summary_rows.append({
            "Order ID": order['order_id'],
            "Customer": customer_label,
            "Order Created By": order['salesperson_name'],
            "Order Date": order['order_date'],
            "Status": order.get('accounts_approval_status', 'Pending')
        })

    df_orders = pd.DataFrame(order_summary_rows)

    # --- Sidebar Filters ---
    st.sidebar.header("🔍 Filter Orders")

    customer_filter = st.sidebar.multiselect("Filter by Customer", options=df_orders["Customer"].unique())
    salesperson_filter = st.sidebar.multiselect("Filter by Order Created By", options=df_orders["Order Created By"].unique())
    order_id_filter = st.sidebar.multiselect("Filter by Order ID", options=df_orders["Order ID"].unique())

    # Apply filters
    filtered_df = df_orders.copy()
    if customer_filter:
        filtered_df = filtered_df[filtered_df["Customer"].isin(customer_filter)]
    if salesperson_filter:
        filtered_df = filtered_df[filtered_df["Order Created By"].isin(salesperson_filter)]
    if order_id_filter:
        filtered_df = filtered_df[filtered_df["Order ID"].isin(order_id_filter)]

    filtered_df.set_index("Order ID", inplace=True)
    st.dataframe(filtered_df, use_container_width=True)

    # --- Order Details Section ---
    st.markdown("### 📄 View Specific Order Details")

    order_display_options = []
    for o in orders:
        customer_info = db.get_customer_by_id(o['customer_id'])
        customer_label = (
            f"{customer_info['customer_name']} ({customer_info['contact_person_name']})"
            if customer_info else "Unknown Customer"
        )
        print(customer_info)
        order_display_options.append(f"{o['order_id']} - {customer_label}")
    selected_order_display = st.selectbox("Select an Order", options=order_display_options)

    selected_order_id = selected_order_display.split(" - ")[0]
    selected_order = next(order for order in orders if order["order_id"] == selected_order_id)

    customer_info = db.get_customer_by_id(selected_order['customer_id'])
    customer_label = (
        f"{customer_info['customer_name']} ({customer_info['contact_person_name']})"
        if customer_info else "Unknown"
    )

    st.markdown(f"### 🧾 Order Details for `{selected_order_id}`")
    st.markdown(f"**Customer:** {customer_label}")
    st.markdown(f"**Salesperson:** {selected_order['salesperson_name']}")
    st.markdown(f"**Order Date:** {selected_order['order_date']}")
    st.markdown(f"**Status:** {selected_order.get('accounts_approval_status', 'Pending')}")
    st.markdown(f"**Payment Terms:** {selected_order.get('payment_terms', 'N/A')}")


    # Show item details
    item_rows = []
    for item in selected_order["items"]:
        item_rows.append({
            "Product": item["product_name"],
            "Quantity": item["quantity_ordered"],
            "Unit Price": item["unit_price"],
            "Total": item.get("total_price", item["quantity_ordered"] * item["unit_price"]),
        })

    st.markdown("#### 📦 Items in This Order")
    item_df = pd.DataFrame(item_rows)
    item_df.index = range(1, len(item_df) + 1)
    st.dataframe(item_df, use_container_width=True)
