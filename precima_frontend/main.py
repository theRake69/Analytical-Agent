import streamlit as st

st.set_page_config(page_title="Precima Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

no_sidebar_style = """
<style>
    div[data-testid="stSidebarNav"] {display: none;}
</style>
"""

radio_button_style = """
<style>
    div[data-testid="stRadio"] label {
    font-size: 18px;
    font-weight: bold;
    margin-right: 20px;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] div[aria-checked="true"] {
    text-decoration: underline;
    }
</style>
"""

style = no_sidebar_style + radio_button_style

st.markdown(style, unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Navigation Bar
selected_page = st.radio("", ["Home 🏠","FAQ 📖"], horizontal=True)

# Update session state when selection changes
if selected_page == "Home 🏠":
    try:
        st.session_state.page = "Home"
    except Exception as e:
        print("Error in Home", e)
elif selected_page == "FAQ 📖":
    st.session_state.page = "FAQ"

# Load the selected page
if st.session_state.page == "Home":
    from pages.Home import show_home
    st.write("Loading Home Page..")
    try:
        st.write("Home page function")
        show_home()
    except Exception as e:
        st.warning("Error in Home", e)
elif st.session_state.page == "FAQ":
    from pages.FAQ import show_faq
    show_faq()
