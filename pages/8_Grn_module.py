import streamlit as st
import pandas as pd
from conn import DatabaseConnection  # ✅ Correct import
from datetime import datetime
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

db = DatabaseConnection()
db.connect()

with st.expander("GRN uploading"):
    st.header("📦 Upload Goods Received Note (GRN) - Accounts Team")

    grn_id = st.text_input("Enter GRN ID (e.g., GRN-20250428-01)")
    uploaded_file = st.file_uploader("Upload GRN Excel File", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.dataframe(df)

        if st.button("Save GRN to Database"):
            for _, row in df.iterrows():
                db.insert_grn_item(
                    grn_id,
                    int(row['product_id']),
                    float(row['ordered_qty']),
                    0.0  # Received quantity set as 0 initially
                )
            st.success("✅ GRN uploaded successfully!")

with st.expander("GRN verification"):
    st.header("✅ Verify Goods Received - Dispatch Team")

    grn_id = st.text_input("Enter GRN ID to Verify")

    if grn_id:
        grn_data = db.get_grn_items(grn_id)

        if grn_data:
            for row in grn_data:
                # Get product details from the products table
                product_details = db.get_product_details(row['product_id'])  # new method to be created
                row['product_name'] = product_details.get('product_name', 'N/A')
                row['unit_of_measure'] = product_details.get('unit_of_measure', 'N/A')

            df = pd.DataFrame(grn_data)
            df['verified_qty'] = 0

            st.write("Update verified quantities:")

            for index, row in df.iterrows():
                label = f"{row['product_id']} - {row['product_name']} ({row['unit_of_measure']}) | Ordered: {row['ordered_qty']}"
                df.at[index, 'verified_qty'] = st.number_input(
                    label,
                    min_value=0.0,
                    value=0.0,
                    key=f"verify_{index}"
                )

            if st.button("Save Verification"):
                for index, row in df.iterrows():
                    discrepancy = float(row['verified_qty']) - float(row['ordered_qty'])

                    db.update_grn_verification(
                        row['id'],
                        row['verified_qty'],
                        discrepancy
                    )

                    db.increase_product_quantity(
                        row['product_id'],
                        row['verified_qty']
                    )

                    db.log_stock_movement(
                        product_id=row['product_id'],
                        movement_type='IN',
                        quantity=row['verified_qty'],
                        reference=row['grn_id'],
                        remarks="GRN Verified Entry"
                    )

                st.success("✅ Verification saved and stock updated!")
                st.rerun()



