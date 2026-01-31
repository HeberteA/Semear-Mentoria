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

def init_conteudos_if_needed(df, username, worksheet):
    has_user = False
    if not df.empty and 'Username' in df.columns:
        if username in df['Username'].values:
            has_user = True
            
    if not has_user:
        template_df = df[df['Username'] == ""]
        
        if not template_df.empty:
            new_data = template_df.copy()
            new_data['Username'] = username
            
            values_to_append = new_data.values.tolist()
            
            worksheet.append_rows(values_to_append)
            st.success("Trilha de conteudos inicializada!")
            sleep(1)
            st.rerun()

def load_view():
    st.markdown("<h2 style='color: #10B981;'>Conteudos e Aulas</h2>", unsafe_allow_html=True)
    
    target_student = st.session_state['target_student']
    if not target_student:
        st.warning("Selecione um aluno.")
        return

    try:
        sh = connect_to_sheets()
        worksheet = sh.worksheet("CONTEUDOS")
        
        raw_data = worksheet.get_all_values()
        
        if not raw_data:
            st.error("A planilha CONTEUDOS esta vazia.")
            return
            
        headers = [h.strip() for h in raw_data[0]]
        rows = raw_data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return

    init_conteudos_if_needed(df, target_student, worksheet)
    
    raw_data = worksheet.get_all_values()
    headers = [h.strip() for h in raw_data[0]]
    df = pd.DataFrame(raw_data[1:], columns=headers)
    
    df_user = df[df['Username'] == target_student].copy()
    
    if df_user.empty:
        st.info("Nenhum conteudo encontrado para este aluno.")
        return

    c_filter1, c_filter2, c_filter3 = st.columns(3)
    
    materias = sorted(df_user['Materia'].unique().tolist())
    if not materias:
        st.warning("Sem materias cadastradas.")
        return
        
    selected_materia = c_filter1.selectbox("Materia", materias)
    
    df_materia = df_user[df_user['Materia'] == selected_materia]
    frentes = sorted(df_materia['Frente'].unique().tolist())
    
    selected_frente = c_filter2.selectbox("Frente", frentes)
    
    df_frente = df_materia[df_materia['Frente'] == selected_frente]
    partes = sorted(df_frente['Parte'].unique().tolist())
    
    selected_parte = c_filter3.selectbox("Parte", partes)
    
    df_filtered = df_frente[df_frente['Parte'] == selected_parte].copy()
    
    st.markdown("---")
    
    with st.form("conteudos_form"):
        st.markdown(f"<div style='margin-bottom:20px; color:#A7F3D0'>Editando: <b>{selected_materia}</b> | <b>{selected_frente}</b> | <b>{selected_parte}</b></div>", unsafe_allow_html=True)
        
        updates = {} 
        col_map = {name: i + 1 for i, name in enumerate(headers)}
        
        for index, row in df_filtered.iterrows():
            row_id = int(index) + 2

            def safe_int(key_name):
                val = row.get(key_name, '')
                val_str = str(val).strip()
                if val_str.isdigit():
                    return int(val_str)
                return 0
            
            imp_val = row.get('Importancia', 'Baixa')
            if imp_val not in ["Baixa", "Média", "Alta"]:
                imp_val = "Baixa"

            imp_icons = {
                "Alta": "🔴",
                "Média": "🟡",
                "Baixa": "🟢"
            }
            icon = imp_icons.get(imp_val, "⚪")
            
            conteudo_title = row.get('Conteudo', 'Sem Titulo')
            
            with st.expander(f"{icon}  {conteudo_title}", expanded=False):
                
                c1, c2, c3 = st.columns([1.5, 1, 1])
                
                sel_imp = c1.selectbox(
                    "Importância", 
                    options=["Baixa", "Média", "Alta"],
                    index=["Baixa", "Média", "Alta"].index(imp_val),
                    key=f"imp_{index}",
                    label_visibility="collapsed" 
                )
                
                is_dado = str(row.get('Status_Dado', '')).upper() == 'TRUE'
                is_estudado = str(row.get('Status_Estudado', '')).upper() == 'TRUE'
                
                chk_dado = c2.toggle("Dado?", value=is_dado, key=f"dado_{index}")
                chk_est = c3.toggle("Estudado?", value=is_estudado, key=f"est_{index}")

                st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True) 
                c4, c5 = st.columns(2)

                val_ex = 0
                if str(row.get('Qtd_Exercicios', '')).isdigit():
                    val_ex = int(row.get('Qtd_Exercicios'))
                    
                val_ac = 0
                if str(row.get('Qtd_Acertos', '')).isdigit():
                    val_ac = int(row.get('Qtd_Acertos'))

                qtd_ex = c4.number_input("Exercicios", min_value=0, value=val_ex, key=f"qtd_{index}")
                qtd_ac = c5.number_input("Acertos", min_value=0, value=val_ac, key=f"ac_{index}")
                
                updates[row_id] = {
                    'Importancia': sel_imp, 
                    'Status_Dado': chk_dado,
                    'Status_Estudado': chk_est,
                    'Qtd_Exercicios': qtd_ex,
                    'Qtd_Acertos': qtd_ac
                }
                
                st.markdown("<div style='margin-top:10px; margin-bottom:5px; border-top:1px solid rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)
                st.caption("Controle de Revisões")
                
                
                r1, r2, r3, r4 = st.columns(4)
                
                def render_revision(col_obj, r_label, r_key_chk, r_key_qtd, db_chk_key, db_qtd_key):
                    with col_obj:
                        is_checked = str(row.get(db_chk_key, '')).upper() == 'TRUE'
                        chk_val = st.toggle(r_label, value=is_checked, key=r_key_chk)
                        
                        qtd_val_db = safe_int(db_qtd_key)
                        
                        qtd_val = st.number_input(
                            f"Qtd {r_label}", 
                            min_value=0, 
                            value=qtd_val_db, 
                            key=r_key_qtd, 
                            label_visibility="collapsed"
                        )
                        return chk_val, qtd_val

                r1_c, r1_q = render_revision(r1, "R1", f"r1_{index}", f"r1q_{index}", 'R1_Feita', 'R1_Qtd')
                r2_c, r2_q = render_revision(r2, "R2", f"r2_{index}", f"r2q_{index}", 'R2_Feita', 'R2_Qtd')
                r3_c, r3_q = render_revision(r3, "R3", f"r3_{index}", f"r3q_{index}", 'R3_Feita', 'R3_Qtd')
                r4_c, r4_q = render_revision(r4, "R4", f"r4_{index}", f"r4q_{index}", 'R4_Feita', 'R4_Qtd')
                
                updates[row_id].update({
                    'R1_Feita': r1_c, 'R1_Qtd': r1_q,
                    'R2_Feita': r2_c, 'R2_Qtd': r2_q,
                    'R3_Feita': r3_c, 'R3_Qtd': r3_q,
                    'R4_Feita': r4_c, 'R4_Qtd': r4_q
                })

        submit = st.form_submit_button("Salvar Progresso", use_container_width=True)
        
        if submit:
            try:
                cells_to_update = []
                
                fields = [
                    'Importancia',
                    'Status_Dado', 'Status_Estudado', 'Qtd_Exercicios', 'Qtd_Acertos',
                    'R1_Feita', 'R1_Qtd',
                    'R2_Feita', 'R2_Qtd',
                    'R3_Feita', 'R3_Qtd',
                    'R4_Feita', 'R4_Qtd'
                ]
                
                for r_id, vals in updates.items():
                    for field, value in vals.items():
                        if field in col_map:
                            col_idx = col_map[field]
                            
                            if isinstance(value, bool):
                                val_str = "TRUE" if value else "FALSE"
                            else:
                                val_str = str(value)
                                
                            cells_to_update.append(gspread.Cell(r_id, col_idx, val_str))
                
                if cells_to_update:
                    worksheet.update_cells(cells_to_update)
                    st.success("Progresso salvo com sucesso!")
                    sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Nenhuma alteracao para salvar.")
                    
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")