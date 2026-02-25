import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep
import plotly.express as px
from datetime import datetime

@st.cache_data(ttl=600)
def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def check_history_sheet(sh):
    try:
        return sh.worksheet("QUESTOES_HISTORICO")
    except:
        ws = sh.add_worksheet(title="QUESTOES_HISTORICO", rows="1000", cols="4")
        ws.append_row(["Username", "Semana", "Materia", "Qtd"])
        return ws

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
        st.success(f"Tabela inicializada para {username}")
        sleep(1)
        st.rerun()

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Controle de Questoes</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state.get('target_student')
    if not target_student:
        st.warning("Selecione um aluno para visualizar.")
        return

    try:
        sh = connect_to_sheets()
        ws_diario = sh.worksheet("QUESTOES_DIARIAS")
        ws_hist = check_history_sheet(sh)
        
        raw_data = ws_diario.get_all_values()
        cols = ['Username', 'Materia', 'Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        
        if not raw_data:
            ws_diario.append_row(cols)
            raw_data = [cols]
            
    except Exception as e:
        st.error(f"Erro de conexao com o Google Sheets: {e}")
        return

    tab_semanal, tab_historico = st.tabs(["Controle Semanal", "Historico Completo"])

    try:
        headers = [h.strip() for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        for c in cols:
            if c not in df.columns:
                df[c] = 0
        
        init_questoes_if_needed(df, target_student, ws_diario)
        
        raw_data = ws_diario.get_all_values()
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        df_user = df[df['Username'] == target_student].copy()
        numeric_cols = ['Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        for col in numeric_cols:
            df_user[col] = pd.to_numeric(df_user[col], errors='coerce').fillna(0).astype(int)
            
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return

    with tab_semanal:
        total_meta = df_user['Meta_Semanal'].sum()
        total_feito = df_user[['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']].sum().sum()
        
        progresso = (total_feito / total_meta) if total_meta > 0 else 0
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
                <span style="color: #A7F3D0; font-size: 14px;">Questoes na Semana</span>
                <h1 style="color: #10B981; margin: 0; font-size: 32px;">{total_feito} <span style="font-size:16px; color:#6EE7B7">/ {total_meta}</span></h1>
            </div>
            <div style="width: 200px; text-align: right;">
                 <span style="color: #6EE7B7; font-size: 12px; font-weight: bold;">{int(progresso*100)}% DA META</span>
                 <div style="background-color: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin-top: 5px;">
                    <div style="background-color: #10B981; width: {int(progresso*100)}%; height: 100%; border-radius: 10px;"></div>
                 </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Painel de Lancamentos")
        
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
                all_values = ws_diario.get_all_values()
                sheet_headers = [h.strip() for h in all_values[0]]
                col_indices = {name: i for i, name in enumerate(sheet_headers)}
                
                cells_to_update = []
                
                row_map = {}
                for i, r in enumerate(all_values):
                    if i == 0: continue
                    u = r[col_indices['Username']] if len(r) > col_indices['Username'] else ""
                    m = r[col_indices['Materia']] if len(r) > col_indices['Materia'] else ""
                    row_map[(u, m)] = i + 1

                for idx, row in edited_df.iterrows():
                    key = (target_student, row['Materia'])
                    row_idx = row_map.get(key)
                    
                    if row_idx:
                        cols_to_check = ['Meta_Semanal', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
                        for col_name in cols_to_check:
                            val_new = str(row[col_name])
                            col_idx = col_indices[col_name] + 1
                            cells_to_update.append(gspread.Cell(row_idx, col_idx, val_new))
                            
                if cells_to_update:
                    ws_diario.update_cells(cells_to_update)
                    st.success("Dados salvos com sucesso!")
                    sleep(1)
                    st.rerun()
                else:
                    st.warning("Nenhuma alteracao detectada.")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        
        st.markdown("---")
        
        st.markdown("### Grafico de Desempenho")
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
            st.info("Sem dados suficientes para gerar grafico.")
        
        st.markdown("---")
        if st.button("FECHAR SEMANA E ARQUIVAR", type="primary", use_container_width=True):
            try:
                week_label = datetime.now().strftime("Semana %d/%m/%Y")
                
                history_rows = []
                cells_to_reset = []
                
                all_values = ws_diario.get_all_values()
                sheet_headers = [h.strip() for h in all_values[0]]
                col_indices = {name: i for i, name in enumerate(sheet_headers)}
                
                row_map = {}
                for i, r in enumerate(all_values):
                    if i == 0: continue
                    u = r[col_indices['Username']] if len(r) > col_indices['Username'] else ""
                    m = r[col_indices['Materia']] if len(r) > col_indices['Materia'] else ""
                    row_map[(u, m)] = i + 1

                days_cols = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
                
                for idx, row in df_user.iterrows():
                    materia = row['Materia']
                    total_mat = row[days_cols].sum()
                    
                    if total_mat > 0:
                        history_rows.append([target_student, week_label, materia, int(total_mat)])
                    
                    row_idx = row_map.get((target_student, materia))
                    if row_idx:
                        for day in days_cols:
                            col_idx = col_indices[day] + 1
                            cells_to_reset.append(gspread.Cell(row_idx, col_idx, 0))
                
                if history_rows:
                    ws_hist.append_rows(history_rows)
                
                if cells_to_reset:
                    ws_diario.update_cells(cells_to_reset)
                    st.success("Semana encerrada! Historico salvo e dias zerados.")
                    sleep(1.5)
                    st.rerun()
                else:
                    st.warning("Nenhuma questao realizada para arquivar.")
                    
            except Exception as e:
                st.error(f"Erro ao finalizar semana: {e}")

    with tab_historico:
        try:
            hist_raw = ws_hist.get_all_values()
            
            if not hist_raw:
                st.info("A tabela de historico esta vazia.")
            else:
                headers_hist = hist_raw[0]
                if len(hist_raw) < 2:
                    st.info("Nenhum historico arquivado ainda.")
                else:
                    df_hist = pd.DataFrame(hist_raw[1:], columns=headers_hist)
                    
                    if 'Username' in df_hist.columns:
                        df_hist_user = df_hist[df_hist['Username'] == target_student].copy()
                        
                        if not df_hist_user.empty:
                            df_hist_user['Qtd'] = pd.to_numeric(df_hist_user['Qtd'], errors='coerce').fillna(0).astype(int)
                            
                            total_geral = df_hist_user['Qtd'].sum()
                            semanas_unicas = df_hist_user['Semana'].nunique()
                            media_semanal = int(total_geral / semanas_unicas) if semanas_unicas > 0 else 0
                            
                            semana_top = df_hist_user.groupby('Semana')['Qtd'].sum().sort_values(ascending=False)
                            melhor_semana_val = semana_top.values[0] if not semana_top.empty else 0
                            
                            materia_top = df_hist_user.groupby('Materia')['Qtd'].sum().sort_values(ascending=False)
                            materia_nome = materia_top.index[0] if not materia_top.empty else "-"
                            materia_val = materia_top.values[0] if not materia_top.empty else 0
                            
                            materias_ativas = df_hist_user['Materia'].nunique()
                            
                            st.markdown("""
                            <style>
                                .metric-card {
                                    background: rgba(6, 78, 59, 0.4);
                                    border: 1px solid rgba(16, 185, 129, 0.2);
                                    border-radius: 8px;
                                    padding: 15px;
                                    text-align: center;
                                }
                                .metric-title { color: #A7F3D0; font-size: 12px; margin-bottom: 5px; }
                                .metric-value { color: #10B981; font-size: 24px; font-weight: bold; }
                                .metric-sub { color: #6EE7B7; font-size: 10px; }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            c1, c2, c3, c4, c5 = st.columns(5)
                            
                            with c1:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-title">Total Acumulado</div>
                                    <div class="metric-value">{total_geral}</div>
                                    <div class="metric-sub">Questoes</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-title">Media Semanal</div>
                                    <div class="metric-value">{media_semanal}</div>
                                    <div class="metric-sub">Questoes/Semana</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c3:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-title">Melhor Semana</div>
                                    <div class="metric-value">{melhor_semana_val}</div>
                                    <div class="metric-sub">Recorde</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c4:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-title">Materia Top</div>
                                    <div class="metric-value">{materia_val}</div>
                                    <div class="metric-sub">{materia_nome}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c5:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-title">Materias Ativas</div>
                                    <div class="metric-value">{materias_ativas}</div>
                                    <div class="metric-sub">Disciplinas</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.write("")
                            st.markdown("### Evolucao por Semana")
                            fig_hist = px.bar(
                                df_hist_user,
                                x="Semana",
                                y="Qtd",
                                color="Materia",
                                barmode="group",
                                color_discrete_sequence=px.colors.qualitative.Pastel,
                                text_auto=True
                            )
                            fig_hist.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font_color='#ECFDF5',
                                xaxis_title=None,
                                yaxis_title=None,
                                legend_title=None
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                            with st.expander("Ver Tabela Detalhada"):
                                st.dataframe(df_hist_user[['Semana', 'Materia', 'Qtd']], use_container_width=True, hide_index=True)
                        else:
                            st.info(f"Nenhum registro encontrado no historico para {target_student}.")
                    else:
                        st.error("Erro: A planilha de historico nao tem a coluna Username.")
        except Exception as e:
            st.error(f"Erro ao carregar historico: {e}")
