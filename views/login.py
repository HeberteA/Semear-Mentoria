import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

st.markdown("""
<style>
     /* Logo Area */
    .sidebar-logo-container {
        text-align: center;
        padding: 5px 0;
        margin-bottom: 20px;
    }
    .sidebar-logo-text {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2rem;
        color: white;
        letter-spacing: 2px;
    }
    .sidebar-logo-sub {
        font-size: 1rem;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 3px;
    }
</style>
""", unsafe_allow_html=True)           

def load_view():
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        c1, c2, c3 = st.columns([1, 5, 1])
        with c2:
            st.image("logo.png")

        st.markdown("""
            <div class="sidebar-logo-container">
                <div class="sidebar-logo-text">SEMEAR</div>
                <div class="sidebar-logo-sub">Mentoria</div>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar", use_container_width=True)

            if submit_button:
                try:
                    sh = connect_to_sheets()
                    worksheet = sh.worksheet("LOGIN")
                    data = worksheet.get_all_records()
                    df = pd.DataFrame(data)
                    
                    user_match = df[(df['Username'] == username) & (df['Senha'].astype(str) == password)]
                    
                    if not user_match.empty:
                        user_data = user_match.iloc[0]
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user_data['Username']
                        st.session_state['name'] = user_data['Nome']
                        st.session_state['role'] = user_data['Tipo']
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")
                
                except Exception as e:
                    st.error(f"Erro ao conectar: {e}")
