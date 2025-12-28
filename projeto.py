import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import base64
from io import BytesIO
import time

# Configuração da página premium
st.set_page_config(
    page_title="🏋️‍♂️ PerformanceFit Pro",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.performancefit.com.br/ajuda',
        'Report a bug': "https://www.performancefit.com.br/bug",
        'About': "### Versão Premium 2.0\nSistema de controle de treinos e nutrição avançado"
    }
)

# CSS Premium com animações e efeitos
def inject_premium_css():
    st.markdown("""
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --accent: #4895ef;
            --light: #f8f9fa;
            --dark: #212529;
            --success: #4cc9f0;
            --warning: #f72585;
        }
        
        /* Efeito de fundo dinâmico */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        
        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        
        /* Cabeçalho premium */
        .stApp header {
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            color: white;
            padding: 1.5rem;
            border-radius: 0 0 15px 15px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            animation: fadeInDown 0.8s ease-out;
        }
        
        /* Sidebar premium */
        .stSidebar {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-right: none;
            box-shadow: 5px 0 15px rgba(0, 0, 0, 0.05);
        }
        
        /* Cards de perfil premium */
        .profile-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1);
            border-left: 4px solid var(--accent);
            animation: fadeIn 0.8s ease-out;
        }
        
        .profile-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 12px 20px rgba(0, 0, 0, 0.1);
        }
        
        /* Cards de treino premium */
        .workout-card {
            background: white;
            padding: 1.8rem;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
            margin-bottom: 2rem;
            border-left: 5px solid var(--primary);
            transition: all 0.3s ease;
            animation: slideInUp 0.6s ease-out;
        }
        
        .workout-card:hover {
            box-shadow: 0 12px 25px rgba(0, 0, 0, 0.12);
        }
        
        /* Abas premium */
        .stTabs [aria-selected="true"] {
            font-weight: 600;
            color: var(--primary) !important;
            position: relative;
        }
        
        .stTabs [aria-selected="true"]:after {
            content: '';
            display: block;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            margin-top: 5px;
            border-radius: 2px;
            animation: tabUnderline 0.4s cubic-bezier(0.65, 0, 0.35, 1);
        }
        
        /* Botões premium */
        .stButton>button {
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.7rem 1.5rem;
            transition: all 0.3s ease;
            font-weight: 500;
            box-shadow: 0 4px 8px rgba(67, 97, 238, 0.2);
        }
        
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 15px rgba(67, 97, 238, 0.3);
            background: linear-gradient(90deg, var(--secondary), var(--primary));
        }
        
        /* Inputs premium */
        .stDateInput>div>div>input {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 0.7rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stDateInput>div>div>input:hover {
            border-color: var(--accent);
        }
        
        /* Animações personalizadas */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes tabUnderline {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        /* Efeito de loading */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Cards de nutrição premium */
        .meal-option {
            background: white;
            padding: 1.2rem;
            margin-bottom: 0.8rem;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            border-left: 4px solid var(--accent);
            animation: fadeIn 0.6s ease-out;
        }
        
        .meal-option:hover {
            transform: translateX(8px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
        }
        
        /* Progress bars */
        .progress-container {
            width: 100%;
            background-color: #e9ecef;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            height: 10px;
            border-radius: 10px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            width: 0;
            transition: width 1s ease-in-out;
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
            border-radius: 6px;
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 100;
        }
    </style>
    """, unsafe_allow_html=True)

# Injetar CSS premium
inject_premium_css()

# Efeito de loading inicial
with st.spinner('Carregando seus dados premium...'):
    time.sleep(1.5)

# Dados do usuário premium
user_data = {
    "nome": "Atleta Elite",
    "idade": 28,
    "altura": 1.87,
    "peso": 108,
    "v02max": 173,
    "objetivo": "Performance Olímpica no Ciclismo",
    "nivel": "Avançado",
    "disponibilidade": "6 dias/semana",
    "membro_desde": "01/01/2023",
    "plano": "Premium Diamond"
}

