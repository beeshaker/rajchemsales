import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from conn import DatabaseConnection
from menu import menu

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()

st.title("📊 Sales & Operations Reports")

db = DatabaseConnection()
db.connect()

orders = db.fetch_all_orders()

if not orders:
    st.info("No orders to report on.")
    st.stop()

# --- Top Products ---
with st.expander("Top Products"):
    st.subheader("🏆 Top Products by Sales Value")
    product_sales = {}
    product_qty = {}
    for order in orders:
        for item in order['items']:
            key = item['product_name']
            product_sales.setdefault(key, 0)
            product_qty.setdefault(key, 0)
            product_sales[key] += item['quantity_ordered'] * item['unit_price']
            product_qty[key] += item['quantity_ordered']

    product_df = pd.DataFrame([
        {"Product": k, "Quantity Sold": product_qty[k], "Total Sales": product_sales[k]}
        for k in product_sales
    ])
    product_df = product_df.sort_values("Total Sales", ascending=False)
    st.dataframe(product_df, use_container_width=True)

    fig = px.bar(product_df.head(10), x="Total Sales", y="Product", orientation="h", title="Top 10 Products")
    st.plotly_chart(fig, use_container_width=True)

# --- Customer Activity ---
with st.expander("Customer Activity"):
    st.subheader("🧾 Customer Activity Report")
    customer_orders = {}
    for order in orders:
        key = order['customer_id']
        customer_info = db.get_customer_by_id(key)
        name = customer_info['customer_name'] if customer_info else "Unknown"

        customer_orders.setdefault(name, {"total_orders": 0, "total_value": 0})
        customer_orders[name]["total_orders"] += 1
        customer_orders[name]["total_value"] += order["total_amount"]

    cust_df = pd.DataFrame([
        {"Customer": k, "Orders Placed": v["total_orders"], "Total Sales": v["total_value"]}
        for k, v in customer_orders.items()
    ])
    cust_df = cust_df.sort_values("Total Sales", ascending=False)
    st.dataframe(cust_df, use_container_width=True)

    fig = px.bar(cust_df.head(10), x="Total Sales", y="Customer", orientation="h", title="Top 10 Customers")
    st.plotly_chart(fig, use_container_width=True)

# --- Loading Variance Report ---
with st.expander("Loading Variance Report"):
    st.subheader("⚠️ Loading Variance Report")
    variance_rows = []
    for order in orders:
        for item in order['items']:
            loaded = item.get('loaded_quantity') or 0
            ordered = item['quantity_ordered']
            if loaded != ordered:
                variance_rows.append({
                    "Order ID": order['order_id'],
                    "Product": item['product_name'],
                    "Ordered Qty": ordered,
                    "Loaded Qty": loaded,
                    "Variance": loaded - ordered,
                    "Customer": db.get_customer_by_id(order['customer_id'])['customer_name'] if db.get_customer_by_id(order['customer_id']) else "Unknown"
                })

    if variance_rows:
        var_df = pd.DataFrame(variance_rows)
        st.dataframe(var_df, use_container_width=True)

        fig = px.bar(var_df, x="Product", y="Variance", color="Customer", title="Loading Variances by Product")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ No variances detected in loaded orders.")

# --- Sales Over Time ---
with st.expander("Sales Over Time"):
    st.subheader("📈 Monthly Sales Summary")
    month_sales = {}
    for order in orders:
        month = pd.to_datetime(order['order_date']).strftime('%Y-%m')
        month_sales.setdefault(month, 0)
        month_sales[month] += order['total_amount']

    month_df = pd.DataFrame([
        {"Month": k, "Total Sales": v} for k, v in sorted(month_sales.items())
    ])
    st.dataframe(month_df, use_container_width=True)

    fig = px.line(month_df, x="Month", y="Total Sales", markers=True, title="Sales Trend Over Time")
    st.plotly_chart(fig, use_container_width=True)

db.disconnect()