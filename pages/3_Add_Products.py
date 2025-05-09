import streamlit as st
import pandas as pd
from conn import DatabaseConnection
import pandas as pd
from io import StringIO
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()


def clean_nullable(value):
    """Return None if value is NaN or empty, otherwise return the value itself."""
    return None if pd.isna(value) or value == "" else value

# Function to generate CSV template
def generate_csv_template():
    sample_data = {
        "product_name": [],
        "barcode": [],
        "unit_of_measure": [],
        "opening_qty": [],
        "batch_number": [],
        "expiration_date": []  # Format: YYYY-MM-DD
    }
    df = pd.DataFrame(sample_data)
    df.columns = [col.strip() for col in df.columns]
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()  # ✅ return as string

db = DatabaseConnection()
db.connect()

st.title("🛠️ Create New Product")

# --- Manual Product Entry Form ---
st.subheader("➕ Add Product Manually")
with st.form("add_product_form"):
    product_name = st.text_input("Product Name", placeholder="e.g. Sugar 1kg")
    barcode = st.text_input("Barcode (optional)", placeholder="e.g. 1234567890123")
    uom = st.selectbox("Unit of Measure", ["Litre", "Barrel", "Box", "Kg", "Piece", "Dozen", "Other"])
    opening_qty = st.number_input("Opening Quantity", min_value=0.0, step=1.0)

    submitted = st.form_submit_button("Add Product")
    if submitted:
        if not product_name or not uom:
            st.warning("Please fill in all required fields.")
        else:
            if db.add_product(product_name, barcode, uom, opening_qty):
                st.success("✅ Product added successfully!")
            else:
                st.error("❌ Failed to add product.")

# --- CSV Upload Section ---
st.subheader("📁 Bulk Upload via CSV")
# Function to generate the Excel template dynamically




# UI Section for download


with st.expander("📄 Download CSV Template"):
    st.download_button(
        label="📥 Download CSV Template",
        data=generate_csv_template(),  # Now returns a string
        file_name="Product_Upload_Template.csv",
        mime="text/csv"
    )



with st.expander("Upload CSV"):
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        required_cols = {"product_name", "unit_of_measure", "opening_qty"}
        if not required_cols.issubset(df.columns):
            st.error("CSV must include at least 'product_name', 'unit_of_measure', and 'opening_qty' columns.")
        else:
            st.dataframe(df)

            if st.button("📥 Upload All"):
                results = []

                for _, row in df.iterrows():
                    product_name = row["product_name"]
                    unit_of_measure = row["unit_of_measure"]
                    opening_qty = row["opening_qty"]
                    barcode = clean_nullable(row.get("barcode"))
                    batch_number = clean_nullable(row.get("batch_number"))
                    expiration_date = clean_nullable(row.get("expiration_date"))

                    # Convert expiration_date to correct format if not None
                    if expiration_date:
                        try:
                            expiration_date = pd.to_datetime(expiration_date).date()
                        except Exception as e:
                            st.error(f"Invalid date format in row {_}: {expiration_date}")
                            continue

                    result = db.add_product(
                        product_name,
                        barcode,
                        unit_of_measure,
                        opening_qty,
                        batch_number,
                        expiration_date
                    )
                    results.append(result)

                if all(results):
                    st.success(f"✅ Uploaded {len(results)} products successfully.")
                else:
                    st.warning(f"⚠️ Some products may have failed to upload. Check your data and try again.")

