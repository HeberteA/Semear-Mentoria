import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def get_data_safe(sh, worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        headers = [h.strip() for h in data[0]]
        return pd.DataFrame(data[1:], columns=headers)
    except:
        return pd.DataFrame()

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Dashboard Geral</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state.get('target_student')
    if not target_student:
        st.warning("Selecione um aluno.")
        return

    try:
        sh = connect_to_sheets()
        df_diaria = get_data_safe(sh, "QUESTOES_DIARIAS")
        df_historico = get_data_safe(sh, "QUESTOES_HISTORICO")
        df_simulados = get_data_safe(sh, "SIMULADOS")
        df_redacoes = get_data_safe(sh, "REDACOES")
        df_conteudos = get_data_safe(sh, "CONTEUDOS")
    except Exception as e:
        st.error(f"Erro: {e}")
        return

    total_semana_atual = 0
    meta_semana_atual = 0
    df_semana_chart = pd.DataFrame()

    if not df_diaria.empty and 'Username' in df_diaria.columns:
        df_user_dia = df_diaria[df_diaria['Username'] == target_student].copy()
        
        cols_dias = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        for col in cols_dias:
            if col in df_user_dia.columns:
                df_user_dia[col] = pd.to_numeric(df_user_dia[col], errors='coerce').fillna(0)
            else:
                df_user_dia[col] = 0
                
        if 'Meta_Semanal' in df_user_dia.columns:
            df_user_dia['Meta_Semanal'] = pd.to_numeric(df_user_dia['Meta_Semanal'], errors='coerce').fillna(0)
            meta_semana_atual = df_user_dia['Meta_Semanal'].sum()

        df_user_dia['Total_Atual'] = df_user_dia[cols_dias].sum(axis=1)
        total_semana_atual = df_user_dia['Total_Atual'].sum()
        df_semana_chart = df_user_dia

    total_historico = 0
    df_timeline = pd.DataFrame()
    df_heatmap_data = pd.DataFrame()

    if not df_historico.empty and 'Username' in df_historico.columns:
        df_user_hist = df_historico[df_historico['Username'] == target_student].copy()
        if 'Qtd' in df_user_hist.columns:
            df_user_hist['Qtd'] = pd.to_numeric(df_user_hist['Qtd'], errors='coerce').fillna(0)
            total_historico = df_user_hist['Qtd'].sum()
            
            if 'Semana' in df_user_hist.columns:
                df_timeline = df_user_hist.groupby('Semana')['Qtd'].sum().reset_index()

    total_geral = total_historico + total_semana_atual

    df_sim_user = pd.DataFrame()
    media_simulados = 0
    if not df_simulados.empty and 'Username' in df_simulados.columns:
        df_sim_user = df_simulados[df_simulados['Username'] == target_student].copy()
        cols_areas = ['Nota_Linguagens', 'Nota_Humanas', 'Nota_Natureza', 'Nota_Matematica', 'Acertos']
        for c in cols_areas:
            if c in df_sim_user.columns:
                df_sim_user[c] = pd.to_numeric(df_sim_user[c], errors='coerce').fillna(0)
        
        if 'Acertos' in df_sim_user.columns:
            media_simulados = df_sim_user['Acertos'].mean()

    df_red_user = pd.DataFrame()
    media_redacao = 0
    if not df_redacoes.empty and 'Username' in df_redacoes.columns:
        df_red_user = df_redacoes[df_redacoes['Username'] == target_student].copy()
        cols_comp = ['Competencia1', 'Competencia2', 'Competencia3', 'Competencia4', 'Competencia5', 'Nota']
        for c in cols_comp:
            if c in df_red_user.columns:
                df_red_user[c] = pd.to_numeric(df_red_user[c], errors='coerce').fillna(0)
        
        if 'Nota' in df_red_user.columns:
            media_redacao = df_red_user['Nota'].mean()

    conteudos_estudados = 0
    df_cont_user = pd.DataFrame()
    if not df_conteudos.empty and 'Username' in df_conteudos.columns:
        df_cont_user = df_conteudos[df_conteudos['Username'] == target_student].copy()
        conteudos_estudados = len(df_cont_user)

    st.markdown("""
    <style>
        .kpi-box {
            background-color: rgba(6, 78, 59, 0.4);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .kpi-val { color: #10B981; font-size: 28px; font-weight: bold; }
        .kpi-lbl { color: #A7F3D0; font-size: 12px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"<div class='kpi-box'><div class='kpi-lbl'>Total Questões</div><div class='kpi-val'>{int(total_geral)}</div></div>", unsafe_allow_html=True)
    with c2:
        perc = (total_semana_atual / meta_semana_atual * 100) if meta_semana_atual > 0 else 0
        st.markdown(f"<div class='kpi-box'><div class='kpi-lbl'>Meta Semanal</div><div class='kpi-val'>{int(perc)}%</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-box'><div class='kpi-lbl'>Média Simulados</div><div class='kpi-val'>{media_simulados:.1f}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi-box'><div class='kpi-lbl'>Média Redação</div><div class='kpi-val'>{media_redacao:.0f}</div></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='kpi-box'><div class='kpi-lbl'>Conteúdos Vistos</div><div class='kpi-val'>{conteudos_estudados}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    col_evo, col_radar = st.columns([2, 1])

    with col_evo:
        st.markdown("### Evolução de Questões")
        if not df_timeline.empty or total_semana_atual > 0:
            df_atual_agg = pd.DataFrame({'Semana': ['Atual'], 'Qtd': [total_semana_atual]})
            df_final = pd.concat([df_timeline, df_atual_agg], ignore_index=True)
            
            fig = px.area(df_final, x='Semana', y='Qtd', markers=True, color_discrete_sequence=['#10B981'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados suficientes.")

    with col_radar:
        st.markdown("### Meta vs Realizado")
        if not df_semana_chart.empty:
            categories = df_semana_chart['Materia'].tolist()
            realizado = df_semana_chart['Total_Atual'].tolist()
            metas = df_semana_chart['Meta_Semanal'].tolist()

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=realizado, theta=categories, fill='toself', name='Feito', line_color='#10B981'))
            fig.add_trace(go.Scatterpolar(r=metas, theta=categories, fill='toself', name='Meta', line_color='#6EE7B7', opacity=0.3))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', margin=dict(t=20, b=20, l=40, r=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados semanais.")

    st.markdown("---")
    
    c_sim, c_red = st.columns(2)

    with c_sim:
        st.markdown("### Evolução por Área (Simulados)")
        if not df_sim_user.empty:
            df_areas = df_sim_user[['Simulado', 'Nota_Linguagens', 'Nota_Humanas', 'Nota_Natureza', 'Nota_Matematica']].copy()
            if not df_areas.empty:
                df_melted = df_areas.melt(id_vars=['Simulado'], var_name='Area', value_name='Nota')
                fig_areas = px.line(df_melted, x='Simulado', y='Nota', color='Area', markers=True, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_areas.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_areas, use_container_width=True)
            else:
                st.info("Colunas de notas não encontradas.")
        else:
            st.info("Sem dados de simulados.")

    with c_red:
        st.markdown("### Competências da Redação")
        if not df_red_user.empty:
            cols_c = ['Competencia1', 'Competencia2', 'Competencia3', 'Competencia4', 'Competencia5']
            medias_comp = df_red_user[cols_c].mean().tolist()
            nomes_comp = ['C1', 'C2', 'C3', 'C4', 'C5']
            
            fig_red = go.Figure()
            fig_red.add_trace(go.Scatterpolar(r=medias_comp, theta=nomes_comp, fill='toself', line_color='#F472B6'))
            fig_red.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 200])), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', margin=dict(t=20, b=20))
            st.plotly_chart(fig_red, use_container_width=True)
        else:
            st.info("Sem dados de redação.")

    st.markdown("---")
    
    c_heat, c_tree = st.columns([1, 2])

    with c_heat:
        st.markdown("### Produtividade Semanal")
        if not df_semana_chart.empty:
            dias = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
            valores = df_semana_chart[dias].sum().tolist()
            
            fig_bar = px.bar(x=dias, y=valores, color=valores, color_continuous_scale='Greens')
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', yaxis_title=None, xaxis_title=None, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sem dados semanais.")

    with c_tree:
        st.markdown("### Distribuição de Conteúdos")
        if not df_cont_user.empty:
            df_tree = df_cont_user.groupby('Materia').size().reset_index(name='Qtd')
            fig_tree = px.treemap(df_tree, path=['Materia'], values='Qtd', color='Qtd', color_continuous_scale='Mint')
            fig_tree.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Sem conteúdos registrados.")
