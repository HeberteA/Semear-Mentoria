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
    st.markdown("<h2 style='color: #10B981;'>Dashboard Analitico Avancado</h2>", unsafe_allow_html=True)
    
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
        df_horario = get_data_safe(sh, "HORARIO")
    except Exception as e:
        st.error(f"Erro: {e}")
        return

    # PROCESSAMENTO DE DADOS

    # 1. QUESTOES (Diaria + Historico)
    total_semana = 0
    meta_semana = 0
    df_semana = pd.DataFrame()
    
    if not df_diaria.empty and 'Username' in df_diaria.columns:
        df_user_dia = df_diaria[df_diaria['Username'] == target_student].copy()
        cols_dias = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        for c in cols_dias:
            if c in df_user_dia.columns:
                df_user_dia[c] = pd.to_numeric(df_user_dia[c], errors='coerce').fillna(0)
            else:
                df_user_dia[c] = 0
        
        if 'Meta_Semanal' in df_user_dia.columns:
            df_user_dia['Meta_Semanal'] = pd.to_numeric(df_user_dia['Meta_Semanal'], errors='coerce').fillna(0)
            meta_semana = df_user_dia['Meta_Semanal'].sum()
            
        df_user_dia['Total_Atual'] = df_user_dia[cols_dias].sum(axis=1)
        total_semana = df_user_dia['Total_Atual'].sum()
        df_semana = df_user_dia

    total_historico = 0
    df_timeline = pd.DataFrame()
    df_hist_materia = pd.DataFrame()

    if not df_historico.empty and 'Username' in df_historico.columns:
        df_user_hist = df_historico[df_historico['Username'] == target_student].copy()
        if 'Qtd' in df_user_hist.columns:
            df_user_hist['Qtd'] = pd.to_numeric(df_user_hist['Qtd'], errors='coerce').fillna(0)
            total_historico = df_user_hist['Qtd'].sum()
            
            if 'Semana' in df_user_hist.columns:
                df_timeline = df_user_hist.groupby('Semana')['Qtd'].sum().reset_index()
            
            if 'Materia' in df_user_hist.columns:
                df_hist_materia = df_user_hist.groupby('Materia')['Qtd'].sum().reset_index()
                df_hist_materia.rename(columns={'Qtd': 'Total_Hist'}, inplace=True)

    df_cons = pd.DataFrame()
    if not df_semana.empty:
        temp_sem = df_semana[['Materia', 'Total_Atual']].copy()
        if not df_hist_materia.empty:
            df_cons = pd.merge(df_hist_materia, temp_sem, on='Materia', how='outer').fillna(0)
        else:
            df_cons = temp_sem
            df_cons['Total_Hist'] = 0
    elif not df_hist_materia.empty:
        df_cons = df_hist_materia
        df_cons['Total_Atual'] = 0
    
    if not df_cons.empty:
        if 'Total_Hist' not in df_cons.columns: df_cons['Total_Hist'] = 0
        if 'Total_Atual' not in df_cons.columns: df_cons['Total_Atual'] = 0
        df_cons['Total_Geral'] = df_cons['Total_Hist'] + df_cons['Total_Atual']
    
    total_geral_questoes = total_historico + total_semana

    df_sim_user = pd.DataFrame()
    media_geral_sim = 0
    if not df_simulados.empty and 'Username' in df_simulados.columns:
        df_sim_user = df_simulados[df_simulados['Username'] == target_student].copy()
        cols_notas = ['Nota_Linguagens', 'Nota_Humanas', 'Nota_Natureza', 'Nota_Matematica', 'Redacao', 'Total']
        for c in cols_notas:
            if c in df_sim_user.columns:
                df_sim_user[c] = pd.to_numeric(df_sim_user[c], errors='coerce').fillna(0)
        
        if 'Total' in df_sim_user.columns:
            media_geral_sim = df_sim_user['Total'].mean()

    df_red_user = pd.DataFrame()
    media_red = 0
    if not df_redacoes.empty and 'Username' in df_redacoes.columns:
        df_red_user = df_redacoes[df_redacoes['Username'] == target_student].copy()
        cols_c = ['C1', 'C2', 'C3', 'C4', 'C5', 'Nota_Final']
        for c in cols_c:
            if c in df_red_user.columns:
                df_red_user[c] = pd.to_numeric(df_red_user[c], errors='coerce').fillna(0)
        if 'Nota_Final' in df_red_user.columns:
            media_red = df_red_user['Nota_Final'].mean()

    df_cont_user = pd.DataFrame()
    taxa_acerto_global = 0
    cobertura_total = 0
    if not df_conteudos.empty and 'Username' in df_conteudos.columns:
        df_cont_user = df_conteudos[df_conteudos['Username'] == target_student].copy()
        if 'Qtd_Acertos' in df_cont_user.columns and 'Qtd_Exercicios' in df_cont_user.columns:
            df_cont_user['Qtd_Acertos'] = pd.to_numeric(df_cont_user['Qtd_Acertos'], errors='coerce').fillna(0)
            df_cont_user['Qtd_Exercicios'] = pd.to_numeric(df_cont_user['Qtd_Exercicios'], errors='coerce').fillna(0)
            
            soma_acertos = df_cont_user['Qtd_Acertos'].sum()
            soma_ex = df_cont_user['Qtd_Exercicios'].sum()
            if soma_ex > 0:
                taxa_acerto_global = (soma_acertos / soma_ex) * 100
        
        cobertura_total = len(df_cont_user)

    df_time = pd.DataFrame()
    if not df_horario.empty and 'Username' in df_horario.columns:
        df_h_user = df_horario[df_horario['Username'] == target_student].copy()
        days_h = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        all_slots = []
        for d in days_h:
            if d in df_h_user.columns:
                all_slots.extend(df_h_user[d].tolist())
        
        clean_slots = [x for x in all_slots if x and x.lower() not in ['livre', '', 'almoco', 'jantar', 'sono']]
        if clean_slots:
            df_time = pd.Series(clean_slots).value_counts().reset_index()
            df_time.columns = ['Materia', 'Qtd_Horas']

    c1, c2, c3, c4, c5 = st.columns(5)
    
    st.markdown("""
    <style>
        .kpi-card { background: rgba(6,78,59,0.4); border: 1px solid #10B981; border-radius: 8px; padding: 15px; text-align: center; }
        .kpi-val { font-size: 24px; font-weight: bold; color: #ECFDF5; }
        .kpi-lbl { font-size: 11px; text-transform: uppercase; color: #6EE7B7; }
    </style>
    """, unsafe_allow_html=True)

    with c1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>Total Questões</div><div class='kpi-val'>{int(total_geral_questoes)}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>Média Simulados</div><div class='kpi-val'>{media_geral_sim:.1f}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>Média Redação</div><div class='kpi-val'>{media_red:.0f}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>Taxa de Acerto</div><div class='kpi-val'>{taxa_acerto_global:.1f}%</div></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='kpi-card'><div class='kpi-lbl'>Tópicos Estudados</div><div class='kpi-val'>{cobertura_total}</div></div>", unsafe_allow_html=True)

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs(["Visao Geral & Produtividade", "Desempenho Academico", "Analise de Conteudos", "Cronograma"])

    with tab1:
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("### Evolucao Temporal de Questoes")
            if not df_timeline.empty or total_semana > 0:
                df_atual_agg = pd.DataFrame({'Semana': ['Atual'], 'Qtd': [total_semana]})
                df_final_time = pd.concat([df_timeline, df_atual_agg], ignore_index=True)
                
                fig_area = px.area(df_final_time, x='Semana', y='Qtd', markers=True, text='Qtd', color_discrete_sequence=['#10B981'])
                fig_area.update_traces(textposition="top center")
                fig_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_area, use_container_width=True)
            else:
                st.info("Sem dados temporais.")

        with c_right:
            st.markdown("### Meta vs Realizado (Semana)")
            if not df_semana.empty:
                categories = df_semana['Materia'].tolist()
                realizado = df_semana['Total_Atual'].tolist()
                metas = df_semana['Meta_Semanal'].tolist()
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=realizado, theta=categories, fill='toself', name='Realizado', line_color='#10B981'))
                fig_radar.add_trace(go.Scatterpolar(r=metas, theta=categories, fill='toself', name='Meta', line_color='#6EE7B7', opacity=0.3))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', margin=dict(t=20, b=20, l=30, r=30))
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Sem dados semanais.")

        st.markdown("### Volume Total Acumulado por Materia")
        if not df_cons.empty:
            df_cons = df_cons.sort_values('Total_Geral', ascending=False)
            fig_bar = px.bar(df_cons, x='Materia', y='Total_Geral', text_auto=True, color='Total_Geral', color_continuous_scale='Greens')
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', coloraxis_showscale=False, yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        col_sim, col_red = st.columns(2)
        
        with col_sim:
            st.markdown("### Historico de Simulados (Notas por Area)")
            if not df_sim_user.empty:
                df_areas = df_sim_user[['Nome_Simulado', 'Nota_Linguagens', 'Nota_Humanas', 'Nota_Natureza', 'Nota_Matematica']].copy()
                df_melt = df_areas.melt(id_vars=['Nome_Simulado'], var_name='Area', value_name='Nota')
                
                fig_line = px.line(df_melt, x='Nome_Simulado', y='Nota', color='Area', markers=True, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_line, use_container_width=True)
                
                st.markdown("#### Volatilidade das Notas (Boxplot)")
                fig_box = px.box(df_melt, x='Area', y='Nota', color='Area', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_box.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("Sem dados de simulados.")

        with col_red:
            st.markdown("### Evolucao da Redacao")
            if not df_red_user.empty:
                fig_red_line = px.line(df_red_user, y='Nota_Final', markers=True, text='Nota_Final', color_discrete_sequence=['#F472B6'])
                fig_red_line.update_traces(textposition="top center")
                fig_red_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', xaxis_title="Redacoes", yaxis_title="Nota")
                st.plotly_chart(fig_red_line, use_container_width=True)
                
                st.markdown("#### Matriz de Competencias")
                cols_comps = ['C1', 'C2', 'C3', 'C4', 'C5']
                valid_comps = [c for c in cols_comps if c in df_red_user.columns]
                if valid_comps:
                    df_heat = df_red_user[valid_comps].reset_index(drop=True)
                    fig_heat = px.imshow(df_heat.T, color_continuous_scale='RdPu', aspect='auto', text_auto=True)
                    fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5')
                    st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Sem dados de redacao.")

    with tab3:
        c_tree, c_acc = st.columns([2, 1])
        
        with c_tree:
            st.markdown("### Mapa de Conteudos Estudados")
            if not df_cont_user.empty:
                df_grp = df_cont_user.groupby('Materia').size().reset_index(name='Qtd')
                fig_tree = px.treemap(df_grp, path=['Materia'], values='Qtd', color='Qtd', color_continuous_scale='Mint')
                fig_tree.update_traces(textinfo="label+value")
                fig_tree.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', margin=dict(t=0, l=0, r=0, b=0))
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("Sem conteudos registrados.")
        
        with c_acc:
            st.markdown("### Eficiencia por Materia")
            if not df_cont_user.empty and 'Qtd_Acertos' in df_cont_user.columns:
                df_eff = df_cont_user.groupby('Materia')[['Qtd_Acertos', 'Qtd_Exercicios']].sum().reset_index()
                df_eff = df_eff[df_eff['Qtd_Exercicios'] > 0]
                df_eff['Taxa'] = (df_eff['Qtd_Acertos'] / df_eff['Qtd_Exercicios'] * 100).round(1)
                
                fig_eff = px.bar(df_eff, x='Taxa', y='Materia', orientation='h', text='Taxa', color='Taxa', color_continuous_scale='RdYlGn')
                fig_eff.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_eff, use_container_width=True)
            else:
                st.info("Sem dados de exercicios.")

    with tab4:
        st.markdown("### Alocacao de Tempo Planejado (Horario)")
        if not df_time.empty:
            c_pie, c_bar_time = st.columns(2)
            with c_pie:
                fig_pie = px.pie(df_time, values='Qtd_Horas', names='Materia', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c_bar_time:
                fig_bar_h = px.bar(df_time.sort_values('Qtd_Horas'), x='Qtd_Horas', y='Materia', orientation='h', text='Qtd_Horas', color_discrete_sequence=['#10B981'])
                fig_bar_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ECFDF5', yaxis_title=None, xaxis_title="Horas Semanais")
                st.plotly_chart(fig_bar_h, use_container_width=True)
        else:
            st.info("Horario nao preenchido ou sem materias definidas.")
