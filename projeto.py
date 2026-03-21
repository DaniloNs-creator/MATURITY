import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(
    page_title="REALI PREMIUM - Análise de KPIs FP&A",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Injeção de CSS Avançado
st.markdown("""
    <style>
    /* Estilização do título principal */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    /* Estilização dos cartões de métricas do Streamlit */
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #1E3A8A;
    }
    /* Cores dos rótulos e valores das métricas */
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #334155;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    /* Ajuste nos inputs para ficarem mais elegantes */
    .stNumberInput > div > div > input {
        border-radius: 5px;
        border: 1px solid #CBD5E1;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Cabeçalho do App
st.markdown('<div class="main-title">REALI PREMIUM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Consultoria Especializada | Dashboard de Análise de KPIs FP&A</div>', unsafe_allow_html=True)
st.divider()

# 4. Estrutura de Abas para Organização
tab1, tab2, tab3 = st.tabs(["💧 Índices de Liquidez", "📈 Índices de Rentabilidade", "🏛️ Estrutura de Capital e Endividamento"])

# --- ABA 1: LIQUIDEZ ---
with tab1:
    st.header("Análise de Liquidez")
    st.write("Avalie a capacidade da empresa de honrar seus compromissos de curto prazo.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Liquidez Corrente")
        lc_ativo = st.number_input("Ativo Circulante (R$)", min_value=0.0, step=1000.0, key="lc_ativo")
        lc_passivo = st.number_input("Passivo Circulante (R$)", min_value=0.0, step=1000.0, key="lc_passivo")
        
        if lc_passivo > 0:
            lc_resultado = lc_ativo / lc_passivo
            st.metric("Índice de Liquidez Corrente", f"{lc_resultado:.2f}")
            if lc_resultado >= 1:
                st.success("Saudável: Ativos cobrem os passivos de curto prazo.")
            else:
                st.warning("Alerta: Passivos de curto prazo superam os ativos.")
        else:
            st.metric("Índice de Liquidez Corrente", "0.00")

    with col2:
        st.subheader("Liquidez Seca")
        ls_estoque = st.number_input("Estoque (R$)", min_value=0.0, step=1000.0, key="ls_estoque")
        # Reutilizando os inputs de passivo circulante para simplificar, mas permitindo o cálculo correto
        if lc_passivo > 0:
            ls_resultado = (lc_ativo - ls_estoque) / lc_passivo
            st.metric("Índice de Liquidez Seca", f"{ls_resultado:.2f}")
        else:
            st.metric("Índice de Liquidez Seca", "0.00")

# --- ABA 2: RENTABILIDADE ---
with tab2:
    st.header("Análise de Rentabilidade")
    st.write("Mensure a eficiência operacional e o retorno gerado pelas vendas e patrimônio.")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.subheader("Margem Bruta")
        mb_rec_liq = st.number_input("Receita Líquida (R$)", min_value=0.0, step=1000.0, key="mb_rec")
        mb_cmv = st.number_input("Custo dos Produtos Vendidos (R$)", min_value=0.0, step=1000.0, key="mb_cmv")
        
        if mb_rec_liq > 0:
            lucro_bruto = mb_rec_liq - mb_cmv
            mb_resultado = (lucro_bruto / mb_rec_liq) * 100
            st.metric("Margem Bruta (%)", f"{mb_resultado:.2f}%")
        else:
            st.metric("Margem Bruta (%)", "0.00%")

    with col4:
        st.subheader("Margem Líquida")
        ml_lucro_liq = st.number_input("Lucro Líquido (R$)", min_value=0.0, step=1000.0, key="ml_lucro")
        
        if mb_rec_liq > 0: # Usa a mesma receita líquida preenchida ao lado
            ml_resultado = (ml_lucro_liq / mb_rec_liq) * 100
            st.metric("Margem Líquida (%)", f"{ml_resultado:.2f}%")
        else:
            st.metric("Margem Líquida (%)", "0.00%")
            st.caption("Preencha a Receita Líquida na coluna ao lado.")

    with col5:
        st.subheader("ROE (Retorno s/ PL)")
        roe_pl = st.number_input("Patrimônio Líquido (R$)", min_value=0.0, step=1000.0, key="roe_pl")
        
        if roe_pl > 0:
            roe_resultado = (ml_lucro_liq / roe_pl) * 100
            st.metric("ROE (%)", f"{roe_resultado:.2f}%")
        else:
            st.metric("ROE (%)", "0.00%")
            st.caption("Requer preenchimento do Lucro Líquido.")

# --- ABA 3: ESTRUTURA DE CAPITAL ---
with tab3:
    st.header("Estrutura de Capital e Endividamento")
    st.write("Analise a dependência de capital de terceiros.")
    
    col6, col7 = st.columns(2)
    
    with col6:
        st.subheader("Grau de Endividamento")
        ge_passivo_total = st.number_input("Passivo Total (Exigível) (R$)", min_value=0.0, step=1000.0, key="ge_passivo")
        ge_ativo_total = st.number_input("Ativo Total (R$)", min_value=0.0, step=1000.0, key="ge_ativo")
        
        if ge_ativo_total > 0:
            ge_resultado = (ge_passivo_total / ge_ativo_total) * 100
            st.metric("Endividamento Geral (%)", f"{ge_resultado:.2f}%")
            st.progress(min(ge_resultado/100, 1.0)) # Barra de progresso visual
        else:
            st.metric("Endividamento Geral (%)", "0.00%")

    with col7:
        st.subheader("Composição do Endividamento")
        ce_passivo_cp = st.number_input("Passivo Circulante (Curto Prazo) (R$)", min_value=0.0, step=1000.0, key="ce_passivo_cp")
        
        if ge_passivo_total > 0:
            ce_resultado = (ce_passivo_cp / ge_passivo_total) * 100
            st.metric("Dívida de Curto Prazo (%)", f"{ce_resultado:.2f}%")
            st.caption("Percentual da dívida total que vence no curto prazo.")
        else:
            st.metric("Dívida de Curto Prazo (%)", "0.00%")
            st.caption("Requer preenchimento do Passivo Total.")

# 5. Rodapé
st.divider()
st.markdown("""
    <div style='text-align: center; color: #94A3B8; font-size: 0.9rem;'>
        © 2026 REALI PREMIUM Consultoria Especializada. Todos os direitos reservados. <br>
        <i>Desenvolvido para análises contábeis e financeiras de alta performance.</i>
    </div>
""", unsafe_allow_html=True)
