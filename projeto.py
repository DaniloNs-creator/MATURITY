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
    .dataframe-container {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E5E7EB;
        margin: 1rem 0;
    }
    .tax-highlight {
        background-color: #FEF3C7;
        padding: 8px;
        border-radius: 4px;
        border-left: 3px solid #F59E0B;
        margin: 2px 0;
    }
</style>
""", unsafe_allow_html=True)

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
        self.current_item = {}
        self.item_buffer = []
        self.current_page_num = 0
        
    def parse_pdf(self, pdf_path: str) -> Dict:
        """Parse completo do PDF"""
        try:
            logger.info(f"Iniciando parsing do PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF com {total_pages} páginas")
                
                # Processar cada página
                for page_num, page in enumerate(pdf.pages, 1):
                    self.current_page_num = page_num
                    logger.info(f"Processando página {page_num}/{total_pages}")
                    text = page.extract_text()
                    
                    if text:
                        # Limpar e normalizar texto
                        text = self._clean_text(text)
                        
                        # Determinar tipo de página
                        if page_num == 1:
                            self._parse_pagina_1(text)
                        elif page_num == 2:
                            self._parse_pagina_2(text)
                        else:
                            # Verificar se é página de item
                            if self._is_item_page(text):
                                self._parse_item_page(text)
                            else:
                                # Pode ser continuação de item
                                self._continue_item(text)
            
            # Processar último item se houver
            if self.current_item:
                self._finalize_current_item()
            
            # Processar itens coletados
            self._process_items()
            
            # Calcular totais
            self._calculate_totals()
            
            logger.info(f"Parsing concluído. {len(self.documento['itens'])} itens processados.")
            return self.documento
            
        except Exception as e:
            logger.error(f"Erro no parsing: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto"""
        # Substituir múltiplos espaços por um único
        text = re.sub(r'\s+', ' ', text)
        # Corrigir quebras de linha problemáticas
        text = re.sub(r'(\d) (\d)', r'\1\2', text)
        return text.strip()
    
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
        start_idx = text.find('CÁLCULOS DOS TRIBUTOS')
        end_idx = text.find('RECEITA', start_idx)
        
        if start_idx != -1:
            tributo_section = text[start_idx:end_idx] if end_idx != -1 else text[start_idx:]
            
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
        seguro_pattern = r'Total\s+\(R\$\)\s+([\d\.,]+)'
        seguro_match = re.search(seguro_pattern, text)
        if seguro_match:
            self.documento['seguro']['total'] = self._parse_valor(seguro_match.group(1))
    
    def _is_item_page(self, text: str) -> bool:
        """Verifica se é uma página de item"""
        # Padrões que indicam início de item
        item_patterns = [
            r'\b\d+\s+\d{4}\.\d{2}\.\d{2}\s+\d+\b',
            r'ITENS DA DUIMP',
            r'DENOMINACAO DO PRODUTO',
            r'CÓDIGO INTERNO',
            r'Valor Unit Cond Venda'
        ]
        
        for pattern in item_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _parse_item_page(self, text: str):
        """Parse de uma página de item"""
        logger.info(f"Parsing página {self.current_page_num} - Item")
        
        # Se houver item em buffer, finalizá-lo
        if self.current_item:
            self._finalize_current_item()
        
        # Iniciar novo item
        self.current_item = {
            'pagina': self.current_page_num,
            'numero_item': '',
            'ncm': '',
            'codigo_produto': '',
            'nome_produto': '',
            'codigo_interno': '',
            'quantidade': 0,
            'peso_liquido': 0,
            'valor_unitario': 0,
            'valor_total': 0,
            'valor_local_embarque': 0,
            'valor_local_aduanero': 0,
            'frete_internacional': 0,
            'seguro_internacional': 0,
            'ii_base_calculo': 0,
            'ii_aliquota': 0,
            'ii_valor_devido': 0,
            'ipi_base_calculo': 0,
            'ipi_aliquota': 0,
            'ipi_valor_devido': 0,
            'pis_base_calculo': 0,
            'pis_aliquota': 0,
            'pis_valor_devido': 0,
            'cofins_base_calculo': 0,
            'cofins_aliquota': 0,
            'cofins_valor_devido': 0,
            'icms_regime': '',
            'icms_base_calculo': 0,
            'icms_valor_devido': 0,
            'total_impostos': 0,
            'valor_total_com_impostos': 0
        }
        
        # Extrair todas as informações
        self._extract_all_item_info(text)
    
    def _continue_item(self, text: str):
        """Continua parsing de item em múltiplas páginas"""
        if self.current_item:
            # Adicionar texto ao buffer do item atual
            self._extract_all_item_info(text)
    
    def _extract_all_item_info(self, text: str):
        """Extrai todas as informações do item de forma robusta"""
        # Número do item, NCM, Código
        header_pattern = r'\b(\d+)\s+(\d{4}\.\d{2}\.\d{2})\s+(\d+)\b'
        header_match = re.search(header_pattern, text)
        
        if header_match and not self.current_item['numero_item']:
            self.current_item['numero_item'] = header_match.group(1)
            self.current_item['ncm'] = header_match.group(2)
            self.current_item['codigo_produto'] = header_match.group(3)
        
        # Nome do produto
        if not self.current_item['nome_produto']:
            nome_pattern = r'DENOMINACAO DO PRODUTO\s*\n?(.+?)(?=\n(?:CÓDIGO|FABRICANTE|DESCRI|CONDI))'
            nome_match = re.search(nome_pattern, text, re.IGNORECASE | re.DOTALL)
            if nome_match:
                self.current_item['nome_produto'] = nome_match.group(1).strip()
        
        # Código interno
        if not self.current_item['codigo_interno']:
            codigo_pattern = r'Código interno\s+(.+?)(?:\n|$)'
            codigo_match = re.search(codigo_pattern, text, re.IGNORECASE)
            if codigo_match:
                self.current_item['codigo_interno'] = codigo_match.group(1).strip()
        
        # Quantidade
        qtd_pattern = r'Qtde Unid\. Comercial\s+([\d\.,]+)'
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
        valor_total_pattern = r'Valor Tot\. Cond Venda\s+([\d\.,]+)'
        valor_total_match = re.search(valor_total_pattern, text)
        if valor_total_match:
            self.current_item['valor_total'] = self._parse_valor(valor_total_match.group(1))
        
        # Valores de embarque e aduaneiro
        valores_pattern = r'Local Embarque \(R\$\)\s+([\d\.,]+)'
        valor_emb_match = re.search(valores_pattern, text)
        if valor_emb_match:
            self.current_item['valor_local_embarque'] = self._parse_valor(valor_emb_match.group(1))
        
        # Valor aduaneiro
        aduaneiro_pattern = r'Local Aduaneiro \(R\$\)\s+([\d\.,]+)'
        aduaneiro_match = re.search(aduaneiro_pattern, text)
        if aduaneiro_match:
            self.current_item['valor_local_aduanero'] = self._parse_valor(aduaneiro_match.group(1))
        
        # Frete internacional
        frete_pattern = r'Frete Internac\. \(R\$\)\s+([\d\.,]+)'
        frete_match = re.search(frete_pattern, text)
        if frete_match:
            self.current_item['frete_internacional'] = self._parse_valor(frete_match.group(1))
        
        # Seguro internacional
        seguro_pattern = r'Seguro Internac\. \(R\$\)\s+([\d\.,]+)'
        seguro_match = re.search(seguro_pattern, text)
        if seguro_match:
            self.current_item['seguro_internacional'] = self._parse_valor(seguro_match.group(1))
        
        # Extrair todos os tributos usando método robusto
        self._extract_all_taxes(text)
    
    def _extract_all_taxes(self, text: str):
        """Extrai todos os tributos de forma robusta"""
        # Dividir o texto em seções para análise
        lines = text.split('\n')
        
        # Procurar por cada tributo linha por linha
        for i, line in enumerate(lines):
            line = line.strip()
            
            # II
            if 'II' in line and 'Base de Cálculo' in line:
                self._extract_tax_value(line, 'ii_base_calculo')
            elif 'II' in line and '% Alíquota' in line:
                self._extract_tax_value(line, 'ii_aliquota')
            elif 'II' in line and 'Valor Devido' in line:
                self._extract_tax_value(line, 'ii_valor_devido')
            
            # IPI
            elif 'IPI' in line and 'Base de Cálculo' in line:
                self._extract_tax_value(line, 'ipi_base_calculo')
            elif 'IPI' in line and '% Alíquota' in line:
                self._extract_tax_value(line, 'ipi_aliquota')
            elif 'IPI' in line and 'Valor Devido' in line:
                self._extract_tax_value(line, 'ipi_valor_devido')
            
            # PIS - MÉTODO ROBUSTO
            elif 'PIS' in line or 'pis' in line.lower():
                # Procurar valores nas próximas linhas
                for j in range(i, min(i + 5, len(lines))):
                    sub_line = lines[j]
                    if 'Base de Cálculo' in sub_line and not self.current_item['pis_base_calculo']:
                        self._extract_tax_value(sub_line, 'pis_base_calculo')
                    elif '% Alíquota' in sub_line and not self.current_item['pis_aliquota']:
                        self._extract_tax_value(sub_line, 'pis_aliquota')
                    elif 'Valor Devido' in sub_line and not self.current_item['pis_valor_devido']:
                        self._extract_tax_value(sub_line, 'pis_valor_devido')
            
            # COFINS - MÉTODO ROBUSTO
            elif 'COFINS' in line or 'cofins' in line.lower():
                # Procurar valores nas próximas linhas
                for j in range(i, min(i + 5, len(lines))):
                    sub_line = lines[j]
                    if 'Base de Cálculo' in sub_line and not self.current_item['cofins_base_calculo']:
                        self._extract_tax_value(sub_line, 'cofins_base_calculo')
                    elif '% Alíquota' in sub_line and not self.current_item['cofins_aliquota']:
                        self._extract_tax_value(sub_line, 'cofins_aliquota')
                    elif 'Valor Devido' in sub_line and not self.current_item['cofins_valor_devido']:
                        self._extract_tax_value(sub_line, 'cofins_valor_devido')
        
        # Método alternativo: buscar padrões específicos
        if not self.current_item['pis_valor_devido']:
            self._extract_tax_by_pattern(text, 'PIS', 'pis_valor_devido')
        
        if not self.current_item['cofins_valor_devido']:
            self._extract_tax_by_pattern(text, 'COFINS', 'cofins_valor_devido')
    
    def _extract_tax_value(self, line: str, field: str):
        """Extrai valor de imposto de uma linha"""
        valor_pattern = r'([\d\.,]+)'
        match = re.search(valor_pattern, line)
        if match:
            valor = self._parse_valor(match.group(1))
            self.current_item[field] = valor
    
    def _extract_tax_by_pattern(self, text: str, tributo: str, field: str):
        """Extrai valor de imposto usando padrões específicos"""
        # Padrão 1: Valor Devido após o nome do tributo
        pattern1 = f'{tributo}.*?Valor Devido.*?([\\d\\.,]+)'
        match1 = re.search(pattern1, text, re.IGNORECASE | re.DOTALL)
        if match1:
            self.current_item[field] = self._parse_valor(match1.group(1))
            return
        
        # Padrão 2: Valor após "Valor Devido (R$)"
        pattern2 = f'{tributo}.*?Valor Devido \\(R\\$\\).*?([\\d\\.,]+)'
        match2 = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)
        if match2:
            self.current_item[field] = self._parse_valor(match2.group(1))
            return
        
        # Padrão 3: Procurar em todo o texto
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if tributo.lower() in line.lower():
                # Procurar números nas próximas linhas
                for j in range(i + 1, min(i + 10, len(lines))):
                    valor_match = re.search(r'([\d\.,]+)', lines[j])
                    if valor_match:
                        self.current_item[field] = self._parse_valor(valor_match.group(1))
                        return
    
    def _finalize_current_item(self):
        """Finaliza o item atual e adiciona à lista"""
        if self.current_item and self.current_item.get('numero_item'):
            # Calcular totais
            ii = self.current_item.get('ii_valor_devido', 0)
            ipi = self.current_item.get('ipi_valor_devido', 0)
            pis = self.current_item.get('pis_valor_devido', 0)
            cofins = self.current_item.get('cofins_valor_devido', 0)
            
            total_impostos = ii + ipi + pis + cofins
            valor_total = self.current_item.get('valor_total', 0)
            
            self.current_item['total_impostos'] = total_impostos
            self.current_item['valor_total_com_impostos'] = valor_total + total_impostos
            
            # Log dos valores extraídos para debug
            logger.info(f"Item {self.current_item['numero_item']}: "
                       f"II={ii:.2f}, IPI={ipi:.2f}, PIS={pis:.2f}, COFINS={cofins:.2f}, "
                       f"Total={total_impostos:.2f}")
            
            # Adicionar à lista de itens
            self.documento['itens'].append(self.current_item.copy())
    
    def _process_items(self):
        """Processa todos os itens do buffer"""
        logger.info(f"Total de itens processados: {len(self.documento['itens'])}")
        
        # Log detalhado dos impostos extraídos
        for item in self.documento['itens']:
            logger.debug(f"Item {item.get('numero_item', 'N/A')}: "
                        f"PIS={item.get('pis_valor_devido', 0):.2f}, "
                        f"COFINS={item.get('cofins_valor_devido', 0):.2f}")
    
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
            totais['total_impostos'] +
            totais['frete_total'] +
            totais['seguro_total']
        )
        
        # Log dos totais
        logger.info(f"Totais: II={totais['ii_total']:.2f}, "
                   f"IPI={totais['ipi_total']:.2f}, "
                   f"PIS={totais['pis_total']:.2f}, "
                   f"COFINS={totais['cofins_total']:.2f}, "
                   f"Total Impostos={totais['total_impostos']:.2f}")
        
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
    """Analisador financeiro completo"""
    
    def __init__(self, documento: Dict):
        self.documento = documento
        self.itens_df = None
        self.totais_df = None
        self.analises = {}
        self.problems = []
        
    def prepare_dataframes(self):
        """Prepara DataFrames para análise"""
        # DataFrame de itens
        itens_data = []
        for idx, item in enumerate(self.documento['itens']):
            item_data = {
                'Item': item.get('numero_item', f'N/A-{idx}'),
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
                'Custo Unitário (R$)': item.get('valor_total_com_impostos', 0) / item.get('quantidade', 1) if item.get('quantidade', 0) > 0 else 0,
                'Pagina': item.get('pagina', 0)
            }
            
            # Verificar problemas na extração
            if item.get('pis_valor_devido', 0) == 0:
                self.problems.append(f"Item {item.get('numero_item', 'N/A')}: PIS não extraído")
            
            if item.get('cofins_valor_devido', 0) == 0:
                self.problems.append(f"Item {item.get('numero_item', 'N/A')}: COFINS não extraído")
            
            itens_data.append(item_data)
        
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
        
        # Log de problemas
        if self.problems:
            logger.warning(f"Problemas encontrados: {len(self.problems)}")
            for problem in self.problems[:5]:  # Mostrar apenas os 5 primeiros
                logger.warning(problem)
    
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
        if self.itens_df is not None and not self.itens_df.empty:
            if 'Valor Total (R$)' in self.itens_df.columns:
                self.analises['top_itens_valor'] = self.itens_df.nlargest(10, 'Valor Total (R$)')
            if 'Total Impostos (R$)' in self.itens_df.columns:
                self.analises['top_itens_impostos'] = self.itens_df.nlargest(10, 'Total Impostos (R$)')
        
        # Análise de problemas
        if self.itens_df is not None:
            zero_pis = (self.itens_df['PIS (R$)'] == 0).sum()
            zero_cofins = (self.itens_df['COFINS (R$)'] == 0).sum()
            self.analises['problemas'] = {
                'itens_sem_pis': zero_pis,
                'itens_sem_cofins': zero_cofins,
                'percent_sem_pis': (zero_pis / len(self.itens_df) * 100) if len(self.itens_df) > 0 else 0,
                'percent_sem_cofins': (zero_cofins / len(self.itens_df) * 100) if len(self.itens_df) > 0 else 0
            }

