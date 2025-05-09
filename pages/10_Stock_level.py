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

st.header("📦📊 Current Stock Levels")

# Fetch product stock
def get_current_stock():
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()

        cursor = db.connection.cursor(dictionary=True)
        query = """
            SELECT 
                product_id,
                product_name,
                opening_qty,
                qty
            FROM products
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results

    except Exception as e:
        print(f"Error fetching stock: {e}")
        return []

# Load stock data
stock_data = get_current_stock()

if stock_data:
    df = pd.DataFrame(stock_data)

    # Calculate Difference column
    df['Difference'] = df['qty'].astype(float) - df['opening_qty'].astype(float)

    # Rename for clean display
    display_df = df.rename(columns={
        'product_id': 'Product ID',
        'product_name': 'Product Name',
        'opening_qty': 'Opening Qty',
        'qty': 'Current Qty',
        'Difference': 'Difference'
    })[['Product ID', 'Product Name', 'Opening Qty', 'Current Qty', 'Difference']]
    
    display_df.set_index('Product ID', inplace=True)

    st.dataframe(display_df, use_container_width=True)

    # 📋 Overall Stock Summary
    st.subheader("📋 Overall Stock Summary")
    total_opening = display_df["Opening Qty"].sum()
    total_current = display_df["Current Qty"].sum()
    total_difference = display_df["Difference"].sum()

    st.write(f"**Total Opening Stock:** {total_opening}")
    st.write(f"**Total Current Stock:** {total_current}")
    st.write(f"**Net Stock Movement:** {total_difference}")

    # 🔍 Search for a specific product
    st.subheader("🔎 Search Product Stock")

    search_product = st.text_input("Enter Product Name or Product ID to Search:")

    if search_product:
        # Try to filter by product_id or product_name (case-insensitive)
        try:
            search_product_lower = search_product.lower()
        except AttributeError:
            search_product_lower = str(search_product).lower()

        search_results = df[
            df['product_name'].str.lower().str.contains(search_product_lower) |
            df['product_id'].astype(str).str.contains(search_product)
        ]

        
    # Fetch and show product movement
        st.subheader("📈 Stock Movement for Selected Product")

        if not search_results.empty:
            search_display_df = search_results.rename(columns={
                'product_id': 'Product ID',
                'product_name': 'Product Name',
                'opening_qty': 'Opening Qty',
                'qty': 'Current Qty',
                'Difference': 'Difference'
            })[['Product ID', 'Product Name', 'Opening Qty', 'Current Qty', 'Difference']]

            search_display_df.set_index('Product ID', inplace=True)

            st.dataframe(search_display_df, use_container_width=True)

            # 📥 Let user select the product
            product_options = search_results[['product_id', 'product_name']].apply(
                lambda row: f"{row['product_id']} - {row['product_name']}", axis=1
            ).tolist()

            selected_product_option = st.selectbox(
                "Select a Product to View Movement:",
                product_options
            )

            if selected_product_option:
                selected_product_id = int(selected_product_option.split(" - ")[0])  # Extract product_id

                # Fetch movements
                st.subheader("📈 Stock Movement for Selected Product")

                def get_product_movements(product_id):
                    try:
                        if not db.connection or not db.connection.is_connected():
                            db.connect()

                        cursor = db.connection.cursor(dictionary=True)
                        query = """
                            SELECT 
                                grn_id,
                                ordered_qty,
                                received_qty,
                                verified_qty,
                                created_at
                            FROM grn_items
                            WHERE product_id = %s
                            ORDER BY created_at DESC
                        """
                        cursor.execute(query, (product_id,))
                        results = cursor.fetchall()
                        return results

                    except Exception as e:
                        print(f"Error fetching product movements: {e}")
                        return []

                movement_data = get_product_movements(selected_product_id)

                if movement_data:
                    movement_df = pd.DataFrame(movement_data)
                    movement_df.rename(columns={
                        'grn_id': 'GRN Number',
                        'ordered_qty': 'Ordered Qty',
                        'received_qty': 'Received Qty',
                        'verified_qty': 'Verified Qty',
                        'created_at': 'Date'
                    }, inplace=True)

                    st.dataframe(movement_df, use_container_width=True)
                else:
                    st.info("ℹ️ No movement records found for this product yet.")


else:
    st.warning("⚠️ No stock data available.")






