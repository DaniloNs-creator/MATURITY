import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import base64
from io import BytesIO
import time
import random

# =============================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================
st.set_page_config(
    page_title="🏆 Elite Performance Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://eliteperformance.com/support',
        'Report a bug': "https://eliteperformance.com/bug",
        'About': "### Elite Performance Pro v4.0\nSistema de alto desempenho para atletas profissionais"
    }
)

# =============================================
# CSS PERSONALIZADO (NOVO DESIGN PREMIUM)
# =============================================
def inject_elite_css():
    st.markdown(f"""
    <style>
        /* Variáveis de design */
        :root {{
            --primary: #6a11cb;
            --primary-dark: #2575fc;
            --secondary: #f54ea2;
            --accent: #17ead9;
            --dark: #0f0c29;
            --light: #f8f9fa;
            --gray: #6c757d;
            --success: #00c9a7;
            --warning: #ffc107;
            --danger: #ff4d6d;
            
            --glass: rgba(255, 255, 255, 0.15);
            --glass-dark: rgba(0, 0, 0, 0.2);
            
            --border-radius-xl: 20px;
            --border-radius-lg: 15px;
            --border-radius: 12px;
            --border-radius-sm: 8px;
            
            --box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
            --box-shadow-lg: 0 16px 32px rgba(0, 0, 0, 0.15);
            
            --transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1);
            --transition-fast: all 0.2s ease-out;
        }}
        
        /* Efeito de fundo gradiente animado */
        .stApp {{
            background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e);
            background-size: 300% 300%;
            animation: gradientBG 12s ease infinite;
            min-height: 100vh;
            color: var(--light);
        }}
        
        @keyframes gradientBG {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        /* Cabeçalho estilo glassmorphism */
        .stApp header {{
            background: var(--glass) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--glass);
            box-shadow: var(--box-shadow);
            padding: 0.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 999;
            animation: fadeInDown 0.6s ease-out;
        }}
        
        /* Sidebar estilo vidro fosco */
        .stSidebar {{
            background: var(--glass-dark) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid var(--glass);
            padding: 1.5rem;
        }}
        
        /* Cards estilo neomorfismo com vidro */
        .card {{
            background: var(--glass);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: var(--border-radius-lg);
            border: 1px solid var(--glass);
            box-shadow: var(--box-shadow);
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
            color: white;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
        }}
        
        .card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--box-shadow-lg);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        
        .card-highlight {{
            background: linear-gradient(135deg, var(--glass), rgba(106, 17, 203, 0.3));
            border: 1px solid var(--primary);
            animation: pulse 3s infinite;
        }}
        
        /* Grid de cards responsivo */
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.75rem;
            margin: 2rem 0;
        }}
        
        /* Botões com gradiente animado */
        .stButton>button, .btn {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white !important;
            border: none;
            border-radius: var(--border-radius);
            padding: 0.85rem 1.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.85rem;
            transition: var(--transition);
            box-shadow: 0 4px 15px rgba(106, 17, 203, 0.4);
            position: relative;
            overflow: hidden;
        }}
        
        .stButton>button:hover, .btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(106, 17, 203, 0.6);
        }}
        
        .stButton>button::after, .btn::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            opacity: 0;
            transition: var(--transition);
        }}
        
        .stButton>button:hover::after, .btn:hover::after {{
            opacity: 1;
        }}
        
        .btn-outline {{
            background: transparent !important;
            color: white !important;
            border: 2px solid white;
            box-shadow: none;
        }}
        
        .btn-outline:hover {{
            background: white !important;
            color: var(--dark) !important;
        }}
        
        /* Animações personalizadas */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(106, 17, 203, 0.4); }}
            70% {{ box-shadow: 0 0 0 15px rgba(106, 17, 203, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(106, 17, 203, 0); }}
        }}
        
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}
        
        /* Efeito de loading moderno */
        .loading-spinner {{
            display: inline-block;
            width: 3rem;
            height: 3rem;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: var(--accent);
            animation: spin 1s ease-in-out infinite;
            margin: 2rem auto;
        }}
        
        /* Personalização de abas */
        .stTabs [aria-selected="true"] {{
            font-weight: 700;
            color: white !important;
        }}
        
        .stTabs [aria-selected="true"]:after {{
            content: '';
            display: block;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--secondary));
            margin-top: 0.25rem;
            border-radius: 3px;
            animation: tabUnderline 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1);
        }}
        
        /* Personalização de inputs */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input,
        .stSelectbox>div>div>select {{
            background: var(--glass) !important;
            color: white !important;
            border-radius: var(--border-radius) !important;
            border: 1px solid var(--glass) !important;
            padding: 0.75rem 1rem !important;
            transition: var(--transition-fast) !important;
        }}
        
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stDateInput>div>div>input:focus {{
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(23, 234, 217, 0.2) !important;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.2);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(var(--primary), var(--primary-dark));
            border-radius: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)

# Aplicar CSS personalizado
inject_elite_css()

# =============================================
# COMPONENTES PERSONALIZADOS
# =============================================
def loading_spinner(text="Carregando dados de performance..."):
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem;">
        <div class="loading-spinner"></div>
        <p style="margin-top: 1.5rem; color: var(--light); font-size: 1rem;">{text}</p>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title, value, change=None, icon="⚡", color="var(--accent)"):
    return f"""
    <div class="card" style="padding: 1.5rem; text-align: center; border-top: 4px solid {color};">
        <div style="font-size: 2rem; margin-bottom: 0.5rem; color: {color};">{icon}</div>
        <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.7);">{title}</p>
        <h3 style="margin: 0; font-size: 1.75rem; color: white;">{value}</h3>
        {f'''<p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: {color};">{change}</p>''' if change else ''}
    </div>
    """

def workout_card(workout):
    intensity_color = {
        "Alta": "var(--danger)",
        "Média": "var(--warning)",
        "Baixa": "var(--success)"
    }.get(workout["Intensidade"], "var(--accent)")
    
    return f"""
    <div class="card {'card-highlight' if workout['Destaque'] else ''}" style="border-top: 4px solid {intensity_color};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
            <div>
                <h3 style="margin: 0 0 0.5rem; color: white; font-size: 1.25rem;">{workout['Tipo']}</h3>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">
                        {workout['DiaSemana']}, {workout['Dia']}
                    </span>
                    {'''<span style="background: var(--secondary); color: white; font-size: 0.7rem; 
                        padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 600; text-transform: uppercase;">
                        Destaque
                    </span>''' if workout['Destaque'] else ''}
                </div>
            </div>
            <div style="background: {intensity_color}20; color: {intensity_color}; 
                        padding: 0.5rem 1rem; border-radius: var(--border-radius); 
                        font-size: 0.85rem; font-weight: 600; border: 1px solid {intensity_color}30;">
                {workout['ZonaFC']}
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1.5rem;">
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Duração</p>
                <p style="margin: 0; font-weight: 600; font-size: 1.25rem; color: white;">{workout['Duração']}</p>
            </div>
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Intensidade</p>
                <p style="margin: 0; font-weight: 600; font-size: 1.25rem; color: {intensity_color};">{workout['Intensidade']}</p>
            </div>
        </div>
        
        <div style="margin-bottom: 1.75rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.7);">Descrição</p>
            <p style="margin: 0; font-weight: 500; color: white;">{workout['Descrição']}</p>
        </div>
        
        <div style="display: flex; gap: 1rem;">
            <button class="btn" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <span>✅</span> Concluir
            </button>
            <button class="btn btn-outline" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                <span>✏️</span> Editar
            </button>
        </div>
    </div>
    """

def user_profile_component():
    st.markdown(f"""
    <div class="card" style="padding: 2rem; text-align: center; background: linear-gradient(135deg, var(--glass), rgba(106, 17, 203, 0.3));">
        <div style="width: 100px; height: 100px; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); 
                    border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                    margin: 0 auto 1.5rem; color: white; font-size: 2.5rem; font-weight: bold; 
                    box-shadow: var(--box-shadow); border: 3px solid white;">
            {user_data['nome'][0]}
        </div>
        
        <h3 style="margin: 0 0 0.5rem; color: white;">{user_data['nome']}</h3>
        <div style="background: rgba(255, 255, 255, 0.1); color: white; 
                    padding: 0.5rem 1rem; border-radius: var(--border-radius); display: inline-block; 
                    font-size: 0.85rem; font-weight: 600; margin-bottom: 1.5rem; backdrop-filter: blur(5px);">
            Plano {user_data['plano']}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left; margin-top: 1.5rem;">
            <div>
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Idade</p>
                <p style="margin: 0; font-weight: 600; color: white;">{user_data['idade']} anos</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Altura</p>
                <p style="margin: 0; font-weight: 600; color: white;">{user_data['altura']}m</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Peso</p>
                <p style="margin: 0; font-weight: 600; color: white;">{user_data['peso']}kg</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">IMC</p>
                <p style="margin: 0; font-weight: 600; color: white;">{user_data['imc']}</p>
            </div>
        </div>
        
        <div style="margin-top: 2rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: rgba(255, 255, 255, 0.7);">🎯 Objetivo Principal</p>
            <p style="margin: 0; font-weight: 500; color: white; font-size: 1rem;">{user_data['objetivo']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# DADOS DO USUÁRIO
# =============================================
@st.cache_data
def get_user_data():
    return {
        "nome": "Alexandre Costa",
        "idade": 29,
        "altura": 1.78,
        "peso": 75,
        "v02max": 65,
        "imc": 23.7,
        "bf": 12.3,
        "objetivo": "Performance em competições de triathlon",
        "nivel": "Elite",
        "disponibilidade": "6-7 dias/semana",
        "membro_desde": "10/05/2022",
        "plano": "Elite Pro",
        "treinos_concluidos": 218,
        "adherencia": 94,
        "fc_repouso": 48,
        "carga_treino": "Alta"
    }

user_data = get_user_data()

# =============================================
# GERAR PLANO DE TREINO
# =============================================
@st.cache_data
def generate_workout_plan():
    plan = []
    current_date = date.today()
    
    workout_types = {
        0: {
            "Tipo": "Natação - Intervalado",
            "ZonaFC": "Z4-Z5",
            "Intensidade": "Alta",
            "Descrição": "10x100m com 30s descanso, ritmo de competição"
        },
        1: {
            "Tipo": "Ciclismo - Longão",
            "ZonaFC": "Z2-Z3",
            "Intensidade": "Média",
            "Descrição": "90km em terreno variado, focando em cadência"
        },
        2: {
            "Tipo": "Corrida - Tempo Run",
            "ZonaFC": "Z3-Z4",
            "Intensidade": "Média-Alta",
            "Descrição": "45min em ritmo constante abaixo do limiar"
        },
        3: {
            "Tipo": "Musculação - Full Body",
            "ZonaFC": "N/A",
            "Intensidade": "Média",
            "Descrição": "Exercícios compostos com ênfase em força"
        },
        4: {
            "Tipo": "Natação - Técnica",
            "ZonaFC": "Z1-Z2",
            "Intensidade": "Baixa",
            "Descrição": "Drills de técnica e eficiência na braçada"
        },
        5: {
            "Tipo": "Brick Session",
            "ZonaFC": "Z3-Z4",
            "Intensidade": "Alta",
            "Descrição": "40km ciclismo + 10km corrida (transição rápida)"
        }
    }
    
    for day in range(14):  # 2 semanas de treino
        workout_date = current_date + timedelta(days=day)
        workout = workout_types[day % len(workout_types)]
        
        # Determinar duração baseada no tipo de treino
        if "Natação" in workout["Tipo"]:
            duration = "1h" if "Intervalado" in workout["Tipo"] else "45min"
        elif "Ciclismo" in workout["Tipo"]:
            duration = "2h30min" if "Longão" in workout["Tipo"] else "1h15min"
        elif "Corrida" in workout["Tipo"]:
            duration = "50min"
        elif "Musculação" in workout["Tipo"]:
            duration = "1h"
        elif "Brick" in workout["Tipo"]:
            duration = "2h"
        
        plan.append({
            "Data": workout_date,
            "Dia": workout_date.strftime("%d/%m/%Y"),
            "DiaSemana": workout_date.strftime("%A"),
            "Tipo": workout["Tipo"],
            "Duração": duration,
            "ZonaFC": workout["ZonaFC"],
            "Intensidade": workout["Intensidade"],
            "Descrição": workout["Descrição"],
            "Destaque": "Brick" in workout["Tipo"] or "Intervalado" in workout["Tipo"]
        })
    
    return pd.DataFrame(plan)

workout_plan = generate_workout_plan()

# =============================================
# INTERFACE PRINCIPAL
# =============================================
st.title("⚡ Elite Performance Pro")
st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); 
                padding: 2rem; margin-bottom: 2rem; position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; 
                    background: rgba(255, 255, 255, 0.05); border-radius: 50%;"></div>
        <div style="position: absolute; bottom: -80px; right: 20px; width: 150px; height: 150px; 
                    background: rgba(255, 255, 255, 0.05); border-radius: 50%;"></div>
        <div style="position: relative;">
            <h1 style="margin: 0 0 0.5rem; color: white; font-size: 2.5rem;">Bem-vindo, {user_data['nome'].split()[0]}!</h1>
            <p style="margin: 0; font-size: 1.1rem; color: rgba(255, 255, 255, 0.9);">
                Seu sistema de alto desempenho para resultados extraordinários
            </p>
        </div>
    </div>
