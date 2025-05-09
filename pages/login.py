import streamlit as st
from conn import DatabaseConnection


db = DatabaseConnection()

st.set_page_config(page_title="Login", page_icon="🔐")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", use_container_width=True)
st.title("Order Management - Login")


username = st.text_input("Username")
password = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    user = db.authenticate_user(username, password)
    if user:
        st.session_state["authenticated"] = True
        st.session_state["username"] = user["username"]
        st.session_state["role"] = user["role"]
        st.success(f"✅ Welcome, {user['username']}!")
        st.switch_page("main.py")
    else:
        st.error("❌ Invalid username or password")