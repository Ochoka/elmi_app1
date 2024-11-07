# Import needed libraries
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Page configuration
st.set_page_config(page_title="Data Handling", page_icon=":bar_chart:",
                   layout="wide")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.login()
except Exception as e:
    st.sidebar.error(e)

if st.session_state['authentication_status']:
    # Use Streamlit's markdown feature to insert HTML with inline CSS
    st.html(
        """
    <style>
    [data-testid="stSidebarContent"] {
        color: Black;
        background-color: #03fcf8;
    }

    [data-testid="stMain"] {
        color: #002A6C;
        background-color: #cce7e8;
    }

    </style>
    """
    )
    st.sidebar.write(f'Welcome **{st.session_state["name"]}**')
    # set title
    st.title("Download, Format and Edit Data")


    authenticator.logout("Logout", "sidebar")
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
