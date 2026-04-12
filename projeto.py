import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Painel FP&A - Reali Consultoria", layout='wide', page_icon="📊")

# CSS customizado apenas para o Painel FP&A
st.markdown("""
<style>
    /* Animação para todos os botões */
    .stButton>button {
        transition: all 0.3s ease;
        transform: scale(1);
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* Header do FP&A - AZUL */
    .fpna-header {
        background: linear-gradient(135deg, #1E88E5 0%, #0D47A1 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Input cards - AZUL */
    .kpi-input {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 4px solid #1E88E5;
    }

    /* Cards responsivos - AZUL */
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
    
    /* Layout responsivo */
    @media (max-width: 768px) {
        .kpi-value {
            font-size: 24px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Logo centralizada
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Usamos o link 'raw' do GitHub para exibir a imagem nativamente
    st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/R%20Reali%20azul%201.png", use_container_width=True)

st.markdown('<div class="fpna-header"><h1>📊 PAINEL FP&A - Análise Completa de KPIs</h1><p>Análise integrada de desempenho financeiro e operacional</p></div>', unsafe_allow_html=True)

# Inicializar session state para os KPIs
if 'kpi_values' not in st.session_state:
    st.session_state.kpi_values = {}

# Definir todos os KPIs por categoria
kpis = {
    "📈 KPIs Financeiros": {
        "Receita Líquida (R$)": {"valor": 0, "formula": "Receita Bruta - Deduções", "meta": 1000000, "tipo": "quanto_maior_melhor"},
        "Lucro Líquido (R$)": {"valor": 0, "formula": "Receita Total - Custos Totais", "meta": 200000, "tipo": "quanto_maior_melhor"},
        "Margem EBITDA (%)": {"valor": 0, "formula": "(EBITDA / Receita Líquida) * 100", "meta": 25, "tipo": "quanto_maior_melhor"},
        "Margem Líquida (%)": {"valor": 0, "formula": "(Lucro Líquido / Receita Líquida) * 100", "meta": 15, "tipo": "quanto_maior_melhor"},
        "ROE - Retorno sobre Patrimônio (%)": {"valor": 0, "formula": "(Lucro Líquido / Patrimônio Líquido) * 100", "meta": 20, "tipo": "quanto_maior_melhor"},
        "ROA - Retorno sobre Ativos (%)": {"valor": 0, "formula": "(Lucro Líquido / Ativo Total) * 100", "meta": 12, "tipo": "quanto_maior_melhor"},
        "ROIC - Retorno sobre Capital Investido (%)": {"valor": 0, "formula": "(NOPAT / Capital Investido) * 100", "meta": 18, "tipo": "quanto_maior_melhor"},
        "CAC - Custo de Aquisição de Cliente (R$)": {"valor": 0, "formula": "Investimento Marketing / Novos Clientes", "meta": 500, "tipo": "quanto_menor_melhor"},
        "LTV - Lifetime Value do Cliente (R$)": {"valor": 0, "formula": "Ticket Médio * Frequência * Tempo de Relacionamento", "meta": 5000, "tipo": "quanto_maior_melhor"},
        "Relação LTV/CAC": {"valor": 0, "formula": "LTV / CAC", "meta": 3, "tipo": "quanto_maior_melhor"},
    },
    "💰 KPIs de Liquidez e Endividamento": {
        "Liquidez Corrente": {"valor": 0, "formula": "Ativo Circulante / Passivo Circulante", "meta": 1.5, "tipo": "quanto_maior_melhor"},
        "Liquidez Seca": {"valor": 0, "formula": "(Ativo Circulante - Estoques) / Passivo Circulante", "meta": 1, "tipo": "quanto_maior_melhor"},
        "Liquidez Imediata": {"valor": 0, "formula": "Disponível / Passivo Circulante", "meta": 0.3, "tipo": "quanto_maior_melhor"},
        "Endividamento Geral (%)": {"valor": 0, "formula": "(Passivo Total / Ativo Total) * 100", "meta": 50, "tipo": "quanto_menor_melhor"},
        "Dívida Líquida/EBITDA": {"valor": 0, "formula": "Dívida Líquida / EBITDA", "meta": 3, "tipo": "quanto_menor_melhor"},
        "Cobertura de Juros (TIE)": {"valor": 0, "formula": "EBIT / Despesas Financeiras", "meta": 2.5, "tipo": "quanto_maior_melhor"},
    },
    "🔄 KPIs de Eficiência Operacional": {
        "Giro do Ativo": {"valor": 0, "formula": "Receita Líquida / Ativo Total Médio", "meta": 1.2, "tipo": "quanto_maior_melhor"},
        "PMR - Prazo Médio de Recebimento (dias)": {"valor": 0, "formula": "(Duplicatas a Receber / Receita Bruta) * 360", "meta": 30, "tipo": "quanto_menor_melhor"},
        "PMP - Prazo Médio de Pagamento (dias)": {"valor": 0, "formula": "(Fornecedores / Compras) * 360", "meta": 60, "tipo": "quanto_maior_melhor"},
        "PME - Prazo Médio de Estocagem (dias)": {"valor": 0, "formula": "(Estoque Médio / CMV) * 360", "meta": 45, "tipo": "quanto_menor_melhor"},
        "Ciclo de Caixa (dias)": {"valor": 0, "formula": "PMR + PME - PMP", "meta": 15, "tipo": "quanto_menor_melhor"},
        "Break-even Point (R$)": {"valor": 0, "formula": "Custos Fixos / Margem de Contribuição", "meta": 500000, "tipo": "quanto_menor_melhor"},
        "Margem de Contribuição (%)": {"valor": 0, "formula": "(Receita - Custos Variáveis) / Receita * 100", "meta": 40, "tipo": "quanto_maior_melhor"},
    },
    "📊 KPIs de Rentabilidade": {
        "Crescimento da Receita (%)": {"valor": 0, "formula": "((Receita Atual - Receita Anterior) / Receita Anterior) * 100", "meta": 15, "tipo": "quanto_maior_melhor"},
        "CAGR - Taxa Anual Composta (%)": {"valor": 0, "formula": "((Valor Final / Valor Inicial)^(1/n) - 1) * 100", "meta": 12, "tipo": "quanto_maior_melhor"},
        "Ticket Médio (R$)": {"valor": 0, "formula": "Receita Total / Número de Vendas", "meta": 1000, "tipo": "quanto_maior_melhor"},
        "Churn Rate (%)": {"valor": 0, "formula": "(Clientes Perdidos / Total Clientes) * 100", "meta": 5, "tipo": "quanto_menor_melhor"},
        "NPS - Net Promoter Score": {"valor": 0, "formula": "% Promotores - % Detratores", "meta": 50, "tipo": "quanto_maior_melhor"},
        "Taxa de Conversão (%)": {"valor": 0, "formula": "(Vendas / Leads) * 100", "meta": 25, "tipo": "quanto_maior_melhor"},
    },
    "👥 KPIs de Recursos Humanos": {
        "Turnover (%)": {"valor": 0, "formula": "(Desligamentos / Total Funcionários) * 100", "meta": 10, "tipo": "quanto_menor_melhor"},
        "Absenteísmo (%)": {"valor": 0, "formula": "(Total Faltas / Total Dias Úteis) * 100", "meta": 3, "tipo": "quanto_menor_melhor"},
        "ROI de Treinamento (%)": {"valor": 0, "formula": "(Ganho Produtividade - Custo Treinamento) / Custo Treinamento * 100", "meta": 200, "tipo": "quanto_maior_melhor"},
        "Produtividade por Funcionário (R$)": {"valor": 0, "formula": "Receita Total / Número Funcionários", "meta": 250000, "tipo": "quanto_maior_melhor"},
    }
}

# Criar abas para cada categoria
tabs = st.tabs(list(kpis.keys()))

# Dicionário para armazenar todos os valores calculados
all_values = {}
achievements = {}

# Para cada categoria, criar inputs
for tab, (category, category_kpis) in zip(tabs, kpis.items()):
    with tab:
        st.markdown(f"### {category}")
        
        # Organizar KPIs em grid responsivo
        cols = st.columns(2)
        col_idx = 0
        
        for kpi_name, kpi_info in category_kpis.items():
            with cols[col_idx % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class="kpi-input">
                        <strong>{kpi_name}</strong><br>
                        <small style="color: #666;">Fórmula: {kpi_info['formula']}</small><br>
                        <small style="color: #666;">Meta: {kpi_info['meta']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Input de valor
                    key = f"{category}_{kpi_name}"
                    value = st.number_input(
                        f"Valor para {kpi_name}",
                        value=st.session_state.kpi_values.get(key, 0.0),
                        key=key,
                        step=1000.0 if "R$" in kpi_name else 1.0,
                        format="%.2f"
                    )
                    st.session_state.kpi_values[key] = value
                    all_values[kpi_name] = value
                    
                    # Calcular achievement
                    if value > 0 and kpi_info['meta'] > 0:
                        if kpi_info['tipo'] == "quanto_maior_melhor":
                            achievement = min(100, (value / kpi_info['meta']) * 100)
                        else:
                            achievement = min(100, (kpi_info['meta'] / value) * 100)
                        achievements[kpi_name] = achievement
                    else:
                        achievements[kpi_name] = 0
            
            col_idx += 1
        
        st.markdown("---")

# Botão para calcular e exibir análises
if st.button("🔍 ANALISAR TODOS OS KPIs", use_container_width=True):
    st.markdown("---")
    st.markdown("## 📊 RESULTADOS DA ANÁLISE COMPLETA")
    
    # 1. Cards de KPIs principais
    st.markdown("### 🎯 Principais Indicadores")
    main_kpis = ["Receita Líquida (R$)", "Lucro Líquido (R$)", "Margem EBITDA (%)", "ROE - Retorno sobre Patrimônio (%)"]
    cols = st.columns(4)
    for idx, kpi in enumerate(main_kpis):
        if kpi in all_values:
            with cols[idx]:
                value = all_values[kpi]
                achievement = achievements.get(kpi, 0)
                color = "#2196F3" if achievement >= 80 else "#FF9800" if achievement >= 50 else "#F44336"
                st.markdown(f"""
                <div class="kpi-card" style="background: linear-gradient(135deg, {color} 0%, {color}cc 100%);">
                    <div class="kpi-label">{kpi}</div>
                    <div class="kpi-value">R$ {value:,.2f}</div>
                    <div class="kpi-label">Meta: {achievement:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 2. Gráfico de Radar com todos os KPIs
    st.markdown("### 📡 Dashboard de Performance - Todos os KPIs")
    if achievements:
        # Selecionar top 15 KPIs para o radar
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
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    title="Achievement (%)"
                )
            ),
            showlegend=True,
            title="Performance dos KPIs vs Meta",
            height=600
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    
    # 3. Análise de Gaps
    st.markdown("### 📉 Análise de Gaps - Oportunidades de Melhoria")
    gaps = []
    for kpi_name, achievement in achievements.items():
        if achievement < 70:  # KPIs com baixa performance
            gaps.append({
                "KPI": kpi_name,
                "Performance": f"{achievement:.1f}%",
                "Gap": f"{100 - achievement:.1f}%",
                "Prioridade": "Alta" if achievement < 50 else "Média"
            })
    
    if gaps:
        gaps_df = pd.DataFrame(gaps)
        gaps_df = gaps_df.sort_values('Performance')
        st.dataframe(gaps_df, use_container_width=True)
    else:
        st.success("🎉 Excelente! Todos os KPIs estão com performance acima de 70% da meta!")
    
    # 4. Gráfico de Barras - Performance por Categoria
    st.markdown("### 📊 Performance por Categoria")
    category_performance = {}
    for category, category_kpis in kpis.items():
        cat_achievements = []
        for kpi_name in category_kpis.keys():
            if kpi_name in achievements:
                cat_achievements.append(achievements[kpi_name])
        if cat_achievements:
            category_performance[category] = sum(cat_achievements) / len(cat_achievements)
    
    if category_performance:
        fig_bar = px.bar(
            x=list(category_performance.keys()),
            y=list(category_performance.values()),
            title="Performance Média por Categoria de KPI",
            labels={'x': 'Categoria', 'y': 'Performance (%)'},
            color=list(category_performance.values()),
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 5. Scorecard Final
    st.markdown("### 🏆 Scorecard Final")
    overall_performance = sum(achievements.values()) / len(achievements) if achievements else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Performance Geral", f"{overall_performance:.1f}%", 
                 delta=f"{overall_performance - 50:.1f}%" if overall_performance != 50 else None)
    with col2:
        kpis_acima_meta = sum(1 for a in achievements.values() if a >= 100)
        st.metric("KPIs Acima da Meta", f"{kpis_acima_meta}/{len(achievements)}")
    with col3:
        kpis_criticos = sum(1 for a in achievements.values() if a < 50)
        st.metric("KPIs Críticos", kpis_criticos, delta="Atenção!" if kpis_criticos > 0 else None)
    
    # 6. Recomendações Estratégicas
    st.markdown("### 💡 Recomendações Estratégicas")
    if kpis_criticos > 0:
        st.warning(f"🔴 **Atenção!** {kpis_criticos} KPIs estão com performance crítica (abaixo de 50% da meta). Recomenda-se uma análise detalhada das causas raiz.")
    elif overall_performance < 70:
        st.info("🟡 **Oportunidade de Melhoria:** A performance geral está abaixo do esperado. Foque nos KPIs com maior gap.")
    else:
        st.success("🟢 **Excelente performance!** Mantenha as boas práticas e busque a excelência contínua.")
    
    # 7. Exportar Relatório
    st.markdown("---")
    if st.button("📥 Exportar Relatório Completo (Excel)", use_container_width=True):
        # Criar DataFrame com todos os resultados
        results = []
        for category, category_kpis in kpis.items():
            for kpi_name, kpi_info in category_kpis.items():
                value = all_values.get(kpi_name, 0)
                achievement = achievements.get(kpi_name, 0)
                results.append({
                    "Categoria": category,
                    "KPI": kpi_name,
                    "Valor Atual": value,
                    "Meta": kpi_info['meta'],
                    "Achievement (%)": f"{achievement:.1f}%",
                    "Status": "✅ Meta Atingida" if achievement >= 100 else "⚠️ Abaixo da Meta" if achievement < 70 else "🟡 Em Progresso",
                    "Fórmula": kpi_info['formula'],
                    "Tipo": kpi_info['tipo']
                })
        
        results_df = pd.DataFrame(results)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            results_df.to_excel(writer, index=False, sheet_name='Análise KPIs')
            
            # Adicionar resumo
            summary_df = pd.DataFrame([{
                "Performance Geral (%)": f"{overall_performance:.1f}%",
                "Total KPIs Analisados": len(achievements),
                "KPIs Acima da Meta": kpis_acima_meta,
                "KPIs Críticos": kpis_criticos,
                "Data da Análise": datetime.now().strftime("%d/%m/%Y %H:%M")
            }])
            summary_df.to_excel(writer, index=False, sheet_name='Resumo')
        
        st.download_button(
            label="💾 Baixar Relatório Excel",
            data=output.getvalue(),
            file_name=f"relatorio_kpis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
