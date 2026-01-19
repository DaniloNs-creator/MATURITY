import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional
import tempfile
import os

# Configuração da página
st.set_page_config(
    page_title="Extrator de Itens Häfele",
    page_icon="📋",
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
    .tax-highlight {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .product-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

class HafeleItemExtractor:
    """Classe especializada para extrair itens e impostos de PDFs da Häfele"""
    
    def __init__(self):
        self.items = []
        self.summary = {}
        
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto"""
        # Substituir múltiplos espaços por um único espaço
        text = re.sub(r'\s+', ' ', text)
        # Remover caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        return text.strip()
    
    def extract_all_pages_text(self, pdf_path: str) -> str:
        """Extrai texto de todas as páginas do PDF"""
        all_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        cleaned_text = self.clean_text(text)
                        all_text.append(cleaned_text)
            return "\n".join(all_text)
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return ""
    
    def find_item_sections(self, text: str) -> List[str]:
        """Encontra seções de itens no texto"""
        # Padrão para identificar início de itens (número de item + NCM)
        # Procurando padrões como "1 3926.30.00" ou "1 3926.30.00 123"
        item_pattern = r'\n(\d+)\s+(\d{4}\.\d{2}\.\d{2})\s+(\d+)'
        
        matches = list(re.finditer(item_pattern, text))
        item_sections = []
        
        for i, match in enumerate(matches):
            start_pos = match.start()
            
            # Determinar fim da seção (próximo item ou fim do texto)
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            item_section = text[start_pos:end_pos].strip()
            item_sections.append(item_section)
        
        return item_sections
    
    def extract_item_info(self, section_text: str) -> Optional[Dict]:
        """Extrai informações de um único item"""
        lines = section_text.split('\n')
        if len(lines) < 2:
            return None
        
        item = {}
        
        # Extrair número do item, NCM e código
        first_line = lines[0]
        first_parts = first_line.split()
        
        if len(first_parts) >= 3:
            item['item_num'] = first_parts[0]
            item['ncm'] = first_parts[1]
            item['codigo_produto'] = first_parts[2]
        
        # Encontrar nome do produto
        for i, line in enumerate(lines[1:], 1):
            if 'DENOMINACAO DO PRODUTO' in line and i + 1 < len(lines):
                # Próxima linha é o nome do produto
                item['nome_produto'] = lines[i + 1].strip()
                break
            elif line and not any(keyword in line for keyword in 
                                 ['CÓDIGO INTERNO', 'FABRICANTE', 'CARACTERIZAÇÃO']):
                # Linha pode ser o nome do produto
                item['nome_produto'] = line.strip()
                break
        
        # Encontrar código interno
        for line in lines:
            if 'CÓDIGO INTERNO' in line or 'Código interno' in line:
                # Procurar código no formato 24980198 - 100 - 637.45.344
                cod_pattern = r'(\d+\s*-\s*\d+\s*-\s*\d+\.\d+\.\d+)'
                cod_match = re.search(cod_pattern, line)
                if cod_match:
                    item['codigo_interno'] = cod_match.group(1)
                else:
                    # Tentar pegar texto após "Código interno"
                    parts = line.split('Código interno')
                    if len(parts) > 1:
                        item['codigo_interno'] = parts[1].strip()
                break
        
        # Extrair quantidade e peso
        for line in lines:
            if 'Qtde Unid. Comercial' in line:
                qty_match = re.search(r'([\d\.,]+)', line)
                if qty_match:
                    item['quantidade'] = float(qty_match.group(1).replace('.', '').replace(',', '.'))
            
            if 'Peso Líquido (KG)' in line:
                peso_match = re.search(r'([\d\.,]+)', line)
                if peso_match:
                    item['peso_liquido'] = float(peso_match.group(1).replace('.', '').replace(',', '.'))
        
        # Extrair valores
        for line in lines:
            if 'Valor Tot. Cond Venda' in line:
                valor_match = re.search(r'([\d\.,]+)', line)
                if valor_match:
                    item['valor_total'] = float(valor_match.group(1).replace('.', '').replace(',', '.'))
        
        # Extrair impostos - método mais robusto
        self._extract_taxes(item, section_text)
        
        return item if 'nome_produto' in item else None
    
    def _extract_taxes(self, item: Dict, text: str):
        """Extrai valores de impostos do texto"""
        # Limpar texto para facilitar busca
        clean_tax_text = re.sub(r'\s+', ' ', text)
        
        # Padrões para cada imposto
        tax_patterns = {
            'ii_devido': r'II.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'ipi_devido': r'IPI.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'pis_devido': r'PIS.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'cofins_devido': r'COFINS.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'icms_devido': r'ICMS.*?Valor Devido \(R\$\)\s*([\d\.,]+)'
        }
        
        for tax_key, pattern in tax_patterns.items():
            match = re.search(pattern, clean_tax_text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace('.', '').replace(',', '.'))
                    item[tax_key] = value
                except:
                    item[tax_key] = 0.0
            else:
                item[tax_key] = 0.0
        
        # Calcular total de impostos
        item['total_impostos'] = sum([
            item.get('ii_devido', 0),
            item.get('ipi_devido', 0),
            item.get('pis_devido', 0),
            item.get('cofins_devido', 0),
            item.get('icms_devido', 0)
        ])
        
        # Calcular valor total com impostos
        if 'valor_total' in item:
            item['valor_total_com_impostos'] = item['valor_total'] + item['total_impostos']
    
    def extract_summary_info(self, text: str):
        """Extrai informações de resumo do documento"""
        summary = {}
        
        # Extrair VMLE (Valor da Mercadoria no Local de Embarque)
        vmle_pattern = r'VMLE \(R\$\)\s*([\d\.,]+)'
        vmle_match = re.search(vmle_pattern, text)
        if vmle_match:
            summary['vmle_reais'] = float(vmle_match.group(1).replace('.', '').replace(',', '.'))
        
        # Extrair totais de impostos da seção de resumo
        tax_summary_patterns = {
            'ii_total': r'II\s+([\d\.,]+)\s+[\d\.,]+\s+[\d\.,]+\s+[\d\.,]+\s+([\d\.,]+)',
            'ipi_total': r'IPI\s+([\d\.,]+)\s+[\d\.,]+\s+[\d\.,]+\s+[\d\.,]+\s+([\d\.,]+)',
            'pis_total': r'PIS\s+([\d\.,]+)\s+[\d\.,]+\s+[\d\.,]+\s+[\d\.,]+\s+([\d\.,]+)',
            'cofins_total': r'COFINS\s+([\d\.,]+)\s+[\d\.,]+\s+[\d\.,]+\s+[\d\.,]+\s+([\d\.,]+)'
        }
        
        for tax_key, pattern in tax_summary_patterns.items():
            match = re.search(pattern, text)
            if match:
                try:
                    summary[tax_key] = float(match.group(2).replace('.', '').replace(',', '.'))
                except:
                    summary[tax_key] = 0.0
        
        self.summary = summary
    
    def process_pdf(self, pdf_path: str) -> bool:
        """Processa o PDF e extrai informações dos itens"""
        try:
            # Extrair texto completo
            full_text = self.extract_all_pages_text(pdf_path)
            if not full_text:
                return False
            
            # Extrair informações de resumo
            self.extract_summary_info(full_text)
            
            # Encontrar e processar seções de itens
            item_sections = self.find_item_sections(full_text)
            
            for section in item_sections:
                item_info = self.extract_item_info(section)
                if item_info:
                    self.items.append(item_info)
            
            return len(self.items) > 0
            
        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
            return False

class ItemVisualizer:
    """Classe para visualização dos itens extraídos"""
    
    @staticmethod
    def create_item_summary(items: List[Dict]) -> pd.DataFrame:
        """Cria resumo dos itens em DataFrame"""
        summary_data = []
        
        for item in items:
            summary_data.append({
                'Item': item.get('item_num', ''),
                'Código': item.get('codigo_produto', ''),
                'Código Interno': item.get('codigo_interno', ''),
                'Produto': item.get('nome_produto', '')[:50] + ('...' if len(item.get('nome_produto', '')) > 50 else ''),
                'NCM': item.get('ncm', ''),
                'Quantidade': item.get('quantidade', 0),
                'Peso (kg)': item.get('peso_liquido', 0),
                'Valor (R$)': item.get('valor_total', 0),
                'II (R$)': item.get('ii_devido', 0),
                'IPI (R$)': item.get('ipi_devido', 0),
                'PIS (R$)': item.get('pis_devido', 0),
                'COFINS (R$)': item.get('cofins_devido', 0),
                'Total Impostos (R$)': item.get('total_impostos', 0),
                'Valor c/ Impostos (R$)': item.get('valor_total_com_impostos', 0)
            })
        
        return pd.DataFrame(summary_data)
    
    @staticmethod
    def create_tax_summary(items: List[Dict]) -> Dict:
        """Cria resumo de impostos"""
        totals = {
            'valor_total_mercadoria': sum(item.get('valor_total', 0) for item in items),
            'ii_total': sum(item.get('ii_devido', 0) for item in items),
            'ipi_total': sum(item.get('ipi_devido', 0) for item in items),
            'pis_total': sum(item.get('pis_devido', 0) for item in items),
            'cofins_total': sum(item.get('cofins_devido', 0) for item in items),
            'total_impostos': sum(item.get('total_impostos', 0) for item in items)
        }
        
        totals['valor_total_com_impostos'] = totals['valor_total_mercadoria'] + totals['total_impostos']
        
        if totals['valor_total_mercadoria'] > 0:
            totals['percentual_impostos'] = (totals['total_impostos'] / totals['valor_total_mercadoria'] * 100)
        else:
            totals['percentual_impostos'] = 0
        
        return totals
    
    @staticmethod
    def create_tax_chart(totals: Dict):
        """Cria gráfico de impostos"""
        tax_data = {
            'II': totals['ii_total'],
            'IPI': totals['ipi_total'],
            'PIS': totals['pis_total'],
            'COFINS': totals['cofins_total']
        }
        
        fig = px.pie(
            values=list(tax_data.values()),
            names=list(tax_data.keys()),
            title='Distribuição dos Impostos',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label+value')
        fig.update_layout(
            height=400,
            showlegend=True,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        return fig

def main():
    """Função principal da aplicação"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">📋 Extrator de Itens e Impostos - Häfele</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #EFF6FF; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
        <p style="margin: 0; color: #1E3A8A; font-size: 1.1rem;">
        Esta aplicação extrai especificamente as informações dos itens e seus impostos de extratos da Häfele.
        Foco em: <strong>Códigos, Descrições e Valores de Impostos</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Upload do Arquivo")
        uploaded_file = st.file_uploader(
            "Carregue o extrato PDF da Häfele",
            type=['pdf'],
            help="Faça upload do arquivo PDF no formato padrão da Häfele"
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ Opções de Extração")
        
        show_raw_data = st.checkbox("Mostrar dados brutos extraídos", value=False)
        group_by_ncm = st.checkbox("Agrupar por NCM", value=True)
        
        st.markdown("---")
        
        st.markdown("### ℹ️ Informações Extraídas")
        st.info("""
        **Por item:**
        - Código e descrição
        - NCM e código interno
        - Quantidade e peso
        - Valores de impostos:
          • II • IPI • PIS • COFINS
        - Totais calculados
        """)
    
    # Processamento principal
    if uploaded_file is not None:
        try:
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Inicializar extrator
            extractor = HafeleItemExtractor()
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Processar PDF
            status_text.text("📄 Lendo arquivo PDF...")
            progress_bar.progress(20)
            
            success = extractor.process_pdf(tmp_path)
            
            if success:
                progress_bar.progress(60)
                status_text.text("📊 Processando itens e impostos...")
                
                # Visualizar dados
                visualizer = ItemVisualizer()
                items_df = visualizer.create_item_summary(extractor.items)
                tax_totals = visualizer.create_tax_summary(extractor.items)
                
                progress_bar.progress(100)
                status_text.text("✅ Processamento concluído!")
                
                # Limpar arquivo temporário
                os.unlink(tmp_path)
                
                # Exibir resultados
                st.success(f"✅ **{len(extractor.items)} itens** extraídos com sucesso!")
                
                # Seção 1: Resumo de Impostos
                st.markdown('<h2 class="sub-header">💰 Resumo de Impostos</h2>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">R$ {tax_totals['valor_total_mercadoria']:,.2f}</div>
                        <div class="metric-label">Valor Mercadoria</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">R$ {tax_totals['total_impostos']:,.2f}</div>
                        <div class="metric-label">Total Impostos</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">R$ {tax_totals['valor_total_com_impostos']:,.2f}</div>
                        <div class="metric-label">Valor Total</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{tax_totals['percentual_impostos']:.1f}%</div>
                        <div class="metric-label">% Impostos</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Tabela detalhada de impostos
                st.markdown("#### 📋 Detalhamento por Tipo de Imposto")
                
                tax_detail_df = pd.DataFrame({
                    'Imposto': ['II', 'IPI', 'PIS', 'COFINS', 'TOTAL'],
                    'Valor (R$)': [
                        tax_totals['ii_total'],
                        tax_totals['ipi_total'],
                        tax_totals['pis_total'],
                        tax_totals['cofins_total'],
                        tax_totals['total_impostos']
                    ],
                    '% do Total': [
                        (tax_totals['ii_total'] / tax_totals['total_impostos'] * 100) if tax_totals['total_impostos'] > 0 else 0,
                        (tax_totals['ipi_total'] / tax_totals['total_impostos'] * 100) if tax_totals['total_impostos'] > 0 else 0,
                        (tax_totals['pis_total'] / tax_totals['total_impostos'] * 100) if tax_totals['total_impostos'] > 0 else 0,
                        (tax_totals['cofins_total'] / tax_totals['total_impostos'] * 100) if tax_totals['total_impostos'] > 0 else 0,
                        100.0
                    ]
                })
                
                st.dataframe(
                    tax_detail_df.style.format({
                        'Valor (R$)': 'R$ {:,.2f}',
                        '% do Total': '{:.1f}%'
                    }).background_gradient(subset=['Valor (R$)'], cmap='YlOrBr'),
                    use_container_width=True
                )
                
                # Gráfico de impostos
                fig = visualizer.create_tax_chart(tax_totals)
                st.plotly_chart(fig, use_container_width=True)
                
                # Seção 2: Lista de Itens
                st.markdown('<h2 class="sub-header">📦 Itens Extraídos</h2>', unsafe_allow_html=True)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    search_term = st.text_input("🔍 Buscar por produto ou código:", "")
                with col2:
                    min_value = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=100.0)
                
                # Aplicar filtros
                filtered_df = items_df.copy()
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Produto'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Código'].astype(str).str.contains(search_term, case=False, na=False) |
                        filtered_df['Código Interno'].astype(str).str.contains(search_term, case=False, na=False)
                    ]
                
                if min_value > 0:
                    filtered_df = filtered_df[filtered_df['Valor (R$)'] >= min_value]
                
                # Exibir tabela
                st.dataframe(
                    filtered_df.style.format({
                        'Quantidade': '{:,.2f}',
                        'Peso (kg)': '{:,.2f}',
                        'Valor (R$)': 'R$ {:,.2f}',
                        'II (R$)': 'R$ {:,.2f}',
                        'IPI (R$)': 'R$ {:,.2f}',
                        'PIS (R$)': 'R$ {:,.2f}',
                        'COFINS (R$)': 'R$ {:,.2f}',
                        'Total Impostos (R$)': 'R$ {:,.2f}',
                        'Valor c/ Impostos (R$)': 'R$ {:,.2f}'
                    }).background_gradient(subset=['Total Impostos (R$)'], cmap='YlOrRd'),
                    use_container_width=True,
                    height=600
                )
                
                # Seção 3: Exportação
                st.markdown('<h2 class="sub-header">💾 Exportação de Dados</h2>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Exportar itens
                    csv_items = items_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Itens (CSV)",
                        data=csv_items,
                        file_name="itens_hafele.csv",
                        mime="text/csv",
                        help="Baixar todos os itens em formato CSV"
                    )
                
                with col2:
                    # Exportar resumo de impostos
                    tax_summary_df = pd.DataFrame([tax_totals])
                    csv_taxes = tax_summary_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Resumo Impostos (CSV)",
                        data=csv_taxes,
                        file_name="resumo_impostos_hafele.csv",
                        mime="text/csv",
                        help="Baixar resumo de impostos em formato CSV"
                    )
                
                with col3:
                    # Exportar em Excel
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        items_df.to_excel(writer, sheet_name='Itens', index=False)
                        tax_summary_df.to_excel(writer, sheet_name='Resumo Impostos', index=False)
                    
                    st.download_button(
                        label="📥 Baixar Excel Completo",
                        data=output.getvalue(),
                        file_name="extracao_hafele.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Baixar todos os dados em Excel"
                    )
                
                # Seção 4: Dados brutos (opcional)
                if show_raw_data:
                    st.markdown('<h2 class="sub-header">🔍 Dados Brutos Extraídos</h2>', unsafe_allow_html=True)
                    
                    tab1, tab2 = st.tabs(["📊 Estrutura dos Dados", "📄 Texto Processado"])
                    
                    with tab1:
                        st.json(extractor.items[:3] if extractor.items else {}, expanded=False)
                        st.caption(f"Exibindo 3 de {len(extractor.items)} itens")
                    
                    with tab2:
                        st.text_area(
                            "Texto extraído (amostra)",
                            value=extractor.extract_all_pages_text(tmp_path)[:5000] if os.path.exists(tmp_path) else "",
                            height=300
                        )
            
            else:
                st.error("Não foi possível extrair itens do PDF. Verifique o formato do arquivo.")
        
        except Exception as e:
            st.error(f"Erro durante o processamento: {str(e)}")
            st.code(str(e), language='python')
    
    else:
        # Tela inicial
        st.info("👈 Faça upload de um arquivo PDF no menu lateral para extrair itens e impostos.")
        
        # Exemplo de layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 **Foco da Extração:**
            
            **1. Informações dos Itens:**
            - Código do produto
            - Código interno
            - Descrição completa
            - NCM
            - Quantidade e peso
            
            **2. Valores de Impostos:**
            - II (Imposto de Importação)
            - IPI (Imposto sobre Produtos Industrializados)
            - PIS (Programação de Integração Social)
            - COFINS (Contribuição para o Financiamento da Seguridade Social)
            """)
        
        with col2:
            st.markdown("""
            ### 📈 **Análises Geradas:**
            
            **Resumo Financeiro:**
            - Totais por tipo de imposto
            - Percentuais sobre valor da mercadoria
            - Valor total com impostos
            
            **Visualizações:**
            - Gráfico de distribuição de impostos
            - Tabela interativa de itens
            - Filtros por valor e busca
            
            **Exportação:**
            - CSV para análise externa
            - Excel com múltiplas planilhas
            - Dados estruturados
            """)

if __name__ == "__main__":
    main()
