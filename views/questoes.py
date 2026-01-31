import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep
import plotly.express as px
from datetime import datetime

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def init_questoes_if_needed(df, username, worksheet):
    has_user = False
    if not df.empty and 'Username' in df.columns:
        if username in df['Username'].values:
            has_user = True
            
    if not has_user:
        materias_base = [
            "Matematica", "Fisica", "Quimica", "Biologia", 
            "Historia", "Geografia", "Filosofia", "Sociologia",
            "Portugues", "Literatura", "Ingles", "Espanhol"
        ]
        
        data_to_append = []
        for mat in materias_base:
            row = [username, mat, 0, 0, 0, 0, 0, 0, 0, 0]
            data_to_append.append(row)
            
        worksheet.append_rows(data_to_append)
        st.success("Tabela de questoes inicializada!")
        sleep(1)
        st.rerun()

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Controle de Questoes</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state['target_student']
    if not target_student:
        st.warning("Selecione um aluno.")
        return

    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("QUESTOES_DIARIAS")
        
        raw_data = worksheet.get_all_values()
        
        cols = ['Username', 'Materia', 'Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        
        if not raw_data:
            df = pd.DataFrame(columns=cols)
            worksheet.append_row(cols)
        else:
            headers = [h.strip() for h in raw_data[0]]
            df = pd.DataFrame(raw_data[1:], columns=headers)
            
            for c in cols:
                if c not in df.columns:
                    df[c] = 0

    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return

    init_questoes_if_needed(df, target_student, worksheet)
    
    raw_data = worksheet.get_all_values()
    headers = [h.strip() for h in raw_data[0]]
    df = pd.DataFrame(raw_data[1:], columns=headers)
    
    df_user = df[df['Username'] == target_student].copy()
    
    numeric_cols = ['Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
    for col in numeric_cols:
        df_user[col] = pd.to_numeric(df_user[col], errors='coerce').fillna(0).astype(int)

    total_meta = df_user['Meta_Semanal'].sum()
    total_feito = df_user[['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']].sum().sum()
    
    progresso = 0
    if total_meta > 0:
        progresso = (total_feito / total_meta)
        if progresso > 1: progresso = 1.0
    
    st.markdown(f"""
    <div style="
        background: rgba(6, 78, 59, 0.4);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <span style="color: #A7F3D0; font-size: 14px;">Total na Semana</span>
            <h1 style="color: #10B981; margin: 0; font-size: 36px;">{total_feito} <span style="font-size:16px; color:#6EE7B7">/ {total_meta}</span></h1>
        </div>
        <div style="width: 200px; text-align: right;">
             <span style="color: #6EE7B7; font-size: 12px; font-weight: bold;">{int(progresso*100)}% DA META</span>
             <div style="background-color: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin-top: 5px;">
                <div style="background-color: #10B981; width: {int(progresso*100)}%; height: 100%; border-radius: 10px;"></div>
             </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Painel de Controle")
    st.info("Edite os valores diretamente na tabela abaixo.")
    
    edited_df = st.data_editor(
        df_user,
        column_config={
            "Username": None,
            "Materia": st.column_config.TextColumn("Materia", disabled=True, width="medium"),
            "Meta_Semanal": st.column_config.NumberColumn("Meta", min_value=0, format="%d"),
            "Segunda": st.column_config.NumberColumn("Seg", min_value=0, width="small"),
            "Terca": st.column_config.NumberColumn("Ter", min_value=0, width="small"),
            "Quarta": st.column_config.NumberColumn("Qua", min_value=0, width="small"),
            "Quinta": st.column_config.NumberColumn("Qui", min_value=0, width="small"),
            "Sexta": st.column_config.NumberColumn("Sex", min_value=0, width="small"),
            "Sabado": st.column_config.NumberColumn("Sab", min_value=0, width="small"),
            "Domingo": st.column_config.NumberColumn("Dom", min_value=0, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    if st.button("Salvar Alteracoes", use_container_width=True):
        try:
            all_values = worksheet.get_all_values()
            headers = [h.strip() for h in all_values[0]]
            
            col_indices = {name: i for i, name in enumerate(headers)}
            
            cells_to_update = []
            
            for idx, row in edited_df.iterrows():
                materia = row['Materia']
                
                row_index_sheet = -1
                
                for i, sheet_row in enumerate(all_values):
                    if i == 0: continue
                    if len(sheet_row) > col_indices['Materia']:
                        if sheet_row[col_indices['Username']] == target_student and sheet_row[col_indices['Materia']] == materia:
                            row_index_sheet = i + 1
                            break
                
                if row_index_sheet != -1:
                    cols_to_check = ['Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
                    
                    for col_name in cols_to_check:
                        val_new = str(row[col_name])
                        col_idx = col_indices[col_name] + 1
                        
                        cells_to_update.append(gspread.Cell(row_index_sheet, col_idx, val_new))
            if cells_to_update:
                worksheet.update_cells(cells_to_update)
                st.success("Dados salvos com sucesso!")
                sleep(1)
                st.rerun()
            else:
                st.warning("Nenhuma alteracao detectada.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
    st.markdown("---")
    
    st.markdown("### Desempenho Atual")
    df_chart = df_user.copy()
    df_chart['Total_Realizado'] = df_chart[['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']].sum(axis=1)
    
    df_chart = df_chart[ (df_chart['Total_Realizado'] > 0) | (df_chart['Meta_Semanal'] > 0) ]
    
    if not df_chart.empty:
        df_melt = df_chart.melt(id_vars=['Materia'], value_vars=['Total_Realizado', 'Meta_Semanal'], var_name='Tipo', value_name='Qtd')
        
        fig = px.bar(
            df_melt, 
            x='Materia', 
            y='Qtd', 
            color='Tipo', 
            barmode='group',
            color_discrete_map={'Total_Realizado': '#10B981', 'Meta_Semanal': '#064E3B'},
            text_auto=True
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ECFDF5',
            xaxis_title=None,
            yaxis_title=None,
            legend_title=None,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para grafico.")
    
    if st.button("FINALIZAR SEMANA", use_container_width=True):
        try:
            ws_hist = sh.worksheet("QUESTOES_HISTORICO")
            
            week_label = datetime.now().strftime("Semana %d/%m/%Y")
            
            history_rows = []
            cells_to_reset = []
            
            all_values = worksheet.get_all_values()
            headers = [h.strip() for h in all_values[0]]
            col_indices = {name: i for i, name in enumerate(headers)}
            
            days_cols = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
            
            for idx, row in df_user.iterrows():
                materia = row['Materia']
                total_mat = row[['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']].sum()
                
                if total_mat > 0:
                    history_rows.append([target_student, week_label, materia, int(total_mat)])
                
                row_index_sheet = -1
                for i, sheet_row in enumerate(all_values):
                    if i == 0: continue
                    if len(sheet_row) > col_indices['Materia']:
                        if sheet_row[col_indices['Username']] == target_student and sheet_row[col_indices['Materia']] == materia:
                            row_index_sheet = i + 1
                            break
                
                if row_index_sheet != -1:
                    for day in days_cols:
                        col_idx = col_indices[day] + 1
                        cells_to_reset.append(gspread.Cell(row_index_sheet, col_idx, 0))
            
            if history_rows:
                ws_hist.append_rows(history_rows)
            
            if cells_to_reset:
                worksheet.update_cells(cells_to_reset)
                st.success("Semana encerrada! Historico salvo e dias zerados.")
                sleep(1.5)
                st.rerun()
            else:
                st.warning("Nenhum dado para salvar.")
                
        except Exception as e:
            st.error(f"Erro ao finalizar semana: {e}")