import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep

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
    st.markdown("<h2 style='color: #10B981;'>Controle de Revisoes</h2>", unsafe_allow_html=True)
    
    if 'edit_rev_idx' not in st.session_state:
        st.session_state['edit_rev_idx'] = -1
    if 'edit_rev_data' not in st.session_state:
        st.session_state['edit_rev_data'] = {}

    target_student = st.session_state['target_student']
    if not target_student:
        st.warning("Selecione um aluno no menu lateral.")
        return

    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("REVISOES")
        
        data = worksheet.get_all_records()
        
        expected_cols = ['Username', 'Data', 'Tipo_Revisao', 'Materia', 'Qtd_Questoes']
        
        if not data:
            df = pd.DataFrame(columns=expected_cols)
        else:
            df = pd.DataFrame(data)
            
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                for c in missing:
                    df[c] = ""

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    df['original_idx'] = df.index
    
    if 'Username' in df.columns:
        df_user = df[df['Username'] == target_student].copy()
    else:
        df_user = pd.DataFrame(columns=expected_cols + ['original_idx'])

    

    with st.expander("Lancar Nova Revisao / Editar", expanded=True):
        is_edit = st.session_state['edit_rev_idx'] != -1
        form_title = "Editar Lancamento" if is_edit else "Nova Revisao"
        st.markdown(f"#### {form_title}")
        
        edit_data = st.session_state['edit_rev_data']
        
        with st.form("revisao_form"):
            col1, col2 = st.columns(2)
            
            materias = [
                "Matematica", "Fisica", "Quimica", "Biologia", 
                "Historia", "Geografia", "Filosofia", "Sociologia",
                "Portugues", "Literatura", "Ingles", "Espanhol"
            ]
            tipos = ["Semanal", "Quinzenal", "Mensal", "Trimestral"]
            
            cur_mat_idx = 0
            if is_edit and edit_data.get('Materia') in materias:
                cur_mat_idx = materias.index(edit_data.get('Materia'))
                
            cur_tipo_idx = 0
            if is_edit and edit_data.get('Tipo_Revisao') in tipos:
                cur_tipo_idx = tipos.index(edit_data.get('Tipo_Revisao'))

            materia = col1.selectbox("Materia", materias, index=cur_mat_idx)
            tipo = col2.selectbox("Tipo de Revisao", tipos, index=cur_tipo_idx)
            
            col3, col4 = st.columns(2)
            date_val = "today"
            date = edit_data.get('Data', '')
            
            if is_edit and date:
                try:
                    date_val = pd.to_datetime(date, dayfirst=True).date()
                except:
                    date_val = "today"
            data_rev = col3.date_input("Data", value=date_val)
            
            val_qtd = 10
            if is_edit and str(edit_data.get('Qtd_Questoes', '')).isdigit():
                val_qtd = int(edit_data.get('Qtd_Questoes'))
                
            qtd = col4.number_input("Qtd. Questoes", min_value=1, value=val_qtd)
            
            submit_label = "Atualizar" if is_edit else "Salvar"
            submitted = st.form_submit_button(submit_label, use_container_width=True)
            
            if submitted:
                if is_edit:
                    row_idx = st.session_state['edit_rev_idx']
                    worksheet.update_cell(row_idx + 2, 2, data_rev)
                    worksheet.update_cell(row_idx + 2, 3, tipo)
                    worksheet.update_cell(row_idx + 2, 4, materia)
                    worksheet.update_cell(row_idx + 2, 5, qtd)
                    st.success("Atualizado com sucesso!")
                    st.session_state['edit_rev_idx'] = -1
                    st.session_state['edit_rev_data'] = {}
                else:
                    new_row = [target_student, data_rev, tipo, materia, qtd]
                    worksheet.append_row(new_row)
                    st.success("Salvo com sucesso!")
                
                sleep(0.5)
                st.rerun()

    if is_edit:
        if st.button("Cancelar Edicao"):
            st.session_state['edit_rev_idx'] = -1
            st.session_state['edit_rev_data'] = {}
            st.rerun()

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Semanal", "Quinzenal", "Mensal", "Trimestral"])
    
    tabs_map = {
        "Semanal": tab1,
        "Quinzenal": tab2,
        "Mensal": tab3,
        "Trimestral": tab4
    }
    
    for tipo_nome, tab_obj in tabs_map.items():
        with tab_obj:
            if not df_user.empty and 'Tipo_Revisao' in df_user.columns:
                filtered_df = df_user[df_user['Tipo_Revisao'] == tipo_nome]
            else:
                filtered_df = pd.DataFrame()

            if filtered_df.empty:
                st.info(f"Nenhuma revisao {tipo_nome} registrada para {target_student}.")
            else:
                for index, row in filtered_df.iterrows():
                    original_idx = row['original_idx']
                    
                    st.markdown(f"""
                    <div style="
                        background: rgba(6, 95, 70, 0.4);
                        backdrop-filter: blur(5px);
                        padding: 15px;
                        border-radius: 12px;
                        border: 1px solid rgba(16, 185, 129, 0.2);
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    ">
                        <div>
                            <h4 style="color: #ECFDF5; margin: 0; font-size: 16px;">{row['Materia']}</h4>
                            <span style="color: #A7F3D0; font-size: 12px;">Data: {row['Data']}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 22px; font-weight: bold; color: #10B981; text-shadow: 0 0 10px rgba(16,185,129,0.3);">{row['Qtd_Questoes']}</span>
                            <br><span style="font-size: 10px; color: #6EE7B7; text-transform: uppercase;">Questoes</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        if st.button("Editar", key=f"ed_{original_idx}", use_container_width=True):
                            st.session_state['edit_rev_idx'] = original_idx
                            st.session_state['edit_rev_data'] = row.to_dict()
                            st.rerun()
                    with c2:
                        if st.button("Excluir", key=f"del_{original_idx}", use_container_width=True):
                            try:
                                worksheet.delete_rows(int(original_idx) + 2)
                                st.success("Excluido!")
                                sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
