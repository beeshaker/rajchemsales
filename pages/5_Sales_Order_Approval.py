import streamlit as st
from conn import DatabaseConnection
import pandas as pd
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

st.title("✔️ Director Review – Final Approval")

# DB connection
db = DatabaseConnection()
db.connect()

orders = db.fetch_director_pending_orders()

if not orders:
    st.info("No orders to review.")
else:
    with st.sidebar:
        st.header("🔍 Filter")
        status_filter = st.selectbox("Filter by Director Status", ["All", "Pending", "Approved", "Rejected"])
    
    if status_filter != "All":
        orders = [o for o in orders if o["director_approval_status"] == status_filter]

    for order in orders:
        customer = db.get_customer_by_id(order["customer_id"])
        customer_label = (
            f"{customer['customer_name']} ({customer['contact_person_name']})"
            if customer else "Unknown Customer"
        )

        with st.expander(f"{order['order_id']} — {customer_label} — [Final: {order['director_approval_status']}]"):
            st.markdown(f"**Customer:** {customer_label}")            
            st.markdown(f"**Salesperson:** {order['salesperson_name']}")
            st.markdown(f"**Order Date:** {order['order_date']}")
            st.markdown(f"**Payment Terms:** {order['payment_terms']}")
            st.markdown(f"**Accounts Status:** `{order['accounts_approval_status']}`")
            st.markdown(f"**Accounts Remarks:** {order.get('accounts_remarks', '')}")
            #st.markdown(f"**Final Director Status:** `{order['director_approval_status']}`")
            #st.markdown(f"**Director Remarks:** {order.get('director_remarks', '')}")

            # Order items
            item_rows = [{
                "Product": item["product_name"],
                "Qty": item["quantity_ordered"],
                "Unit Price": item["unit_price"],
                "Total": item["quantity_ordered"] * item["unit_price"],
                "Remarks": item.get("remarks", "")
            } for item in order["items"]]

            df = pd.DataFrame(item_rows)
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

            # If still pending final approval, show action form
            if order["director_approval_status"] == "Pending":
                st.markdown("### ✅ Final Approval Decision")
                director_remarks = st.text_area("Remarks (visible to accounts & sales)", key=f"remarks_{order['order_id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{order['order_id']}"):
                        if db.update_director_approval(order["order_id"], "Approved", director_remarks):
                            st.success("Order approved by Director.")
                            st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{order['order_id']}"):
                        if db.update_director_approval(order["order_id"], "Rejected", director_remarks):
                            st.warning("Order rejected by Director.")
                            st.rerun()
