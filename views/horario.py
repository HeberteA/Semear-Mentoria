import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def init_schedule_if_needed(df, username, worksheet):
    has_user = False
    if not df.empty and 'Username' in df.columns:
        if username in df['Username'].values:
            has_user = True
            
    if not has_user:
        hours = [f"{h:02d}:00" for h in range(5, 24)] + ["00:00:00"]
        data_to_append = []
        for h in hours:
            row_data = [username, h] + ['Livre'] * 7
            data_to_append.append(row_data)
        
        try:
            worksheet.append_rows(data_to_append)
            st.success(f"Horario base criado para {username}!")
            sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao inicializar: {e}")

def render_schedule_html(df_user):
    days = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
    
    html = """
    <style>
        .planner-grid {
            display: grid;
            grid-template-columns: 50px repeat(7, 1fr);
            gap: 4px;
            margin-top: 15px;
            font-family: 'Poppins', sans-serif;
        }
        .header-cell {
            background: rgba(6, 78, 59, 0.8);
            color: #10B981;
            padding: 8px;
            text-align: center;
            font-weight: 600;
            font-size: 12px;
            border-radius: 6px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .time-cell {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6EE7B7;
            font-size: 10px;
            font-weight: bold;
        }
        .slot-cell {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            padding: 4px;
            font-size: 11px;
            color: #A7F3D0;
            text-align: center;
            min-height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .slot-cell:hover {
            border-color: #10B981;
            background: rgba(16, 185, 129, 0.1);
        }
        .slot-filled {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #ECFDF5;
            font-weight: 500;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
        }
        .slot-free {
            opacity: 0.5;
            font-style: italic;
            font-size: 10px;
        }
    </style>
    <div class="planner-grid">
        <div class="header-cell" style="background:transparent; border:none;"></div>
        <div class="header-cell">SEG</div>
        <div class="header-cell">TER</div>
        <div class="header-cell">QUA</div>
        <div class="header-cell">QUI</div>
        <div class="header-cell">SEX</div>
        <div class="header-cell">SAB</div>
        <div class="header-cell">DOM</div>
    """
    
    for index, row in df_user.iterrows():
        time_str = str(row.get('Hora', ''))[:5]
        html += f'<div class="time-cell">{time_str}</div>'
        
        for day in days:
            materia = row.get(day, "")
            is_filled = materia != "Livre" and materia != ""
            css_class = "slot-filled" if is_filled else "slot-free"
            display_text = materia if materia else "Livre"
            
            html += f'<div class="slot-cell {css_class}">{display_text}</div>'
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Planejamento Semanal</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state['target_student']
    if not target_student:
        st.warning("Selecione um aluno.")
        return
    
    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("HORARIO")
        raw_data = worksheet.get_all_values()
        
        days_cols = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        cols = ['Username', 'Hora'] + days_cols
        
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
        st.error(f"Erro ao conectar: {e}")
        return
    
    init_schedule_if_needed(df, target_student, worksheet)
    
    raw_data = worksheet.get_all_values()
    headers = [h.strip() for h in raw_data[0]]
    df = pd.DataFrame(raw_data[1:], columns=headers)
    
    df_user = df[df['Username'] == target_student].copy()
    if not df_user.empty:
        df_user['Hora_Sort'] = pd.to_datetime(df_user['Hora'], format='%H:%M:%S', errors='coerce')
        df_user = df_user.sort_values('Hora_Sort')
    

    tab_visual, tab_edit = st.tabs(["Visualizar Planner", "Editar Grade"])
    
    with tab_visual:
        if not df_user.empty:
            render_schedule_html(df_user)
        else:
            st.info("Nenhum horario preenchido.")
            
    with tab_edit:
        st.markdown("### Edicao Rapida")
        st.info("Edite os campos diretamente na tabela abaixo e clique em Salvar.")
        
        df_editor = df_user.drop(columns=['Hora_Sort'], errors='ignore') if not df_user.empty else pd.DataFrame(columns=cols)
        
        edited_df = st.data_editor(
            df_editor,
            column_config={
                "Username": None, 
                "Hora": st.column_config.TextColumn("Horario", disabled=True, width="small"),
                "Segunda": st.column_config.SelectboxColumn("Seg", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Terca": st.column_config.SelectboxColumn("Ter", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Quarta": st.column_config.SelectboxColumn("Qua", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Quinta": st.column_config.SelectboxColumn("Qui", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Sexta": st.column_config.SelectboxColumn("Sex", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Sabado": st.column_config.SelectboxColumn("Sab", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
                "Domingo": st.column_config.SelectboxColumn("Dom", options=["Livre", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Filosofia", "Sociologia", "Portugues", "Literatura", "Redacao", "Ingles", "Espanhol", "Simulado", "Revisao", "Exercicios"], required=True),
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )
        
        if st.button("Salvar Grade", use_container_width=True):
            try:
                all_values = worksheet.get_all_values()
                headers = [h.strip() for h in all_values[0]]
                
                col_indices = {name: i for i, name in enumerate(headers)}
                
                cells_to_update = []
                
                for idx, row in edited_df.iterrows():
                    hora = row['Hora']
                    
                    row_idx_sheet = -1
                    for i, s_row in enumerate(all_values):
                        if i == 0: continue
                        if len(s_row) > col_indices['Hora']:
                            if s_row[col_indices['Username']] == target_student and s_row[col_indices['Hora']] == hora:
                                row_idx_sheet = i + 1
                                break
                    
                    if row_idx_sheet != -1:
                        for day in days_cols:
                            new_val = row[day]
                            col_idx = col_indices[day] + 1
                            cells_to_update.append(gspread.Cell(row_idx_sheet, col_idx, new_val))
                
                if cells_to_update:
                    worksheet.update_cells(cells_to_update)
                    st.success("Horario atualizado com sucesso!")
                    sleep(1)
                    st.rerun()
                else:
                    st.warning("Nenhuma alteracao.")
                    
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")