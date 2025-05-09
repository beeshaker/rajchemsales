import streamlit as st
from conn import DatabaseConnection
import streamlit as st
from menu import menu   

# DB connection
db = DatabaseConnection()
db.connect()


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # Redirect to login page
    st.stop()  # Stop further execution


if st.session_state["authenticated"]:
    menu()


# Fetch pending approvals
pending_orders = db.fetch_pending_orders()
pending_count = len(pending_orders)

#st.image("logo.png", width=300) 
st.markdown("## 📊 Dashboard")


# Proper role check
role = st.session_state.get("role", "")

# Example counts from your database
accounts_pending = db.count_pending_approvals_for_accounts()
director_pending = db.count_pending_approvals_for_director()
loading_pending = db.count_pending_for_loading()

# Shared card-rendering function
def approval_card(title, count, color, target_page, button_key):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style='
                background-color: #1f2937;
                padding: 1.5rem;
                border-radius: 1rem;
                box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
                border-left: 6px solid {color};
                margin-bottom: 1.5rem;
            '>
                <h4 style='margin-bottom: 0.5rem; color: {color};'>{title}</h4>
                <p style='font-size: 2rem; font-weight: bold; color: white;'>{count}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        btn_style = f"""
            <style>
            div[data-testid="stButton"] > button#{button_key} {{
                background-color: {color};
                color: black;
                font-weight: bold;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                border: none;
                margin-top: 1.2rem;
            }}
            </style>
        """
        st.markdown(btn_style, unsafe_allow_html=True)
        if st.button("View", key=button_key):
            st.switch_page(target_page)


# Display cards based on role
if role in ["admin", "accounts", "director"]:
    approval_card("💰 Pending Accounts Approvals", accounts_pending, "#facc15", "pages/4_Accounts_Approval.py", "acc_card")

if role in ["admin", "director"]:
    approval_card("✔️ Pending Director Approvals", director_pending, "#38bdf8", "pages/5_Sales_Order_Approval.py", "dir_card")

if role in ["admin", "loading", "director"]:
    approval_card("🚚 Orders Pending Loading", loading_pending, "#34d399", "pages/6_Loading_pages.py", "load_card")
