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
    st.markdown("<h2 style='color: #10B981;'>Minhas Redações</h2>", unsafe_allow_html=True)
    
    if 'edit_redacao_idx' not in st.session_state:
        st.session_state['edit_redacao_idx'] = -1
    if 'edit_redacao_data' not in st.session_state:
        st.session_state['edit_redacao_data'] = {}

    username = st.session_state['username']
    
    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("REDACOES")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not df.empty:
        df['original_idx'] = df.index
        df_user = df[df['Username'] == username].copy()
    else:
        df_user = pd.DataFrame()

    with st.expander("Gerenciar Redação (Adicionar / Editar)", expanded=True):
        is_edit = st.session_state['edit_redacao_idx'] != -1
        form_title = "Editar Redação" if is_edit else "Nova Redação"
        st.markdown(f"#### {form_title}")
        
        edit_data = st.session_state['edit_redacao_data']
        
        with st.form("redacao_form"):
            tema = st.text_input("Tema da Redação", value=edit_data.get('Tema', ''))
            
            st.markdown("Insira as notas por competência:")
            c1_col, c2_col, c3_col, c4_col, c5_col = st.columns(5)
            
            val_c1 = int(edit_data.get('C1', 0))
            val_c2 = int(edit_data.get('C2', 0))
            val_c3 = int(edit_data.get('C3', 0))
            val_c4 = int(edit_data.get('C4', 0))
            val_c5 = int(edit_data.get('C5', 0))
            
            c1 = c1_col.number_input("Comp. 1", min_value=0, max_value=200, step=20, value=val_c1)
            c2 = c2_col.number_input("Comp. 2", min_value=0, max_value=200, step=20, value=val_c2)
            c3 = c3_col.number_input("Comp. 3", min_value=0, max_value=200, step=20, value=val_c3)
            c4 = c4_col.number_input("Comp. 4", min_value=0, max_value=200, step=20, value=val_c4)
            c5 = c5_col.number_input("Comp. 5", min_value=0, max_value=200, step=20, value=val_c5)
            
            submit_label = "Atualizar Redação" if is_edit else "Salvar Redação"
            submitted = st.form_submit_button(submit_label, use_container_width=True)
            
            if submitted:
                nota_final = c1 + c2 + c3 + c4 + c5
                
                if is_edit:
                    row_idx = st.session_state['edit_redacao_idx']
                    worksheet.update_cell(row_idx + 2, 2, tema)
                    worksheet.update_cell(row_idx + 2, 3, c1)
                    worksheet.update_cell(row_idx + 2, 4, c2)
                    worksheet.update_cell(row_idx + 2, 5, c3)
                    worksheet.update_cell(row_idx + 2, 6, c4)
                    worksheet.update_cell(row_idx + 2, 7, c5)
                    worksheet.update_cell(row_idx + 2, 8, nota_final)
                    
                    st.success("Redação atualizada!")
                    st.session_state['edit_redacao_idx'] = -1
                    st.session_state['edit_redacao_data'] = {}
                else:
                    new_row = [username, tema, c1, c2, c3, c4, c5, nota_final]
                    worksheet.append_row(new_row)
                    st.success("Redação salva!")
                
                sleep(1)
                st.rerun()

    if is_edit:
        if st.button("Cancelar Edição"):
            st.session_state['edit_redacao_idx'] = -1
            st.session_state['edit_redacao_data'] = {}
            st.rerun()

    st.markdown("---")

    if df_user.empty:
        st.info("Nenhuma redação cadastrada.")
    else:
        for index, row in df_user.iterrows():
            original_idx = row['original_idx']
            
            st.markdown(f"""
            <div style="background-color: #064E3B; padding: 20px; border-radius: 12px; border-left: 5px solid #10B981; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="color: #ECFDF5; margin: 0; font-size: 1.1rem;">{row['Tema']}</h3>
                    <div style="background-color: #10B981; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                        {row['Nota_Final']}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; text-align: center;">
                    <div style="background-color: rgba(6, 95, 70, 0.5); padding: 5px; border-radius: 5px;">
                        <span style="font-size: 0.7rem; color: #A7F3D0;">C1</span><br>
                        <span style="color: white; font-weight: bold;">{row['C1']}</span>
                    </div>
                    <div style="background-color: rgba(6, 95, 70, 0.5); padding: 5px; border-radius: 5px;">
                        <span style="font-size: 0.7rem; color: #A7F3D0;">C2</span><br>
                        <span style="color: white; font-weight: bold;">{row['C2']}</span>
                    </div>
                    <div style="background-color: rgba(6, 95, 70, 0.5); padding: 5px; border-radius: 5px;">
                        <span style="font-size: 0.7rem; color: #A7F3D0;">C3</span><br>
                        <span style="color: white; font-weight: bold;">{row['C3']}</span>
                    </div>
                    <div style="background-color: rgba(6, 95, 70, 0.5); padding: 5px; border-radius: 5px;">
                        <span style="font-size: 0.7rem; color: #A7F3D0;">C4</span><br>
                        <span style="color: white; font-weight: bold;">{row['C4']}</span>
                    </div>
                    <div style="background-color: rgba(6, 95, 70, 0.5); padding: 5px; border-radius: 5px;">
                        <span style="font-size: 0.7rem; color: #A7F3D0;">C5</span><br>
                        <span style="color: white; font-weight: bold;">{row['C5']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_edit, c_del = st.columns([3, 1])
            with c_edit:
                if st.button("Editar", key=f"edit_red_{original_idx}", use_container_width=True):
                    st.session_state['edit_redacao_idx'] = original_idx
                    st.session_state['edit_redacao_data'] = row.to_dict()
                    st.rerun()
            with c_del:
                if st.button("Excluir", key=f"del_red_{original_idx}", use_container_width=True):
                    try:
                        worksheet.delete_rows(int(original_idx) + 2)
                        st.success("Excluído!")
                        sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