# Zonas de frequência cardíaca com visualização premium
def calculate_zones(v02max):
    zones = {
        "Z1 (Recuperação)": (0.50 * v02max, 0.60 * v02max),
        "Z2 (Aeróbico)": (0.60 * v02max, 0.70 * v02max),
        "Z3 (Tempo)": (0.70 * v02max, 0.80 * v02max),
        "Z4 (Limiar)": (0.80 * v02max, 0.90 * v02max),
        "Z5 (VO2 Max)": (0.90 * v02max, 1.00 * v02max)
    }
    
    # Adicionar cores para cada zona
    zone_colors = {
        "Z1 (Recuperação)": "#4cc9f0",
        "Z2 (Aeróbico)": "#4895ef",
        "Z3 (Tempo)": "#4361ee",
        "Z4 (Limiar)": "#3f37c9",
        "Z5 (VO2 Max)": "#3a0ca3"
    }
    
    return zones, zone_colors

zones, zone_colors = calculate_zones(user_data["v02max"])

# Dieta premium com opções avançadas
diet_plan = {
    "Café da Manhã": {
        "Opção 1": "🥚 3 ovos + 🍞 2 fatias pão integral + 🍌 1 banana + 🌾 1 colher aveia",
        "Opção 2": "🥛 Vitamina (200ml leite + 🍌 1 banana + 🌾 1 colher aveia + 🌱 1 colher chia)",
        "Opção 3": "🍞 2 fatias pão integral + 🧀 queijo cottage + 🍓 1 fruta"
    },
    "Lanche da Manhã": {
        "Opção 1": "🍎 1 fruta + 🌰 10 castanhas",
        "Opção 2": "🥛 1 iogurte natural + 🌱 1 colher linhaça",
        "Opção 3": "🍞 1 fatia pão integral + 🥜 1 colher pasta amendoim"
    },
    "Almoço": {
        "Opção 1": "🍚 1 concha arroz + 🫘 1 concha feijão + 🍗 150g frango + 🥗 salada",
        "Opção 2": "🥔 2 batatas médias + 🥩 150g carne moída + 🥦 legumes refogados",
        "Opção 3": "🍚 1 concha arroz integral + 🐟 150g peixe + 🥦 brócolis cozido"
    },
    "Lanche da Tarde": {
        "Opção 1": "🥚 1 ovo cozido + 🍞 1 torrada integral",
        "Opção 2": "🥛 1 copo de vitamina (leite + fruta)",
        "Opção 3": "🥛 1 iogurte + 🍯 1 colher granola caseira"
    },
    "Jantar": {
        "Opção 1": "🍳 Omelete (3 ovos) + 🥗 salada + 🍞 1 fatia pão integral",
        "Opção 2": "🥩 150g carne + 🎃 purê de abóbora + 🥗 salada",
        "Opção 3": "🍜 Sopa de legumes com frango desfiado"
    },
    "Ceia": {
        "Opção 1": "🥛 1 copo leite morno",
        "Opção 2": "🥛 1 iogurte natural",
        "Opção 3": "🧀 1 fatia queijo branco"
    }
}

