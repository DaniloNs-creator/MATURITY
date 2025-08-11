import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import base64
from io import BytesIO
import time
from streamlit.components.v1 import html

# Configuração da página premium
st.set_page_config(
    page_title="🏋️‍♂️ PerformanceFit Pro",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.performancefit.com.br/ajuda',
        'Report a bug': "https://www.performancefit.com.br/bug",
        'About': "### Versão Premium 3.0\nSistema de performance esportiva avançado"
    }
)

# CSS Premium com animações e efeitos
def inject_premium_css():
    st.markdown("""
    <style>
        :root {
            --primary: #4361ee;
            --primary-dark: #3a0ca3;
            --primary-light: #4895ef;
            --secondary: #f72585;
            --accent: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --success: #38b000;
            --warning: #ff9e00;
            --danger: #ef233c;
            
            --border-radius: 12px;
            --border-radius-sm: 8px;
            --box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            --box-shadow-lg: 0 15px 30px rgba(0, 0, 0, 0.15);
            --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-fast: all 0.15s ease;
        }
        
        /* Efeito de fundo gradiente animado */
        .stApp {
            background: linear-gradient(-45deg, #f5f7fa 0%, #e4e8eb 50%, #f0f2f5 100%);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            min-height: 100vh;
        }
        
        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        
        /* Cabeçalho personalizado */
        .stApp header {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            padding: 1rem 2rem;
            border-radius: 0 0 var(--border-radius) var(--border-radius);
            box-shadow: var(--box-shadow);
            position: sticky;
            top: 0;
            z-index: 999;
            animation: fadeInDown 0.5s ease-out;
            backdrop-filter: blur(10px);
            border: none;
        }
        
        /* Sidebar premium */
        .stSidebar {
            background: rgba(255, 255, 255, 0.98) !important;
            backdrop-filter: blur(10px);
            padding: 1.5rem 1rem;
            border-right: none;
            box-shadow: 5px 0 25px rgba(0, 0, 0, 0.05);
        }
        
        /* Cards modernos com hover */
        .card {
            background: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: 1.5rem;
            transition: var(--transition);
            border-left: 4px solid var(--primary-light);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--primary-light));
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: var(--box-shadow-lg);
        }
        
        .card-highlight {
            border-left: 4px solid var(--primary);
            background: linear-gradient(to right, #ffffff, #f8f9fa);
        }
        
        /* Grid de cards responsivo */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }
        
        /* Botões premium */
        .stButton>button, .btn {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            border-radius: var(--border-radius-sm);
            padding: 0.75rem 1.5rem;
            transition: var(--transition);
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.85rem;
        }
        
        .stButton>button:hover, .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(67, 97, 238, 0.4);
            background: linear-gradient(135deg, var(--primary-light), var(--primary));
        }
        
        .btn-outline {
            background: transparent !important;
            color: var(--primary);
            border: 2px solid var(--primary);
            box-shadow: none;
        }
        
        .btn-outline:hover {
            background: var(--primary) !important;
            color: white;
        }
        
        /* Animações */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        /* Efeito de loading */
        .loading-spinner {
            display: inline-block;
            width: 2rem;
            height: 2rem;
            border: 3px solid rgba(67, 97, 238, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Títulos e textos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--dark);
            font-weight: 700;
        }
        
        .text-primary {
            color: var(--primary) !important;
        }
        
        .text-muted {
            color: var(--gray) !important;
        }
        
        /* Abas estilizadas */
        .stTabs [aria-selected="true"] {
            font-weight: 700;
            color: var(--primary) !important;
        }
        
        .stTabs [aria-selected="true"]:after {
            content: '';
            display: block;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            margin-top: 0.25rem;
            border-radius: 3px;
            animation: tabUnderline 0.3s ease-out;
        }
        
        /* Inputs modernos */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input {
            border-radius: var(--border-radius-sm) !important;
            border: 1px solid #dee2e6 !important;
            padding: 0.5rem 1rem !important;
            transition: var(--transition-fast) !important;
        }
        
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stDateInput>div>div>input:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(72, 149, 239, 0.2) !important;
        }
        
        /* Progress bars */
        .progress {
            height: 8px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 4px;
            transition: width 0.6s ease;
        }
        
        /* Tooltips */
        [data-tooltip] {
            position: relative;
            cursor: pointer;
        }
        
        [data-tooltip]:hover:after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--dark);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius-sm);
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: var(--box-shadow);
            animation: fadeIn 0.2s ease-out;
        }
        
        /* Efeito de pulse para destaques */
        .pulse {
            animation: pulse 2s infinite;
        }
    </style>
    """, unsafe_allow_html=True)

