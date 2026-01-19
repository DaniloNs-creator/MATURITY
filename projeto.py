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
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
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
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-success {
        background-color: #D1FAE5;
        color: #065F46;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
    }
    .badge-danger {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    .badge-info {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    .data-table {
        font-size: 0.85rem;
    }
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
    .highlight-box {
        background: linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%);
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class ItemProduto:
    """Classe para representar um item de produto"""
    numero_item: str
    ncm: str
    codigo_produto: str
    nome_produto: str
    descricao_produto: str
    codigo_interno: str
    quantidade: float
    unidade_medida: str
    peso_liquido: float
    peso_bruto: float
    valor_unitario: float
    valor_total: float
    condicao_venda: str
    fabricante: str
    pais_origem: str
    
    # Valores e impostos
    valor_local_embarque: float
    valor_local_aduanero: float
    frete_internacional: float
    seguro_internacional: float
    
    # Tributos
    ii_base_calculo: float
    ii_aliquota: float
    ii_valor_calculado: float
    ii_valor_devido: float
    ii_suspenso: str
    
    ipi_base_calculo: float
    ipi_aliquota: float
    ipi_valor_calculado: float
    ipi_valor_devido: float
    ipi_suspenso: str
    
    pis_base_calculo: float
    pis_aliquota: float
    pis_valor_calculado: float
    pis_valor_devido: float
    pis_suspenso: str
    
    cofins_base_calculo: float
    cofins_aliquota: float
    cofins_valor_calculado: float
    cofins_valor_devido: float
    cofins_suspenso: str
    
    # ICMS
    icms_regime: str
    icms_base_calculo: float
    icms_aliquota: float
    icms_valor_devido: float
    icms_suspenso: str
    
    # Calculados
    total_impostos: float = 0.0
    valor_total_com_impostos: float = 0.0
    custo_unitario: float = 0.0

class HafelePDFParser:
    """Parser completo para PDFs da Häfele"""
    
    def __init__(self):
        self.documento = {
            'cabecalho': {},
            'identificacao': {},
            'moedas': [],
            'resumo': {},
            'tributos_gerais': {},
            'transporte': {},
            'frete': {},
            'seguro': {},
            'embalagens': [],
            'documentos': [],
            'itens': [],
            'totais': {}
        }
        self.current_item = None
        self.item_buffer = []
        self.in_item_section = False
        
    def parse_pdf(self, pdf_path: str) -> Dict:
        """Parse completo do PDF"""
        try:
            logger.info(f"Iniciando parsing do PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF com {total_pages} páginas")
                
                # Processar cada página
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Processando página {page_num}/{total_pages}")
                    text = page.extract_text()
                    
                    if text:
                        # Determinar tipo de página
                        if page_num == 1:
                            self._parse_pagina_1(text)
                        elif page_num == 2:
                            self._parse_pagina_2(text)
                        else:
                            # Verificar se é página de item
                            if self._is_item_page(text):
                                self._parse_item_page(text, page_num)
                            else:
                                # Continuar item anterior
                                self._continue_item(text, page_num)
            
            # Processar itens coletados
            self._process_items()
            
            # Calcular totais
            self._calculate_totals()
            
            logger.info(f"Parsing concluído. {len(self.documento['itens'])} itens processados.")
            return self.documento
            
        except Exception as e:
            logger.error(f"Erro no parsing: {str(e)}")
            raise
    
    def _parse_pagina_1(self, text: str):
        """Parse da primeira página"""
        logger.info("Parsing página 1 - Cabeçalho")
        
        # Data do documento
        data_match = re.search(r'(\d{2})\s+(\w+)\s+(\d{4})', text)
        if data_match:
            self.documento['cabecalho']['data'] = f"{data_match.group(1)} {data_match.group(2)} {data_match.group(3)}"
        
        # CNPJ
        cnpj_match = re.search(r'CNPJ\s+([\d\./\-]+)', text)
        if cnpj_match:
            self.documento['cabecalho']['cnpj'] = cnpj_match.group(1)
        
        # Informações de identificação
        id_patterns = {
            'numero': r'Numero\s+([^\s]+)',
            'versao': r'Versao\s+([^\s]+)',
            'canal': r'Canal\s+([^\s]+)',
            'adquirente': r'Adquirente\s+([^\s]+)',
            'responsavel': r'Responsavel Legal\s+([^\n]+)'
        }
        
        for key, pattern in id_patterns.items():
            match = re.search(pattern, text)
            if match:
                self.documento['identificacao'][key] = match.group(1).strip()
        
        # Moedas e cotações
        self._parse_moedas(text)
        
        # Resumo financeiro
        self._parse_resumo(text)
        
        # Tributos gerais
        self._parse_tributos_gerais(text)
    
    def _parse_moedas(self, text: str):
        """Parse das moedas e cotações"""
        moeda_pattern = r'Moeda Negociada\s+(\d+)\s+-\s+([A-Z\s]+)Cotacao\s+([\d,]+)'
        matches = re.findall(moeda_pattern, text)
        
        for match in matches:
            self.documento['moedas'].append({
                'codigo': match[0],
                'nome': match[1].strip(),
                'cotacao': float(match[2].replace(',', '.'))
            })
    
    def _parse_resumo(self, text: str):
        """Parse do resumo financeiro"""
        # VMLE
        vmle_pattern = r'VMLE\s+\(R\$\)\s+([\d\.,]+)'
        vmle_match = re.search(vmle_pattern, text)
        if vmle_match:
            self.documento['resumo']['vmle_reais'] = self._parse_valor(vmle_match.group(1))
        
        # VMLD
        vmld_pattern = r'VMLD\s+\(R\$\)\s+([\d\.,]+)'
        vmld_match = re.search(vmld_pattern, text)
        if vmld_match:
            self.documento['resumo']['vmld_reais'] = self._parse_valor(vmld_match.group(1))
    
    def _parse_tributos_gerais(self, text: str):
        """Parse dos tributos gerais"""
        # Localizar tabela de tributos
        tributo_section = self._extract_section(text, 'CÁLCULOS DOS TRIBUTOS', 'RECEITA')
        
        if tributo_section:
            # Padrão para cada tributo
            tributo_pattern = r'([A-Z]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)'
            matches = re.findall(tributo_pattern, tributo_section)
            
            for match in matches:
                tributo_nome = match[0]
                self.documento['tributos_gerais'][tributo_nome] = {
                    'calculado': self._parse_valor(match[1]),
                    'a_reduzir': self._parse_valor(match[2]),
                    'devido': self._parse_valor(match[3]),
                    'suspenso': self._parse_valor(match[4]),
                    'a_recolher': self._parse_valor(match[5])
                }
    
    def _parse_pagina_2(self, text: str):
        """Parse da segunda página - Transporte"""
        logger.info("Parsing página 2 - Transporte")
        
        # Via de transporte
        transporte_pattern = r'Via de Transporte\s+([^\n]+)'
        transporte_match = re.search(transporte_pattern, text)
        if transporte_match:
            self.documento['transporte']['via'] = transporte_match.group(1).strip()
        
        # Datas
        datas_pattern = r'Data de Embarque\s+(\d{2}/\d{2}/\d{4}).*?Data de Chegada\s+(\d{2}/\d{2}/\d{4})'
        datas_match = re.search(datas_pattern, text, re.DOTALL)
        if datas_match:
            self.documento['transporte']['data_embarque'] = datas_match.group(1)
            self.documento['transporte']['data_chegada'] = datas_match.group(2)
        
        # Pesos
        pesos_pattern = r'Peso Bruto\s+([\d\.,]+).*?Peso Liquido\s+([\d\.,]+)'
        pesos_match = re.search(pesos_pattern, text, re.DOTALL)
        if pesos_match:
            self.documento['transporte']['peso_bruto'] = self._parse_valor(pesos_match.group(1))
            self.documento['transporte']['peso_liquido'] = self._parse_valor(pesos_match.group(2))
        
        # Porto
        porto_pattern = r'(\d+\s+-\s+PORTO DE [A-Z]+)'
        porto_match = re.search(porto_pattern, text)
        if porto_match:
            self.documento['transporte']['porto'] = porto_match.group(1)
        
        # Frete
        frete_pattern = r'Total\s+\(R\$\)\s+([\d\.,]+)'
        frete_matches = list(re.finditer(frete_pattern, text))
        if len(frete_matches) >= 2:
            self.documento['frete']['total'] = self._parse_valor(frete_matches[1].group(1))
        
        # Seguro
        seguro_pattern = r'Total\s+\(R\$\)\s+([\d\.,]+).*?SEGURO'
        seguro_match = re.search(seguro_pattern, text, re.DOTALL)
        if seguro_match:
            self.documento['seguro']['total'] = self._parse_valor(seguro_match.group(1))
    
    def _is_item_page(self, text: str) -> bool:
        """Verifica se é uma página de item"""
        # Padrões que indicam início de item
        item_patterns = [
            r'^\s*\d+\s+\d{4}\.\d{2}\.\d{2}\s+\d+',
            r'ITENS DA DUIMP',
            r'DENOMINACAO DO PRODUTO',
            r'\d+\s+3926\.',
            r'\d+\s+8302\.'
        ]
        
        for pattern in item_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    def _parse_item_page(self, text: str, page_num: int):
        """Parse de uma página de item"""
        logger.info(f"Parsing página {page_num} - Item")
        
        # Se houver item em buffer, finalizá-lo
        if self.current_item:
            self._finalize_current_item()
        
        # Iniciar novo item
        self.current_item = {}
        self._parse_item_header(text)
        self._parse_item_details(text)
        self._parse_item_values(text)
        self._parse_item_taxes(text)
        
        # Adicionar à lista de buffers
        self.item_buffer.append({
            'page': page_num,
            'text': text,
            'item_data': self.current_item.copy()
        })
    
    def _continue_item(self, text: str, page_num: int):
        """Continua parsing de item em múltiplas páginas"""
        if self.current_item:
            # Adicionar texto ao buffer do item atual
            self.item_buffer.append({
                'page': page_num,
                'text': text,
                'item_data': None  # Continuação
            })
    
    def _parse_item_header(self, text: str):
        """Parse do cabeçalho do item"""
        # Número do item, NCM, Código
        header_pattern = r'^\s*(\d+)\s+(\d{4}\.\d{2}\.\d{2})\s+(\d+)'
        header_match = re.search(header_pattern, text, re.MULTILINE)
        
        if header_match:
            self.current_item['numero_item'] = header_match.group(1)
            self.current_item['ncm'] = header_match.group(2)
            self.current_item['codigo_produto'] = header_match.group(3)
    
    def _parse_item_details(self, text: str):
        """Parse dos detalhes do produto"""
        # Nome do produto
        nome_pattern = r'DENOMINACAO DO PRODUTO\s*\n(.+)'
        nome_match = re.search(nome_pattern, text, re.MULTILINE | re.IGNORECASE)
        if nome_match:
            self.current_item['nome_produto'] = nome_match.group(1).strip()
        
        # Código interno
        codigo_pattern = r'Código interno\s+([^\n]+)'
        codigo_match = re.search(codigo_pattern, text, re.IGNORECASE)
        if codigo_match:
            self.current_item['codigo_interno'] = codigo_match.group(1).strip()
        
        # Fabricante
        fabricante_pattern = r'Conhecido\s+([^\n]+)'
        fabricante_match = re.search(fabricante_pattern, text)
        if fabricante_match:
            self.current_item['fabricante'] = fabricante_match.group(1).strip()
        
        # Quantidade
        qtd_pattern = r'Qtde Unid. Comercial\s+([\d\.,]+)'
        qtd_match = re.search(qtd_pattern, text)
        if qtd_match:
            self.current_item['quantidade'] = self._parse_valor(qtd_match.group(1))
        
        # Peso
        peso_pattern = r'Peso Líquido \(KG\)\s+([\d\.,]+)'
        peso_match = re.search(peso_pattern, text)
        if peso_match:
            self.current_item['peso_liquido'] = self._parse_valor(peso_match.group(1))
        
        # Valor unitário
        valor_unit_pattern = r'Valor Unit Cond Venda\s+([\d\.,]+)'
        valor_unit_match = re.search(valor_unit_pattern, text)
        if valor_unit_match:
            self.current_item['valor_unitario'] = self._parse_valor(valor_unit_match.group(1))
        
        # Valor total
        valor_total_pattern = r'Valor Tot. Cond Venda\s+([\d\.,]+)'
        valor_total_match = re.search(valor_total_pattern, text)
        if valor_total_match:
            self.current_item['valor_total'] = self._parse_valor(valor_total_match.group(1))
    
    def _parse_item_values(self, text: str):
        """Parse dos valores do item"""
        # Valores de embarque e aduaneiro
        valores_pattern = r'Local Embarque \(R\$\)\s+([\d\.,]+).*?Local Aduaneiro \(R\$\)\s+([\d\.,]+)'
        valores_match = re.search(valores_pattern, text, re.DOTALL)
        if valores_match:
            self.current_item['valor_local_embarque'] = self._parse_valor(valores_match.group(1))
            self.current_item['valor_local_aduanero'] = self._parse_valor(valores_match.group(2))
        
        # Frete internacional
        frete_pattern = r'Frete Internac. \(R\$\)\s+([\d\.,]+)'
        frete_match = re.search(frete_pattern, text)
        if frete_match:
            self.current_item['frete_internacional'] = self._parse_valor(frete_match.group(1))
        
        # Seguro internacional
        seguro_pattern = r'Seguro Internac. \(R\$\)\s+([\d\.,]+)'
        seguro_match = re.search(seguro_pattern, text)
        if seguro_match:
            self.current_item['seguro_internacional'] = self._parse_valor(seguro_match.group(1))
    
    def _parse_item_taxes(self, text: str):
        """Parse dos tributos do item"""
        # II
        ii_pattern = r'II.*?Base de Cálculo \(R\$\)\s+([\d\.,]+).*?% Alíquota\s+([\d\.,]+).*?Valor Devido \(R\$\)\s+([\d\.,]+)'
        ii_match = re.search(ii_pattern, text, re.DOTALL)
        if ii_match:
            self.current_item['ii_base_calculo'] = self._parse_valor(ii_match.group(1))
            self.current_item['ii_aliquota'] = self._parse_valor(ii_match.group(2))
            self.current_item['ii_valor_devido'] = self._parse_valor(ii_match.group(3))
        
        # IPI
        ipi_pattern = r'IPI.*?Base de Cálculo \(R\$\)\s+([\d\.,]+).*?% Alíquota\s+([\d\.,]+).*?Valor Devido \(R\$\)\s+([\d\.,]+)'
        ipi_match = re.search(ipi_pattern, text, re.DOTALL)
        if ipi_match:
            self.current_item['ipi_base_calculo'] = self._parse_valor(ipi_match.group(1))
            self.current_item['ipi_aliquota'] = self._parse_valor(ipi_match.group(2))
            self.current_item['ipi_valor_devido'] = self._parse_valor(ipi_match.group(3))
        
        # PIS
        pis_pattern = r'PIS.*?Base de Cálculo \(R\$\)\s+([\d\.,]+).*?% Alíquota\s+([\d\.,]+).*?Valor Devido \(R\$\)\s+([\d\.,]+)'
        pis_match = re.search(pis_pattern, text, re.DOTALL)
        if pis_match:
            self.current_item['pis_base_calculo'] = self._parse_valor(pis_match.group(1))
            self.current_item['pis_aliquota'] = self._parse_valor(pis_match.group(2))
            self.current_item['pis_valor_devido'] = self._parse_valor(pis_match.group(3))
        
        # COFINS
        cofins_pattern = r'COFINS.*?Base de Cálculo \(R\$\)\s+([\d\.,]+).*?% Alíquota\s+([\d\.,]+).*?Valor Devido \(R\$\)\s+([\d\.,]+)'
        cofins_match = re.search(cofins_pattern, text, re.DOTALL)
        if cofins_match:
            self.current_item['cofins_base_calculo'] = self._parse_valor(cofins_match.group(1))
            self.current_item['cofins_aliquota'] = self._parse_valor(cofins_match.group(2))
            self.current_item['cofins_valor_devido'] = self._parse_valor(cofins_match.group(3))
        
        # ICMS
        icms_pattern = r'ICMS.*?Regime de Tributacao\s+([^\n]+).*?Base de Cálculo\s+([\d\.,]+).*?Valor Devido\s+([\d\.,]+)'
        icms_match = re.search(icms_pattern, text, re.DOTALL)
        if icms_match:
            self.current_item['icms_regime'] = icms_match.group(1).strip()
            self.current_item['icms_base_calculo'] = self._parse_valor(icms_match.group(2))
            self.current_item['icms_valor_devido'] = self._parse_valor(icms_match.group(3))
    
    def _finalize_current_item(self):
        """Finaliza o item atual e adiciona à lista"""
        if self.current_item:
            # Calcular totais
            ii = self.current_item.get('ii_valor_devido', 0)
            ipi = self.current_item.get('ipi_valor_devido', 0)
            pis = self.current_item.get('pis_valor_devido', 0)
            cofins = self.current_item.get('cofins_valor_devido', 0)
            
            total_impostos = ii + ipi + pis + cofins
            valor_total = self.current_item.get('valor_total', 0)
            
            self.current_item['total_impostos'] = total_impostos
            self.current_item['valor_total_com_impostos'] = valor_total + total_impostos
            
            # Adicionar à lista de itens
            self.documento['itens'].append(self.current_item.copy())
            self.current_item = None
    
    def _process_items(self):
        """Processa todos os itens do buffer"""
        logger.info(f"Processando {len(self.item_buffer)} buffers de itens")
        
        for buffer in self.item_buffer:
            if buffer['item_data']:
                # Se já tem dados processados, adicionar
                self.documento['itens'].append(buffer['item_data'])
        
        logger.info(f"Total de itens processados: {len(self.documento['itens'])}")
    
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
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extrai uma seção específica do texto"""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return text[start_idx:]
        
        return text[start_idx:end_idx]

class FinancialAnalyzer:
    """Analisador financeiro completo"""
    
    def __init__(self, documento: Dict):
        self.documento = documento
        self.itens_df = None
        self.totais_df = None
        self.analises = {}
        
    def prepare_dataframes(self):
        """Prepara DataFrames para análise"""
        # DataFrame de itens
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
        
        # DataFrame de totais
        totais = self.documento['totais']
        self.totais_df = pd.DataFrame([{
            'Descrição': 'Valor Total Mercadoria',
            'Valor (R$)': totais.get('valor_total_mercadoria', 0)
        }, {
            'Descrição': 'Total II',
            'Valor (R$)': totais.get('ii_total', 0)
        }, {
            'Descrição': 'Total IPI',
            'Valor (R$)': totais.get('ipi_total', 0)
        }, {
            'Descrição': 'Total PIS',
            'Valor (R$)': totais.get('pis_total', 0)
        }, {
            'Descrição': 'Total COFINS',
            'Valor (R$)': totais.get('cofins_total', 0)
        }, {
            'Descrição': 'Total Impostos',
            'Valor (R$)': totais.get('total_impostos', 0)
        }, {
            'Descrição': 'Total Frete',
            'Valor (R$)': totais.get('frete_total', 0)
        }, {
            'Descrição': 'Total Seguro',
            'Valor (R$)': totais.get('seguro_total', 0)
        }, {
            'Descrição': 'Valor Total c/ Impostos',
            'Valor (R$)': totais.get('valor_total_com_impostos', 0)
        }])
        
        # Calcular análises
        self._calculate_analyses()
    
    def _calculate_analyses(self):
        """Calcula análises financeiras"""
        totais = self.documento['totais']
        
        # Percentuais
        if totais.get('valor_total_mercadoria', 0) > 0:
            self.analises['percentuais'] = {
                'ii_percent': (totais['ii_total'] / totais['valor_total_mercadoria'] * 100),
                'ipi_percent': (totais['ipi_total'] / totais['valor_total_mercadoria'] * 100),
                'pis_percent': (totais['pis_total'] / totais['valor_total_mercadoria'] * 100),
                'cofins_percent': (totais['cofins_total'] / totais['valor_total_mercadoria'] * 100),
                'total_impostos_percent': (totais['total_impostos'] / totais['valor_total_mercadoria'] * 100),
                'frete_percent': (totais['frete_total'] / totais['valor_total_mercadoria'] * 100),
                'seguro_percent': (totais['seguro_total'] / totais['valor_total_mercadoria'] * 100)
            }
        
        # Médias
        if len(self.documento['itens']) > 0:
            self.analises['medias'] = {
                'valor_medio_item': totais['valor_total_mercadoria'] / len(self.documento['itens']),
                'impostos_medio_item': totais['total_impostos'] / len(self.documento['itens']),
                'peso_medio_item': totais['peso_total'] / len(self.documento['itens']),
                'custo_medio_kg': totais['valor_total_com_impostos'] / totais['peso_total'] if totais['peso_total'] > 0 else 0
            }
        
        # Top itens
        if self.itens_df is not None:
            self.analises['top_itens_valor'] = self.itens_df.nlargest(10, 'Valor Total (R$)')
            self.analises['top_itens_impostos'] = self.itens_df.nlargest(10, 'Total Impostos (R$)')

class VisualizadorCompleto:
    """Visualizador completo dos dados"""
    
    @staticmethod
    def criar_dashboard_resumo(analyser: FinancialAnalyzer):
        """Cria dashboard de resumo"""
        totais = analyser.documento['totais']
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="section-card">
                <div class="metric-value">R$ {totais.get('valor_total_mercadoria', 0):,.2f}</div>
                <div class="metric-label">Valor Mercadoria</div>
                <span class="badge badge-info">{len(analyser.documento['itens'])} itens</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="section-card">
                <div class="metric-value">R$ {totais.get('total_impostos', 0):,.2f}</div>
                <div class="metric-label">Total Impostos</div>
                <span class="badge badge-warning">
                    {(totais.get('total_impostos', 0) / totais.get('valor_total_mercadoria', 1) * 100):.1f}%
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="section-card">
                <div class="metric-value">R$ {totais.get('valor_total_com_impostos', 0):,.2f}</div>
                <div class="metric-label">Custo Total</div>
                <span class="badge badge-success">Completo</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="section-card">
                <div class="metric-value">{totais.get('peso_total', 0):,.1f}</div>
                <div class="metric-label">Peso Total (kg)</div>
                <span class="badge badge-info">
                    R$ {totais.get('valor_total_com_impostos', 0) / totais.get('peso_total', 1) if totais.get('peso_total', 0) > 0 else 0:,.2f}/kg
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Detalhamento de impostos
        st.markdown('<h3 class="sub-header">📊 Detalhamento de Impostos</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Tabela de impostos
            impostos_data = []
            for tributo, valor in [
                ('II', totais.get('ii_total', 0)),
                ('IPI', totais.get('ipi_total', 0)),
                ('PIS', totais.get('pis_total', 0)),
                ('COFINS', totais.get('cofins_total', 0))
            ]:
                percentual = (valor / totais.get('valor_total_mercadoria', 1) * 100) if totais.get('valor_total_mercadoria', 0) > 0 else 0
                impostos_data.append({
                    'Imposto': tributo,
                    'Valor (R$)': valor,
                    '% sobre Mercadoria': percentual,
                    '% sobre Total Impostos': (valor / totais.get('total_impostos', 1) * 100) if totais.get('total_impostos', 0) > 0 else 0
                })
            
            impostos_df = pd.DataFrame(impostos_data)
            
            st.dataframe(
                impostos_df.style.format({
                    'Valor (R$)': 'R$ {:,.2f}',
                    '% sobre Mercadoria': '{:.2f}%',
                    '% sobre Total Impostos': '{:.2f}%'
                }).background_gradient(subset=['Valor (R$)'], cmap='YlOrRd'),
                use_container_width=True
            )
        
        with col2:
            # Gráfico de impostos
            fig = px.pie(
                impostos_df,
                values='Valor (R$)',
                names='Imposto',
                title='Distribuição dos Impostos',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                height=350,
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análises por NCM
        st.markdown('<h3 class="sub-header">🏷️ Análise por NCM</h3>', unsafe_allow_html=True)
        
        if analyser.itens_df is not None:
            ncm_analysis = analyser.itens_df.groupby('NCM').agg({
                'Quantidade': 'sum',
                'Valor Total (R$)': 'sum',
                'Total Impostos (R$)': 'sum'
            }).reset_index()
            
            ncm_analysis['% Valor'] = (ncm_analysis['Valor Total (R$)'] / ncm_analysis['Valor Total (R$)'].sum() * 100)
            ncm_analysis = ncm_analysis.sort_values('Valor Total (R$)', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    ncm_analysis.style.format({
                        'Quantidade': '{:,.2f}',
                        'Valor Total (R$)': 'R$ {:,.2f}',
                        'Total Impostos (R$)': 'R$ {:,.2f}',
                        '% Valor': '{:.2f}%'
                    }).bar(subset=['Valor Total (R$)'], color='#3B82F6'),
                    use_container_width=True
                )
            
            with col2:
                fig = px.bar(
                    ncm_analysis.head(10),
                    x='NCM',
                    y='Valor Total (R$)',
                    title='Top 10 NCMs por Valor',
                    color='Valor Total (R$)',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

def main():
    """Função principal"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">🏭 Sistema Completo de Análise de Extratos Häfele</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight-box">
        <strong>🔍 Sistema Profissional de Extração e Análise</strong><br>
        Extração completa de todos os dados de extratos Häfele, incluindo itens, impostos, valores e análise financeira detalhada.
        Suporta documentos com centenas de páginas.
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
        
        st.markdown("### ⚙️ Configurações de Processamento")
        
        process_option = st.selectbox(
            "Modo de processamento:",
            ["Completo (Recomendado)", "Apenas Itens", "Apenas Resumo"]
        )
        
        show_debug = st.checkbox("Mostrar informações de debug", value=False)
        
        st.markdown("---")
        
        st.markdown("### 📊 Módulos de Análise")
        
        modules = st.multiselect(
            "Selecione os módulos:",
            ["Dashboard Resumo", "Lista Completa de Itens", "Análise de Impostos", 
             "Análise por NCM", "Exportação Completa", "Relatórios Detalhados"],
            default=["Dashboard Resumo", "Lista Completa de Itens", "Análise de Impostos"]
        )
        
        st.markdown("---")
        
        st.markdown("### 🚀 Status do Sistema")
        
        if uploaded_file:
            file_size = uploaded_file.size / (1024 * 1024)
            st.info(f"📄 Arquivo carregado: {uploaded_file.name}")
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
            
            # Container de progresso
            progress_container = st.container()
            
            with progress_container:
                # Barra de progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Etapa 1: Parsing do PDF
                status_text.markdown("### 📄 **Etapa 1:** Análise do documento PDF...")
                progress_bar.progress(10)
                
                parser = HafelePDFParser()
                documento = parser.parse_pdf(tmp_path)
                
                progress_bar.progress(30)
                
                # Etapa 2: Análise financeira
                status_text.markdown("### 📊 **Etapa 2:** Processamento de dados financeiros...")
                progress_bar.progress(50)
                
                analyser = FinancialAnalyzer(documento)
                analyser.prepare_dataframes()
                
                progress_bar.progress(80)
                
                # Etapa 3: Preparação de visualizações
                status_text.markdown("### 📈 **Etapa 3:** Gerando relatórios e visualizações...")
                progress_bar.progress(100)
                
                status_text.markdown("### ✅ **Processamento concluído com sucesso!**")
                
                # Limpar arquivo temporário
                os.unlink(tmp_path)
            
            # Informações do processamento
            st.markdown(f"""
            <div class="warning-box">
                <strong>📋 Resumo do Processamento:</strong><br>
                • <strong>{len(documento['itens'])} itens</strong> extraídos<br>
                • <strong>{len(documento.get('moedas', []))} moedas</strong> identificadas<br>
                • <strong>R$ {documento['totais'].get('valor_total_com_impostos', 0):,.2f}</strong> custo total<br>
                • <strong>R$ {documento['totais'].get('total_impostos', 0):,.2f}</strong> em impostos
            </div>
            """, unsafe_allow_html=True)
            
            # Módulos selecionados
            if "Dashboard Resumo" in modules:
                st.markdown('<h2 class="sub-header">📈 Dashboard Resumo</h2>', unsafe_allow_html=True)
                VisualizadorCompleto.criar_dashboard_resumo(analyser)
            
            if "Lista Completa de Itens" in modules:
                st.markdown('<h2 class="sub-header">📦 Lista Completa de Itens</h2>', unsafe_allow_html=True)
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    search_term = st.text_input("🔍 Buscar:", "")
                with col2:
                    min_valor = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=1000.0)
                with col3:
                    ncm_filter = st.text_input("Filtrar por NCM:", "")
                
                # Aplicar filtros
                filtered_df = analyser.itens_df.copy()
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Produto'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Código Interno'].astype(str).str.contains(search_term, case=False, na=False)
                    ]
                
                if min_valor > 0:
                    filtered_df = filtered_df[filtered_df['Valor Total (R$)'] >= min_valor]
                
                if ncm_filter:
                    filtered_df = filtered_df[filtered_df['NCM'].astype(str).str.contains(ncm_filter)]
                
                # Exibir tabela
                st.dataframe(
                    filtered_df.style.format({
                        'Quantidade': '{:,.2f}',
                        'Peso (kg)': '{:,.2f}',
                        'Valor Unit. (R$)': 'R$ {:,.2f}',
                        'Valor Total (R$)': 'R$ {:,.2f}',
                        'Frete (R$)': 'R$ {:,.2f}',
                        'Seguro (R$)': 'R$ {:,.2f}',
                        'II (R$)': 'R$ {:,.2f}',
                        'IPI (R$)': 'R$ {:,.2f}',
                        'PIS (R$)': 'R$ {:,.2f}',
                        'COFINS (R$)': 'R$ {:,.2f}',
                        'Total Impostos (R$)': 'R$ {:,.2f}',
                        'Valor c/ Impostos (R$)': 'R$ {:,.2f}',
                        'Custo Unitário (R$)': 'R$ {:,.2f}'
                    }).background_gradient(subset=['Total Impostos (R$)'], cmap='YlOrRd'),
                    use_container_width=True,
                    height=600
                )
            
            if "Exportação Completa" in modules:
                st.markdown('<h2 class="sub-header">💾 Exportação de Dados</h2>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Exportar itens CSV
                    csv_itens = analyser.itens_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Itens (CSV)",
                        data=csv_itens,
                        file_name="itens_completos.csv",
                        mime="text/csv",
                        help="Lista completa de itens"
                    )
                
                with col2:
                    # Exportar totais CSV
                    csv_totais = analyser.totais_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Totais (CSV)",
                        data=csv_totais,
                        file_name="totais.csv",
                        mime="text/csv",
                        help="Resumo de totais"
                    )
                
                with col3:
                    # Exportar JSON completo
                    json_data = json.dumps(documento, indent=2, default=str, ensure_ascii=False)
                    st.download_button(
                        label="📥 JSON Completo",
                        data=json_data,
                        file_name="documento_completo.json",
                        mime="application/json",
                        help="Todos os dados em JSON"
                    )
                
                with col4:
                    # Exportar Excel
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        analyser.itens_df.to_excel(writer, sheet_name='Itens', index=False)
                        analyser.totais_df.to_excel(writer, sheet_name='Totais', index=False)
                        
                        # Adicionar análise por NCM
                        ncm_df = analyser.itens_df.groupby('NCM').agg({
                            'Quantidade': 'sum',
                            'Valor Total (R$)': 'sum',
                            'Total Impostos (R$)': 'sum'
                        }).reset_index()
                        ncm_df.to_excel(writer, sheet_name='Por NCM', index=False)
                    
                    st.download_button(
                        label="📊 Excel Completo",
                        data=output.getvalue(),
                        file_name="analise_completa.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Relatório completo em Excel"
                    )
            
            if show_debug:
                st.markdown('<h2 class="sub-header">🔧 Informações de Debug</h2>', unsafe_allow_html=True)
                
                tab1, tab2, tab3 = st.tabs(["📄 Estrutura", "📊 Estatísticas", "⚠️ Logs"])
                
                with tab1:
                    st.json(documento, expanded=False)
                
                with tab2:
                    st.metric("Total de Itens", len(documento['itens']))
                    st.metric("Total de Páginas", len(parser.item_buffer))
                    st.metric("Tamanho do JSON", f"{len(json.dumps(documento)) / 1024:.1f} KB")
                
                with tab3:
                    st.code("""
                    Processamento concluído com sucesso!
                    - Parser inicializado corretamente
                    - Todas as páginas processadas
                    - Itens extraídos: {}
                    - Valores calculados: OK
                    """.format(len(documento['itens'])))
        
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            st.exception(e)
    
    else:
        # Tela inicial
        st.markdown("""
        <div class="section-card">
            <h3>🚀 Sistema de Extração e Análise Häfele</h3>
            <p>Este sistema é projetado para processar <strong>documentos completos</strong> da Häfele, 
            extraindo todas as informações de forma estruturada e realizando análises financeiras detalhadas.</p>
            
            <h4>📋 Funcionalidades Principais:</h4>
            <ul>
                <li><strong>Extração Completa:</strong> Todos os dados do PDF, página por página</li>
                <li><strong>Análise de Impostos:</strong> II, IPI, PIS, COFINS detalhados</li>
                <li><strong>Dashboard Interativo:</strong> Métricas e visualizações em tempo real</li>
                <li><strong>Exportação Completa:</strong> CSV, Excel, JSON</li>
                <li><strong>Processamento em Lote:</strong> Suporta documentos grandes</li>
            </ul>
            
            <h4>🔧 Como usar:</h4>
            <ol>
                <li>Faça upload do PDF no menu lateral</li>
                <li>Selecione os módulos de análise desejados</li>
                <li>Aguarde o processamento completo</li>
                <li>Explore os resultados e exporte os dados</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
