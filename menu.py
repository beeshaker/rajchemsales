import streamlit as st

def menu():
    #st.sidebar.image("logo.png", width=200) 

    # Check for login
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("🔐 Please log in to continue.")
        st.stop()

    username = st.session_state["username"]
    role = st.session_state["role"]

    st.sidebar.markdown(f"👤 **User:** `{username}`")
    #st.sidebar.markdown(f"🔑 **Role:** `{role.capitalize()}`")
    st.sidebar.divider()
    

    # Define role-based access to pages
    pages_by_role = {
        "admin": [
            ("main.py", "🏠 Dashboard"),            
            ("pages/1_Create_Sales_Order.py", "📝 Create Sales Order"),
            ("pages/2_Pending_Approvals.py", "🕓 Pending Approvals"),
            ("pages/3_Add_Products.py", "📦 Add Products"),
            ("pages/4_Accounts_Approval.py", "💰 Accounts Approval"),
            ("pages/5_Sales_Order_Approval.py", "✔️ Director Approval"),
            ("pages/6_Loading_pages.py", "🚚 Loading Status"),
            ("pages/7_Loading_History.py", "📜 Loading History"),
            ("pages/8_Grn_module.py", "📤 GRN"),
            ("pages/9_Grn_history.py", "🗃️  GRN History"),
            ("pages/10_Stock_level.py", "📊 Stocks"),
            ("pages/11_Stock_ledger.py", "📋 Movement Ledger"),
            ("pages/12_Create_Customer.py", "➕ Create Customer"),
            ("pages/13_Reports.py", "📈 Reports"),
            ("pages/14_Stock_Adjustments.py", "🔧 Stock Adjustments"),
            ("pages/0_Create_User.py", "🧑‍💼 Create User")
        ],
        "accounts": [
            ("main.py", "🏠 Dashboard"),
            ("pages/2_Pending_Approvals.py", "🕓 Pending Approvals"),
            ("pages/3_Add_Products.py", "📦 Add Products"),
            ("pages/4_Accounts_Approval.py", "💰 Accounts Approval"),
            ("pages/8_Grn_module.py", "📤 GRN"),
            ("pages/9_Grn_history.py", "🗃️  GRN History"),
            ("pages/10_Stock_level.py", "📊 Stocks"),
            ("pages/11_Stock_ledger.py", "📋 Movement Ledger")
        ],
        "sales": [
            ("main.py", "🏠 Dashboard"),
            ("pages/1_Create_Sales_Order.py", "📝 Create Sales Order"),
            ("pages/12_Create_Customer.py", "➕ Create Customer"),
            ("pages/13_Reports.py", "📈 Reports")
        ],
        "director": [
            ("main.py", "🏠 Dashboard"),
            ("pages/2_Pending_Approvals.py", "🕓 Pending Approvals"),
            ("pages/5_Sales_Order_Approval.py", "✔️ Director Approval"),
            ("pages/8_Grn_module.py", "📤 GRN"),
            ("pages/14_Stock_Adjustments.py", "🔧 Stock Adjustments"),
            ("pages/13_Reports.py", "📈 Reports")
        ],
        "loading": [
            ("main.py", "🏠 Dashboard"),
            ("pages/6_Loading_pages.py", "🚚 Loading Status"),
            ("pages/7_Loading_History.py", "📜 Loading History"),
            ("pages/8_Grn_module.py", "🗃️  GRN")
        ],
    }
    
    
    for path, label in pages_by_role[role]:
        st.sidebar.page_link(path, label=label)

    st.sidebar.divider()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.switch_page("pages/login.py")