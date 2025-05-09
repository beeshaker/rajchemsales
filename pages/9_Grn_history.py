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

# Connect to DB
db = DatabaseConnection()
db.connect()

st.header("🔎 GRN History Lookup")

search_grn_id = st.text_input("Enter GRN Number to Search (e.g., GRN-20250428-01)")

if search_grn_id:
    grn_data = db.get_grn_items(search_grn_id)

    if grn_data:
        df = pd.DataFrame(grn_data)

        # Create clean display table
        display_df = df[[
            'product_id', 'ordered_qty', 'received_qty', 'verified_qty', 'discrepancy', 'remarks'
        ]].copy()

        display_df.rename(columns={
            'product_id': 'Product ID',
            'ordered_qty': 'Ordered Qty',
            'received_qty': 'Received Qty (Accounts)',
            'verified_qty': 'Verified Qty (Dispatch)',
            'discrepancy': 'Discrepancy',
            'remarks': 'Remarks'
        }, inplace=True)

        st.dataframe(display_df, use_container_width=True)

        # Optional summary
        total_ordered = display_df["Ordered Qty"].sum()
        total_verified = display_df["Verified Qty (Dispatch)"].sum()
        total_discrepancy = display_df["Discrepancy"].sum()

        st.subheader("📋 GRN Summary")
        st.write(f"**Total Ordered:** {total_ordered}")
        st.write(f"**Total Verified:** {total_verified}")
        st.write(f"**Total Discrepancy:** {total_discrepancy}")

    else:
        st.warning("⚠️ No GRN records found for this number.")
