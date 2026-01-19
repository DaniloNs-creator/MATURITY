import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
import re
import json
from typing import Dict, List, Tuple, Optional, Any
import tempfile
import os
from dataclasses import dataclass
from collections import defaultdict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Sistema Completo de Análise Häfele",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E3A8A;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #E5E7EB;
        padding-bottom: 0.5rem;
        font-weight: 600;
    }
    .section-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #E5E7EB;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E3A8A;
        line-height: 1;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
        margin-top: 0.5rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

class HafelePDFParser:
    """Parser robusto para PDFs da Häfele"""
    
    def __init__(self):
        self.documento = {
            'cabecalho': {},
            'itens': [],
            'totais': {}
        }
        
    def parse_pdf(self, pdf_path: str) -> Dict:
        """Parse completo do PDF"""
        try:
            logger.info(f"Iniciando parsing do PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF com {total_pages} páginas")
                
                all_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Processando página {page_num}/{total_pages}")
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            # Processar todo o texto
            self._process_full_text(all_text)
            
            logger.info(f"Parsing concluído. {len(self.documento['itens'])} itens processados.")
            return self.documento
            
        except Exception as e:
            logger.error(f"Erro no parsing: {str(e)}")
            raise
    
    def _process_full_text(self, text: str):
        """Processa todo o texto do PDF"""
        # Encontrar todos os itens
        items = self._find_all_items(text)
        self.documento['itens'] = items
        
        # Calcular totais
        self._calculate_totals()
    
    def _find_all_items(self, text: str) -> List[Dict]:
        """Encontra todos os itens no texto"""
        items = []
        
        # Padrão para encontrar início de itens
        # Procurando: número_item NCM código (ex: "1 3926.30.00 123")
        item_pattern = r'(\d+)\s+(\d{4}\.\d{2}\.\d{2})\s+(\d+)\s'
        matches = list(re.finditer(item_pattern, text))
        
        logger.info(f"Encontrados {len(matches)} padrões de itens")
        
        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            item_text = text[start_pos:end_pos]
            item_data = self._parse_item(item_text, match.group(1), match.group(2), match.group(3))
            
            if item_data:
                items.append(item_data)
        
        return items
    
    def _parse_item(self, text: str, item_num: str, ncm: str, codigo: str) -> Optional[Dict]:
        """Parse de um item individual"""
        try:
            item = {
                'numero_item': item_num,
                'ncm': ncm,
                'codigo_produto': codigo,
                'nome_produto': '',
                'codigo_interno': '',
                'quantidade': 0,
                'peso_liquido': 0,
                'valor_unitario': 0,
                'valor_total': 0,
                'frete_internacional': 0,
                'seguro_internacional': 0,
                'ii_valor_devido': 0,
                'ipi_valor_devido': 0,
                'pis_valor_devido': 0,
                'cofins_valor_devido': 0,
                'total_impostos': 0,
                'valor_total_com_impostos': 0
            }
            
            # Extrair nome do produto
            nome_match = re.search(r'DENOMINACAO DO PRODUTO\s*\n(.+?)\n', text, re.IGNORECASE)
            if nome_match:
                item['nome_produto'] = nome_match.group(1).strip()
            
            # Extrair código interno
            codigo_match = re.search(r'Código interno\s+(.+?)\n', text, re.IGNORECASE)
            if codigo_match:
                item['codigo_interno'] = codigo_match.group(1).strip()
            
            # Extrair quantidade
            qtd_match = re.search(r'Qtde Unid\. Comercial\s+([\d\.,]+)', text)
            if qtd_match:
                item['quantidade'] = self._parse_valor(qtd_match.group(1))
            
            # Extrair peso
            peso_match = re.search(r'Peso Líquido \(KG\)\s+([\d\.,]+)', text)
            if peso_match:
                item['peso_liquido'] = self._parse_valor(peso_match.group(1))
            
            # Extrair valor unitário
            valor_unit_match = re.search(r'Valor Unit Cond Venda\s+([\d\.,]+)', text)
            if valor_unit_match:
                item['valor_unitario'] = self._parse_valor(valor_unit_match.group(1))
            
            # Extrair valor total
            valor_total_match = re.search(r'Valor Tot\. Cond Venda\s+([\d\.,]+)', text)
            if valor_total_match:
                item['valor_total'] = self._parse_valor(valor_total_match.group(1))
            
            # Extrair frete
            frete_match = re.search(r'Frete Internac\. \(R\$\)\s+([\d\.,]+)', text)
            if frete_match:
                item['frete_internacional'] = self._parse_valor(frete_match.group(1))
            
            # Extrair seguro
            seguro_match = re.search(r'Seguro Internac\. \(R\$\)\s+([\d\.,]+)', text)
            if seguro_match:
                item['seguro_internacional'] = self._parse_valor(seguro_match.group(1))
            
            # Extrair impostos - MÉTODO DIRETO E ROBUSTO
            item = self._extract_taxes_directly(text, item)
            
            # Calcular totais
            item['total_impostos'] = (
                item['ii_valor_devido'] + 
                item['ipi_valor_devido'] + 
                item['pis_valor_devido'] + 
                item['cofins_valor_devido']
            )
            
            item['valor_total_com_impostos'] = item['valor_total'] + item['total_impostos']
            
            return item
            
        except Exception as e:
            logger.error(f"Erro ao parsear item {item_num}: {str(e)}")
            return None
    
    def _extract_taxes_directly(self, text: str, item: Dict) -> Dict:
        """Extrai impostos diretamente do texto"""
        # Método 1: Buscar padrões específicos
        patterns = {
            'ii_valor_devido': r'II.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'ipi_valor_devido': r'IPI.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'pis_valor_devido': r'PIS.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'cofins_valor_devido': r'COFINS.*?Valor Devido \(R\$\)\s*([\d\.,]+)'
        }
        
        # Método 2: Buscar todas as ocorrências de "Valor Devido"
        valor_devido_pattern = r'Valor Devido \(R\$\)\s*([\d\.,]+)'
        valor_devido_matches = list(re.finditer(valor_devido_pattern, text))
        
        # Se encontrou os valores, atribuir na ordem
        if len(valor_devido_matches) >= 4:
            item['ii_valor_devido'] = self._parse_valor(valor_devido_matches[0].group(1))
            item['ipi_valor_devido'] = self._parse_valor(valor_devido_matches[1].group(1))
            item['pis_valor_devido'] = self._parse_valor(valor_devido_matches[2].group(1))
            item['cofins_valor_devido'] = self._parse_valor(valor_devido_matches[3].group(1))
        
        # Método 3: Buscar por cada imposto individualmente
        else:
            for tax_key, pattern in patterns.items():
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    item[tax_key] = self._parse_valor(match.group(1))
        
        # Método 4: Buscar por valores próximos aos nomes dos impostos
        if item['pis_valor_devido'] == 0:
            item['pis_valor_devido'] = self._find_tax_near_text(text, 'PIS')
        
        if item['cofins_valor_devido'] == 0:
            item['cofins_valor_devido'] = self._find_tax_near_text(text, 'COFINS')
        
        return item
    
    def _find_tax_near_text(self, text: str, tax_name: str) -> float:
        """Encontra valor de imposto próximo ao nome"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if tax_name in line.upper():
                # Procurar números nas próximas 5 linhas
                for j in range(i, min(i + 5, len(lines))):
                    # Padrão para valores monetários
                    valor_match = re.search(r'([\d\.,]+)\s*$', lines[j])
                    if valor_match:
                        return self._parse_valor(valor_match.group(1))
        
        return 0.0
    
    def _calculate_totals(self):
        """Calcula totais do documento"""
        totais = {
            'valor_total_mercadoria': 0,
            'peso_total': 0,
            'quantidade_total': 0,
            'ii_total': 0,
            'ipi_total': 0,
            'pis_total': 0,
            'cofins_total': 0,
            'total_impostos': 0,
            'frete_total': 0,
            'seguro_total': 0
        }
        
        for item in self.documento['itens']:
            totais['valor_total_mercadoria'] += item.get('valor_total', 0)
            totais['peso_total'] += item.get('peso_liquido', 0)
            totais['quantidade_total'] += item.get('quantidade', 0)
            totais['ii_total'] += item.get('ii_valor_devido', 0)
            totais['ipi_total'] += item.get('ipi_valor_devido', 0)
            totais['pis_total'] += item.get('pis_valor_devido', 0)
            totais['cofins_total'] += item.get('cofins_valor_devido', 0)
            totais['total_impostos'] += item.get('total_impostos', 0)
            totais['frete_total'] += item.get('frete_internacional', 0)
            totais['seguro_total'] += item.get('seguro_internacional', 0)
        
        totais['valor_total_com_impostos'] = (
            totais['valor_total_mercadoria'] + 
            totais['total_impostos']
        )
        
        self.documento['totais'] = totais
    
    def _parse_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            if not valor_str or valor_str.strip() == '':
                return 0.0
            
            # Remover pontos de milhar e converter vírgula decimal
            valor_limpo = valor_str.replace('.', '').replace(',', '.')
            return float(valor_limpo)
        except:
            return 0.0

class FinancialAnalyzer:
    """Analisador financeiro simples"""
    
    def __init__(self, documento: Dict):
        self.documento = documento
        self.itens_df = None
        
    def prepare_dataframe(self):
        """Prepara DataFrame para análise"""
        itens_data = []
        
        for item in self.documento['itens']:
            itens_data.append({
                'Item': item.get('numero_item', ''),
                'NCM': item.get('ncm', ''),
                'Código': item.get('codigo_produto', ''),
                'Código Interno': item.get('codigo_interno', ''),
                'Produto': item.get('nome_produto', ''),
                'Quantidade': item.get('quantidade', 0),
                'Peso (kg)': item.get('peso_liquido', 0),
                'Valor Unit. (R$)': item.get('valor_unitario', 0),
                'Valor Total (R$)': item.get('valor_total', 0),
                'Frete (R$)': item.get('frete_internacional', 0),
                'Seguro (R$)': item.get('seguro_internacional', 0),
                'II (R$)': item.get('ii_valor_devido', 0),
                'IPI (R$)': item.get('ipi_valor_devido', 0),
                'PIS (R$)': item.get('pis_valor_devido', 0),
                'COFINS (R$)': item.get('cofins_valor_devido', 0),
                'Total Impostos (R$)': item.get('total_impostos', 0),
                'Valor c/ Impostos (R$)': item.get('valor_total_com_impostos', 0),
                'Custo Unitário (R$)': item.get('valor_total_com_impostos', 0) / item.get('quantidade', 1) if item.get('quantidade', 0) > 0 else 0
            })
        
        self.itens_df = pd.DataFrame(itens_data)
        return self.itens_df

def main():
    """Função principal"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">🏭 Sistema de Análise de Extratos Häfele</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-card">
        <strong>🔍 Extração Simplificada e Robusta</strong><br>
        Sistema focado em extrair todos os dados dos itens, incluindo impostos PIS e COFINS.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Upload do Documento")
        
        uploaded_file = st.file_uploader(
            "Selecione o arquivo PDF",
            type=['pdf'],
            help="Documento PDF no formato padrão Häfele"
        )
        
        st.markdown("---")
        
        if uploaded_file:
            file_size = uploaded_file.size / (1024 * 1024)
            st.info(f"📄 Arquivo: {uploaded_file.name}")
            st.success(f"📊 Tamanho: {file_size:.2f} MB")
        else:
            st.warning("⏳ Aguardando upload do arquivo")
    
    # Processamento principal
    if uploaded_file is not None:
        try:
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Etapa 1: Parsing
            status_text.text("📄 Analisando documento PDF...")
            progress_bar.progress(30)
            
            parser = HafelePDFParser()
            documento = parser.parse_pdf(tmp_path)
            
            # Etapa 2: Análise
            status_text.text("📊 Processando dados...")
            progress_bar.progress(60)
            
            analyser = FinancialAnalyzer(documento)
            df = analyser.prepare_dataframe()
            
            progress_bar.progress(100)
            status_text.text("✅ Processamento concluído!")
            
            # Limpar arquivo
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            # Informações do processamento
            totais = documento['totais']
            st.success(f"✅ **{len(documento['itens'])} itens** extraídos com sucesso!")
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="section-card">
                    <div class="metric-value">R$ {totais.get('valor_total_mercadoria', 0):,.2f}</div>
                    <div class="metric-label">Valor Mercadoria</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="section-card">
                    <div class="metric-value">R$ {totais.get('total_impostos', 0):,.2f}</div>
                    <div class="metric-label">Total Impostos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="section-card">
                    <div class="metric-value">R$ {totais.get('pis_total', 0):,.2f}</div>
                    <div class="metric-label">Total PIS</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="section-card">
                    <div class="metric-value">R$ {totais.get('cofins_total', 0):,.2f}</div>
                    <div class="metric-label">Total COFINS</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tabela de itens
            st.markdown('<h2 class="sub-header">📦 Lista de Itens</h2>', unsafe_allow_html=True)
            
            # Filtros simples
            search_term = st.text_input("🔍 Buscar por produto ou código:", "")
            
            if search_term:
                filtered_df = df[
                    df['Produto'].str.contains(search_term, case=False, na=False) |
                    df['Código Interno'].astype(str).str.contains(search_term, case=False, na=False) |
                    df['Código'].astype(str).str.contains(search_term, case=False, na=False)
                ]
            else:
                filtered_df = df
            
            # Formatar valores
            display_df = filtered_df.copy()
            
            # Formatar colunas numéricas
            format_cols = ['Quantidade', 'Peso (kg)', 'Valor Unit. (R$)', 'Valor Total (R$)',
                         'Frete (R$)', 'Seguro (R$)', 'II (R$)', 'IPI (R$)',
                         'PIS (R$)', 'COFINS (R$)', 'Total Impostos (R$)',
                         'Valor c/ Impostos (R$)', 'Custo Unitário (R$)']
            
            for col in format_cols:
                if col in display_df.columns:
                    if 'Unitário' in col or 'Unit.' in col:
                        display_df[col] = display_df[col].apply(lambda x: f'R$ {x:,.4f}' if pd.notnull(x) else 'R$ 0,0000')
                    else:
                        display_df[col] = display_df[col].apply(lambda x: f'R$ {x:,.2f}' if pd.notnull(x) else 'R$ 0,00')
            
            # Exibir tabela
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600
            )
            
            # Estatísticas de extração
            zero_pis = (df['PIS (R$)'] == 0).sum()
            zero_cofins = (df['COFINS (R$)'] == 0).sum()
            
            if zero_pis > 0 or zero_cofins > 0:
                st.warning(f"""
                ⚠️ **Atenção:** Alguns impostos não foram extraídos completamente:
                - {zero_pis} itens sem valor de PIS
                - {zero_cofins} itens sem valor de COFINS
                """)
            
            # Exportação
            st.markdown('<h2 class="sub-header">💾 Exportação</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv_data,
                    file_name="itens_hafele.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Excel
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Itens', index=False)
                
                st.download_button(
                    label="📊 Baixar Excel",
                    data=output.getvalue(),
                    file_name="itens_hafele.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Resumo por NCM
            st.markdown('<h2 class="sub-header">🏷️ Análise por NCM</h2>', unsafe_allow_html=True)
            
            if not df.empty:
                ncm_analysis = df.groupby('NCM').agg({
                    'Quantidade': 'sum',
                    'Valor Total (R$)': 'sum',
                    'Total Impostos (R$)': 'sum'
                }).reset_index()
                
                ncm_analysis = ncm_analysis.sort_values('Valor Total (R$)', ascending=False)
                
                st.dataframe(
                    ncm_analysis,
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
    
    else:
        # Tela inicial
        st.markdown("""
        <div class="section-card">
            <h3>🚀 Sistema de Extração Häfele</h3>
            <p>Este sistema extrai todos os dados dos itens de extratos da Häfele, incluindo:</p>
            
            <ul>
                <li><strong>Códigos e descrições</strong> dos produtos</li>
                <li><strong>Quantidades e pesos</strong></li>
                <li><strong>Valores</strong> (unitário e total)</li>
                <li><strong>Impostos</strong> (II, IPI, PIS, COFINS)</li>
            </ul>
            
            <h4>📋 Como usar:</h4>
            <ol>
                <li>Faça upload do PDF no menu lateral</li>
                <li>Aguarde o processamento</li>
                <li>Explore os resultados na tabela</li>
                <li>Exporte os dados para análise</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
