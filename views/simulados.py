import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from main import fetch_sheet_data, connect_to_sheets

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Controle de Simulados</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state.get('target_student')
    if not target_student:
        st.warning("Selecione um aluno no menu lateral.")
        return

    if 'edit_sim_idx' not in st.session_state:
        st.session_state['edit_sim_idx'] = -1
    if 'edit_sim_data' not in st.session_state:
        st.session_state['edit_sim_data'] = {}

    try:
        sh = fetch_sheet_data()
        worksheet = sh.worksheet("SIMULADOS")
        
        raw_data = worksheet.get_all_values()
        cols = ['Username', 'Nome_Simulado', 'Data', 'Linguagens', 'Humanas', 'Natureza', 'Matematica', 'Redacao', 'Total']
        
        if not raw_data:
            df = pd.DataFrame(columns=cols)
            worksheet.append_row(cols)
        else:
            headers = [h.strip() for h in raw_data[0]]
            df = pd.DataFrame(raw_data[1:], columns=headers)
            
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
                    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    df['original_idx'] = df.index
    df_user = df[df['Username'] == target_student].copy()

    with st.expander("Lançar Novo Simulado / Editar", expanded=True):
        is_edit = st.session_state['edit_sim_idx'] != -1
        form_title = "Editar Simulado" if is_edit else "Novo Simulado"
        st.markdown(f"#### {form_title}")
        
        edit_data = st.session_state['edit_sim_data']
        
        with st.form("simulado_form"):
            c_nome, c_date = st.columns([2, 1])
            
            nome_val = edit_data.get('Nome_Simulado', '')
            c_nome.text_input("Nome do Simulado", value=nome_val, key="input_nome")
            
            date_val = "today"
            raw_date = edit_data.get('Data', '')
            
            if is_edit and raw_date:
                try:
                    date_val = pd.to_datetime(raw_date, dayfirst=True).date()
                except:
                    date_val = "today"
            
            data_sim = c_date.date_input("Data de Realização", value=date_val)
            
            st.markdown("<small style='color:#A7F3D0'>Acertos por Area</small>", unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            
            def safe_num(key):
                val = edit_data.get(key, 0)
                try: return float(val)
                except: return 0.0

            ling = c1.number_input("Linguagens", min_value=0, max_value=45, value=int(safe_num('Linguagens')))
            hum = c2.number_input("Humanas", min_value=0, max_value=45, value=int(safe_num('Humanas')))
            nat = c3.number_input("Natureza", min_value=0, max_value=45, value=int(safe_num('Natureza')))
            mat = c4.number_input("Matematica", min_value=0, max_value=45, value=int(safe_num('Matematica')))
            red = c5.number_input("Redacao", min_value=0, max_value=1000, value=int(safe_num('Redacao')))
            
            submit_label = "Atualizar Simulado" if is_edit else "Salvar Simulado"
            submitted = st.form_submit_button(submit_label, use_container_width=True)
            
            if submitted:
                total_acertos = ling + hum + nat + mat
                data_str = data_sim.strftime("%d/%m/%Y")
                
                try:
                    all_values = worksheet.get_all_values()
                    
                    if is_edit:
                        target_row_idx = -1
                        old_name = edit_data.get('Nome_Simulado')
                        
                        header = all_values[0]
                        idx_user = header.index('Username')
                        idx_nome = header.index('Nome_Simulado')
                        
                        for i, row in enumerate(all_values):
                            if i == 0: continue
                            if row[idx_user] == target_student and row[idx_nome] == old_name:
                                target_row_idx = i + 1
                                break
                        
                        if target_row_idx != -1:
                            worksheet.update_row(target_row_idx, [target_student, st.session_state.input_nome, data_str, ling, hum, nat, mat, red, total_acertos])
                            st.success("Simulado atualizado!")
                        else:
                            st.error("Erro ao encontrar o registro original.")
                            
                    else:
                        new_row = [target_student, st.session_state.input_nome, data_str, ling, hum, nat, mat, red, total_acertos]
                        worksheet.append_row(new_row)
                        st.success("Simulado salvo!")
                    
                    st.session_state['edit_sim_idx'] = -1
                    st.session_state['edit_sim_data'] = {}
                    sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    if is_edit:
        if st.button("Cancelar Edição"):
            st.session_state['edit_sim_idx'] = -1
            st.session_state['edit_sim_data'] = {}
            st.rerun()

    st.markdown("---")

    col_list, col_chart = st.columns([1, 1])
    
    with col_list:
        st.markdown("### Histórico")
        if df_user.empty:
            st.info("Nenhum simulado cadastrado.")
        else:
            df_user['Data_Sort'] = pd.to_datetime(df_user['Data'], dayfirst=True, errors='coerce')
            df_user = df_user.sort_values(by='Data_Sort', ascending=False)
            
            for index, row in df_user.iterrows():
                st.markdown(f"""
                <div style="
                    background: rgba(6, 95, 70, 0.4);
                    backdrop-filter: blur(5px);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <h4 style="color: #ECFDF5; margin:0; font-size:16px;">{row['Nome_Simulado']}</h4>
                        <span style="color: #A7F3D0; font-size:12px;">{row['Data']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 20px; font-weight: bold; color: #10B981;">{row['Total']}</span>
                        <span style="font-size: 10px; color: #6EE7B7; margin-right: 8px;">Acertos</span>
                        <span style="font-size: 20px; font-weight: bold; color: #10B981;">{row['Redacao']}</span>
                        <span style="font-size: 10px; color: #6EE7B7;">Redação</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    if st.button("Editar", key=f"ed_{index}", use_container_width=True):
                        st.session_state['edit_sim_idx'] = index
                        st.session_state['edit_sim_data'] = row.to_dict()
                        st.rerun()
                with c2:
                    if st.button("Excluir", key=f"del_{index}", use_container_width=True):
                        try:
                            all_vals = worksheet.get_all_values()
                            header = all_vals[0]
                            idx_u = header.index('Username')
                            idx_n = header.index('Nome_Simulado')
                            
                            row_del = -1
                            for i, r in enumerate(all_vals):
                                if r[idx_u] == target_student and r[idx_n] == row['Nome_Simulado']:
                                    row_del = i + 1
                                    break
                            
                            if row_del != -1:
                                worksheet.delete_rows(row_del)
                                st.success("Excluido!")
                                sleep(0.5)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

    with col_chart:
        st.markdown("### Evolução")
        if not df_user.empty:
            df_chart = df_user.sort_values(by='Data_Sort')
            
            df_chart['Total'] = pd.to_numeric(df_chart['Total'], errors='coerce')
            df_chart['Redacao'] = pd.to_numeric(df_chart['Redacao'], errors='coerce')

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=df_chart['Data'], y=df_chart['Total'], name="Total Acertos", 
                          text=df_chart['Total'], textposition="top center", line=dict(color='#10B981', width=4), mode='lines+markers+text')
            )

            fig.add_trace(
                go.Scatter(x=df_chart['Data'], y=df_chart['Redacao'], name="Redação", text=df_chart['Redacao'], textposition="top center",
                          line=dict(color='#6EE7B7', width=3, dash='dot'), mode='lines+markers+text')
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ECFDF5',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Pontos / Acertos"),
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            last_sim = df_chart.iloc[-1]
            areas = {'Linguagens': last_sim['Linguagens'], 'Humanas': last_sim['Humanas'], 
                     'Natureza': last_sim['Natureza'], 'Matematica': last_sim['Matematica']}
            
            areas_clean = {}
            for k, v in areas.items():
                try: areas_clean[k] = float(v)
                except: areas_clean[k] = 0
            
            df_area = pd.DataFrame(list(areas_clean.items()), columns=['Area', 'Acertos'])
            
            fig2 = px.bar(df_area, x='Area', y='Acertos', color='Acertos', color_continuous_scale='greens')
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ECFDF5',
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            fig2.update_traces(text=df_area['Acertos'], textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados para gerar graficos.")
