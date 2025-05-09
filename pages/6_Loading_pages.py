import streamlit as st
import pandas as pd
from conn import DatabaseConnection
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

st.title("🚛 Loading Team – Order Fulfillment")

db = DatabaseConnection()
db.connect()

orders = db.fetch_director_approved_orders()

if not orders:
    st.info("No orders pending loading.")
else:
    # Sort orders by date (oldest first)
    orders = sorted(orders, key=lambda x: x["order_date"])

    for order in orders:
        customer = db.get_customer_by_id(order["customer_id"])
        customer_label = (
            f"{customer['customer_name']} ({customer['contact_person_name']})"
            if customer else "Unknown Customer"
        )

        with st.expander(f"{order['order_id']} – {customer_label} – {order['order_date']}"):
            st.markdown(f"**Salesperson:** {order['salesperson_name']}")
            st.markdown(f"**Director Approval:** ✅ Approved")
            st.markdown("### 📦 Update Items")

            item_updates = []
            for item in order["items"]:
                st.markdown(
                        f"""
                        <div style='
                            padding: 10px;
                            background-color: #000000;
                            border-left: 5px solid #2c7be5;
                            border-radius: 5px;
                            font-weight: bold;
                            font-size: 16px;
                            color: white;
                        '>
                            {item['product_name']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.metric(
                    label=f"Ordered Qty",
                    value=item["quantity_ordered"]
                )
                col1, col2 = st.columns([1.5, 1])

                with col1:
                    loaded_qty = st.number_input(
                        f"Loaded Qty ", 
                        min_value=0.0,
                        value=item.get("loaded_quantity", item["quantity_ordered"]),
                        step=0.01,
                        key=f"loaded_qty_{item['id']}"            )
                
                    
                with col2:
                    remarks = st.text_input(
                        f"Remarks ",
                        key=f"load_remarks_{item['id']}"
                    )

                item_updates.append({
                    "item_id": item["id"],
                    "loaded_quantity": loaded_qty,
                    "loading_remarks": remarks
                })

            # General remarks
            st.markdown("### 📝 General Loading Remarks")
            loading_remarks = st.text_area(
                f"Loading remarks for Order {order['order_id']}",
                key=f"loading_remarks_{order['order_id']}"
            )

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"✅ Mark as Loaded ({order['order_id']})"):
                    if db.update_loading_status(order["order_id"], "Loaded", loading_remarks, item_updates):
                        # ✅ After marking as Loaded, decrease stock
                        for item_update in item_updates:
                            item_id = item_update["item_id"]
                            loaded_qty = item_update["loaded_quantity"]

                            # You need product_id for this item
                            product_id = None
                            for item in order["items"]:
                                if item["id"] == item_id:
                                    product_id = item["product_id"]
                                    break

                            if product_id and loaded_qty > 0:
                                db.decrease_product_quantity(product_id, loaded_qty)
                                db.log_stock_movement(
                                product_id=product_id,
                                movement_type='OUT',
                                quantity=loaded_qty,
                                reference=f"Order {order['order_id']}",
                                remarks=item_update["loading_remarks"]
                            )

                    st.success("Order marked as Loaded and stock updated!")
                    st.rerun()

            with col2:
                if st.button(f"🕓 Still Pending ({order['order_id']})"):
                    if db.update_loading_status(order["order_id"], "Pending Loading", loading_remarks, item_updates):
                        st.warning("Order marked as Pending")
                        st.rerun()
            with col3:
                if st.button(f"❌ Cancel Order ({order['order_id']})"):
                    if db.update_loading_status(order["order_id"], "Cancelled", loading_remarks, item_updates):
                        st.error("Order has been Cancelled")
                        st.rerun()
