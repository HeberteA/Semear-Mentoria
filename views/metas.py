import streamlit as st
import pandas as pd
import gspread
from time import sleep
from google.oauth2.service_account import Credentials

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Minhas Metas</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state.get('target_student')
    
    if not target_student:
        st.warning("Selecione um aluno no menu lateral para visualizar ou adicionar metas.")
        return
    
    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("METAS")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    with st.form("add_meta_form"):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            new_meta = st.text_input("Nova Meta / Objetivo", label_visibility="collapsed", placeholder="Digite sua nova meta aqui...")
        with col_btn:
            submitted = st.form_submit_button("Adicionar", use_container_width=True)
            
        if submitted and new_meta:
            try:
                worksheet.append_row([target_student, new_meta, "Pendente"])
                st.success("Meta adicionada!")
                sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    st.markdown("---")
    
    if df.empty:
        st.info("Nenhuma meta cadastrada.")
    else:
        if 'Username' in df.columns:
            df_user = df[df['Username'] == target_student].copy()
        else:
            df_user = pd.DataFrame()
        
        if df_user.empty:
            st.info("Nenhuma meta encontrada para este aluno.")
        else:
            all_records = worksheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if record.get('Username') == target_student:
                    row_num = i + 2 
                    desc = record['Descricao']
                    status = record['Status']
                    
                    if status == "Concluida":
                        card_bg = "rgba(6, 78, 59, 0.5)"
                        border_color = "#10B981"
                        text_style = "text-decoration: line-through; color: #6EE7B7;"
                        status_badge = "<span style='background-color: #10B981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px;'>CONCLUIDA</span>"
                    else:
                        card_bg = "rgba(31, 41, 55, 0.5)" 
                        border_color = "#F59E0B"
                        text_style = "color: #ECFDF5;"
                        status_badge = "<span style='background-color: #F59E0B; color: black; padding: 2px 8px; border-radius: 4px; font-size: 10px;'>PENDENTE</span>"

                    st.markdown(f"""
                    <div style="
                        background-color: {card_bg};
                        padding: 15px;
                        border-radius: 8px;
                        border-left: 4px solid {border_color};
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <div>
                            <div style="margin-bottom: 4px;">{status_badge}</div>
                            <span style="font-size: 16px; font-weight: 500; {text_style}">{desc}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        btn_label = "Reabrir" if status == "Concluida" else "Concluir"
                        if st.button(btn_label, key=f"done_{row_num}", use_container_width=True):
                            new_status = "Pendente" if status == "Concluida" else "Concluida"
                            worksheet.update_cell(row_num, 3, new_status)
                            sleep(0.5)
                            st.rerun()
                    with c2:
                        if st.button("Excluir", key=f"del_{row_num}", use_container_width=True):
                            worksheet.delete_rows(row_num)
                            sleep(0.5)
                            st.rerun()