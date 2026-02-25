import streamlit as st
from streamlit_option_menu import option_menu
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from database import fetch_sheet_data, connect_to_sheets

st.set_page_config(
    page_title="Semear Mentoria",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
        <style>
        /* Importando Fonte Moderna */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

        /* Variáveis de Cor - Tema Esmeralda Profissional */
        :root {
            --bg-dark: #022C22;
            --glass-bg: rgba(6, 78, 59, 0.4);
            --glass-border: rgba(16, 185, 129, 0.2);
            --neon-green: #10B981;
            --text-primary: #ECFDF5;
            --text-secondary: #A7F3D0;
        }

        /* Reset Geral */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            color: var(--text-primary);
        }

        /* Fundo Principal */
        .stApp {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.1) 0%, transparent 20%),
                              radial-gradient(circle at 90% 80%, rgba(6, 78, 59, 0.2) 0%, transparent 20%);
        }

        /* Sidebar com Efeito Glass */
        section[data-testid="stSidebar"] {
            background-color: rgba(2, 44, 34, 0.85);
            backdrop-filter: blur(12px);
            border-right: 1px solid var(--glass-border);
            border-radius: 8px;
        }

        /* Títulos */
        h1, h2, h3 {
            color: var(--neon-green) !important;
            font-weight: 600 !important;
            letter-spacing: -0.5px;
        }
        
        
        /* BOTÕES (Estilo Call-to-Action) */
        .stButton > button {
            background: linear-gradient(135deg, #059669 0%, #10B981 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 28px;
            font-weight: 600;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
            color: white;
        }


        /* Tabs e Navegação */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px;
            color: var(--text-secondary);
            border: none;
            padding: 5px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: rgba(16, 185, 129, 0.2) !important;
            color: white !important;
            font-weight: bold;
            padding: 10px;
        }

        /* Scrollbar Customizada */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }
        ::-webkit-scrollbar-thumb {
            background: #065F46;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--neon-green);
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border-radius: 10px !important;
            color: var(--text-primary) !important;
        }

        /* Remover bordas feias de dataframe se houver */
        .stDataFrame {
            border: 1px solid var(--glass-border) !important;
            border-radius: 10px;
        }
        .sidebar-logo-container {
            text-align: center;
            padding: 5px 0;
            margin-bottom: 20px;
        }
        .sidebar-logo-text {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 2rem;
            color: white;
            letter-spacing: 2px;
        }
        .sidebar-logo-sub {
            font-size: 1rem;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 3px;
        }
        </style>
        """, unsafe_allow_html=True)

local_css()

@st.cache_data(ttl=300)
def get_all_students():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=scopes
        )
        client = gspread.authorize(credentials)
        
        sh = client.open("Semear Mentoria")
        worksheet = sh.worksheet("LOGIN")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        students = df[df['Tipo'] == 'Aluno']['Username'].unique().tolist()
        return students
    except Exception as e:
        st.error(f"Erro ao buscar alunos: {e}")
        return []

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['name'] = None
    st.session_state['role'] = None
    st.session_state['target_student'] = None

if not st.session_state['logged_in']:
    from views import login
    login.load_view()

else:
    with st.sidebar:
        st.image("logo.png")
        st.markdown("""
            <div class="sidebar-logo-container">
                <div class="sidebar-logo-text">SEMEAR</div>
                <div class="sidebar-logo-sub">Mentoria</div>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state['role'] == 'Mentor':
            st.markdown("<p style='font-size: 12px; color: #6EE7B7; font-weight: bold; margin-bottom: 5px;'>GERENCIAMENTO</p>", unsafe_allow_html=True)
            
            student_list = get_all_students()
            index_padrao = 0
            if st.session_state['target_student'] in student_list:
                index_padrao = student_list.index(st.session_state['target_student'])
            
            if student_list:
                target = st.selectbox("Aluno Selecionado", student_list, index=index_padrao)
                st.session_state['target_student'] = target
            else:
                st.warning("Sem alunos cadastrados")
                st.session_state['target_student'] = None
            
            st.markdown("---")
            
            selected = option_menu(
                menu_title="Menu",
                options=["Dashboard", "Horário", "Simulados", "Questões", "Metas", "Redações", "Revisões", "Conteúdos", "Configurações"],
                icons=["graph-up", "calendar2-week", "file-text", "pencil", "check-circle", "journal-richtext", "arrow-repeat", "book", "gear"],
                default_index=0,
                styles={
                    "container": {"border-radius": "8px", "padding": "5!important", "background-color": "rgba(12, 89, 64, 0.15)"},
                    "icon": {"color": "#10B981", "font-size": "16px"}, 
                    "nav-link": {
                        "font-size": "14px", 
                        "text-align": "left", 
                        "margin": "5px", 
                        "padding": "10px",
                        "border-radius": "8px",
                        "color": "#ECFDF5",
                    },
                    "nav-link-selected": {"background-color": "rgba(16, 185, 129, 0.2)", "color": "#10B981", "font-weight": "600", "border-left": "3px solid rgba(16, 185, 129, 0.3)"},
                }
            )

        else: 
            st.session_state['target_student'] = st.session_state['username']
            st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); text-align: center;'><small>Bem-vindo,</small><br><strong style='color:#10B981; font-size:16px;'>{st.session_state['name']}</strong></div>", unsafe_allow_html=True)
            
            selected = option_menu(
                menu_title="Menu",
                options=["Dashboard", "Horário", "Simulados", "Questões", "Metas", "Redações", "Revisões", "Conteúdos"],
                icons=["speedometer2", "calendar2-week", "file-text", "pencil", "check-circle", "journal-richtext", "arrow-repeat", "book"],
                default_index=0,
                styles={
                    "container": {"border-radius": "8px", "padding": "5!important", "background-color": "rgba(12, 89, 64, 0.15)"},
                    "icon": {"color": "#10B981", "font-size": "16px"}, 
                    "nav-link": {
                        "font-size": "14px", 
                        "text-align": "left", 
                        "margin": "5px", 
                        "padding": "10px",
                        "border-radius": "8px",
                        "color": "#ECFDF5",
                    },
                    "nav-link-selected": {"background-color": "rgba(16, 185, 129, 0.2)", "color": "#10B981", "font-weight": "600", "border-left": "3px solid rgba(16, 185, 129, 0.3)"},
                }
            )
        
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        if st.button("Encerrar Sessão", key="logout_btn", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['role'] = None
            st.session_state['target_student'] = None
            st.rerun()

    if selected == "Dashboard":
        from views import dashboard
        dashboard.load_view()
    
    elif selected == "Horário":
        from views import horario
        horario.load_view()
        
    elif selected == "Simulados":
        from views import simulados
        simulados.load_view()
        
    elif selected == "Questões":
        from views import questoes
        questoes.load_view()
        
    elif selected == "Metas":
        from views import metas
        metas.load_view()
        
    elif selected == "Redações":
        from views import redacoes
        redacoes.load_view()
        
    elif selected == "Revisões":
        from views import revisoes
        revisoes.load_view()
        
    elif selected == "Conteúdos":
        from views import conteudos
        conteudos.load_view()
        
    elif selected == "Configurações":
        from views import configuracoes
        configuracoes.load_view()
