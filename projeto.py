import streamlit as st

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="REALI PREMIUM - CFO & CEO Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS AVANÇADO (UI PREMIUM)
# ==========================================
st.markdown("""
    <style>
    /* Tipografia e Cores Base */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Cabeçalho */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #0F172A; /* Slate 900 */
        text-align: center;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748B; /* Slate 500 */
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Cartões de Métricas (st.metric) */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff, #f1f5f9);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.03), -4px -4px 10px rgba(255, 255, 255, 0.8);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.06), -6px -6px 15px rgba(255, 255, 255, 1);
        border-color: #3B82F6; /* Blue 500 */
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A; /* Blue 900 */
    }
    
    /* Inputs numéricos */
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        background-color: #F8FAFC;
        font-weight: 600;
        color: #334155;
    }
    .stNumberInput > div > div > input:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 1px #3B82F6;
    }
    
    /* Abas Customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CABEÇALHO DO APLICATIVO
# ==========================================
st.markdown('<div class="main-title">REALI PREMIUM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">CFO & CEO | Painel Executivo de Indicadores (FP&A)</div>', unsafe_allow_html=True)
st.divider()

# ==========================================
# 4. ESTRUTURA DE ABAS
# ==========================================
tabs = st.tabs([
    "💧 Liquidez", 
    "📈 Rentabilidade", 
    "⚙️ Eficiência Operacional", 
    "🏛️ Endividamento", 
    "💎 EBITDA & Valor"
])

# ==========================================
# ABA 1: LIQUIDEZ E CAPITAL DE GIRO
# ==========================================
with tabs[0]:
    st.header("Análise de Liquidez")
    st.write("Capacidade de pagamento das obrigações da empresa no curto e curtíssimo prazo.")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("Liquidez Corrente")
        lc_ac = st.number_input("Ativo Circulante (R$)", 0.0, step=1000.0, key="lc_ac")
        lc_pc = st.number_input("Passivo Circulante (R$)", 0.0, step=1000.0, key="lc_pc")
        if lc_pc > 0:
            st.metric("Índice", f"{lc_ac / lc_pc:.2f}x")
        else:
            st.metric("Índice", "0.00x")
            
    with c2:
        st.subheader("Liquidez Seca")
        ls_ac = st.number_input("Ativo Circulante (R$)", 0.0, step=1000.0, key="ls_ac")
        ls_est = st.number_input("Estoques (R$)", 0.0, step=1000.0, key="ls_est")
        ls_pc = st.number_input("Passivo Circulante (R$)", 0.0, step=1000.0, key="ls_pc")
        if ls_pc > 0:
            st.metric("Índice", f"{(ls_ac - ls_est) / ls_pc:.2f}x")
        else:
            st.metric("Índice", "0.00x")

    with c3:
        st.subheader("Capital de Giro Líquido (CGL)")
        cgl_ac = st.number_input("Ativo Circulante (R$)", 0.0, step=1000.0, key="cgl_ac")
        cgl_pc = st.number_input("Passivo Circulante (R$)", 0.0, step=1000.0, key="cgl_pc")
        cgl = cgl_ac - cgl_pc
        st.metric("CGL (R$)", f"R$ {cgl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# ==========================================
# ABA 2: RENTABILIDADE (DRE & BALANÇO)
# ==========================================
with tabs[1]:
    st.header("Rentabilidade e Retorno")
    st.write("Indicadores de performance sobre as vendas, ativos e patrimônio investido.")
    
    c4, c5, c6, c7 = st.columns(4)
    
    with c4:
        st.subheader("Margem Bruta")
        mb_rl = st.number_input("Receita Líquida (R$)", 0.0, step=1000.0, key="mb_rl")
        mb_cmv = st.number_input("CMV/CPV (R$)", 0.0, step=1000.0, key="mb_cmv")
        if mb_rl > 0:
            st.metric("Margem Bruta", f"{((mb_rl - mb_cmv) / mb_rl) * 100:.2f}%")
        else:
            st.metric("Margem Bruta", "0.00%")

    with c5:
        st.subheader("Margem Líquida")
        ml_ll = st.number_input("Lucro Líquido (R$)", 0.0, step=1000.0, key="ml_ll")
        ml_rl = st.number_input("Receita Líquida (R$)", 0.0, step=1000.0, key="ml_rl")
        if ml_rl > 0:
            st.metric("Margem Líquida", f"{(ml_ll / ml_rl) * 100:.2f}%")
        else:
            st.metric("Margem Líquida", "0.00%")
            
    with c6:
        st.subheader("ROA (Retorno s/ Ativo)")
        roa_ll = st.number_input("Lucro Líquido (R$)", 0.0, step=1000.0, key="roa_ll")
        roa_at = st.number_input("Ativo Total (R$)", 0.0, step=1000.0, key="roa_at")
        if roa_at > 0:
            st.metric("ROA", f"{(roa_ll / roa_at) * 100:.2f}%")
        else:
            st.metric("ROA", "0.00%")

    with c7:
        st.subheader("ROE (Retorno s/ PL)")
        roe_ll = st.number_input("Lucro Líquido (R$)", 0.0, step=1000.0, key="roe_ll")
        roe_pl = st.number_input("Patrimônio Líquido (R$)", 0.0, step=1000.0, key="roe_pl")
        if roe_pl > 0:
            st.metric("ROE", f"{(roe_ll / roe_pl) * 100:.2f}%")
        else:
            st.metric("ROE", "0.00%")

# ==========================================
# ABA 3: EFICIÊNCIA OPERACIONAL (CICLOS)
# ==========================================
with tabs[2]:
    st.header("Eficiência Operacional e Ciclos")
    st.write("Análise da gestão de prazos com clientes, fornecedores e estoques.")
    
    c8, c9, c10 = st.columns(3)
    
    with c8:
        st.subheader("PMR (Prazo Médio Recebimento)")
        pmr_cr = st.number_input("Clientes/Contas a Receber (R$)", 0.0, step=1000.0, key="pmr_cr")
        pmr_rb = st.number_input("Receita Bruta Anual (R$)", 0.0, step=1000.0, key="pmr_rb")
        if pmr_rb > 0:
            pmr = (pmr_cr / pmr_rb) * 360
            st.metric("PMR (Dias)", f"{pmr:.0f} dias")
        else:
            st.metric("PMR (Dias)", "0 dias")

    with c9:
        st.subheader("PMP (Prazo Médio Pagamento)")
        pmp_cp = st.number_input("Fornecedores (R$)", 0.0, step=1000.0, key="pmp_cp")
        pmp_cmp = st.number_input("Compras Anuais (R$)", 0.0, step=1000.0, key="pmp_cmp")
        if pmp_cmp > 0:
            pmp = (pmp_cp / pmp_cmp) * 360
            st.metric("PMP (Dias)", f"{pmp:.0f} dias")
        else:
            st.metric("PMP (Dias)", "0 dias")
            
    with c10:
        st.subheader("PME (Prazo Médio Estoque)")
        pme_est = st.number_input("Estoque Médio (R$)", 0.0, step=1000.0, key="pme_est")
        pme_cmv = st.number_input("CMV Anual (R$)", 0.0, step=1000.0, key="pme_cmv")
        if pme_cmv > 0:
            pme = (pme_est / pme_cmv) * 360
            st.metric("PME (Dias)", f"{pme:.0f} dias")
        else:
            st.metric("PME (Dias)", "0 dias")

    st.divider()
    # Cálculo Automático do Ciclo de Caixa (Se houver dados acima)
    st.markdown("### Ciclo Financeiro (Ciclo de Caixa)")
    if pmr_rb > 0 and pmp_cmp > 0 and pme_cmv > 0:
        ciclo_caixa = pme + pmr - pmp
        st.info(f"**Resultado:** {ciclo_caixa:.0f} dias (Tempo entre o pagamento a fornecedores e o recebimento de clientes).")
    else:
        st.caption("Preencha PMR, PMP e PME para calcular o Ciclo Financeiro automaticamente.")

# ==========================================
# ABA 4: ESTRUTURA DE CAPITAL (ENDIVIDAMENTO)
# ==========================================
with tabs[3]:
    st.header("Endividamento e Estrutura de Capital")
    st.write("Análise da alavancagem financeira e solvência da companhia.")
    
    c11, c12, c13 = st.columns(3)
    
    with c11:
        st.subheader("Debt to Equity (Dívida/PL)")
        de_passivo = st.number_input("Passivo Exigível Total (R$)", 0.0, step=1000.0, key="de_passivo")
        de_pl = st.number_input("Patrimônio Líquido (R$)", 0.0, step=1000.0, key="de_pl")
        if de_pl > 0:
            st.metric("Dívida / PL", f"{(de_passivo / de_pl):.2f}x")
        else:
            st.metric("Dívida / PL", "0.00x")

    with c12:
        st.subheader("Índice de Cobertura de Juros")
        icj_ebit = st.number_input("EBIT (Lucro Operacional) (R$)", 0.0, step=1000.0, key="icj_ebit")
        icj_desp = st.number_input("Despesas Financeiras (R$)", 0.0, step=1000.0, key="icj_desp")
        if icj_desp > 0:
            st.metric("Cobertura de Juros", f"{(icj_ebit / icj_desp):.2f}x")
        else:
            st.metric("Cobertura de Juros", "0.00x")
            
    with c13:
        st.subheader("Composição do Endividamento")
        ce_pc = st.number_input("Passivo Circulante (R$)", 0.0, step=1000.0, key="ce_pc")
        ce_pt = st.number_input("Passivo Exigível Total (R$)", 0.0, step=1000.0, key="ce_pt")
        if ce_pt > 0:
            st.metric("Dívida Curto Prazo (%)", f"{(ce_pc / ce_pt) * 100:.2f}%")
        else:
            st.metric("Dívida Curto Prazo (%)", "0.00%")

# ==========================================
# ABA 5: EBITDA E GERAÇÃO DE VALOR
# ==========================================
with tabs[4]:
    st.header("EBITDA e Geração de Caixa")
    st.write("Principal proxy de geração de caixa operacional da empresa.")
    
    st.subheader("Calculadora de EBITDA (Método Indireto)")
    c14, c15 = st.columns(2)
    
    with c14:
        ebitda_ll = st.number_input("Lucro Líquido (R$)", 0.0, step=1000.0, key="ebitda_ll")
        ebitda_ir = st.number_input("IR e CSLL (R$)", 0.0, step=1000.0, key="ebitda_ir")
        ebitda_rf = st.number_input("Resultado Financeiro Líquido (R$)", 0.0, step=1000.0, key="ebitda_rf")
        ebitda_da = st.number_input("Depreciação e Amortização (R$)", 0.0, step=1000.0, key="ebitda_da")
        
    with c15:
        ebitda_valor = ebitda_ll + ebitda_ir + ebitda_rf + ebitda_da
        st.write("")
        st.write("")
        st.metric("EBITDA Total (R$)", f"R$ {ebitda_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        ebitda_rl = st.number_input("Receita Líquida p/ Margem EBITDA (R$)", 0.0, step=1000.0, key="ebitda_rl")
        if ebitda_rl > 0:
            st.metric("Margem EBITDA (%)", f"{(ebitda_valor / ebitda_rl) * 100:.2f}%")
        else:
            st.metric("Margem EBITDA (%)", "0.00%")

# ==========================================
# 5. RODAPÉ
# ==========================================
st.divider()
st.markdown("""
    <div style='text-align: center; color: #94A3B8; font-size: 0.85rem; padding-top: 20px;'>
        <b>REALI PREMIUM Consultoria Especializada</b><br>
        <i>Ferramenta de uso restrito para análise financeira avançada e controladoria executiva.</i>
    </div>
""", unsafe_allow_html=True)
