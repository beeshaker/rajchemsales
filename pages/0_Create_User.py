import streamlit as st
import bcrypt
from conn import DatabaseConnection
from menu import menu

st.title("👤 Admin – Create New User")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()




db = DatabaseConnection()
db.connect()

with st.form("create_user_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["sales", "accounts", "director", "loading", "admin"])
    submitted = st.form_submit_button("Create User")

    if submitted:
        if username and password:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            try:
                cursor = db.connection.cursor()
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                               (username, hashed, role))
                db.connection.commit()
                st.success(f"✅ User '{username}' created successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Username and password required.")
