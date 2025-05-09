import streamlit as st
import pandas as pd
from conn import DatabaseConnection
from io import BytesIO
from menu import menu

# Protect the page
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()
else:
    menu()



st.header("➕ Create Single Customer")

db = DatabaseConnection()
db.connect()


with st.form("single_customer_form"):
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name", placeholder="e.g. ABC Ltd")
        contact = st.text_input("Contact Info", placeholder="Phone or Email")

    with col2:
        contact_person = st.text_input("Contact Person", placeholder="e.g. Jane Doe")
        address = st.text_input("Address", placeholder="e.g. Nairobi Industrial Area")

    submit = st.form_submit_button("Create Customer")

    if submit:
        if not customer_name or not contact or not contact_person:
            st.error("Please fill in all required fields (Name, Contact, Contact Person).")
        else:
            success = db.insert_customer(customer_name, contact, address, contact_person)
            if success:
                st.success("✅ Customer created successfully.")
            else:
                st.error("❌ Failed to create customer.")
                
st.markdown("---")

st.title("📤 Bulk Upload Customers")

def generate_template():
    df = pd.DataFrame(columns=["customer_name", "contact", "address", "contact_person_name"])
    output = BytesIO()
    df.to_csv(output, index=False)
    st.download_button(
        label="📥 Download Template CSV",
        data=output.getvalue(),
        file_name="customer_upload_template.csv",
        mime="text/csv"
    )

generate_template()

# 🔼 Upload CSV
uploaded_file = st.file_uploader("Upload Filled CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Validate columns
        expected_cols = {"customer_name", "contact", "address", "contact_person_name"}
        if not expected_cols.issubset(set(df.columns)):
            st.error(f"❌ CSV must contain columns: {', '.join(expected_cols)}")
        else:
            st.dataframe(df)

            if st.button("Upload Customers"):
                success_count = 0
                skipped_count = 0

                for _, row in df.iterrows():
                    if pd.notna(row['customer_name']) and pd.notna(row['contact']):
                        if db.customer_exists(row['customer_name'], row['contact']):
                            skipped_count += 1
                            continue

                        success = db.insert_customer(
                            name=row['customer_name'],
                            contact=row['contact'],
                            address=row.get('address', None),
                            contact_person_name=row.get('contact_person_name', None)
                        )
                        if success:
                            success_count += 1

                st.success(f"✅ Uploaded {success_count} customers. Skipped {skipped_count} duplicate(s).")
    except Exception as e:
        st.error(f"Error reading file: {e}")

db.disconnect()



