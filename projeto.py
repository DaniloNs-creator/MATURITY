import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time

# =============================================
# CONFIGURAÇÃO INICIAL
# =============================================
st.set_page_config(
    page_title="🏋️‍♂️ PerformanceFit Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://example.com/help',
        'Report a bug': "https://example.com/bug",
        'About': "### Sistema de Performance Esportiva\nVersão 2.0"
    }
)

# =============================================
# CSS PERSONALIZADO
# =============================================
def inject_custom_css():
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
            --danger: #ef233c;
            --border-radius: 12px;
            --box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .stApp {
            background-color: #f5f7fa;
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .card {
            background: white;
            padding: 1.25rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: 1.25rem;
            border-left: 4px solid var(--accent);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .card-highlight {
            border-left: 4px solid var(--primary);
        }
        
        .stButton>button {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background: var(--secondary);
            transform: translateY(-2px);
            box-shadow: var(--box-shadow);
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# =============================================
# DADOS DO USUÁRIO (COM VERIFICAÇÃO)
# =============================================
def get_user_data():
    """Retorna dados do usuário com valores padrão seguros"""
    return {
        "nome": "João Silva",
        "idade": 30,
        "altura": 1.75,
        "peso": 70,
        "v02max": 50,
        "objetivo": "Melhorar performance esportiva",
        "plano": "Premium",
        "treinos_concluidos": 12,
        "adherencia": 85,
        "membro_desde": "01/01/2023"
    }

user_data = get_user_data()

def get_first_name(full_name):
    """Extrai o primeiro nome de forma segura"""
    try:
        return full_name.split()[0]
    except:
        return "Atleta"

# =============================================
# GERADOR DE PLANO DE TREINO
# =============================================
def generate_workout_plan():
    plan = []
    current_date = date.today()
    
    workout_types = [
        {
            "Tipo": "Ciclismo - Endurance",
            "Duração": "1h30min",
            "ZonaFC": "Z2",
            "Intensidade": "Moderada",
            "Descrição": "Pedal constante em terreno plano"
        },
        {
            "Tipo": "Corrida - Intervalado",
            "Duração": "45min",
            "ZonaFC": "Z4-Z5",
            "Intensidade": "Alta",
            "Descrição": "8x400m com recuperação ativa"
        },
        {
            "Tipo": "Musculação - Membros Inferiores",
            "Duração": "1h",
            "ZonaFC": "N/A",
            "Intensidade": "Moderada",
            "Descrição": "Agachamentos, leg press e panturrilha"
        },
        {
            "Tipo": "Natação - Técnica",
            "Duração": "45min",
            "ZonaFC": "Z1-Z2",
            "Intensidade": "Leve",
            "Descrição": "Exercícios de técnica e respiração"
        }
    ]
    
    for i in range(14):  # 2 semanas de treino
        workout_date = current_date + timedelta(days=i)
        workout = workout_types[i % len(workout_types)].copy()
        workout.update({
            "Data": workout_date,
            "Dia": workout_date.strftime("%d/%m/%Y"),
            "DiaSemana": workout_date.strftime("%A"),
            "Destaque": i % 3 == 0  # Destacar alguns treinos
        })
        plan.append(workout)
    
    return pd.DataFrame(plan)

workout_plan = generate_workout_plan()

# =============================================
# COMPONENTES REUTILIZÁVEIS
# =============================================
def workout_card(workout):
    """Componente de card de treino seguro"""
    zone_color = {
        "Z1": "#4cc9f0",
        "Z2": "#4895ef",
        "Z3": "#4361ee",
        "Z4": "#3f37c9",
        "Z5": "#3a0ca3"
    }.get(workout.get("ZonaFC", ""), "#6c757d")
    
    return f"""
    <div class="card {'card-highlight' if workout.get('Destaque', False) else ''}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0;">{workout.get('Tipo', 'Treino')}</h3>
            <div style="background: {zone_color}15; color: {zone_color}; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem;">
                {workout.get('DiaSemana', '')}
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: #6c757d;">Duração</p>
                <p style="margin: 0; font-weight: 500;">{workout.get('Duração', '')}</p>
            </div>
            <div>
                <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: #6c757d;">Intensidade</p>
                <p style="margin: 0; font-weight: 500;">{workout.get('Intensidade', '')}</p>
            </div>
        </div>
        
        <p style="margin: 0 0 0.5rem; font-weight: 500; color: #6c757d;">Descrição</p>
        <p style="margin: 0;">{workout.get('Descrição', '')}</p>
        
        <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
            <button style="background: var(--primary); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer;">
                Concluir
            </button>
            <button style="background: white; color: var(--primary); border: 1px solid var(--primary); padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer;">
                Editar
            </button>
        </div>
    </div>
    """

def user_profile_card():
    """Componente de perfil do usuário"""
    return f"""
    <div class="card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="width: 50px; height: 50px; background: linear-gradient(135deg, var(--primary), var(--accent)); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                        margin-right: 1rem; color: white; font-size: 1.25rem; font-weight: bold;">
                {get_first_name(user_data.get('nome', '')).upper()[0]}
            </div>
            <div>
                <h3 style="margin: 0; font-size: 1.1rem;">{user_data.get('nome', 'Usuário')}</h3>
                <p style="margin: 0; font-size: 0.8rem; color: #6c757d;">Plano {user_data.get('plano', '')}</p>
            </div>
        </div>
        
        <div style="margin-top: 1rem;">
            <p><strong>Idade:</strong> {user_data.get('idade', '')}</p>
            <p><strong>Altura:</strong> {user_data.get('altura', '')}m</p>
            <p><strong>Peso:</strong> {user_data.get('peso', '')}kg</p>
            <p><strong>Objetivo:</strong> {user_data.get('objetivo', '')}</p>
        </div>
    </div>
    """

# =============================================
# INTERFACE PRINCIPAL
# =============================================
st.title("🏋️‍♂️ PerformanceFit Pro")

# Header personalizado
st.markdown(f"""
<div class="card" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; margin-bottom: 2rem;">
    <h2 style="margin: 0 0 0.5rem; color: white;">Bem-vindo, {get_first_name(user_data.get('nome', 'Atleta'))}!</h2>
    <p style="margin: 0; opacity: 0.9;">Seu plano de treino personalizado</p>
</div>
""", unsafe_allow_html=True)

# =============================================
# SIDEBAR
# =============================================
with st.sidebar:
    st.markdown(user_profile_card(), unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Estatísticas")
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;">
        <div class="card" style="padding: 0.75rem; text-align: center;">
            <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: #6c757d;">Treinos</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700;">{user_data.get('treinos_concluidos', 0)}</p>
        </div>
        <div class="card" style="padding: 0.75rem; text-align: center;">
            <p style="margin: 0 0 0.25rem; font-size: 0.9rem; color: #6c757d;">Adesão</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: var(--success);">{user_data.get('adherencia', 0)}%</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# ABAS PRINCIPAIS
# =============================================
tab1, tab2 = st.tabs(["📅 Meus Treinos", "📈 Performance"])

with tab1:
    # Treino de hoje
    today = date.today()
    today_workout = workout_plan[workout_plan['Data'] == today]
    
    if not today_workout.empty:
        st.markdown("### 🎯 Treino de Hoje")
        workout = today_workout.iloc[0].to_dict()
        st.markdown(workout_card(workout), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <h3 style="margin: 0 0 1rem;">🏝️ Dia de Descanso</h3>
            <p style="margin: 0; color: #6c757d;">Aproveite para se recuperar!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Próximos treinos
    st.markdown("### 📅 Próximos Treinos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Tipo de Treino", ["Todos", "Ciclismo", "Corrida", "Musculação", "Natação"])
    with col2:
        filter_days = st.slider("Próximos dias", 1, 14, 7)
    
    # Aplicar filtros
    filtered_plan = workout_plan[
        (workout_plan['Data'] > today) & 
        (workout_plan['Data'] <= today + timedelta(days=filter_days))
    ]
    
    if filter_type != "Todos":
        filtered_plan = filtered_plan[filtered_plan['Tipo'].str.contains(filter_type)]
    
    # Mostrar treinos
    if not filtered_plan.empty:
        cols = st.columns(2)
        for i, (_, workout) in enumerate(filtered_plan.iterrows()):
            with cols[i % 2]:
                st.markdown(workout_card(workout.to_dict()), unsafe_allow_html=True)
    else:
        st.info("Nenhum treino encontrado com os filtros selecionados")

with tab2:
    st.markdown("### 📊 Suas Métricas")
    
    # Métricas em cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 1.25rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: #6c757d;">VO2 Máx</p>
            <p style="margin: 0; font-size: 1.75rem; font-weight: 700; color: var(--primary);">{user_data.get('v02max', 0)}</p>
            <p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: var(--success);">+5% desde o início</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 1.25rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: #6c757d;">IMC</p>
            <p style="margin: 0; font-size: 1.75rem; font-weight: 700; color: var(--primary);">{user_data.get('peso', 0)/(user_data.get('altura', 1)**2):.1f}</p>
            <p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: var(--success);">-0.5 desde o início</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="card" style="text-align: center; padding: 1.25rem;">
            <p style="margin: 0 0 0.5rem; font-size: 0.9rem; color: #6c757d;">Adesão</p>
            <p style="margin: 0; font-size: 1.75rem; font-weight: 700; color: var(--primary);">{user_data.get('adherencia', 0)}%</p>
            <p style="margin: 0.25rem 0 0; font-size: 0.85rem; color: var(--success);">+10% desde o mês passado</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráfico de progresso
    st.markdown("### 📈 Progresso Mensal")
    
    # Dados simulados
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    progress_data = {
        "VO2 Máx": [50, 52, 54, 56, 58, 60],
        "Treinos": [8, 10, 12, 14, 16, 18],
        "Adesão": [70, 75, 80, 85, 90, 95]
    }
    
    selected_metric = st.selectbox("Selecione a métrica", list(progress_data.keys()))
    
    fig = px.line(
        x=months, y=progress_data[selected_metric],
        labels={"x": "Mês", "y": selected_metric},
        title=f"Progresso de {selected_metric}"
    )
    fig.update_traces(line_color='#4361ee', line_width=3)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# RODAPÉ
# =============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; margin-top: 2rem;">
    <p>PerformanceFit Pro © 2023 - Versão 2.0</p>
</div>
""", unsafe_allow_html=True)