def main():
    """Função principal"""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">🏭 Sistema Completo de Análise de Extratos Häfele</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight-box">
        <strong>🔍 Sistema Profissional de Extração e Análise</strong><br>
        Extração completa de todos os dados de extratos Häfele, incluindo <strong>PIS e COFINS</strong> de todos os itens.
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
        
        show_tax_details = st.checkbox("Mostrar detalhes de impostos por item", value=True)
        show_problems = st.checkbox("Mostrar problemas de extração", value=True)
        
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
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            # Informações do processamento
            totais = documento['totais']
            st.markdown(f"""
            <div class="warning-box">
                <strong>📋 Resumo do Processamento:</strong><br>
                • <strong>{len(documento['itens'])} itens</strong> extraídos<br>
                • <strong>R$ {totais.get('valor_total_com_impostos', 0):,.2f}</strong> custo total<br>
                • <strong>R$ {totais.get('total_impostos', 0):,.2f}</strong> em impostos<br>
                • <strong>R$ {totais.get('pis_total', 0):,.2f}</strong> em PIS<br>
                • <strong>R$ {totais.get('cofins_total', 0):,.2f}</strong> em COFINS
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar problemas de extração
            if show_problems and analyser.problems:
                with st.expander("⚠️ Problemas de Extração Identificados", expanded=True):
                    st.warning(f"Encontrados {len(analyser.problems)} problemas na extração de impostos:")
                    for problem in analyser.problems[:10]:  # Mostrar apenas os 10 primeiros
                        st.markdown(f"• {problem}")
                    
                    if len(analyser.problems) > 10:
                        st.info(f"... e mais {len(analyser.problems) - 10} problemas")
            
            # Módulos selecionados
            if "Dashboard Resumo" in modules:
                st.markdown('<h2 class="sub-header">📈 Dashboard Resumo</h2>', unsafe_allow_html=True)
                
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="section-card">
                        <div class="metric-value">R$ {totais.get('valor_total_mercadoria', 0):,.2f}</div>
                        <div class="metric-label">Valor Mercadoria</div>
                        <span class="badge badge-info">{len(documento['itens'])} itens</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    percent_impostos = (totais.get('total_impostos', 0) / totais.get('valor_total_mercadoria', 1) * 100) if totais.get('valor_total_mercadoria', 0) > 0 else 0
                    st.markdown(f"""
                    <div class="section-card">
                        <div class="metric-value">R$ {totais.get('total_impostos', 0):,.2f}</div>
                        <div class="metric-label">Total Impostos</div>
                        <span class="badge badge-warning">{percent_impostos:.1f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="section-card">
                        <div class="metric-value">R$ {totais.get('pis_total', 0):,.2f}</div>
                        <div class="metric-label">Total PIS</div>
                        <span class="badge badge-info">
                            {(totais.get('pis_total', 0) / totais.get('valor_total_mercadoria', 1) * 100) if totais.get('valor_total_mercadoria', 0) > 0 else 0:.2f}%
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="section-card">
                        <div class="metric-value">R$ {totais.get('cofins_total', 0):,.2f}</div>
                        <div class="metric-label">Total COFINS</div>
                        <span class="badge badge-info">
                            {(totais.get('cofins_total', 0) / totais.get('valor_total_mercadoria', 1) * 100) if totais.get('valor_total_mercadoria', 0) > 0 else 0:.2f}%
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
                        percent_merc = (valor / totais.get('valor_total_mercadoria', 1) * 100) if totais.get('valor_total_mercadoria', 0) > 0 else 0
                        percent_impostos_total = (valor / totais.get('total_impostos', 1) * 100) if totais.get('total_impostos', 0) > 0 else 0
                        impostos_data.append({
                            'Imposto': tributo,
                            'Valor (R$)': f'R$ {valor:,.2f}',
                            '% sobre Mercadoria': f'{percent_merc:.2f}%',
                            '% sobre Total Impostos': f'{percent_impostos_total:.2f}%'
                        })
                    
                    impostos_df = pd.DataFrame(impostos_data)
                    
                    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                    st.dataframe(
                        impostos_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    # Gráfico de impostos
                    impostos_chart_data = {
                        'Imposto': ['II', 'IPI', 'PIS', 'COFINS'],
                        'Valor': [
                            totais.get('ii_total', 0),
                            totais.get('ipi_total', 0),
                            totais.get('pis_total', 0),
                            totais.get('cofins_total', 0)
                        ]
                    }
                    
                    impostos_chart_df = pd.DataFrame(impostos_chart_data)
                    
                    fig = px.pie(
                        impostos_chart_df,
                        values='Valor',
                        names='Imposto',
                        title='Distribuição dos Impostos',
                        hole=0.4,
                        color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(
                        height=350,
                        margin=dict(t=50, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            if "Lista Completa de Itens" in modules and analyser.itens_df is not None:
                st.markdown('<h2 class="sub-header">📦 Lista Completa de Itens</h2>', unsafe_allow_html=True)
                
                # Estatísticas de extração
                if 'analises' in analyser.analises and 'problemas' in analyser.analises['analises']:
                    problemas = analyser.analises['analises']['problemas']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Itens sem PIS", problemas['itens_sem_pis'], f"{problemas['percent_sem_pis']:.1f}%")
                    with col2:
                        st.metric("Itens sem COFINS", problemas['itens_sem_cofins'], f"{problemas['percent_sem_cofins']:.1f}%")
                
                # Filtros
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    search_term = st.text_input("🔍 Buscar:", "", key="search_items")
                with col2:
                    min_valor = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=1000.0, key="min_valor")
                with col3:
                    ncm_filter = st.text_input("Filtrar por NCM:", "", key="ncm_filter")
                with col4:
                    show_zero_tax = st.checkbox("Mostrar itens sem impostos", value=False)
                
                # Aplicar filtros
                filtered_df = analyser.itens_df.copy()
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Produto'].astype(str).str.contains(search_term, case=False, na=False) |
                        filtered_df['Código Interno'].astype(str).str.contains(search_term, case=False, na=False) |
                        filtered_df['Código'].astype(str).str.contains(search_term, case=False, na=False)
                    ]
                
                if min_valor > 0 and 'Valor Total (R$)' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Valor Total (R$)'] >= min_valor]
                
                if ncm_filter and 'NCM' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['NCM'].astype(str).str.contains(ncm_filter)]
                
                if not show_zero_tax:
                    if 'PIS (R$)' in filtered_df.columns and 'COFINS (R$)' in filtered_df.columns:
                        filtered_df = filtered_df[(filtered_df['PIS (R$)'] > 0) & (filtered_df['COFINS (R$)'] > 0)]
                
                # Exibir tabela
                if not filtered_df.empty:
                    # Formatar para exibição
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
                    
                    # Destacar valores zero em PIS e COFINS
                    def highlight_zero(val):
                        if isinstance(val, str) and 'R$ 0,00' in val:
                            return 'background-color: #FEE2E2'
                        return ''
                    
                    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                    st.dataframe(
                        display_df.style.applymap(highlight_zero, subset=['PIS (R$)', 'COFINS (R$)']),
                        use_container_width=True,
                        height=600
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("Nenhum item encontrado com os filtros aplicados.")
                
                # Detalhes de impostos por item
                if show_tax_details:
                    with st.expander("📋 Detalhes de Impostos por Item", expanded=False):
                        tax_details_df = analyser.itens_df[['Item', 'Produto', 'II (R$)', 'IPI (R$)', 'PIS (R$)', 'COFINS (R$)', 'Total Impostos (R$)']].copy()
                        tax_details_df = tax_details_df.sort_values('Total Impostos (R$)', ascending=False)
                        
                        # Formatar
                        for col in ['II (R$)', 'IPI (R$)', 'PIS (R$)', 'COFINS (R$)', 'Total Impostos (R$)']:
                            tax_details_df[col] = tax_details_df[col].apply(lambda x: f'R$ {x:,.2f}')
                        
                        st.dataframe(
                            tax_details_df,
                            use_container_width=True,
                            height=400
                        )
            
            if "Exportação Completa" in modules:
                st.markdown('<h2 class="sub-header">💾 Exportação de Dados</h2>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Exportar itens CSV
                    if analyser.itens_df is not None:
                        csv_itens = analyser.itens_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Itens (CSV)",
                            data=csv_itens,
                            file_name="itens_completos.csv",
                            mime="text/csv",
                            help="Lista completa de itens com impostos"
                        )
                
                with col2:
                    # Exportar totais CSV
                    if analyser.totais_df is not None:
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
                    
                    try:
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            if analyser.itens_df is not None:
                                analyser.itens_df.to_excel(writer, sheet_name='Itens', index=False)
                            
                            if analyser.totais_df is not None:
                                analyser.totais_df.to_excel(writer, sheet_name='Totais', index=False)
                            
                            # Adicionar análise por NCM
                            if analyser.itens_df is not None and not analyser.itens_df.empty:
                                required_cols = ['NCM', 'Quantidade', 'Valor Total (R$)', 'Total Impostos (R$)']
                                if all(col in analyser.itens_df.columns for col in required_cols):
                                    ncm_df = analyser.itens_df.groupby('NCM').agg({
                                        'Quantidade': 'sum',
                                        'Valor Total (R$)': 'sum',
                                        'Total Impostos (R$)': 'sum'
                                    }).reset_index()
                                    ncm_df.to_excel(writer, sheet_name='Por NCM', index=False)
                            
                            # Adicionar problemas de extração
                            if analyser.problems:
                                problems_df = pd.DataFrame({'Problemas': analyser.problems})
                                problems_df.to_excel(writer, sheet_name='Problemas', index=False)
                        
                        st.download_button(
                            label="📊 Excel Completo",
                            data=output.getvalue(),
                            file_name="analise_completa.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Relatório completo em Excel"
                        )
                    except Exception as e:
                        st.error(f"Erro ao criar Excel: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            st.code(str(e), language='python')
    
    else:
        # Tela inicial
        st.markdown("""
        <div class="section-card">
            <h3>🚀 Sistema de Extração e Análise Häfele</h3>
            <p>Este sistema é projetado para processar <strong>documentos completos</strong> da Häfele, 
            extraindo <strong>TODOS os impostos (II, IPI, PIS, COFINS)</strong> de forma precisa e realizando análises financeiras detalhadas.</p>
            
            <h4>🔧 Melhorias Implementadas:</h4>
            <ul>
                <li><strong>Extração Robusta de PIS/COFINS:</strong> Múltiplos métodos para garantir captura completa</li>
                <li><strong>Detecção de Problemas:</strong> Identifica itens onde impostos não foram extraídos</li>
                <li><strong>Logging Detalhado:</strong> Para debug e monitoramento</li>
                <li><strong>Interface Aprimorada:</strong> Destaque para valores problemáticos</li>
            </ul>
            
            <h4>📋 Como usar:</h4>
            <ol>
                <li>Faça upload do PDF no menu lateral</li>
                <li>Selecione "Mostrar problemas de extração" para verificar PIS/COFINS</li>
                <li>Explore os resultados com os filtros disponíveis</li>
                <li>Exporte os dados para análise externa</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
