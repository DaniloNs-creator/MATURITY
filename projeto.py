import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional
import tempfile
import os

# Configuração da página
st.set_page_config(
    page_title="Análise de Extrato Häfele",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
        margin-top: 0.5rem;
    }
    .data-table {
        font-size: 0.9rem;
    }
    .highlight {
        background-color: #DBEAFE;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class HafelePDFProcessor:
    """Classe para processar PDFs da Häfele"""
    
    def __init__(self):
        self.data = {
            'cabecalho': {},
            'itens': [],
            'resumo_financeiro': {},
            'tributos_totais': {},
            'transportes': {}
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extrai texto de todas as páginas do PDF"""
        all_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        all_text.append(f"===== Page {page_num} =====\n{text}")
            return all_text
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return []
    
    def parse_identification_section(self, text: str):
        """Parse da seção de identificação"""
        patterns = {
            'importador': r"IMPORTADOR HAFELE BRASIL",
            'cnpj': r"CNPJ (\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",
            'data': r"Data de Cadastro (\d{2}/\d{2}/\d{4})",
            'numero': r"Numero (\w+)",
            'responsavel': r"Responsavel Legal ([A-Z\s]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.data['cabecalho'][key] = match.group(1) if key != 'importador' else match.group(0)
    
    def parse_currency_rates(self, text: str):
        """Parse das cotações de moedas"""
        currency_pattern = r"Moeda Negociada (\d+) - ([A-Z\s]+)Cotacao (\d+,\d+)"
        matches = re.findall(currency_pattern, text)
        
        if matches:
            self.data['cabecalho']['cotacoes'] = []
            for match in matches:
                self.data['cabecalho']['cotacoes'].append({
                    'codigo': match[0],
                    'moeda': match[1],
                    'cotacao': float(match[2].replace(',', '.'))
                })
    
    def parse_summary_section(self, text: str):
        """Parse da seção de resumo"""
        # Valor da mercadoria
        vmle_pattern = r"VMLE \(R\$\) ([\d\.,]+)"
        vmle_match = re.search(vmle_pattern, text)
        if vmle_match:
            self.data['resumo_financeiro']['vmle_reais'] = float(
                vmle_match.group(1).replace('.', '').replace(',', '.')
            )
    
    def parse_tax_calculation(self, text: str):
        """Parse dos cálculos de tributos"""
        tax_pattern = r"([A-Z]+)\s+([\d\.,]+)\s+[\d\.,]+\s+[\d\.,]+\s+[\d\.,]+\s+([\d\.,]+)"
        tax_matches = re.findall(tax_pattern, text)
        
        tributos = {}
        for match in tax_matches:
            tributo_nome = match[0]
            valor_calculado = float(match[1].replace('.', '').replace(',', '.'))
            valor_a_recolher = float(match[2].replace('.', '').replace(',', '.'))
            
            tributos[tributo_nome] = {
                'calculado': valor_calculado,
                'a_recolher': valor_a_recolher
            }
        
        self.data['tributos_totais'] = tributos
    
    def parse_transport_section(self, text: str):
        """Parse da seção de transporte"""
        transporte_data = {}
        
        # Informações básicas de transporte
        patterns = {
            'via_transporte': r"Via de Transporte ([^ ]+)",
            'data_embarque': r"Data de Embarque (\d{2}/\d{2}/\d{4})",
            'data_chegada': r"Data de Chegada (\d{2}/\d{2}/\d{4})",
            'pais_procedencia': r"Pais de Procedencia ([^(]+)",
            'porto': r"(\d+ - PORTO DE [A-Z]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transporte_data[key] = match.group(1)
        
        # Frete
        frete_pattern = r"Total \(R\\) ([\d\.,]+)"
        frete_match = re.search(frete_pattern, text)
        if frete_match:
            transporte_data['frete_total'] = float(
                frete_match.group(1).replace('.', '').replace(',', '.')
            )
        
        self.data['transportes'] = transporte_data
    
    def parse_product_items(self, text: str) -> List[Dict]:
        """Parse dos itens de produto"""
        items = []
        
        # Padrão para identificar seções de produto
        product_sections = re.split(r'\n(?=\d+\s+\d{4}\.?\d{2}\.?\d{2}\s+\d+)', text)
        
        for section in product_sections[1:]:  # Pular o primeiro que é cabeçalho
            item = self._parse_single_product(section)
            if item:
                items.append(item)
        
        return items
    
    def _parse_single_product(self, text: str) -> Optional[Dict]:
        """Parse de um único produto"""
        lines = text.split('\n')
        if len(lines) < 5:
            return None
        
        item = {}
        
        # Primeira linha contém NCM, código, etc.
        first_line_parts = lines[0].split()
        if len(first_line_parts) >= 4:
            item['item_num'] = first_line_parts[0]
            item['ncm'] = first_line_parts[1]
            item['codigo_produto'] = first_line_parts[2]
        
        # Nome do produto (normalmente na segunda linha)
        if len(lines) > 1:
            item['nome_produto'] = lines[1].strip()
        
        # Extrair informações específicas
        patterns = {
            'valor_unitario': r"Valor Unit Cond Venda ([\d\.,]+)",
            'valor_total': r"Valor Tot. Cond Venda ([\d\.,]+)",
            'peso_liquido': r"Peso Líquido \(KG\) ([\d\.,]+)",
            'quantidade': r"Qtde Unid. Comercial ([\d\.,]+)",
            'frete_internacional': r"Frete Internac. \(R\$\) ([\d\.,]+)",
            'seguro_internacional': r"Seguro Internac. \(R\$\) ([\d\.,]+)",
            'ii_devido': r"Valor Devido \(R\$\) ([\d\.,]+).*?SIM",
            'ipi_devido': r"Valor Devido \(R\$\) ([\d\.,]+).*?SIM.*?IPI",
            'pis_devido': r"Valor Devido \(R\$\) ([\d\.,]+).*?SIM.*?PIS",
            'cofins_devido': r"Valor Devido \(R\$\) ([\d\.,]+).*?SIM.*?COFINS"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace('.', '').replace(',', '.'))
                    item[key] = value
                except:
                    item[key] = 0
        
        return item if item else None
    
    def process_pdf(self, pdf_path: str):
        """Processa todo o PDF"""
        st.info("Processando PDF...")
        
        all_text = self.extract_text_from_pdf(pdf_path)
        if not all_text:
            return False
        
        full_text = "\n".join(all_text)
        
        # Executar todos os parsers
        self.parse_identification_section(full_text)
        self.parse_currency_rates(full_text)
        self.parse_summary_section(full_text)
        self.parse_tax_calculation(full_text)
        self.parse_transport_section(full_text)
        
        # Processar itens
        items = self.parse_product_items(full_text)
        self.data['itens'] = items
        
        return True

class FinancialAnalyzer:
    """Classe para análise financeira dos dados"""
    
    @staticmethod
    def calculate_totals(items: List[Dict]) -> Dict:
        """Calcula totais financeiros"""
        totals = {
            'valor_total_mercadoria': 0,
            'peso_total': 0,
            'quantidade_total': 0,
            'frete_total': 0,
            'seguro_total': 0,
            'ii_total': 0,
            'ipi_total': 0,
            'pis_total': 0,
            'cofins_total': 0,
            'custo_total': 0
        }
        
        for item in items:
            totals['valor_total_mercadoria'] += item.get('valor_total', 0)
            totals['peso_total'] += item.get('peso_liquido', 0)
            totals['quantidade_total'] += item.get('quantidade', 0)
            totals['frete_total'] += item.get('frete_internacional', 0)
            totals['seguro_total'] += item.get('seguro_internacional', 0)
            totals['ii_total'] += item.get('ii_devido', 0)
            totals['ipi_total'] += item.get('ipi_devido', 0)
            totals['pis_total'] += item.get('pis_devido', 0)
            totals['cofins_total'] += item.get('cofins_devido', 0)
        
        # Custo total = mercadoria + frete + seguro + tributos
        totals['custo_total'] = (
            totals['valor_total_mercadoria'] +
            totals['frete_total'] +
            totals['seguro_total'] +
            totals['ii_total'] +
            totals['ipi_total'] +
            totals['pis_total'] +
            totals['cofins_total']
        )
        
        return totals

class VisualizationGenerator:
    """Classe para geração de visualizações"""
    
    @staticmethod
    def create_tax_distribution_chart(totals: Dict):
        """Cria gráfico de distribuição de tributos"""
        tax_data = {
            'II': totals['ii_total'],
            'IPI': totals['ipi_total'],
            'PIS': totals['pis_total'],
            'COFINS': totals['cofins_total']
        }
        
        fig = px.pie(
            values=list(tax_data.values()),
            names=list(tax_data.keys()),
            title='Distribuição dos Tributos',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            height=400,
            showlegend=True,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        return fig
    
    @staticmethod
    def create_cost_breakdown_chart(totals: Dict):
        """Cria gráfico de breakdown de custos"""
        cost_data = {
            'Mercadoria': totals['valor_total_mercadoria'],
            'Frete': totals['frete_total'],
            'Seguro': totals['seguro_total'],
            'Tributos': totals['ii_total'] + totals['ipi_total'] + 
                       totals['pis_total'] + totals['cofins_total']
        }
        
        fig = px.bar(
            x=list(cost_data.keys()),
            y=list(cost_data.values()),
            title='Breakdown de Custos por Componente',
            color=list(cost_data.keys()),
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            xaxis_title='Componente',
            yaxis_title='Valor (R$)',
            height=400,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_top_products_chart(items: List[Dict], top_n: int = 10):
        """Cria gráfico dos produtos com maior valor"""
        # Ordenar por valor total
        sorted_items = sorted(items, key=lambda x: x.get('valor_total', 0), reverse=True)
        top_items = sorted_items[:top_n]
        
        product_names = [item.get('nome_produto', f"Produto {i}")[:30] + "..." 
                        for i, item in enumerate(top_items)]
        product_values = [item.get('valor_total', 0) for item in top_items]
        
        fig = px.bar(
            x=product_values,
            y=product_names,
            orientation='h',
            title=f'Top {top_n} Produtos por Valor',
            color=product_values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title='Valor Total (R$)',
            yaxis_title='Produto',
            height=500,
            showlegend=False
        )
        
        return fig

def main():
    """Função principal da aplicação"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">📊 Sistema de Análise de Extrato Häfele</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #EFF6FF; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
        <p style="margin: 0; color: #1E3A8A; font-size: 1.1rem;">
        Esta aplicação processa extratos de conferência da Häfele, extraindo informações financeiras,
        calculando tributos e gerando análises detalhadas para tomada de decisão.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para upload
    with st.sidebar:
        st.markdown("### 📁 Upload de Arquivo")
        uploaded_file = st.file_uploader(
            "Carregue o extrato PDF da Häfele",
            type=['pdf'],
            help="Faça upload do arquivo PDF no formato padrão da Häfele"
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ Configurações")
        
        analysis_options = st.multiselect(
            "Análises a realizar:",
            ["Resumo Financeiro", "Análise de Tributos", "Análise por Produto", 
             "Comparativo de Custos", "Exportar Dados"],
            default=["Resumo Financeiro", "Análise de Tributos"]
        )
        
        show_details = st.checkbox("Mostrar detalhes completos", value=True)
        st.markdown("---")
        
        st.markdown("### ℹ️ Sobre")
        st.info("""
        **Funcionalidades:**
        - Processamento automático de PDF
        - Cálculo de tributos (II, IPI, PIS, COFINS)
        - Análise de custos
        - Visualizações interativas
        - Exportação de dados
        """)
    
    # Processamento principal
    if uploaded_file is not None:
        try:
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Inicializar processador
            processor = HafelePDFProcessor()
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processar PDF
            status_text.text("Iniciando processamento...")
            progress_bar.progress(10)
            
            success = processor.process_pdf(tmp_path)
            
            if success:
                progress_bar.progress(40)
                status_text.text("Processando dados financeiros...")
                
                # Análise financeira
                analyzer = FinancialAnalyzer()
                totals = analyzer.calculate_totals(processor.data['itens'])
                
                progress_bar.progress(70)
                status_text.text("Gerando visualizações...")
                
                # Gerador de visualizações
                viz = VisualizationGenerator()
                
                progress_bar.progress(100)
                status_text.text("Processamento concluído!")
                
                # Limpar arquivo temporário
                os.unlink(tmp_path)
                
                # Exibir resultados
                st.success("✅ PDF processado com sucesso!")
                
                # Seção 1: Resumo Executivo
                if "Resumo Financeiro" in analysis_options:
                    st.markdown('<h2 class="sub-header">📈 Resumo Executivo</h2>', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">R$ {totals['custo_total']:,.2f}</div>
                            <div class="metric-label">Custo Total</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">R$ {totals['valor_total_mercadoria']:,.2f}</div>
                            <div class="metric-label">Valor Mercadoria</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">R$ {totals['ii_total'] + totals['ipi_total'] + totals['pis_total'] + totals['cofins_total']:,.2f}</div>
                            <div class="metric-label">Tributos Totais</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{len(processor.data['itens'])}</div>
                            <div class="metric-label">Itens Processados</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Seção 2: Análise de Tributos
                if "Análise de Tributos" in analysis_options:
                    st.markdown('<h2 class="sub-header">💰 Análise de Tributos</h2>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tabela de tributos
                        tax_df = pd.DataFrame({
                            'Tributo': ['II', 'IPI', 'PIS', 'COFINS', 'Total'],
                            'Valor (R$)': [
                                totals['ii_total'],
                                totals['ipi_total'],
                                totals['pis_total'],
                                totals['cofins_total'],
                                totals['ii_total'] + totals['ipi_total'] + totals['pis_total'] + totals['cofins_total']
                            ]
                        })
                        
                        tax_df['% do Total'] = (tax_df['Valor (R$)'] / tax_df['Valor (R$)'].iloc[-1] * 100).round(2)
                        
                        st.dataframe(
                            tax_df.style.format({
                                'Valor (R$)': 'R$ {:,.2f}',
                                '% do Total': '{:.2f}%'
                            }).background_gradient(subset=['Valor (R$)'], cmap='Blues'),
                            use_container_width=True
                        )
                    
                    with col2:
                        # Gráfico de distribuição
                        fig = viz.create_tax_distribution_chart(totals)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Seção 3: Análise por Produto
                if "Análise por Produto" in analysis_options:
                    st.markdown('<h2 class="sub-header">📦 Análise por Produto</h2>', unsafe_allow_html=True)
                    
                    # Gráfico top produtos
                    fig = viz.create_top_products_chart(processor.data['itens'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela detalhada
                    if show_details:
                        st.markdown("#### 📋 Detalhamento por Item")
                        
                        items_df = pd.DataFrame(processor.data['itens'])
                        if not items_df.empty:
                            # Selecionar e renomear colunas
                            display_cols = ['item_num', 'nome_produto', 'ncm', 'quantidade', 
                                          'peso_liquido', 'valor_total', 'frete_internacional',
                                          'ii_devido', 'ipi_devido']
                            
                            available_cols = [col for col in display_cols if col in items_df.columns]
                            items_display = items_df[available_cols].copy()
                            
                            # Renomear colunas
                            rename_map = {
                                'item_num': 'Item',
                                'nome_produto': 'Produto',
                                'ncm': 'NCM',
                                'quantidade': 'Quantidade',
                                'peso_liquido': 'Peso (kg)',
                                'valor_total': 'Valor (R$)',
                                'frete_internacional': 'Frete (R$)',
                                'ii_devido': 'II (R$)',
                                'ipi_devido': 'IPI (R$)'
                            }
                            
                            items_display = items_display.rename(columns=rename_map)
                            
                            # Formatação
                            st.dataframe(
                                items_display.style.format({
                                    'Quantidade': '{:,.2f}',
                                    'Peso (kg)': '{:,.2f}',
                                    'Valor (R$)': 'R$ {:,.2f}',
                                    'Frete (R$)': 'R$ {:,.2f}',
                                    'II (R$)': 'R$ {:,.2f}',
                                    'IPI (R$)': 'R$ {:,.2f}'
                                }),
                                use_container_width=True,
                                height=400
                            )
                
                # Seção 4: Comparativo de Custos
                if "Comparativo de Custos" in analysis_options:
                    st.markdown('<h2 class="sub-header">📊 Comparativo de Custos</h2>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de breakdown
                        fig = viz.create_cost_breakdown_chart(totals)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Métricas de eficiência
                        efficiency_metrics = {
                            'Tributos/Mercadoria': ((totals['ii_total'] + totals['ipi_total'] + 
                                                   totals['pis_total'] + totals['cofins_total']) / 
                                                   totals['valor_total_mercadoria'] * 100),
                            'Frete/Mercadoria': (totals['frete_total'] / totals['valor_total_mercadoria'] * 100),
                            'Custo por Kg': (totals['custo_total'] / totals['peso_total'] if totals['peso_total'] > 0 else 0),
                            'Custo por Item': (totals['custo_total'] / len(processor.data['itens']))
                        }
                        
                        efficiency_df = pd.DataFrame({
                            'Métrica': list(efficiency_metrics.keys()),
                            'Valor': list(efficiency_metrics.values())
                        })
                        
                        st.dataframe(
                            efficiency_df.style.format({
                                'Valor': lambda x: f'{x:.2f}%' if '%' in efficiency_df.loc[efficiency_df['Valor'] == x, 'Métrica'].iloc[0] 
                                                  else f'R$ {x:,.2f}'
                            }).bar(subset=['Valor'], color='#60A5FA'),
                            use_container_width=True
                        )
                
                # Seção 5: Exportação de Dados
                if "Exportar Dados" in analysis_options:
                    st.markdown('<h2 class="sub-header">💾 Exportação de Dados</h2>', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    # Preparar dados para exportação
                    summary_data = {
                        'Custo Total': totals['custo_total'],
                        'Valor Mercadoria': totals['valor_total_mercadoria'],
                        'Frete Total': totals['frete_total'],
                        'Seguro Total': totals['seguro_total'],
                        'II Total': totals['ii_total'],
                        'IPI Total': totals['ipi_total'],
                        'PIS Total': totals['pis_total'],
                        'COFINS Total': totals['cofins_total'],
                        'Peso Total': totals['peso_total'],
                        'Quantidade Total': totals['quantidade_total']
                    }
                    
                    summary_df = pd.DataFrame([summary_data])
                    items_df = pd.DataFrame(processor.data['itens'])
                    
                    with col1:
                        # Exportar resumo
                        csv_summary = summary_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar Resumo (CSV)",
                            data=csv_summary,
                            file_name="resumo_financeiro_hafele.csv",
                            mime="text/csv",
                            help="Baixar resumo financeiro em formato CSV"
                        )
                    
                    with col2:
                        # Exportar itens
                        if not items_df.empty:
                            csv_items = items_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Baixar Itens (CSV)",
                                data=csv_items,
                                file_name="itens_detalhados_hafele.csv",
                                mime="text/csv",
                                help="Baixar detalhamento de itens em formato CSV"
                            )
                    
                    with col3:
                        # Gerar relatório consolidado
                        st.info("Para relatório completo em PDF, entre em contato com o departamento financeiro.")
                
                # Seção 6: Informações Detalhadas (se habilitado)
                if show_details:
                    st.markdown('<h2 class="sub-header">🔍 Informações Detalhadas do Processamento</h2>', unsafe_allow_html=True)
                    
                    tab1, tab2, tab3 = st.tabs(["📋 Cabeçalho", "🚚 Transporte", "📊 Estatísticas"])
                    
                    with tab1:
                        if processor.data['cabecalho']:
                            st.json(processor.data['cabecalho'], expanded=False)
                    
                    with tab2:
                        if processor.data['transportes']:
                            st.json(processor.data['transportes'], expanded=False)
                    
                    with tab3:
                        stats = {
                            'Total de Itens Processados': len(processor.data['itens']),
                            'Itens com Tributos Calculados': sum(1 for item in processor.data['itens'] 
                                                                if 'ii_devido' in item),
                            'Valor Médio por Item': totals['custo_total'] / len(processor.data['itens']) 
                                                    if processor.data['itens'] else 0,
                            'Peso Médio por Item': totals['peso_total'] / len(processor.data['itens']) 
                                                  if processor.data['itens'] else 0
                        }
                        
                        for key, value in stats.items():
                            st.metric(label=key, value=f"{value:,.2f}")
            
            else:
                st.error("Falha no processamento do PDF. Verifique se o formato está correto.")
        
        except Exception as e:
            st.error(f"Erro durante o processamento: {str(e)}")
            st.exception(e)
    
    else:
        # Tela inicial quando não há arquivo
        st.info("👈 Faça upload de um arquivo PDF no menu lateral para começar a análise.")
        
        # Exemplo de layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🚀 Como usar:
            1. Faça upload do PDF no menu lateral
            2. Selecione as análises desejadas
            3. Configure as opções de visualização
            4. Explore os resultados e exporte os dados
            
            ### 📋 Formato esperado:
            - PDF no layout padrão Häfele
            - Extrato de conferência de importação
            - Com informações de tributos e valores
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Análises disponíveis:
            
            **Resumo Financeiro**
            - Custo total da operação
            - Breakdown de valores
            - Métricas principais
            
            **Análise de Tributos**
            - Distribuição por tipo
            - Impacto no custo total
            - Comparativos
            
            **Análise por Produto**
            - Top produtos por valor
            - Detalhamento completo
            - Análise de rentabilidade
            
            **Exportação de Dados**
            - CSV para análise externa
            - Relatórios customizados
            - Integração com outros sistemas
            """)

if __name__ == "__main__":
    main()
