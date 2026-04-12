import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Painel FP&A - Reali Consultoria", layout='wide', page_icon="📊")

# CSS customizado (mantido igual)
st.markdown("""
<style>
    .stButton>button {
        transition: all 0.3s ease;
        transform: scale(1);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .fpna-header {
        background: linear-gradient(135deg, #1E88E5 0%, #0D47A1 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .kpi-input {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 4px solid #1E88E5;
    }
    .kpi-card {
        border-radius: 15px;
        padding: 20px;
        color: white;
        margin: 10px;
        transition: transform 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 14px;
        opacity: 0.9;
    }
    @media (max-width: 768px) {
        .kpi-value {
            font-size: 24px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Logo
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/R%20Reali%20azul%201.png", use_container_width=True)

st.markdown('<div class="fpna-header"><h1>📊 PAINEL FP&A - Análise Completa de KPIs</h1><p>Insira os dados brutos e os indicadores são calculados automaticamente</p></div>', unsafe_allow_html=True)

# Inicializar session state para armazenar os valores dos inputs
if 'input_values' not in st.session_state:
    st.session_state.input_values = {}

# ============================================
# DEFINIÇÃO DE CADA KPI COM SEUS INPUTS E CÁLCULO
# ============================================

kpis_definition = {
    "📈 KPIs Financeiros": {
        "Receita Líquida (R$)": {
            "inputs": ["Receita Bruta", "Deduções"],
            "calc": lambda vals: vals["Receita Bruta"] - vals["Deduções"],
            "meta": 1000000, "tipo": "quanto_maior_melhor"
        },
        "Lucro Líquido (R$)": {
            "inputs": ["Receita Total", "Custos Totais"],
            "calc": lambda vals: vals["Receita Total"] - vals["Custos Totais"],
            "meta": 200000, "tipo": "quanto_maior_melhor"
        },
        "Margem EBITDA (%)": {
            "inputs": ["EBITDA", "Receita Líquida"],
            "calc": lambda vals: (vals["EBITDA"] / vals["Receita Líquida"]) * 100 if vals["Receita Líquida"] != 0 else 0,
            "meta": 25, "tipo": "quanto_maior_melhor"
        },
        "Margem Líquida (%)": {
            "inputs": ["Lucro Líquido", "Receita Líquida"],
            "calc": lambda vals: (vals["Lucro Líquido"] / vals["Receita Líquida"]) * 100 if vals["Receita Líquida"] != 0 else 0,
            "meta": 15, "tipo": "quanto_maior_melhor"
        },
        "ROE - Retorno sobre Patrimônio (%)": {
            "inputs": ["Lucro Líquido", "Patrimônio Líquido"],
            "calc": lambda vals: (vals["Lucro Líquido"] / vals["Patrimônio Líquido"]) * 100 if vals["Patrimônio Líquido"] != 0 else 0,
            "meta": 20, "tipo": "quanto_maior_melhor"
        },
        "ROA - Retorno sobre Ativos (%)": {
            "inputs": ["Lucro Líquido", "Ativo Total"],
            "calc": lambda vals: (vals["Lucro Líquido"] / vals["Ativo Total"]) * 100 if vals["Ativo Total"] != 0 else 0,
            "meta": 12, "tipo": "quanto_maior_melhor"
        },
        "ROIC - Retorno sobre Capital Investido (%)": {
            "inputs": ["NOPAT", "Capital Investido"],
            "calc": lambda vals: (vals["NOPAT"] / vals["Capital Investido"]) * 100 if vals["Capital Investido"] != 0 else 0,
            "meta": 18, "tipo": "quanto_maior_melhor"
        },
        "CAC - Custo de Aquisição de Cliente (R$)": {
            "inputs": ["Investimento Marketing", "Novos Clientes"],
            "calc": lambda vals: vals["Investimento Marketing"] / vals["Novos Clientes"] if vals["Novos Clientes"] != 0 else 0,
            "meta": 500, "tipo": "quanto_menor_melhor"
        },
        "LTV - Lifetime Value do Cliente (R$)": {
            "inputs": ["Ticket Médio", "Frequência", "Tempo de Relacionamento"],
            "calc": lambda vals: vals["Ticket Médio"] * vals["Frequência"] * vals["Tempo de Relacionamento"],
            "meta": 5000, "tipo": "quanto_maior_melhor"
        },
        "Relação LTV/CAC": {
            "inputs": ["LTV", "CAC"],
            "calc": lambda vals: vals["LTV"] / vals["CAC"] if vals["CAC"] != 0 else 0,
            "meta": 3, "tipo": "quanto_maior_melhor"
        },
    },
    "💰 KPIs de Liquidez e Endividamento": {
        "Liquidez Corrente": {
            "inputs": ["Ativo Circulante", "Passivo Circulante"],
            "calc": lambda vals: vals["Ativo Circulante"] / vals["Passivo Circulante"] if vals["Passivo Circulante"] != 0 else 0,
            "meta": 1.5, "tipo": "quanto_maior_melhor"
        },
        "Liquidez Seca": {
            "inputs": ["Ativo Circulante", "Estoques", "Passivo Circulante"],
            "calc": lambda vals: (vals["Ativo Circulante"] - vals["Estoques"]) / vals["Passivo Circulante"] if vals["Passivo Circulante"] != 0 else 0,
            "meta": 1, "tipo": "quanto_maior_melhor"
        },
        "Liquidez Imediata": {
            "inputs": ["Disponível", "Passivo Circulante"],
            "calc": lambda vals: vals["Disponível"] / vals["Passivo Circulante"] if vals["Passivo Circulante"] != 0 else 0,
            "meta": 0.3, "tipo": "quanto_maior_melhor"
        },
        "Endividamento Geral (%)": {
            "inputs": ["Passivo Total", "Ativo Total"],
            "calc": lambda vals: (vals["Passivo Total"] / vals["Ativo Total"]) * 100 if vals["Ativo Total"] != 0 else 0,
            "meta": 50, "tipo": "quanto_menor_melhor"
        },
        "Dívida Líquida/EBITDA": {
            "inputs": ["Dívida Líquida", "EBITDA"],
            "calc": lambda vals: vals["Dívida Líquida"] / vals["EBITDA"] if vals["EBITDA"] != 0 else 0,
            "meta": 3, "tipo": "quanto_menor_melhor"
        },
        "Cobertura de Juros (TIE)": {
            "inputs": ["EBIT", "Despesas Financeiras"],
            "calc": lambda vals: vals["EBIT"] / vals["Despesas Financeiras"] if vals["Despesas Financeiras"] != 0 else 0,
            "meta": 2.5, "tipo": "quanto_maior_melhor"
        },
    },
    "🔄 KPIs de Eficiência Operacional": {
        "Giro do Ativo": {
            "inputs": ["Receita Líquida", "Ativo Total Médio"],
            "calc": lambda vals: vals["Receita Líquida"] / vals["Ativo Total Médio"] if vals["Ativo Total Médio"] != 0 else 0,
            "meta": 1.2, "tipo": "quanto_maior_melhor"
        },
        "PMR - Prazo Médio de Recebimento (dias)": {
            "inputs": ["Duplicatas a Receber", "Receita Bruta"],
            "calc": lambda vals: (vals["Duplicatas a Receber"] / vals["Receita Bruta"]) * 360 if vals["Receita Bruta"] != 0 else 0,
            "meta": 30, "tipo": "quanto_menor_melhor"
        },
        "PMP - Prazo Médio de Pagamento (dias)": {
            "inputs": ["Fornecedores", "Compras"],
            "calc": lambda vals: (vals["Fornecedores"] / vals["Compras"]) * 360 if vals["Compras"] != 0 else 0,
            "meta": 60, "tipo": "quanto_maior_melhor"
        },
        "PME - Prazo Médio de Estocagem (dias)": {
            "inputs": ["Estoque Médio", "CMV"],
            "calc": lambda vals: (vals["Estoque Médio"] / vals["CMV"]) * 360 if vals["CMV"] != 0 else 0,
            "meta": 45, "tipo": "quanto_menor_melhor"
        },
        "Ciclo de Caixa (dias)": {
            "inputs": ["PMR", "PME", "PMP"],
            "calc": lambda vals: vals["PMR"] + vals["PME"] - vals["PMP"],
            "meta": 15, "tipo": "quanto_menor_melhor"
        },
        "Break-even Point (R$)": {
            "inputs": ["Custos Fixos", "Margem de Contribuição"],
            "calc": lambda vals: vals["Custos Fixos"] / vals["Margem de Contribuição"] if vals["Margem de Contribuição"] != 0 else 0,
            "meta": 500000, "tipo": "quanto_menor_melhor"
        },
        "Margem de Contribuição (%)": {
            "inputs": ["Receita", "Custos Variáveis"],
            "calc": lambda vals: ((vals["Receita"] - vals["Custos Variáveis"]) / vals["Receita"]) * 100 if vals["Receita"] != 0 else 0,
            "meta": 40, "tipo": "quanto_maior_melhor"
        },
    },
    "📊 KPIs de Rentabilidade": {
        "Crescimento da Receita (%)": {
            "inputs": ["Receita Atual", "Receita Anterior"],
            "calc": lambda vals: ((vals["Receita Atual"] - vals["Receita Anterior"]) / vals["Receita Anterior"]) * 100 if vals["Receita Anterior"] != 0 else 0,
            "meta": 15, "tipo": "quanto_maior_melhor"
        },
        "CAGR - Taxa Anual Composta (%)": {
            "inputs": ["Valor Final", "Valor Inicial", "n"],
            "calc": lambda vals: ((vals["Valor Final"] / vals["Valor Inicial"]) ** (1 / vals["n"]) - 1) * 100 if vals["Valor Inicial"] != 0 else 0,
            "meta": 12, "tipo": "quanto_maior_melhor"
        },
        "Ticket Médio (R$)": {
            "inputs": ["Receita Total", "Número de Vendas"],
            "calc": lambda vals: vals["Receita Total"] / vals["Número de Vendas"] if vals["Número de Vendas"] != 0 else 0,
            "meta": 1000, "tipo": "quanto_maior_melhor"
        },
        "Churn Rate (%)": {
            "inputs": ["Clientes Perdidos", "Total Clientes"],
            "calc": lambda vals: (vals["Clientes Perdidos"] / vals["Total Clientes"]) * 100 if vals["Total Clientes"] != 0 else 0,
            "meta": 5, "tipo": "quanto_menor_melhor"
        },
        "NPS - Net Promoter Score": {
            "inputs": ["% Promotores", "% Detratores"],
            "calc": lambda vals: vals["% Promotores"] - vals["% Detratores"],
            "meta": 50, "tipo": "quanto_maior_melhor"
        },
        "Taxa de Conversão (%)": {
            "inputs": ["Vendas", "Leads"],
            "calc": lambda vals: (vals["Vendas"] / vals["Leads"]) * 100 if vals["Leads"] != 0 else 0,
            "meta": 25, "tipo": "quanto_maior_melhor"
        },
    },
    "👥 KPIs de Recursos Humanos": {
        "Turnover (%)": {
            "inputs": ["Desligamentos", "Total Funcionários"],
            "calc": lambda vals: (vals["Desligamentos"] / vals["Total Funcionários"]) * 100 if vals["Total Funcionários"] != 0 else 0,
            "meta": 10, "tipo": "quanto_menor_melhor"
        },
        "Absenteísmo (%)": {
            "inputs": ["Total Faltas", "Total Dias Úteis"],
            "calc": lambda vals: (vals["Total Faltas"] / vals["Total Dias Úteis"]) * 100 if vals["Total Dias Úteis"] != 0 else 0,
            "meta": 3, "tipo": "quanto_menor_melhor"
        },
        "ROI de Treinamento (%)": {
            "inputs": ["Ganho Produtividade", "Custo Treinamento"],
            "calc": lambda vals: ((vals["Ganho Produtividade"] - vals["Custo Treinamento"]) / vals["Custo Treinamento"]) * 100 if vals["Custo Treinamento"] != 0 else 0,
            "meta": 200, "tipo": "quanto_maior_melhor"
        },
        "Produtividade por Funcionário (R$)": {
            "inputs": ["Receita Total", "Número Funcionários"],
            "calc": lambda vals: vals["Receita Total"] / vals["Número Funcionários"] if vals["Número Funcionários"] != 0 else 0,
            "meta": 250000, "tipo": "quanto_maior_melhor"
        },
    }
}

# ============================================
# CONSTRUÇÃO DA INTERFACE POR ABAS
# ============================================

tabs = st.tabs(list(kpis_definition.keys()))

# Dicionários para armazenar os resultados calculados
calculated_values = {}   # nome do KPI -> valor calculado
achievements = {}        # nome do KPI -> % da meta atingida

# Para cada categoria e cada KPI, exibir os campos de input conforme definição
for tab, (category, category_kpis) in zip(tabs, kpis_definition.items()):
    with tab:
        st.markdown(f"### {category}")
        cols = st.columns(2)
        col_idx = 0
        
        for kpi_name, kpi_config in category_kpis.items():
            with cols[col_idx % 2]:
                st.markdown(f"""
                <div class="kpi-input">
                    <strong>{kpi_name}</strong><br>
                    <small style="color: #666;">Fórmula: {' / '.join(kpi_config['inputs'])}</small><br>
                    <small style="color: #666;">Meta: {kpi_config['meta']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Criar campos de entrada para cada variável da fórmula
                input_dict = {}
                for var in kpi_config['inputs']:
                    # Chave única no session_state
                    key = f"{category}_{kpi_name}_{var}"
                    value = st.number_input(
                        f"{var}",
                        value=st.session_state.input_values.get(key, 0.0),
                        key=key,
                        step=1000.0 if "R$" in var or "Receita" in var or "Custo" in var else 1.0,
                        format="%.2f"
                    )
                    st.session_state.input_values[key] = value
                    input_dict[var] = value
                
                # Calcular o KPI com base nos inputs
                try:
                    kpi_value = kpi_config['calc'](input_dict)
                except:
                    kpi_value = 0.0
                
                calculated_values[kpi_name] = kpi_value
                
                # Mostrar o resultado calculado
                st.markdown(f"**✅ Resultado calculado:** `{kpi_value:,.2f}`")
                
                # Calcular achievement
                meta = kpi_config['meta']
                tipo = kpi_config['tipo']
                if kpi_value > 0 and meta > 0:
                    if tipo == "quanto_maior_melhor":
                        ach = min(100, (kpi_value / meta) * 100)
                    else:
                        ach = min(100, (meta / kpi_value) * 100)
                else:
                    ach = 0.0
                achievements[kpi_name] = ach
                
                # Barra de progresso visual
                st.progress(min(1.0, ach/100))
                st.caption(f"Achievement: {ach:.1f}%")
                
            col_idx += 1
        st.markdown("---")

# ============================================
# BOTÃO DE ANÁLISE E RELATÓRIOS
# ============================================

if st.button("🔍 ANALISAR TODOS OS KPIs", use_container_width=True):
    st.markdown("---")
    st.markdown("## 📊 RESULTADOS DA ANÁLISE COMPLETA")
    
    # 1. Cards principais
    st.markdown("### 🎯 Principais Indicadores")
    main_kpis = ["Receita Líquida (R$)", "Lucro Líquido (R$)", "Margem EBITDA (%)", "ROE - Retorno sobre Patrimônio (%)"]
    cols = st.columns(4)
    for idx, kpi in enumerate(main_kpis):
        if kpi in calculated_values:
            with cols[idx]:
                value = calculated_values[kpi]
                ach = achievements.get(kpi, 0)
                color = "#2196F3" if ach >= 80 else "#FF9800" if ach >= 50 else "#F44336"
                st.markdown(f"""
                <div class="kpi-card" style="background: linear-gradient(135deg, {color} 0%, {color}cc 100%);">
                    <div class="kpi-label">{kpi}</div>
                    <div class="kpi-value">{value:,.2f}</div>
                    <div class="kpi-label">Meta: {ach:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 2. Gráfico de Radar
    st.markdown("### 📡 Dashboard de Performance - Todos os KPIs")
    if achievements:
        top_kpis = list(achievements.keys())[:15]
        top_values = [achievements[k] for k in top_kpis]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=top_values + top_values[:1],
            theta=top_kpis + top_kpis[:1],
            fill='toself',
            name='Performance',
            line_color='#1E88E5',
            fillcolor='rgba(30, 136, 229, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], title="Achievement (%)")),
            showlegend=True,
            title="Performance dos KPIs vs Meta",
            height=600
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    
    # 3. Análise de Gaps
    st.markdown("### 📉 Análise de Gaps - Oportunidades de Melhoria")
    gaps = []
    for kpi_name, ach in achievements.items():
        if ach < 70:
            gaps.append({
                "KPI": kpi_name,
                "Performance": f"{ach:.1f}%",
                "Gap": f"{100 - ach:.1f}%",
                "Prioridade": "Alta" if ach < 50 else "Média"
            })
    if gaps:
        gaps_df = pd.DataFrame(gaps).sort_values('Performance')
        st.dataframe(gaps_df, use_container_width=True)
    else:
        st.success("🎉 Excelente! Todos os KPIs estão com performance acima de 70% da meta!")
    
    # 4. Performance por Categoria
    st.markdown("### 📊 Performance por Categoria")
    cat_perf = {}
    for cat, cat_kpis in kpis_definition.items():
        perf_list = [achievements.get(k, 0) for k in cat_kpis.keys()]
        if perf_list:
            cat_perf[cat] = sum(perf_list) / len(perf_list)
    if cat_perf:
        fig_bar = px.bar(
            x=list(cat_perf.keys()), y=list(cat_perf.values()),
            title="Performance Média por Categoria",
            labels={'x': 'Categoria', 'y': 'Performance (%)'},
            color=list(cat_perf.values()), color_continuous_scale='Blues'
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 5. Scorecard Final
    st.markdown("### 🏆 Scorecard Final")
    overall = sum(achievements.values()) / len(achievements) if achievements else 0
    acima_meta = sum(1 for a in achievements.values() if a >= 100)
    criticos = sum(1 for a in achievements.values() if a < 50)
    col1, col2, col3 = st.columns(3)
    col1.metric("Performance Geral", f"{overall:.1f}%")
    col2.metric("KPIs Acima da Meta", f"{acima_meta}/{len(achievements)}")
    col3.metric("KPIs Críticos", criticos, delta="Atenção!" if criticos > 0 else None)
    
    # 6. Recomendações
    st.markdown("### 💡 Recomendações Estratégicas")
    if criticos > 0:
        st.warning(f"🔴 **Atenção!** {criticos} KPIs estão com performance crítica (abaixo de 50% da meta).")
    elif overall < 70:
        st.info("🟡 **Oportunidade de Melhoria:** Performance geral abaixo do esperado.")
    else:
        st.success("🟢 **Excelente performance!** Continue assim.")
    
    # 7. Exportar
    st.markdown("---")
    if st.button("📥 Exportar Relatório Completo (Excel)", use_container_width=True):
        results = []
        for cat, cat_kpis in kpis_definition.items():
            for kpi_name, cfg in cat_kpis.items():
                value = calculated_values.get(kpi_name, 0)
                ach = achievements.get(kpi_name, 0)
                results.append({
                    "Categoria": cat,
                    "KPI": kpi_name,
                    "Valor Calculado": value,
                    "Meta": cfg['meta'],
                    "Achievement (%)": f"{ach:.1f}%",
                    "Status": "✅ Meta Atingida" if ach >= 100 else "⚠️ Abaixo da Meta" if ach < 70 else "🟡 Em Progresso",
                    "Tipo": cfg['tipo']
                })
        df = pd.DataFrame(results)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='KPIs_Calculados')
            summary = pd.DataFrame([{
                "Performance Geral (%)": f"{overall:.1f}%",
                "Total KPIs": len(achievements),
                "Acima da Meta": acima_meta,
                "Críticos": criticos,
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M")
            }])
            summary.to_excel(writer, index=False, sheet_name='Resumo')
        st.download_button("💾 Baixar Excel", output.getvalue(),
                           file_name=f"fpa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