# Plano de treino premium com progressão dinâmica
def generate_workout_plan():
    plan = []
    current_date = date(2025, 8, 11)  # Data fixa de início
    
    for week in range(1, 9):  # 8 semanas
        for day in range(1, 7):  # 6 dias de treino/semana
            
            # Progressão de intensidade baseada na semana
            intensity = min(week / 8, 1.0)  # 0 a 1
            
            if day == 1:  # Segunda - Endurance
                duration = f"{int(60 + 15 * intensity)}min"
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Ciclismo - Endurance",
                    "Duração": duration,
                    "Zona FC": "Z2 (Aeróbico)",
                    "FC Alvo": f"{int(zones['Z2 (Aeróbico)'][0])}-{int(zones['Z2 (Aeróbico)'][1])} bpm",
                    "Descrição": f"Pedal constante em terreno plano, mantendo FC na Z2. Semana {week}/8",
                    "Intensidade": f"{int(intensity * 100)}%",
                    "Semana": week
                }
            elif day == 2:  # Terça - Força
                sets = 3 + (1 if week > 4 else 0)
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Força - Membros Inferiores",
                    "Duração": "1h",
                    "Zona FC": "N/A",
                    "FC Alvo": "N/A",
                    "Descrição": f"Agachamento {sets}x12, Leg Press {sets}x12, Cadeira Extensora {sets}x15, Panturrilha {sets}x20",
                    "Intensidade": f"{int(intensity * 100)}%",
                    "Semana": week
                }
            elif day == 3:  # Quarta - Intervalado
                intervals = 6 + (2 if week > 2 else 0)
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Ciclismo - Intervalado",
                    "Duração": "1h",
                    "Zona FC": "Z4-Z5 (Limiar-VO2)",
                    "FC Alvo": f"{int(zones['Z4 (Limiar)'][0])}-{int(zones['Z5 (VO2 Max)'][1])} bpm",
                    "Descrição": f"{intervals}x (2min Z4 + 2min Z1 recuperação)",
                    "Intensidade": f"{int(intensity * 100)}%",
                    "Semana": week
                }
            elif day == 4:  # Quinta - Recuperação
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Ciclismo - Recuperação Ativa",
                    "Duração": "45min",
                    "Zona FC": "Z1 (Recuperação)",
                    "FC Alvo": f"{int(zones['Z1 (Recuperação)'][0])}-{int(zones['Z1 (Recuperação)'][1])} bpm",
                    "Descrição": "Pedal leve em terreno plano",
                    "Intensidade": "30%",
                    "Semana": week
                }
            elif day == 5:  # Sexta - Core/Superior
                sets = 3 + (1 if week > 3 else 0)
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Força - Core e Superior",
                    "Duração": "1h",
                    "Zona FC": "N/A",
                    "FC Alvo": "N/A",
                    "Descrição": f"Flexões {sets}x12, Remada Curvada {sets}x12, Prancha {sets}x1min, Abdominal Supra {sets}x20",
                    "Intensidade": f"{int(intensity * 100)}%",
                    "Semana": week
                }
            elif day == 6:  # Sábado - Longão
                duration = "2h30min" if week < 3 else "3h" if week < 6 else "3h30min"
                workout = {
                    "Dia": current_date.strftime("%d/%m/%Y"),
                    "Data": current_date,
                    "Dia da Semana": current_date.strftime("%A"),
                    "Tipo de Treino": "Ciclismo - Longão",
                    "Duração": duration,
                    "Zona FC": "Z2-Z3 (Aeróbico-Tempo)",
                    "FC Alvo": f"{int(zones['Z2 (Aeróbico)'][0])}-{int(zones['Z3 (Tempo)'][1])} bpm",
                    "Descrição": f"Pedal longo com variação de terreno. Duração: {duration}",
                    "Intensidade": f"{int(intensity * 100)}%",
                    "Semana": week
                }
            
            plan.append(workout)
            current_date += timedelta(days=1)
        
        current_date += timedelta(days=1)  # Domingo de descanso
    
    return pd.DataFrame(plan)

