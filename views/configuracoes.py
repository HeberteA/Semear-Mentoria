import streamlit as st
import pandas as pd
import gspread
from time import sleep
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=600)
def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")
def load_view():
    st.markdown("<h2 style='color: #10B981;'>Configurações Administrativas</h2>", unsafe_allow_html=True)
    
    if st.session_state['role'] != 'Mentor':
        st.error("Acesso negado. Apenas mentores podem acessar esta área.")
        return

    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("LOGIN")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    st.markdown("### Cadastrar Novo Aluno")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        new_name = col1.text_input("Nome Completo")
        new_user = col2.text_input("Username (Login)")
        
        col3, col4 = st.columns(2)
        new_pass = col3.text_input("Senha Provisória", type="password")
        user_type = col4.selectbox("Tipo de Acesso", ["Aluno", "Mentor"])
        
        submitted = st.form_submit_button("Cadastrar Usuário", use_container_width=True)
        
        if submitted:
            if new_user in df['Username'].values:
                st.error("Erro: Username já existe.")
            elif not new_user or not new_pass or not new_name:
                st.error("Erro: Preencha todos os campos.")
            else:
                try:
                    worksheet.append_row([new_user, new_pass, new_name, user_type])
                    st.success(f"Usuário {new_name} cadastrado com sucesso!")
                    sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.markdown("### Usuários Ativos")

    if not df.empty:
        for index, row in df.iterrows():
            if row['Username'] == st.session_state['username']:
                continue
                
            st.markdown(f"""
            <div style="
                background-color: #064E3B;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #10B981;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <strong style="color: #ECFDF5; font-size: 16px;">{row['Nome']}</strong>
                    <br>
                    <span style="color: #6EE7B7; font-size: 12px;">User: {row['Username']} | Tipo: {row['Tipo']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Remover Acesso", key=f"del_user_{index}", use_container_width=True):
                try:
                    worksheet.delete_rows(index + 2)
                    st.success("Usuário removido.")
                    sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
    else:
        st.info("Nenhum outro usuário cadastrado.")
