import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

def get_data(sheet_name):
    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Dashboard de Desempenho</h2>", unsafe_allow_html=True)
    
    role = st.session_state['role']
    username = st.session_state['username']
    
    df_simulados = get_data("SIMULADOS")
    df_redacoes = get_data("REDACOES")
    df_questoes = get_data("QUESTOES_HISTORICO")
    
    target_student = username
    
    if role == 'Mentor':
        all_students = df_simulados['Username'].unique().tolist() if not df_simulados.empty else []
        
        st.markdown("### Visão Geral da Turma")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        if not df_simulados.empty:
            avg_geral = df_simulados['Total'].mean()
            col_m1.metric("Média Geral da Turma (Simulados)", f"{avg_geral:.1f}")
        
        if not df_questoes.empty:
            total_q_turma = df_questoes['Qtd'].sum()
            col_m2.metric("Total de Questões da Turma", f"{total_q_turma}")
            
        st.markdown("---")
        target_student = st.selectbox("Selecione o Aluno para Análise Detalhada", all_students)
    
    if target_student:
        student_simulados = df_simulados[df_simulados['Username'] == target_student].copy() if not df_simulados.empty else pd.DataFrame()
        student_redacoes = df_redacoes[df_redacoes['Username'] == target_student].copy() if not df_redacoes.empty else pd.DataFrame()
        student_questoes = df_questoes[df_questoes['Username'] == target_student].copy() if not df_questoes.empty else pd.DataFrame()
        
        col1, col2, col3 = st.columns(3)
        
        if not student_simulados.empty:
            last_simulado = student_simulados.iloc[-1]
            col1.metric("Último Simulado", f"{last_simulado['Total']}", delta=f"{last_simulado['Nome_Simulado']}")
            
            fig_simulados = px.line(student_simulados, x='Data', y='Total', markers=True, title="Evolução Notas Simulados")
            fig_simulados.update_traces(line_color='#10B981', line_width=4)
            fig_simulados.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5')
            col1.plotly_chart(fig_simulados, use_container_width=True)
        else:
            col1.info("Sem dados de simulados.")

        if not student_redacoes.empty:
            last_redacao = student_redacoes.iloc[-1]
            media_red = student_redacoes['Nota_Final'].mean()
            col2.metric("Média Redação", f"{media_red:.1f}", delta=f"Última: {last_redacao['Nota_Final']}")
            
            categories = ['C1', 'C2', 'C3', 'C4', 'C5']
            values = [last_redacao[c] for c in categories]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=last_redacao['Tema'],
                line_color='#10B981',
                fillcolor='rgba(16, 185, 129, 0.4)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 200])),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#ECFDF5',
                title="Competências (Última Redação)"
            )
            col2.plotly_chart(fig_radar, use_container_width=True)
        else:
            col2.info("Sem dados de redação.")

        if not student_questoes.empty:
            total_questoes = student_questoes['Total_Feito'].sum()
            col3.metric("Questões Resolvidas (Total)", f"{total_questoes}")
            
            fig_bar = px.bar(student_questoes, x='Materia', y='Total_Feito', title="Questões por Matéria", color_discrete_sequence=['#10B981'])
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5')
            col3.plotly_chart(fig_bar, use_container_width=True)
        else:
            col3.info("Sem histórico de questões.")