# Injetar CSS premium
inject_premium_css()

# Componente de loading personalizado
def loading_spinner(text="Carregando..."):
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem;">
        <div class="loading-spinner"></div>
        <p style="margin-top: 1rem; color: var(--gray);">{text}</p>
    </div>
    """, unsafe_allow_html=True)

# Efeito de loading inicial
with st.spinner('Inicializando sistema...'):
    with st.empty():
        loading_spinner("Carregando seus dados premium")
        time.sleep(2)

# Dados do usuário premium
@st.cache_data
def get_user_data():
    return {
        "nome": "Carlos Silva",
        "idade": 32,
        "altura": 1.82,
        "peso": 85,
        "v02max": 62,
        "imc": 25.7,
        "bf": 14.5,
        "objetivo": "Melhorar performance no ciclismo",
        "nivel": "Avançado",
        "disponibilidade": "5-6 dias/semana",
        "membro_desde": "15/03/2023",
        "plano": "Premium Elite",
        "treinos_concluidos": 142,
        "adherencia": 89
    }

user_data = get_user_data()

# Zonas de frequência cardíaca personalizadas
@st.cache_data
def calculate_zones(v02max):
    zones = {
        "Z1 (Recuperação)": (0.50 * v02max, 0.60 * v02max),
        "Z2 (Aeróbico)": (0.60 * v02max, 0.70 * v02max),
        "Z3 (Tempo)": (0.70 * v02max, 0.80 * v02max),
        "Z4 (Limiar)": (0.80 * v02max, 0.90 * v02max),
        "Z5 (VO2 Max)": (0.90 * v02max, 1.00 * v02max)
    }
    
    zone_colors = {
        "Z1 (Recuperação)": "#4cc9f0",
        "Z2 (Aeróbico)": "#4895ef",
        "Z3 (Tempo)": "#4361ee",
        "Z4 (Limiar)": "#3f37c9",
        "Z5 (VO2 Max)": "#3a0ca3"
    }
    
    return zones, zone_colors

zones, zone_colors = calculate_zones(user_data["v02max"])

# Componente de perfil do usuário para sidebar
def user_profile_card():
    st.markdown(f"""
    <div class="card" style="padding: 1.5rem; text-align: center;">
        <div style="width: 80px; height: 80px; background: linear-gradient(135deg, var(--primary), var(--accent)); 
                    border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                    margin: 0 auto 1rem; color: white; font-size: 2rem; font-weight: bold; box-shadow: var(--box-shadow);">
            {user_data['nome'][0]}
        </div>
        
        <h3 style="margin: 0 0 0.25rem; color: var(--dark);">{user_data['nome']}</h3>
        <div style="background: var(--primary-light)15; color: var(--primary-dark); 
                    padding: 0.25rem 0.75rem; border-radius: 20px; display: inline-block; 
                    font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem;">
            {user_data['plano']}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; text-align: left; margin-top: 1rem;">
            <div>
                <p style="margin: 0; font-size: 0.8rem; color: var(--gray);">Idade</p>
                <p style="margin: 0; font-weight: 600;">{user_data['idade']} anos</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.8rem; color: var(--gray);">Altura</p>
                <p style="margin: 0; font-weight: 600;">{user_data['altura']}m</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.8rem; color: var(--gray);">Peso</p>
                <p style="margin: 0; font-weight: 600;">{user_data['peso']}kg</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.8rem; color: var(--gray);">IMC</p>
                <p style="margin: 0; font-weight: 600;">{user_data['imc']}</p>
            </div>
        </div>
        
        <div style="margin-top: 1.5rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: var(--gray);">🎯 Objetivo</p>
            <p style="margin: 0; font-weight: 500;">{user_data['objetivo']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Componente de zonas de FC
def heart_rate_zones():
    st.markdown("""
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 1rem; display: flex; align-items: center;">
            <span style="color: var(--primary); margin-right: 0.5rem;">❤️</span>
            Zonas de Frequência Cardíaca
        </h3>
    """, unsafe_allow_html=True)
    
    for zone, (min_fc, max_fc) in zones.items():
        color = zone_colors[zone]
        st.markdown(f"""
        <div style="background: {color}10; padding: 0.75rem; border-radius: var(--border-radius-sm); 
                    margin-bottom: 0.5rem; border-left: 3px solid {color}; transition: var(--transition);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <p style="margin: 0; font-weight: 600; color: {color};">{zone}</p>
                <p style="margin: 0; font-size: 0.85rem; font-weight: 600;">{int(min_fc)}-{int(max_fc)} bpm</p>
            </div>
            <div class="progress" style="margin-top: 0.5rem;">
                <div class="progress-bar" style="width: {(max_fc/zones['Z5 (VO2 Max)'][1])*100}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Gerar plano de treino semanal
@st.cache_data
def generate_workout_plan():
    plan = []
    current_date = date.today()
    
    # Dados de exemplo para 4 semanas
    for week in range(1, 5):
        for day in range(1, 6):  # 5 dias de treino/semana
            workout_date = current_date + timedelta(days=(week-1)*7 + day-1)
            
            if day == 1:  # Segunda - Endurance
                workout = {
                    "Data": workout_date,
                    "Dia": workout_date.strftime("%d/%m/%Y"),
                    "DiaSemana": workout_date.strftime("%A"),
                    "Tipo": "Ciclismo - Endurance",
                    "Duração": "1h30min",
                    "ZonaFC": "Z2 (Aeróbico)",
                    "Intensidade": "65%",
                    "Descrição": "Pedal constante em terreno plano, mantendo FC na Z2",
                    "Cor": zone_colors["Z2 (Aeróbico)"],
                    "Destaque": False
                }
            elif day == 2:  # Terça - Intervalado
                workout = {
                    "Data": workout_date,
                    "Dia": workout_date.strftime("%d/%m/%Y"),
                    "DiaSemana": workout_date.strftime("%A"),
                    "Tipo": "Ciclismo - Intervalado",
                    "Duração": "1h",
                    "ZonaFC": "Z4-Z5 (Limiar-VO2)",
                    "Intensidade": "85%",
                    "Descrição": "8x (2min Z4 + 2min Z1 recuperação)",
                    "Cor": zone_colors["Z4 (Limiar)"],
                    "Destaque": True
                }
            elif day == 3:  # Quarta - Força
                workout = {
                    "Data": workout_date,
                    "Dia": workout_date.strftime("%d/%m/%Y"),
                    "DiaSemana": workout_date.strftime("%A"),
                    "Tipo": "Musculação - Inferiores",
                    "Duração": "45min",
                    "ZonaFC": "N/A",
                    "Intensidade": "75%",
                    "Descrição": "Agachamento 4x12, Leg Press 4x12, Panturrilha 4x20",
                    "Cor": "#6c757d",
                    "Destaque": False
                }
            elif day == 4:  # Quinta - Recuperação
                workout = {
                    "Data": workout_date,
                    "Dia": workout_date.strftime("%d/%m/%Y"),
                    "DiaSemana": workout_date.strftime("%A"),
                    "Tipo": "Ciclismo - Recuperação",
                    "Duração": "45min",
                    "ZonaFC": "Z1 (Recuperação)",
                    "Intensidade": "30%",
                    "Descrição": "Pedal leve em terreno plano",
                    "Cor": zone_colors["Z1 (Recuperação)"],
                    "Destaque": False
                }
            elif day == 5:  # Sexta - Longão
                workout = {
                    "Data": workout_date,
                    "Dia": workout_date.strftime("%d/%m/%Y"),
                    "DiaSemana": workout_date.strftime("%A"),
                    "Tipo": "Ciclismo - Longão",
                    "Duração": "2h30min",
                    "ZonaFC": "Z2-Z3 (Aeróbico-Tempo)",
                    "Intensidade": "70%",
                    "Descrição": "Pedal longo com variação de terreno",
                    "Cor": zone_colors["Z3 (Tempo)"],
                    "Destaque": True
                }
            
            plan.append(workout)
    
    return pd.DataFrame(plan)

workout_plan = generate_workout_plan()

# Componente de card de treino premium
def workout_card(workout):
    return f"""
    <div class="card {'card-highlight' if workout['Destaque'] else ''}" style="border-left-color: {workout['Cor']};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
                <h3 style="margin: 0 0 0.25rem; color: var(--dark);">{workout['Tipo']}</h3>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 0.85rem; color: var(--gray);">{workout['DiaSemana']}, {workout['Dia']}</span>
                    {'''<span style="background: var(--primary-light); color: white; font-size: 0.7rem; 
                        padding: 0.15rem 0.5rem; border-radius: 10px; font-weight: 600;">DESTAQUE</span>''' if workout['Destaque'] else ''}
                </div>
            </div>
            <div style="background: {workout['Cor']}15; color: {workout['Cor']}; 
                        padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                {workout['ZonaFC']}
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: var(--gray);">Duração</p>
                <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">{workout['Duração']}</p>
            </div>
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: var(--gray);">Intensidade</p>
                <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">{workout['Intensidade']}</p>
            </div>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: var(--gray);">Descrição</p>
            <p style="margin: 0; font-weight: 500;">{workout['Descrição']}</p>
        </div>
        
        <div style="display: flex; gap: 0.75rem;">
            <button class="btn" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <span>✅</span> Concluir
            </button>
            <button class="btn btn-outline" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <span>✏️</span> Editar
            </button>
        </div>
    </div>
    """

# Componente de métrica premium
def metric_card(title, value, change=None, goal=None, icon="📊"):
    change_color = "var(--success)" if (isinstance(change, str) and "+" in change) or (isinstance(change, (int, float)) and change >= 0) else "var(--danger)"
    
    return f"""
    <div class="card" style="padding: 1.25rem; text-align: center;">
        <div style="width: 50px; height: 50px; background: {icon_color(icon)}; 
                    border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                    margin: 0 auto 0.75rem; color: white; font-size: 1.25rem;">
            {icon}
        </div>
        <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: var(--gray);">{title}</p>
        <h3 style="margin: 0; color: var(--dark);">{value}</h3>
        {f'''<p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: {change_color}; font-weight: 600;">{change}</p>''' if change else ''}
        {f'''<div class="progress" style="margin-top: 0.75rem;">
            <div class="progress-bar" style="width: {goal}%;"></div>
        </div>
        <p style="margin: 0.25rem 0 0; font-size: 0.75rem; color: var(--gray);">Progresso: {goal}%</p>''' if goal else ''}
    </div>
    """

def icon_color(icon):
    colors = {
        "📊": "var(--primary)",
        "❤️": "var(--danger)",
        "🏋️‍♂️": "var(--primary-dark)",
        "⏱️": "var(--accent)",
        "📈": "var(--success)",
        "🔥": "var(--warning)"
    }
    return colors.get(icon, "var(--primary)")

# Interface Principal
st.title("🏋️‍♂️ PerformanceFit Pro")
st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); 
                color: white; margin-bottom: 2rem; padding: 1.5rem; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; 
                    background: rgba(255, 255, 255, 0.1); border-radius: 50%;"></div>
        <div style="position: absolute; bottom: -80px; right: 20px; width: 150px; height: 150px; 
                    background: rgba(255, 255, 255, 0.1); border-radius: 50%;"></div>
        <h2 style="margin: 0 0 0.5rem; color: white; position: relative;">Bem-vindo, {user_data['nome'].split()[0]}!</h2>
        <p style="margin: 0; opacity: 0.9; position: relative;">Seu plano de treino personalizado para alta performance</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Premium
with st.sidebar:
    user_profile_card()
    st.markdown("---")
    heart_rate_zones()
    st.markdown("---")
    
    # Progresso do plano
    st.markdown("### 📅 Progresso Semanal")
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <span style="font-size: 0.9rem; color: var(--gray);">Adesão</span>
        <span style="font-weight: 600;">{user_data['adherencia']}%</span>
    </div>
    <div class="progress">
        <div class="progress-bar" style="width: {user_data['adherencia']}%;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
        <div style="text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; color: var(--gray);">Treinos</p>
            <p style="margin: 0; font-size: 1.25rem; font-weight: 700;">{user_data['treinos_concluidos']}</p>
        </div>
        <div style="text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; color: var(--gray);">Semanas</p>
            <p style="margin: 0; font-size: 1.25rem; font-weight: 700;">{len(workout_plan['Data'].dt.isocalendar().week.unique())}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Download do plano
    if st.button("💾 Exportar Plano", key="export_btn"):
        with st.spinner('Preparando arquivo...'):
            time.sleep(1.5)
            st.success("Plano exportado com sucesso!")

# Abas principais
tab1, tab2, tab3 = st.tabs(["🏋️‍♂️ Meus Treinos", "📈 Performance", "⚙️ Configurações"])

with tab1:
    # Seção de hoje
    today = date.today()
    today_workout = workout_plan[workout_plan['Data'] == today]
    
    if not today_workout.empty:
        workout = today_workout.iloc[0]
        st.markdown("### 🎯 Treino de Hoje")
        st.markdown(workout_card(workout), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <h3 style="margin: 0 0 1rem; color: var(--gray);">🏝️ Dia de Descanso</h3>
            <p style="margin: 0; color: var(--gray);">Aproveite para recuperar suas energias!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Calendário de treinos
    st.markdown("### 📅 Próximos Treinos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filtrar por tipo", ["Todos", "Ciclismo", "Musculação"])
    with col2:
        filter_intensity = st.select_slider("Filtrar por intensidade", options=["Baixa", "Média", "Alta"])
    
    # Aplicar filtros
    filtered_plan = workout_plan[workout_plan['Data'] > today]
    if filter_type != "Todos":
        filtered_plan = filtered_plan[filtered_plan['Tipo'].str.contains(filter_type)]
    
    # Mostrar treinos filtrados
    if not filtered_plan.empty:
        cols = st.columns(2)
        for i, (_, workout) in enumerate(filtered_plan.iterrows()):
            with cols[i % 2]:
                st.markdown(workout_card(workout), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <p style="margin: 0; color: var(--gray);">Nenhum treino encontrado com os filtros selecionados</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    # Métricas de performance
    st.markdown("### 📊 Suas Métricas")
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.markdown(metric_card("VO2 Máx", user_data['v02max'], "+5%", 75, "❤️"), unsafe_allow_html=True)
    with metric_cols[1]:
        st.markdown(metric_card("Freq. Cardíaca", "58 bpm", "-3 bpm", 90, "📈"), unsafe_allow_html=True)
    with metric_cols[2]:
        st.markdown(metric_card("% Gordura", f"{user_data['bf']}%", "-1.5%", 65, "🔥"), unsafe_allow_html=True)
    with metric_cols[3]:
        st.markdown(metric_card("IMC", user_data['imc'], "-0.8", None, "🏋️‍♂️"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos de evolução
    st.markdown("### 📈 Evolução Mensal")
    
    # Dados simulados
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    vo2_data = [55, 56, 58, 59, 60, 62]
    fc_data = [62, 61, 60, 59, 58, 58]
    bf_data = [18.2, 17.5, 16.8, 16.0, 15.3, 14.5]
    
    tab_vo2, tab_fc, tab_bf = st.tabs(["VO2 Máx", "Freq. Cardíaca", "% Gordura"])
    
    with tab_vo2:
        fig = px.line(x=months, y=vo2_data, title="VO2 Máx (ml/kg/min)")
        fig.update_traces(line_color=zone_colors["Z5 (VO2 Max)"], line_width=3, marker_size=10)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_fc:
        fig = px.line(x=months, y=fc_data, title="Frequência Cardíaca de Repouso (bpm)")
        fig.update_traces(line_color=zone_colors["Z1 (Recuperação)"], line_width=3, marker_size=10)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_bf:
        fig = px.line(x=months, y=bf_data, title="Percentual de Gordura Corporal (%)")
        fig.update_traces(line_color="#f72585", line_width=3, marker_size=10)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Configurações do usuário
    st.markdown("### ⚙️ Configurações da Conta")
    
    with st.form("user_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Nome", value=user_data['nome'])
            st.selectbox("Nível", ["Iniciante", "Intermediário", "Avançado", "Elite"], index=2)
            st.number_input("Peso (kg)", value=user_data['peso'], min_value=40, max_value=150)
        
        with col2:
            st.text_input("Email", value="carlos.silva@email.com")
            st.selectbox("Objetivo Principal", ["Perda de Gordura", "Ganho de Massa", "Performance Esportiva", "Saúde Geral"], index=2)
            st.number_input("Altura (cm)", value=int(user_data['altura']*100), min_value=140, max_value=220)
        
        st.form_submit_button("Salvar Alterações", type="primary")
    
    st.markdown("---")
    st.markdown("### 🔒 Privacidade e Segurança")
    st.checkbox("Receber notificações por email", value=True)
    st.checkbox("Compartilhar dados anônimos para pesquisa", value=False)
    st.button("Alterar Senha", type="secondary")

# Rodapé Premium
st.markdown("---")
st.markdown("""
<div class="card" style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); 
            color: white; text-align: center; margin-top: 3rem; padding: 1.5rem; position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                background: url('https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1200&q=80') 
                center/cover; opacity: 0.1;"></div>
    <h3 style="margin: 0 0 0.5rem; font-size: 1.5rem; position: relative;">PerformanceFit Pro</h3>
    <p style="margin: 0; opacity: 0.9; position: relative;">Sistema de performance esportiva avançado</p>
    <p style="margin: 0.75rem 0 0; font-size: 0.8rem; opacity: 0.7; position: relative;">© 2023 Todos os direitos reservados | Versão 3.0 Premium</p>
</div>
""", unsafe_allow_html=True)

# Efeitos JS para interações
st.markdown("""
<script>
// Efeito de hover nos cards
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-5px)';
        card.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.15)';
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = '';
        card.style.boxShadow = '';
    });
});

// Animação ao rolar a página
function animateOnScroll() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        const cardPosition = card.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;
        
        if(cardPosition < screenPosition) {
            card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;
        }
    });
}

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);
</script>
""", unsafe_allow_html=True)
