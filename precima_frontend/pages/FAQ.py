import streamlit as st

def show_faq():
    # Set page Title
    st.title("📌 Frequently Asked Question")

    with st.expander("❓ What is Precima Agent?"):
        st.write("Precima Agent is a MySQL-based AI assistant that helps generate SQL queries based on natural language inputs.")

    with st.expander("🔹 How do I use this app?"):
        st.write("Simply enter a query in the text box and click **Execute**. The app will generate an SQL query and fetch the corresponding results.")

    with st.expander("💾 What databases doest it support?"):
        st.write("Currently, Precima Agent supports only **MySQL**. Future updates may include support for other databases.")

    with st.expander("⚠️ Why am I seeing errors?"):
        st.write("""
        - Ensure your database is running and properly configured.
        - It's using a Large Language Model behind the scene. So performace and accuracy is dependedent on it.
        """)

    with st.expander("🐞 How do I report a bug ?"):
        st.write("If you encounter any issues, please reach out to our development team.")