# Interface Premium
st.title("🏋️‍♂️ PerformanceFit Pro")
st.markdown("""
    <div style="background: linear-gradient(90deg, #4361ee, #3f37c9); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 2rem; box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);">
        <h2 style="color: white; margin: 0;">Sistema de Controle de Treinos Premium</h2>
        <p style="margin: 0.5rem 0 0; opacity: 0.9;">Plano personalizado iniciando em 11/08/2025</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Premium
with st.sidebar:
    st.markdown(f"""
    <div class="user-profile">
        <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #4361ee, #4895ef); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem; color: white; font-size: 1.5rem; font-weight: bold;">{user_data['nome'][0]}</div>
            <div>
                <h3 style="margin: 0;">{user_data['nome']}</h3>
                <p style="margin: 0; font-size: 0.9rem; color: #6c757d;">{user_data['plano']}</p>
            </div>
        </div>
        
        <div class="profile-card">
            <h4 style="margin-top: 0;">📊 Métricas</h4>
            <p><strong>📏 Altura:</strong> {user_data['altura']}m</p>
            <p><strong>⚖️ Peso:</strong> {user_data['peso']}kg</p>
            <p><strong>❤️ VO2 Máx:</strong> {user_data['v02max']} bpm</p>
            <p><strong>🎯 Objetivo:</strong> {user_data['objetivo']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Visualização das zonas de FC com cores
    st.markdown("### ❤️ Zonas de Frequência Cardíaca")
    for zone, (min_fc, max_fc) in zones.items():
        color = zone_colors[zone]
        st.markdown(f"""
        <div style="background: {color}20; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid {color};">
            <p style="margin: 0; font-weight: 500; color: {color};">{zone}</p>
            <p style="margin: 0; font-size: 0.9rem;">{int(min_fc)}-{int(max_fc)} bpm</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Progresso do plano
    st.markdown("### 📅 Progresso do Plano")
    workout_plan = generate_workout_plan()
    total_weeks = 8
    current_week = 1  # Simulação - poderia ser dinâmico
    
    st.markdown(f"**Semana {current_week} de {total_weeks}**")
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {current_week/total_weeks*100}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Download premium
    st.markdown("### 📤 Exportar Plano")
    if st.button("💾 Exportar para Excel", key="export_btn"):
        with st.spinner('Gerando arquivo premium...'):
            time.sleep(1.5)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workout_plan.to_excel(writer, sheet_name='Plano de Treino', index=False)
                
                diet_sheet = pd.DataFrame.from_dict({(i,j): diet_plan[i][j] 
                                                   for i in diet_plan.keys() 
                                                   for j in diet_plan[i].keys()},
                                                   orient='index')
                diet_sheet.to_excel(writer, sheet_name='Plano Alimentar')
            
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="PerformanceFit_Plano_Premium.xlsx" style="color: white; text-decoration: none;">⬇️ Baixar Plano Completo</a>'
            st.markdown(f"""
            <div style="background: var(--success); padding: 0.8rem; border-radius: 8px; text-align: center; margin-top: 1rem; animation: fadeIn 0.5s ease-out;">
                {href}
            </div>
            """, unsafe_allow_html=True)

# Abas principais premium
tab1, tab2, tab3 = st.tabs(["🏋️‍♂️ Plano de Treino", "🍏 Nutrição Premium", "📊 Análises"])

with tab1:
    # Seção de calendário premium
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h2>📅 Calendário de Treinos</h2>
        <div style="background: white; padding: 0.5rem 1rem; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <p style="margin: 0; font-weight: 500;">Início: 11/08/2025</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seletor de data premium
    min_date = workout_plan["Data"].min()
    max_date = workout_plan["Data"].max()
    
    selected_date = st.date_input(
        "🔍 Selecione a data para ver o treino:",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY",
        key="date_selector"
    )
    
    # Card de treino do dia
    selected_date_str = selected_date.strftime("%d/%m/%Y")
    selected_workout = workout_plan[workout_plan["Dia"] == selected_date_str]
    
    if not selected_workout.empty:
        workout = selected_workout.iloc[0]
        zone_color = zone_colors.get(workout["Zona FC"], "#4361ee")
        
        st.markdown(f"""
        <div class="workout-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0;">Treino do dia {workout['Dia']}</h3>
                <div style="background: {zone_color}20; color: {zone_color}; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.9rem; font-weight: 500;">
                    {workout['Dia da Semana']}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                    <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Tipo de Treino</p>
                    <p style="margin: 0; font-weight: 500;">{workout['Tipo de Treino']}</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                    <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Duração</p>
                    <p style="margin: 0; font-weight: 500;">{workout['Duração']}</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                    <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Zona FC</p>
                    <p style="margin: 0; font-weight: 500; color: {zone_color};">{workout['Zona FC']}</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                    <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Intensidade</p>
                    <p style="margin: 0; font-weight: 500;">{workout['Intensidade']}</p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <p style="margin: 0 0 0.5rem; font-weight: 500; color: #6c757d;">Descrição do Treino</p>
                <p style="margin: 0;">{workout['Descrição']}</p>
            </div>
            
            <div style="display: flex; gap: 1rem;">
                <button style="background: #4361ee; color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">✅ Marcar como Concluído</button>
                <button style="background: white; color: #4361ee; border: 1px solid #4361ee; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; transition: all 0.3s ease;">✏️ Editar Treino</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum treino encontrado para a data selecionada.")
    
    # Filtros avançados
    st.markdown("---")
    st.markdown("### 🔍 Filtros Avançados")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Tipo de Treino", ["Todos"] + list(workout_plan["Tipo de Treino"].unique()))
    with col2:
        filter_week = st.selectbox("Semana", ["Todas"] + [f"Semana {i}" for i in range(1, 9)])
    with col3:
        filter_intensity = st.select_slider("Intensidade", options=["0-30%", "30-60%", "60-80%", "80-100%"])
    
    # Aplicar filtros
    filtered_plan = workout_plan.copy()
    if filter_type != "Todos":
        filtered_plan = filtered_plan[filtered_plan["Tipo de Treino"] == filter_type]
    if filter_week != "Todas":
        week_num = int(filter_week.split()[1])
        filtered_plan = filtered_plan[filtered_plan["Semana"] == week_num]
    
    # Mostrar tabela premium
    st.markdown("### 📋 Lista Completa de Treinos")
    st.dataframe(
        filtered_plan.drop(columns=["Data", "Semana"]), 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Dia": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Duração": st.column_config.ProgressColumn(
                "Duração",
                help="Duração do treino",
                format="%f",
                min_value=0,
                max_value=240
            )
        }
    )
    
    # Gráficos de análise
    st.markdown("---")
    st.markdown("### 📊 Análise de Treinos")
    
    fig1 = px.pie(
        workout_plan, 
        names="Tipo de Treino", 
        title="Distribuição de Tipos de Treino",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h2>🍏 Plano Nutricional Premium</h2>
        <div style="background: #4cc9f020; color: #4cc9f0; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
            {user_data['peso']}kg | {user_data['altura']}m
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de macros
    st.markdown("### 📊 Macronutrientes Diários")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div style="background: #4895ef20; padding: 1rem; border-radius: 8px; text-align: center;">
            <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Calorias</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #4895ef;">2,800</p>
            <p style="margin: 0.3rem 0 0; font-size: 0.8rem;">kcal/dia</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: #4cc9f020; padding: 1rem; border-radius: 8px; text-align: center;">
            <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Proteínas</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #4cc9f0;">210g</p>
            <p style="margin: 0.3rem 0 0; font-size: 0.8rem;">(30% kcal)</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: #4895ef20; padding: 1rem; border-radius: 8px; text-align: center;">
            <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Carboidratos</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #4895ef;">350g</p>
            <p style="margin: 0.3rem 0 0; font-size: 0.8rem;">(50% kcal)</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div style="background: #4361ee20; padding: 1rem; border-radius: 8px; text-align: center;">
            <p style="margin: 0 0 0.3rem; font-size: 0.9rem; color: #6c757d;">Gorduras</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #4361ee;">78g</p>
            <p style="margin: 0.3rem 0 0; font-size: 0.8rem;">(20% kcal)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Plano alimentar premium
    for meal, options in diet_plan.items():
        with st.expander(f"🍽️ {meal}", expanded=True):
            cols = st.columns(len(options))
            for i, (opt, desc) in enumerate(options.items()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="meal-option">
                        <h4 style="margin-top: 0; color: #4361ee;">{opt}</h4>
                        <p style="margin-bottom: 0;">{desc}</p>
                        <button style="background: #4361ee; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 6px; margin-top: 0.5rem; font-size: 0.8rem; cursor: pointer;">➕ Adicionar</button>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💡 Recomendações Nutricionais")
    
    rec_col1, rec_col2 = st.columns(2)
    with rec_col1:
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h4 style="margin-top: 0;">📌 Dicas de Alimentação</h4>
            <ul style="padding-left: 1.2rem;">
                <li>Consuma proteína em todas as refeições</li>
                <li>Hidrate-se bem (3-4L de água/dia)</li>
                <li>Prefira carboidratos complexos</li>
                <li>Gorduras saudáveis em quantidades moderadas</li>
                <li>Legumes e verduras à vontade</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with rec_col2:
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h4 style="margin-top: 0;">⏰ Timing Nutricional</h4>
            <ul style="padding-left: 1.2rem;">
                <li><strong>Pré-treino:</strong> Carboidratos + proteína leve</li>
                <li><strong>Pós-treino:</strong> Proteína + carboidratos rápidos</li>
                <li><strong>Noite:</strong> Proteína de digestão lenta</li>
                <li><strong>Dia de descanso:</strong> Menos carboidratos, mais gordura</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h2>📊 Análises de Performance</h2>
        <div style="background: #f7258520; color: #f72585; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500;">
            Última Atualização: Hoje
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Gráficos de performance
    st.markdown("### 📈 Progresso Semanal")
    
    # Dados simulados para os gráficos
    weeks = list(range(1, 9))
    performance_data = {
        "Volume de Treino (horas)": [4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8],
        "Intensidade Média (%)": [60, 65, 70, 75, 80, 85, 90, 95],
        "Frequência Cardíaca Média": [140, 138, 136, 134, 132, 130, 128, 126],
        "Peso (kg)": [108, 106, 105, 104, 103, 102, 101, 100]
    }
    
    # Seleção de métrica
    metric = st.selectbox("Selecione a métrica", list(performance_data.keys()))
    
    fig = px.line(
        x=weeks,
        y=performance_data[metric],
        title=f"Progresso de {metric}",
        labels={"x": "Semana", "y": metric},
        markers=True
    )
    fig.update_traces(line_color='#4361ee', line_width=2.5)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f2f6')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Métricas de performance
    st.markdown("---")
    st.markdown("### 🏆 Métricas Chave")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
            <h4 style="margin-top: 0; color: #4361ee;">VO2 Máx</h4>
            <div style="display: flex; align-items: baseline;">
                <span style="font-size: 2rem; font-weight: 700;">173</span>
                <span style="margin-left: 0.5rem; color: #4cc9f0; font-weight: 500;">(+5% desde o início)</span>
            </div>
            <div class="progress-container" style="margin-top: 0.5rem;">
                <div class="progress-bar" style="width: 85%; background: #4cc9f0;"></div>
            </div>
            <p style="margin: 0.5rem 0 0; font-size: 0.9rem; color: #6c757d;">Objetivo: 180</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h4 style="margin-top: 0; color: #4361ee;">Frequência Cardíaca de Repouso</h4>
            <div style="display: flex; align-items: baseline;">
                <span style="font-size: 2rem; font-weight: 700;">58</span>
                <span style="margin-left: 0.5rem; color: #4cc9f0; font-weight: 500;">(-3 bpm desde o início)</span>
            </div>
            <div class="progress-container" style="margin-top: 0.5rem;">
                <div class="progress-bar" style="width: 75%; background: #4cc9f0;"></div>
            </div>
            <p style="margin: 0.5rem 0 0; font-size: 0.9rem; color: #6c757d;">Objetivo: 55</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
            <h4 style="margin-top: 0; color: #4361ee;">Força Relativa</h4>
            <div style="display: flex; align-items: baseline;">
                <span style="font-size: 2rem; font-weight: 700;">1.6x</span>
                <span style="margin-left: 0.5rem; color: #4cc9f0; font-weight: 500;">(+0.2x desde o início)</span>
            </div>
            <div class="progress-container" style="margin-top: 0.5rem;">
                <div class="progress-bar" style="width: 65%; background: #4cc9f0;"></div>
            </div>
            <p style="margin: 0.5rem 0 0; font-size: 0.9rem; color: #6c757d;">Objetivo: 1.8x peso corporal</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h4 style="margin-top: 0; color: #4361ee;">% Gordura Corporal</h4>
            <div style="display: flex; align-items: baseline;">
                <span style="font-size: 2rem; font-weight: 700;">18%</span>
                <span style="margin-left: 0.5rem; color: #4cc9f0; font-weight: 500;">(-2% desde o início)</span>
            </div>
            <div class="progress-container" style="margin-top: 0.5rem;">
                <div class="progress-bar" style="width: 60%; background: #4cc9f0;"></div>
            </div>
            <p style="margin: 0.5rem 0 0; font-size: 0.9rem; color: #6c757d;">Objetivo: 15%</p>
        </div>
        """, unsafe_allow_html=True)

# Rodapé Premium
st.markdown("---")
st.markdown("""
<div style="background: linear-gradient(90deg, #4361ee, #3f37c9); padding: 1.5rem; border-radius: 12px; color: white; text-align: center; margin-top: 2rem;">
    <h3 style="margin: 0 0 0.5rem;">PerformanceFit Pro</h3>
    <p style="margin: 0; opacity: 0.8;">Sistema de controle de treinos e nutrição avançado</p>
    <p style="margin: 0.5rem 0 0; font-size: 0.9rem; opacity: 0.7;">© 2025 Todos os direitos reservados | Versão 2.0 Premium</p>
</div>
""", unsafe_allow_html=True)