""".format(user_data['nome'].split()[0]), unsafe_allow_html=True)

# =============================================
# SIDEBAR PREMIUM
# =============================================
with st.sidebar:
    user_profile_component()
    
    st.markdown("---")
    
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h3 style="color: white; margin-bottom: 1rem;">📊 Estatísticas</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div style="background: var(--glass); padding: 0.75rem; border-radius: var(--border-radius);">
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Treinos</p>
                <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: white;">{user_data['treinos_concluidos']}</p>
            </div>
            <div style="background: var(--glass); padding: 0.75rem; border-radius: var(--border-radius);">
                <p style="margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Adesão</p>
                <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: var(--success);">{user_data['adherencia']}%</p>
            </div>
        </div>
    </div>
    """.format(**user_data), unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div>
        <h3 style="color: white; margin-bottom: 1rem;">❤️ Saúde</h3>
        <div style="background: var(--glass); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem;">
            <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Freq. Cardíaca Repouso</p>
            <p style="margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--accent);">{fc_repouso} bpm</p>
        </div>
        <div style="background: var(--glass); padding: 1rem; border-radius: var(--border-radius);">
            <p style="margin: 0 0 0.25rem; font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Carga de Treino</p>
            <p style="margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--warning);">{carga_treino}</p>
        </div>
    </div>
    """.format(**user_data), unsafe_allow_html=True)

# =============================================
# ABAS PRINCIPAIS
# =============================================
tab1, tab2, tab3 = st.tabs(["🏋️‍♂️ Meu Plano", "📈 Performance", "⚙️ Configurações"])

with tab1:
    # Treino de hoje
    today = date.today()
    today_workout = workout_plan[workout_plan['Data'] == today]
    
    if not today_workout.empty:
        workout = today_workout.iloc[0]
        st.markdown("### ⚡ Treino do Dia")
        st.markdown(workout_card(workout), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🏝️</div>
            <h3 style="margin: 0 0 0.5rem; color: white;">Dia de Recuperação</h3>
            <p style="margin: 0; color: rgba(255, 255, 255, 0.7);">Aproveite para se recuperar e preparar para os próximos desafios!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Próximos treinos
    st.markdown("### 📅 Próximos Treinos")
    
    # Filtros avançados
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_treino = st.selectbox("Tipo de Treino", ["Todos", "Natação", "Ciclismo", "Corrida", "Musculação", "Brick"])
    with col2:
        intensidade = st.multiselect("Intensidade", ["Baixa", "Média", "Alta"], default=["Baixa", "Média", "Alta"])
    with col3:
        dias = st.slider("Próximos dias", 1, 14, 7)
    
    # Aplicar filtros
    filtered_plan = workout_plan[
        (workout_plan['Data'] > today) & 
        (workout_plan['Data'] <= today + timedelta(days=dias))
    ]
    
    if tipo_treino != "Todos":
        filtered_plan = filtered_plan[filtered_plan['Tipo'].str.contains(tipo_treino)]
    
    if intensidade:
        filtered_plan = filtered_plan[filtered_plan['Intensidade'].isin(intensidade)]
    
    # Mostrar treinos filtrados
    if not filtered_plan.empty:
        cols = st.columns(2)
        for i, (_, workout) in enumerate(filtered_plan.iterrows()):
            with cols[i % 2]:
                st.markdown(workout_card(workout), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <p style="margin: 0; color: rgba(255, 255, 255, 0.7);">Nenhum treino encontrado com os filtros selecionados</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    # Métricas chave
    st.markdown("### 📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("VO2 Máx", f"{user_data['v02max']} ml/kg/min", "+3.5%", "❤️", "var(--danger)"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Gordura Corporal", f"{user_data['bf']}%", "-1.2%", "🔥", "var(--warning)"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Freq. Cardíaca", f"{user_data['fc_repouso']} bpm", "-2 bpm", "📉", "var(--accent)"), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card("Treinos/Mês", "26", "+4", "🏋️‍♂️", "var(--success)"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos de performance
    st.markdown("### 📈 Evolução de Performance")
    
    # Dados simulados
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul"]
    vo2_data = [58, 59, 60, 61, 62, 63, 65]
    fc_data = [52, 51, 50, 49, 48, 48, 48]
    bf_data = [14.5, 14.2, 13.8, 13.5, 13.1, 12.8, 12.3]
    
    selected_metric = st.selectbox("Selecione a métrica", ["VO2 Máx", "Frequência Cardíaca", "% Gordura Corporal"])
    
    if selected_metric == "VO2 Máx":
        fig = px.line(
            x=months, y=vo2_data,
            labels={"x": "Mês", "y": "VO2 Máx (ml/kg/min)"},
            title="Evolução do VO2 Máx"
        )
        fig.update_traces(
            line=dict(color="var(--danger)", width=4),
            marker=dict(size=10, color="var(--danger)"),
            mode="lines+markers"
        )
    elif selected_metric == "Frequência Cardíaca":
        fig = px.line(
            x=months, y=fc_data,
            labels={"x": "Mês", "y": "FC Repouso (bpm)"},
            title="Evolução da Frequência Cardíaca de Repouso"
        )
        fig.update_traces(
            line=dict(color="var(--accent)", width=4),
            marker=dict(size=10, color="var(--accent)"),
            mode="lines+markers"
        )
    else:
        fig = px.line(
            x=months, y=bf_data,
            labels={"x": "Mês", "y": "% Gordura Corporal"},
            title="Evolução do Percentual de Gordura Corporal"
        )
        fig.update_traces(
            line=dict(color="var(--warning)", width=4),
            marker=dict(size=10, color="var(--warning)"),
            mode="lines+markers"
        )
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        hoverlabel=dict(
            bgcolor="var(--dark)",
            font_size=14,
            font_family="Arial"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Configurações do usuário
    st.markdown("### ⚙️ Configurações da Conta")
    
    with st.form("user_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome Completo", value=user_data['nome'])
            email = st.text_input("Email", value="alexandre.costa@email.com")
            level = st.selectbox(
                "Nível de Treino", 
                ["Iniciante", "Intermediário", "Avançado", "Elite"],
                index=3
            )
        
        with col2:
            height = st.number_input("Altura (cm)", value=int(user_data['altura']*100), min_value=140, max_value=220)
            weight = st.number_input("Peso (kg)", value=user_data['peso'], min_value=40, max_value=150)
            goal = st.selectbox(
                "Objetivo Principal", 
                ["Saúde Geral", "Perda de Gordura", "Ganho de Massa", "Performance Esportiva"],
                index=3
            )
        
        st.form_submit_button("Salvar Alterações", type="primary")
    
    st.markdown("---")
    
    # Preferências
    st.markdown("### 🌟 Preferências")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Receber notificações por email", value=True)
        st.checkbox("Receber lembretes de treino", value=True)
    with col2:
        st.checkbox("Compartilhar dados anônimos para pesquisa", value=False)
        st.checkbox("Modo escuro (padrão)", value=True, disabled=True)
    
    st.markdown("---")
    
    # Área perigosa
    st.markdown("### ⚠️ Área de Risco")
    st.warning("Ações nesta seção são irreversíveis. Proceda com cautela.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔒 Alterar Senha", type="secondary"):
            st.success("Link para alteração de senha enviado para seu email")
    with col2:
        if st.button("🗑️ Excluir Conta", type="primary"):
            st.error("Esta ação não pode ser desfeita. Tem certeza?")
            st.checkbox("Confirmar exclusão permanente da minha conta")

# =============================================
# RODAPÉ PREMIUM
# =============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem 0; color: rgba(255, 255, 255, 0.7);">
    <p style="margin: 0; font-size: 0.9rem;">⚡ Elite Performance Pro v4.0</p>
    <p style="margin: 0.5rem 0 0; font-size: 0.8rem;">© 2023 Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)

# =============================================
# ANIMAÇÕES E INTERAÇÕES AVANÇADAS
# =============================================
st.markdown("""
<script>
// Animação de hover nos cards
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.2)';
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = '';
        card.style.boxShadow = '';
    });
});

// Efeito de digitação no título
const title = document.querySelector('.stApp header h1');
if (title) {
    const originalText = title.innerText;
    title.innerText = '';
    
    let i = 0;
    const typingEffect = setInterval(() => {
        if (i < originalText.length) {
            title.innerText += originalText.charAt(i);
            i++;
        } else {
            clearInterval(typingEffect);
        }
    }, 100);
}

// Animação ao rolar a página
const animateOnScroll = () => {
    const cards = document.querySelectorAll('.card');
    const windowHeight = window.innerHeight;
    
    cards.forEach((card, index) => {
        const cardPosition = card.getBoundingClientRect().top;
        const animationPoint = windowHeight * 0.8;
        
        if (cardPosition < animationPoint) {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }
    });
};

// Inicializar elementos como invisíveis
document.querySelectorAll('.card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
});

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);
animateOnScroll(); // Executar uma vez ao carregar
</script>
""", unsafe_allow_html=True)
