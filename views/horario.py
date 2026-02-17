import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from time import sleep

def get_contrast_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return '#000000' if brightness > 128 else '#FFFFFF'
    except:
        return '#FFFFFF'

def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

def get_or_create_materias_config(sh, username):
    try:
        worksheet = sh.worksheet("MATERIAS")
    except:
        worksheet = sh.add_worksheet("MATERIAS", rows=100, cols=3)
        worksheet.append_row(["Username", "Materia", "Cor"])
    
    all_records = worksheet.get_all_records()
    df = pd.DataFrame(all_records)
    
    user_subjects = {}
    
    if not df.empty and 'Username' in df.columns:
        user_df = df[df['Username'] == username]
        for _, row in user_df.iterrows():
            user_subjects[row['Materia']] = row['Cor']
            
    return user_subjects, worksheet

def add_new_subject(worksheet, username, materia, cor):
    try:
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty and 'Username' in df.columns:
            exists = df[(df['Username'] == username) & (df['Materia'] == materia)]
            if not exists.empty:
                return False, "Materia ja existe"
        
        worksheet.append_row([username, materia, cor])
        return True, "Materia adicionada"
    except Exception as e:
        return False, str(e)

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
            st.success(f"Horario base criado para {username}")
            sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao inicializar: {e}")

def render_schedule_html(df_user, subject_colors):
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
            border-radius: 6px;
            padding: 4px;
            font-size: 11px;
            text-align: center;
            min-height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .slot-empty {
            background: rgba(255, 255, 255, 0.03);
            color: #A7F3D0;
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
            
            if is_filled:
                bg_color = subject_colors.get(materia, "rgba(16, 185, 129, 0.15)")
                
                text_color = "#ECFDF5"
                if bg_color.startswith("#"):
                    text_color = get_contrast_text_color(bg_color)
                
                style = f'background-color: {bg_color}; color: {text_color}; font-weight: 500; box-shadow: 0 0 5px {bg_color}40;'
                css_class = ""
            else:
                style = ""
                css_class = "slot-empty"
                
            display_text = materia if materia else "Livre"
            
            html += f'<div class="slot-cell {css_class}" style="{style}">{display_text}</div>'
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Planejamento Semanal</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state.get('target_student')
    if not target_student:
        st.warning("Selecione um aluno.")
        return
    
    is_mentor = st.session_state.get('role') == 'Mentor'
    
    try:
        sh = connect_to_sheets()
        
        ws_horario = sh.worksheet("HORARIO")
        raw_data = ws_horario.get_all_values()
        
        days_cols = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
        cols = ['Username', 'Hora'] + days_cols
        
        if not raw_data:
            df = pd.DataFrame(columns=cols)
            ws_horario.append_row(cols)
        else:
            headers = [h.strip() for h in raw_data[0]]
            df = pd.DataFrame(raw_data[1:], columns=headers)
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
        
        init_schedule_if_needed(df, target_student, ws_horario)
        
        raw_data = ws_horario.get_all_values()
        headers = [h.strip() for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        df_user = df[df['Username'] == target_student].copy()
        if not df_user.empty:
            df_user['Hora_Sort'] = pd.to_datetime(df_user['Hora'], format='%H:%M:%S', errors='coerce')
            df_user = df_user.sort_values('Hora_Sort')

        subject_colors, ws_materias = get_or_create_materias_config(sh, target_student)

    except Exception as e:
        st.error(f"Erro ao conectar ou processar dados: {e}")
        return

    tab_names = ["Visualizar Planner"]
    if is_mentor:
        tab_names.append("Editar Grade & Materias")
        
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        if not df_user.empty:
            render_schedule_html(df_user, subject_colors)
        else:
            st.info("Nenhum horario preenchido.")
            
    if is_mentor:
        with tabs[1]:
            with st.expander("Cadastrar Nova Materia / Cor", expanded=False):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    new_materia = st.text_input("Nome da Materia")
                with c2:
                    new_cor = st.color_picker("Cor da Etiqueta", "#10B981")
                with c3:
                    st.write("")
                    st.write("")
                    if st.button("Adicionar", use_container_width=True):
                        if new_materia:
                            success, msg = add_new_subject(ws_materias, target_student, new_materia, new_cor)
                            if success:
                                st.success(msg)
                                sleep(1)
                                st.rerun()
                            else:
                                st.warning(msg)
                        else:
                            st.warning("Digite um nome.")

                if subject_colors:
                    st.caption("Materias cadastradas: " + ", ".join([f"{k}" for k in subject_colors.keys()]))

            st.markdown("---")
            st.markdown("### Preencher Grade")
            st.info("Escreva o nome da materia ou copie e cole das cadastradas.")
            
            df_editor = df_user.drop(columns=['Hora_Sort'], errors='ignore') if not df_user.empty else pd.DataFrame(columns=cols)
            
            column_cfg = {
                "Username": None, 
                "Hora": st.column_config.TextColumn("Horario", disabled=True, width="small"),
            }
            
            for day in days_cols:
                column_cfg[day] = st.column_config.TextColumn(
                    day[:3],
                    width="medium"
                )

            edited_df = st.data_editor(
                df_editor,
                column_config=column_cfg,
                hide_index=True,
                use_container_width=True,
                height=600
            )
            
            if st.button("Salvar Grade", use_container_width=True):
                try:
                    all_values = ws_horario.get_all_values()
                    headers_sheet = [h.strip() for h in all_values[0]]
                    col_indices = {name: i for i, name in enumerate(headers_sheet)}
                    
                    cells_to_update = []
                    
                    sheet_map = {}
                    for i, row_val in enumerate(all_values):
                        if i == 0: continue
                        u = row_val[col_indices['Username']] if len(row_val) > col_indices['Username'] else ""
                        h = row_val[col_indices['Hora']] if len(row_val) > col_indices['Hora'] else ""
                        sheet_map[(u, h)] = i + 1
                    
                    for idx, row in edited_df.iterrows():
                        hora = row['Hora']
                        sheet_row_idx = sheet_map.get((target_student, hora))
                        
                        if sheet_row_idx:
                            for day in days_cols:
                                new_val = row[day]
                                col_idx = col_indices[day] + 1
                                cells_to_update.append(gspread.Cell(sheet_row_idx, col_idx, new_val))
                    
                    if cells_to_update:
                        ws_horario.update_cells(cells_to_update)
                        st.success("Horario atualizado com sucesso!")
                        sleep(1)
                        st.rerun()
                    else:
                        st.warning("Nenhuma alteracao detectada.")
                        
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
