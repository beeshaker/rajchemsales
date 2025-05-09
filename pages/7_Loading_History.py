import streamlit as st
import pandas as pd
from datetime import datetime
from conn import DatabaseConnection
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

st.title("📦 Loading History – Fulfilled & Cancelled Orders")

db = DatabaseConnection()
db.connect()

orders = db.fetch_loading_history()

if not orders:
    st.info("No loaded or cancelled orders found.")
else:
    # --- Sidebar filters ---
    with st.sidebar:
        st.header("🔍 Filter Orders")
        
        # Enrich orders with customer info
        for order in orders:
            customer = db.get_customer_by_id(order["customer_id"])
            if customer:
                order["customer_name"] = customer["customer_name"]
                order["contact_person_name"] = customer["contact_person_name"]
            else:
                order["customer_name"] = "Unknown"
                order["contact_person_name"] = ""

        all_customers = sorted(list(set([f"{o['customer_name']} ({o['contact_person_name']})" for o in orders])))

        customer_filter = st.multiselect("Customer", options=all_customers)
        
        status_filter = st.multiselect("Loading Status", options=["Loaded", "Cancelled"])
        
        date_min = min([o["order_date"] for o in orders])
        date_max = max([o["order_date"] for o in orders])
        start_date, end_date = st.date_input("Filter by Order Date", value=[date_min, date_max])

    # Apply filters
    filtered = []
    for order in orders:
        date_ok = start_date <= order["order_date"].date() <= end_date
        customer_ok = not customer_filter or order["customer_name"] in customer_filter
        status_ok = not status_filter or order["loading_status"] in status_filter

        if date_ok and customer_ok and status_ok:
            filtered.append(order)

    if not filtered:
        st.warning("No matching orders found.")
    else:
        # Summary
        total_loaded = sum(1 for o in filtered if o['loading_status'] == 'Loaded')
        total_cancelled = sum(1 for o in filtered if o['loading_status'] == 'Cancelled')
        st.success(f"✅ Loaded Orders: {total_loaded}")
        st.error(f"❌ Cancelled Orders: {total_cancelled}")

        # Group orders
        grouped = {
            "Loaded": [o for o in filtered if o["loading_status"] == "Loaded"],
            "Cancelled": [o for o in filtered if o["loading_status"] == "Cancelled"]
        }

        for status, group in grouped.items():
            if group:
                st.subheader(f"{'✅' if status == 'Loaded' else '❌'} {status} Orders")
                for order in group:
                    # Variance check
                    has_variance = any((item.get("loaded_quantity") or 0) != item["quantity_ordered"] for item in order['items'])

                    title = f"{order['order_id']} – {order['customer_name']} – {order['order_date'].strftime('%Y-%m-%d')} – Status: {order['loading_status']}"

                    # Color-coded summary box
                    if has_variance:
                        st.markdown(
                            f"""
                            <div style='background-color:#fee2e2; padding:0.75rem 1rem; border-radius:0.5rem; font-weight:600;'>
                                🚨 {title} <span style='color:#dc2626'>(Variance Detected)</span>
                            </div>
                            """, unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style='background-color:#e0f7ef; padding:0.75rem 1rem; border-radius:0.5rem; font-weight:600;'>
                                ✅ {title}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    # Expandable order detail
                    with st.expander("📋 View Order Details", expanded=False):
                        st.markdown(f"**Salesperson:** {order['salesperson_name']}")
                        st.markdown(f"**Director Status:** {order.get('director_approval_status', '')}")
                        st.markdown(f"**Director Remarks:** {order.get('director_remarks', '')}")
                        st.markdown(f"**Accounts status:** {order.get('accounts_approval_status', '')}")
                        st.markdown(f"**Accounts Remarks:** {order.get('accounts_remarks', '')}")
                        st.markdown(f"**Loading Remarks:** {order.get('loading_remarks', '')}")

                        item_rows = []
                        for item in order['items']:
                            loaded_qty = item.get("loaded_quantity") or 0
                            variance = loaded_qty - item["quantity_ordered"]
                            item_rows.append({
                                "Product": item["product_name"],
                                "Ordered Qty": item["quantity_ordered"],
                                "Loaded Qty": loaded_qty,
                                "Variance": variance,
                                "Remarks": item.get("loading_remarks", "")
                            })

                        df = pd.DataFrame(item_rows)
                        df.index = range(1, len(df) + 1)

                        def highlight_variances(row):
                            color = 'background-color: #fde68a' if row['Variance'] != 0 else ''
                            return [color] * len(row)

                        styled_df = df.style.apply(highlight_variances, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
