# app_conversor_duimp.py
import streamlit as st
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import base64
import zipfile
from io import BytesIO, StringIO
import pdfplumber
import fitz  # PyMuPDF como alternativa
import io

# Configuração da página
st.set_page_config(
    page_title="Conversor DUIMP - PDF para XML",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F59E0B;
    }
    .info-box {
        background-color: #DBEAFE;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
    }
    .stat-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #64748B;
    }
    .xml-preview {
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        background-color: #F1F5F9;
        padding: 1rem;
        border-radius: 0.5rem;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

class ConversorDUIMPStreamlit:
    def __init__(self):
        self.duimp_data = {
            "cabecalho": {},
            "adicoes": [],
            "transportes": {},
            "tributos_totais": {},
            "pagamentos": [],
            "documentos": []
        }
        self.stats = {
            "paginas_processadas": 0,
            "itens_encontrados": 0,
            "adicoes_geradas": 0,
            "tempo_processamento": 0
        }
    
    def extrair_texto_pdf(self, pdf_bytes: bytes, usar_pymupdf: bool = False) -> str:
        """Extrai texto do PDF usando pdfplumber ou PyMuPDF"""
        texto_completo = ""
        
        try:
            if usar_pymupdf:
                # Usar PyMuPDF (mais rápido para alguns PDFs)
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for pagina in doc:
                    texto_completo += pagina.get_text()
                self.stats["paginas_processadas"] = len(doc)
            else:
                # Usar pdfplumber (mais preciso para tabelas)
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for i, pagina in enumerate(pdf.pages):
                        texto = pagina.extract_text()
                        if texto:
                            texto_completo += texto + "\n"
                    self.stats["paginas_processadas"] = len(pdf.pages)
            
            return texto_completo
        except Exception as e:
            st.error(f"Erro na extração do PDF: {str(e)}")
            return ""
    
    def processar_pdf(self, pdf_bytes: bytes, config: Dict) -> bool:
        """Processa o PDF e extrai todas as informações"""
        import time
        inicio = time.time()
        
        try:
            # Extrair texto
            texto = self.extrair_texto_pdf(pdf_bytes, config.get("usar_pymupdf", False))
            
            if not texto:
                st.error("Não foi possível extrair texto do PDF")
                return False
            
            # Processar diferentes seções
            self._parse_cabecalho(texto)
            self._parse_adicoes(texto, config)
            self._parse_transporte(texto)
            self._parse_tributos(texto)
            self._parse_documentos(texto)
            
            self.stats["itens_encontrados"] = len(self.duimp_data["adicoes"])
            self.stats["adicoes_geradas"] = len(self.duimp_data["adicoes"])
            self.stats["tempo_processamento"] = time.time() - inicio
            
            return True
            
        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
            return False
    
    def _parse_cabecalho(self, texto: str):
        """Extrai informações do cabeçalho"""
        cabecalho = {}
        
        # Processo
        match = re.search(r'PROCESSO\s*#\s*(\d+)', texto)
        if match:
            cabecalho['processo'] = match.group(1)
        
        # CNPJ Importador
        match = re.search(r'HAFELE BRASIL\s*([\d./-]+)', texto)
        if match:
            cabecalho['cnpj'] = match.group(1).strip()
        
        # Número DUIMP
        match = re.search(r'Número\s*([A-Z0-9]+)', texto)
        if match:
            cabecalho['numero_duimp'] = match.group(1)
        else:
            # Gerar número fictício se não encontrado
            cabecalho['numero_duimp'] = f"DUIMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Data
        match = re.search(r'Data de Cadastro\s*(\d{2}/\d{2}/\d{4})', texto)
        if match:
            data_str = match.group(1)
            cabecalho['data_cadastro'] = datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y%m%d')
        else:
            cabecalho['data_cadastro'] = datetime.now().strftime('%Y%m%d')
        
        # Moeda
        match = re.search(r'Moeda Negociada\s*(\d+)\s*-\s*([\w\s/]+)', texto)
        if match:
            cabecalho['moeda_codigo'] = match.group(1)
            cabecalho['moeda_nome'] = match.group(2)
        
        # Cotação
        match = re.search(r'Cotacao\s*([\d.,]+)', texto)
        if match:
            cabecalho['cotacao'] = match.group(1).replace('.', '').replace(',', '.')
        
        self.duimp_data["cabecalho"] = cabecalho
    
    def _parse_adicoes(self, texto: str, config: Dict):
        """Extrai adições e itens"""
        adicoes = []
        
        # Padrões para encontrar itens
        padrao_item = r'Item\s*\|\s*Integracao\s*\|\s*NCM\s*\|\s*Codigo'
        if padrao_item in texto:
            # Dividir por páginas/sessões
            secoes = texto.split('Item | Integracao | NCM | Codigo')
            
            for secao in secoes[1:]:  # Ignorar primeira seção (cabeçalho)
                linhas = secao.split('\n')
                
                for i, linha in enumerate(linhas):
                    if re.match(r'^\s*\d+\s*[✓✗×]\s*[\d.]+\s*\d+', linha.strip()):
                        item = self._extrair_item(linha.strip(), linhas, i, config)
                        if item:
                            adicoes.append(item)
        
        # Se não encontrar no formato tabela, busca alternativa
        if not adicoes:
            self._buscar_itens_alternativo(texto, adicoes, config)
        
        self.duimp_data["adicoes"] = adicoes
    
    def _extrair_item(self, linha_item: str, linhas: List[str], idx: int, config: Dict) -> Dict:
        """Extrai informações de um item específico"""
        item = {}
        
        # Dividir linha do item
        partes = re.split(r'\s{2,}', linha_item.strip())
        if len(partes) >= 6:
            item['numero_item'] = partes[0].zfill(2)
            item['ncm'] = partes[2].replace('.', '').ljust(8, '0')
            item['condicao_venda'] = partes[5] if len(partes) > 5 else 'FOB'
        
        # Buscar detalhes nas linhas seguintes
        for j in range(idx + 1, min(idx + 20, len(linhas))):
            linha = linhas[j]
            
            # Descrição
            if 'DENOMINACAO DO PRODUTO' in linha or 'DESCRICAO DO PRODUTO' in linha:
                if j + 1 < len(linhas):
                    item['descricao'] = linhas[j + 1].strip()[:200]
            
            # Código interno
            elif 'Código interno' in linha:
                match = re.search(r'Código interno\s*([\d.]+)', linha)
                if match:
                    item['codigo_interno'] = match.group(1)
            
            # Quantidade
            elif 'Qtde Unid. Comercial' in linha:
                match = re.search(r'([\d.,]+)', linha)
                if match:
                    qtde = match.group(1).replace('.', '').replace(',', '.')
                    item['quantidade'] = self._formatar_valor_xml(qtde, 14)
            
            # Valor unitário
            elif 'Valor Unit Cond Venda' in linha:
                match = re.search(r'([\d.,]+)', linha)
                if match:
                    valor = match.group(1).replace('.', '').replace(',', '.')
                    item['valor_unitario'] = self._formatar_valor_xml(valor, 20)
            
            # Valor total
            elif 'Vlr Cond Venda (Moeda' in linha or 'Valor Tot. Cond Venda' in linha:
                match = re.search(r'([\d.,]+)', linha)
                if match:
                    valor = match.group(1).replace('.', '').replace(',', '.')
                    item['valor_total_moeda'] = self._formatar_valor_xml(valor, 15)
        
        # Calcular valores em Reais se houver cotação
        if 'valor_total_moeda' in item and 'cotacao' in self.duimp_data["cabecalho"]:
            try:
                valor_moeda = float(item['valor_total_moeda']) / 100
                cotacao = float(self.duimp_data["cabecalho"]["cotacao"])
                valor_reais = valor_moeda * cotacao
                item['valor_total_reais'] = self._formatar_valor_xml(str(valor_reais), 15)
            except:
                item['valor_total_reais'] = '000000000000000'
        
        # Calcular tributos
        self._calcular_tributos_item(item)
        
        return item if item.get('ncm') else None
    
    def _calcular_tributos_item(self, item: Dict):
        """Calcula tributos para um item"""
        # Valores padrão
        valor_base = float(item.get('valor_total_reais', '0')) / 100 if item.get('valor_total_reais') != '0' else 0
        
        # II - baseado no NCM
        ncm_prefixo = item.get('ncm', '0000')[:4]
        aliquotas_ii = {
            '8302': '01800', '3926': '01800', '7318': '01440',
            '8505': '01600', '8414': '01600', '8479': '01400'
        }
        aliquota_ii = aliquotas_ii.get(ncm_prefixo, '01800')
        item['ii_aliquota'] = aliquota_ii
        item['ii_valor'] = self._formatar_valor_xml(str(int(valor_base * float(aliquota_ii) / 10000 * 100)), 15)
        
        # IPI - 3.25% padrão
        item['ipi_aliquota'] = '00325'
        item['ipi_valor'] = self._formatar_valor_xml(str(int(valor_base * 0.0325 * 100)), 15)
        
        # PIS - 2.10%
        item['pis_aliquota'] = '00210'
        item['pis_valor'] = self._formatar_valor_xml(str(int(valor_base * 0.021 * 100)), 15)
        
        # COFINS - 9.65%
        item['cofins_aliquota'] = '00965'
        item['cofins_valor'] = self._formatar_valor_xml(str(int(valor_base * 0.0965 * 100)), 15)
        
        # ICMS - 18% com diferimento 50%
        item['icms_aliquota'] = '01800'
        item['icms_valor'] = self._formatar_valor_xml(str(int(valor_base * 0.18 * 100)), 15)
        item['icms_diferido'] = self._formatar_valor_xml(str(int(valor_base * 0.09 * 100)), 15)
    
    def _parse_transporte(self, texto: str):
        """Extrai dados de transporte"""
        transporte = {}
        
        match = re.search(r'Via de Transporte\s*(\d+)\s*-\s*([\w]+)', texto)
        if match:
            transporte['codigo'] = match.group(1).zfill(2)
            transporte['nome'] = match.group(2)
        else:
            transporte['codigo'] = '01'
            transporte['nome'] = 'MARÍTIMA'
        
        match = re.search(r'Data de Embarque\s*(\d{2}/\d{2}/\d{4})', texto)
        if match:
            transporte['data_embarque'] = match.group(1)
        
        match = re.search(r'Peso Bruto\s*([\d.,]+)', texto)
        if match:
            transporte['peso_bruto'] = self._formatar_valor_xml(match.group(1).replace('.', '').replace(',', '.'), 15)
        
        match = re.search(r'Unidade de Despacho\s*(\d+)\s*-\s*([\w\s]+)', texto)
        if match:
            transporte['urf_codigo'] = match.group(1)
            transporte['urf_nome'] = match.group(2)
        
        self.duimp_data["transportes"] = transporte
    
    def _parse_tributos(self, texto: str):
        """Extrai totais de tributos"""
        tributos = {}
        
        # Padrões para diferentes formatos de tabela
        padroes = [
            r'II\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            r'II\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            r'Imposto de Importacao\s+([\d.,]+)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                tributos['ii_total'] = self._formatar_valor_xml(match.group(1).replace('.', '').replace(',', '.'), 15)
                break
        
        self.duimp_data["tributos_totais"] = tributos
    
    def _parse_documentos(self, texto: str):
        """Extrai documentos listados"""
        documentos = []
        
        # Buscar conhecimentos
        padrao_conhecimento = r'CONHECIMENTO DE EMBARQUE.*?NUMERO[:\s]*([A-Z0-9]+)'
        matches = re.finditer(padrao_conhecimento, texto, re.IGNORECASE | re.DOTALL)
        for match in matches:
            documentos.append({
                'tipo': 'CONHECIMENTO',
                'numero': match.group(1)
            })
        
        # Buscar faturas
        padrao_fatura = r'FATURA COMERCIAL.*?NUMERO[:\s]*([\d/]+)'
        matches = re.finditer(padrao_fatura, texto, re.IGNORECASE | re.DOTALL)
        for match in matches:
            documentos.append({
                'tipo': 'FATURA',
                'numero': match.group(1)
            })
        
        self.duimp_data["documentos"] = documentos
    
    def _buscar_itens_alternativo(self, texto: str, adicoes: List, config: Dict):
        """Busca alternativa por itens quando formato tabela não é encontrado"""
        # Buscar por padrões de NCM
        padrao_ncm = r'(\d{4}\.?\d{2}\.?\d{2})'
        matches = re.finditer(padrao_ncm, texto)
        
        for match in matches:
            ncm = match.group(1).replace('.', '')
            
            # Encontrar contexto ao redor do NCM
            inicio = max(0, match.start() - 200)
            fim = min(len(texto), match.end() + 200)
            contexto = texto[inicio:fim]
            
            item = {
                'numero_item': f"{len(adicoes) + 1:02d}",
                'ncm': ncm.ljust(8, '0'),
                'descricao': self._extrair_descricao_contexto(contexto),
                'quantidade': self._formatar_valor_xml('1', 14),
                'valor_unitario': self._formatar_valor_xml('100', 20),
                'condicao_venda': 'FOB'
            }
            
            self._calcular_tributos_item(item)
            adicoes.append(item)
            
            if len(adicoes) >= config.get("max_itens", 100):
                break
    
    def _extrair_descricao_contexto(self, contexto: str) -> str:
        """Extrai descrição do contexto"""
        # Buscar palavras-chave após o NCM
        linhas = contexto.split('\n')
        for i, linha in enumerate(linhas):
            if any(ncm in linha for ncm in ['8302', '3926', '7318', '8505']):
                if i + 1 < len(linhas):
                    return linhas[i + 1].strip()[:100]
        return "Mercadoria importada"
    
    def _formatar_valor_xml(self, valor_str: str, digitos: int = 15) -> str:
        """Formata valor para padrão XML"""
        try:
            # Converter para float
            valor = float(valor_str)
            # Converter para centavos e formatar
            valor_centavos = int(valor * 100)
            return f"{valor_centavos:0{digitos}d}"
        except:
            return "0" * digitos
    
    def gerar_xml(self) -> str:
        """Gera XML completo no formato DUIMP"""
        try:
            # Criar elemento raiz
            lista_declaracoes = ET.Element('ListaDeclaracoes')
            duimp = ET.SubElement(lista_declaracoes, 'duimp')
            
            # Adicionar cabeçalho
            self._adicionar_cabecalho_xml(duimp)
            
            # Adicionar adições
            for idx, adicao in enumerate(self.duimp_data["adicoes"], 1):
                self._adicionar_adicao_xml(duimp, adicao, idx)
            
            # Adicionar transporte
            self._adicionar_transporte_xml(duimp)
            
            # Adicionar pagamentos
            self._adicionar_pagamentos_xml(duimp)
            
            # Adicionar documentos
            self._adicionar_documentos_xml(duimp)
            
            # Adicionar informações complementares
            self._adicionar_info_complementar(duimp)
            
            # Converter para string formatada
            xml_string = ET.tostring(lista_declaracoes, encoding='unicode', method='xml')
            xml_formatado = minidom.parseString(xml_string).toprettyxml(indent="    ")
            
            return xml_formatado
            
        except Exception as e:
            st.error(f"Erro ao gerar XML: {str(e)}")
            return ""
    
    def _adicionar_cabecalho_xml(self, duimp_element):
        """Adiciona cabeçalho ao XML"""
        cab = self.duimp_data["cabecalho"]
        
        ET.SubElement(duimp_element, 'numeroDUIMP').text = cab.get('numero_duimp', '0000000000')
        ET.SubElement(duimp_element, 'totalAdicoes').text = f"{len(self.duimp_data['adicoes']):03d}"
        ET.SubElement(duimp_element, 'dataRegistro').text = cab.get('data_cadastro', datetime.now().strftime('%Y%m%d'))
        ET.SubElement(duimp_element, 'dataDesembaraco').text = datetime.now().strftime('%Y%m%d')
        
        # Importador
        ET.SubElement(duimp_element, 'importadorNome').text = 'HAFELE BRASIL LTDA'
        ET.SubElement(duimp_element, 'importadorNumero').text = cab.get('cnpj', '02473058000188')
        
        # Tipo de declaração
        ET.SubElement(duimp_element, 'tipoDeclaracaoCodigo').text = '01'
        ET.SubElement(duimp_element, 'tipoDeclaracaoNome').text = 'CONSUMO'
    
    def _adicionar_adicao_xml(self, duimp_element, adicao: Dict, numero: int):
        """Adiciona uma adição ao XML"""
        adicao_elem = ET.SubElement(duimp_element, 'adicao')
        
        # Número da adição
        ET.SubElement(adicao_elem, 'numeroAdicao').text = f"{numero:03d}"
        
        # Dados da mercadoria
        ET.SubElement(adicao_elem, 'dadosMercadoriaCodigoNcm').text = adicao.get('ncm', '00000000')
        ET.SubElement(adicao_elem, 'dadosMercadoriaNomeNcm').text = self._obter_descricao_ncm(adicao.get('ncm', ''))
        ET.SubElement(adicao_elem, 'dadosMercadoriaCondicao').text = 'NOVA'
        ET.SubElement(adicao_elem, 'dadosMercadoriaAplicacao').text = 'REVENDA'
        
        # Mercadoria detalhada
        mercadoria = ET.SubElement(adicao_elem, 'mercadoria')
        ET.SubElement(mercadoria, 'descricaoMercadoria').text = adicao.get('descricao', 'Mercadoria importada')[:100]
        ET.SubElement(mercadoria, 'numeroSequencialItem').text = adicao.get('numero_item', '01')
        ET.SubElement(mercadoria, 'quantidade').text = adicao.get('quantidade', '00000000000000')
        ET.SubElement(mercadoria, 'unidadeMedida').text = 'PECA                '
        ET.SubElement(mercadoria, 'valorUnitario').text = adicao.get('valor_unitario', '00000000000000000000')
        
        # Condição de venda
        ET.SubElement(adicao_elem, 'condicaoVendaIncoterm').text = adicao.get('condicao_venda', 'FOB')
        ET.SubElement(adicao_elem, 'condicaoVendaValorMoeda').text = adicao.get('valor_total_moeda', '000000000000000')
        ET.SubElement(adicao_elem, 'condicaoVendaValorReais').text = adicao.get('valor_total_reais', '000000000000000')
        
        # Fornecedor
        ET.SubElement(adicao_elem, 'fornecedorNome').text = 'FORNECEDOR INTERNACIONAL'
        ET.SubElement(adicao_elem, 'paisOrigemMercadoriaCodigo').text = '156'
        ET.SubElement(adicao_elem, 'paisOrigemMercadoriaNome').text = 'CHINA, REPUBLICA POPULAR'
        
        # Tributos
        ET.SubElement(adicao_elem, 'iiAliquotaAdValorem').text = adicao.get('ii_aliquota', '01800')
        ET.SubElement(adicao_elem, 'iiBaseCalculo').text = adicao.get('valor_total_reais', '000000000000000')
        ET.SubElement(adicao_elem, 'iiAliquotaValorRecolher').text = adicao.get('ii_valor', '000000000000000')
        
        ET.SubElement(adicao_elem, 'ipiAliquotaAdValorem').text = adicao.get('ipi_aliquota', '00325')
        ET.SubElement(adicao_elem, 'ipiAliquotaValorRecolher').text = adicao.get('ipi_valor', '000000000000000')
        
        ET.SubElement(adicao_elem, 'pisPasepAliquotaAdValorem').text = adicao.get('pis_aliquota', '00210')
        ET.SubElement(adicao_elem, 'pisPasepAliquotaValorRecolher').text = adicao.get('pis_valor', '000000000000000')
        
        ET.SubElement(adicao_elem, 'cofinsAliquotaAdValorem').text = adicao.get('cofins_aliquota', '00965')
        ET.SubElement(adicao_elem, 'cofinsAliquotaValorRecolher').text = adicao.get('cofins_valor', '000000000000000')
        
        # ICMS
        ET.SubElement(adicao_elem, 'icmsBaseCalculoValor').text = adicao.get('valor_total_reais', '000000000000000')
        ET.SubElement(adicao_elem, 'icmsBaseCalculoAliquota').text = adicao.get('icms_aliquota', '01800')
        ET.SubElement(adicao_elem, 'icmsBaseCalculoValorImposto').text = adicao.get('icms_valor', '000000000000000')
        ET.SubElement(adicao_elem, 'icmsBaseCalculoValorDiferido').text = adicao.get('icms_diferido', '000000000000000')
    
    def _obter_descricao_ncm(self, ncm: str) -> str:
        """Retorna descrição do NCM"""
        descricoes = {
            '83021000': '- Outros, para móveis',
            '83024200': '-- Outros, para móveis',
            '39263000': '- Guarnições para móveis, carroçarias ou semelhantes',
            '73181200': '-- Outros parafusos para madeira',
            '85051100': '-- De metal'
        }
        return descricoes.get(ncm, f'- Mercadoria NCM {ncm}')
    
    def _adicionar_transporte_xml(self, duimp_element):
        """Adiciona dados de transporte"""
        transp = self.duimp_data["transportes"]
        
        ET.SubElement(duimp_element, 'viaTransporteCodigo').text = transp.get('codigo', '01')
        ET.SubElement(duimp_element, 'viaTransporteNome').text = transp.get('nome', 'MARÍTIMA')
        
        ET.SubElement(duimp_element, 'cargaPesoBruto').text = transp.get('peso_bruto', '000000000000000')
        ET.SubElement(duimp_element, 'urfDespachoCodigo').text = transp.get('urf_codigo', '0917800')
        ET.SubElement(duimp_element, 'urfDespachoNome').text = transp.get('urf_nome', 'PORTO DE PARANAGUA')
    
    def _adicionar_pagamentos_xml(self, duimp_element):
        """Adiciona pagamentos ao XML"""
        # Pagamento II
        pagamento = ET.SubElement(duimp_element, 'pagamento')
        ET.SubElement(pagamento, 'codigoReceita').text = '0086'
        ET.SubElement(pagamento, 'valorReceita').text = self.duimp_data["tributos_totais"].get('ii_total', '000000000000000')
        ET.SubElement(pagamento, 'dataPagamento').text = datetime.now().strftime('%Y%m%d')
    
    def _adicionar_documentos_xml(self, duimp_element):
        """Adiciona documentos ao XML"""
        for doc in self.duimp_data["documentos"]:
            doc_elem = ET.SubElement(duimp_element, 'documentoInstrucaoDespacho')
            ET.SubElement(doc_elem, 'nomeDocumentoDespacho').text = doc.get('tipo', 'DOCUMENTO')
            ET.SubElement(doc_elem, 'numeroDocumentoDespacho').text = doc.get('numero', 'S/N').ljust(25)
    
    def _adicionar_info_complementar(self, duimp_element):
        """Adiciona informações complementares"""
        info = f"""INFORMACOES COMPLEMENTARES
--------------------------
PROCESSO: {self.duimp_data["cabecalho"].get('processo', 'N/I')}
IMPORTADOR: HAFELE BRASIL LTDA
CNPJ: {self.duimp_data["cabecalho"].get('cnpj', '02473058000188')}
DATA PROCESSAMENTO: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
TOTAL DE ITENS: {len(self.duimp_data["adicoes"])}
SISTEMA: CONVERSOR PDF->XML DUIMP
"""
        ET.SubElement(duimp_element, 'informacaoComplementar').text = info
    
    def get_resumo_dataframe(self) -> pd.DataFrame:
        """Retorna resumo das adições como DataFrame"""
        dados = []
        for idx, adicao in enumerate(self.duimp_data["adicoes"], 1):
            dados.append({
                'Adição': idx,
                'NCM': adicao.get('ncm', ''),
                'Descrição': adicao.get('descricao', '')[:50] + '...',
                'Quantidade': float(adicao.get('quantidade', '0')) / 10000,
                'Valor Total (R$)': float(adicao.get('valor_total_reais', '0')) / 100,
                'II (R$)': float(adicao.get('ii_valor', '0')) / 100,
                'IPI (R$)': float(adicao.get('ipi_valor', '0')) / 100
            })
        
        return pd.DataFrame(dados) if dados else pd.DataFrame()

# Funções auxiliares para Streamlit
def create_download_link(content: str, filename: str, label: str):
    """Cria link de download para arquivo"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/xml;base64,{b64}" download="{filename}">{label}</a>'
    return href

def create_zip_download(files: Dict[str, str], zip_filename: str):
    """Cria arquivo ZIP para download múltiplo"""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(filename, content)
    buffer.seek(0)
    
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{zip_filename}">📦 Baixar todos os arquivos (ZIP)</a>'
    return href

# Interface Streamlit
def main():
    # Cabeçalho
    st.markdown('<h1 class="main-header">📄 Conversor DUIMP - PDF para XML</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    Converta arquivos PDF no formato "Extrato de Conferência" para XML DUIMP completo.
    Suporta até 500 páginas e 500 itens por processamento.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        config = {
            "usar_pymupdf": st.checkbox("Usar PyMuPDF (mais rápido)", value=False),
            "max_itens": st.slider("Máximo de itens a processar", 10, 500, 100),
            "gerar_excel": st.checkbox("Gerar Excel de resumo", value=True),
            "dividir_por_adição": st.checkbox("Dividir XML por adição", value=False),
            "processar_paralelo": st.checkbox("Processamento paralelo", value=False)
        }
        
        st.markdown("---")
        st.header("📊 Sobre")
        st.info("""
        **Funcionalidades:**
        - Extração automática de dados do PDF
        - Cálculo de tributos (II, IPI, PIS, COFINS, ICMS)
        - Geração de XML no padrão DUIMP
        - Resumo em Excel
        - Suporte a múltiplos arquivos
        """)
    
    # Área principal
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Conversão", "📋 Visualização", "⚙️ Configurações Avançadas"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Upload de Arquivos PDF")
            
            uploaded_files = st.file_uploader(
                "Selecione os arquivos PDF",
                type=['pdf'],
                accept_multiple_files=True,
                help="Selecione um ou mais arquivos PDF no formato 'Extrato de Conferência'"
            )
            
            if uploaded_files:
                st.success(f"{len(uploaded_files)} arquivo(s) selecionado(s)")
                
                # Processar cada arquivo
                resultados = []
                
                for uploaded_file in uploaded_files:
                    with st.spinner(f"Processando {uploaded_file.name}..."):
                        # Ler arquivo
                        pdf_bytes = uploaded_file.read()
                        
                        # Criar conversor
                        conversor = ConversorDUIMPStreamlit()
                        
                        # Processar PDF
                        if conversor.processar_pdf(pdf_bytes, config):
                            # Gerar XML
                            xml_content = conversor.gerar_xml()
                            
                            # Gerar Excel se configurado
                            excel_content = None
                            if config["gerar_excel"] and not conversor.get_resumo_dataframe().empty:
                                excel_buffer = BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    conversor.get_resumo_dataframe().to_excel(writer, sheet_name='Resumo', index=False)
                                    # Adicionar estatísticas
                                    stats_df = pd.DataFrame([conversor.stats])
                                    stats_df.to_excel(writer, sheet_name='Estatísticas', index=False)
                                excel_content = excel_buffer.getvalue()
                            
                            resultados.append({
                                'nome': uploaded_file.name,
                                'conversor': conversor,
                                'xml': xml_content,
                                'excel': excel_content,
                                'stats': conversor.stats.copy()
                            })
                
                # Exibir resultados
                if resultados:
                    st.markdown("---")
                    st.markdown('<h3 class="sub-header">✅ Resultados da Conversão</h3>', unsafe_allow_html=True)
                    
                    # Estatísticas gerais
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    
                    total_itens = sum(r['stats']['itens_encontrados'] for r in resultados)
                    total_adicoes = sum(r['stats']['adicoes_geradas'] for r in resultados)
                    total_paginas = sum(r['stats']['paginas_processadas'] for r in resultados)
                    tempo_medio = np.mean([r['stats']['tempo_processamento'] for r in resultados])
                    
                    with col_stat1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value">{total_paginas}</div>
                            <div class="stat-label">Páginas</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_stat2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value">{total_itens}</div>
                            <div class="stat-label">Itens</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_stat3:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value">{total_adicoes}</div>
                            <div class="stat-label">Adições</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_stat4:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value">{tempo_medio:.2f}s</div>
                            <div class="stat-label">Tempo/arquivo</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Downloads
                    st.markdown("---")
                    st.subheader("📥 Downloads")
                    
                    for resultado in resultados:
                        with st.expander(f"📄 {resultado['nome']}"):
                            col_dl1, col_dl2, col_dl3 = st.columns(3)
                            
                            with col_dl1:
                                st.markdown(create_download_link(
                                    resultado['xml'],
                                    f"{os.path.splitext(resultado['nome'])[0]}_DUIMP.xml",
                                    "📥 Baixar XML"
                                ), unsafe_allow_html=True)
                            
                            with col_dl2:
                                if resultado['excel']:
                                    b64_excel = base64.b64encode(resultado['excel']).decode()
                                    href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{os.path.splitext(resultado["nome"])[0]}_RESUMO.xlsx">📊 Baixar Excel</a>'
                                    st.markdown(href_excel, unsafe_allow_html=True)
                            
                            with col_dl3:
                                # Preview do XML
                                if st.button(f"👁️ Preview XML", key=f"preview_{resultado['nome']}"):
                                    st.session_state[f"preview_xml_{resultado['nome']}"] = resultado['xml'][:5000] + "..." if len(resultado['xml']) > 5000 else resultado['xml']
                    
                    # Download em lote
                    if len(resultados) > 1:
                        st.markdown("---")
                        st.subheader("📦 Download em Lote")
                        
                        zip_files = {}
                        for resultado in resultados:
                            xml_filename = f"{os.path.splitext(resultado['nome'])[0]}_DUIMP.xml"
                            zip_files[xml_filename] = resultado['xml']
                            
                            if resultado['excel']:
                                excel_filename = f"{os.path.splitext(resultado['nome'])[0]}_RESUMO.xlsx"
                                zip_files[excel_filename] = resultado['excel']
                        
                        st.markdown(create_zip_download(
                            zip_files,
                            f"DUIMP_Conversao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        ), unsafe_allow_html=True)
        
        with col2:
            st.subheader("📋 Informações do Sistema")
            
            st.markdown("""
            **Formato suportado:**
            - PDF "Extrato de Conferência"
            - Até 500 páginas por arquivo
            - Até 500 itens por processamento
            
            **Campos extraídos:**
            - Dados do importador
            - NCM e descrição
            - Valores e quantidades
            - Tributos calculados
            - Documentos anexos
            
            **XML gerado inclui:**
            - Cabeçalho completo
            - Adições detalhadas
            - Cálculos de tributos
            - Dados de transporte
            - Informações complementares
            """)
            
            st.markdown("---")
            
            # Exemplo de PDF
            st.subheader("📝 Exemplo de Estrutura")
            with st.expander("Ver estrutura esperada do PDF"):
                st.markdown("""
                **Seções esperadas no PDF:**
                
                1. **Cabeçalho**
                   - PROCESSO #28523
                   - HAFELE BRASIL 02.473.058/0001-88
                   - Número 25BR00001916620
                
                2. **Adições/Itens**
                   - Tabela com NCM, descrição, valores
                   - Item | Integracao | NCM | Codigo Produto
                
                3. **Transporte**
                   - Via de Transporte 01 - MARITIMA
                   - Data de Embarque
                   - Peso Bruto
                
                4. **Tributos**
                   - Tabela com II, IPI, PIS, COFINS
                   - Valores Calculados/Devidos/Recolher
                """)
    
    with tab2:
        st.subheader("👁️ Visualização de Dados")
        
        # Exibir preview se disponível
        preview_keys = [k for k in st.session_state.keys() if k.startswith('preview_xml_')]
        
        if preview_keys:
            for key in preview_keys:
                filename = key.replace('preview_xml_', '')
                st.markdown(f"**Preview: {filename}**")
                st.code(st.session_state[key], language='xml')
        else:
            st.info("Clique em 'Preview XML' na aba de conversão para visualizar aqui.")
        
        # Exibir dados estruturados
        if 'resultados' in locals() and resultados:
            st.subheader("📊 Dados Extraídos")
            
            for resultado in resultados:
                with st.expander(f"Dados de {resultado['nome']}"):
                    # DataFrame de resumo
                    df = resultado['conversor'].get_resumo_dataframe()
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                        
                        # Gráfico de valores
                        st.subheader("📈 Distribuição de Valores")
                        col_chart1, col_chart2 = st.columns(2)
                        
                        with col_chart1:
                            if 'Valor Total (R$)' in df.columns:
                                st.bar_chart(df.set_index('Adição')['Valor Total (R$)'])
                        
                        with col_chart2:
                            if 'II (R$)' in df.columns:
                                st.bar_chart(df.set_index('Adição')['II (R$)'])
    
    with tab3:
        st.subheader("⚙️ Configurações Avançadas")
        
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            st.markdown("""
            **Configurações de Extração:**
            
            - **OCR**: Habilitar reconhecimento de texto em imagens
            - **Idioma OCR**: Português (padrão)
            - **Limite de páginas**: 500
            - **Limite de itens**: 500
            - **Timeout por arquivo**: 300 segundos
            """)
            
            # Configurações de mapeamento
            st.subheader("🗺️ Mapeamentos")
            
            mapeamento_ncm = st.text_area(
                "Mapeamento NCM -> Descrição (JSON)",
                value=json.dumps({
                    "83021000": "Outros, para móveis",
                    "39263000": "Guarnições para móveis"
                }, indent=2),
                height=200
            )
            
            try:
                mapeamento_ncm_dict = json.loads(mapeamento_ncm)
                st.success("JSON válido!")
            except:
                st.error("JSON inválido")
        
        with col_config2:
            st.markdown("""
            **Configurações de XML:**
            
            - **Encoding**: UTF-8
            - **Indentação**: 4 espaços
            - **Incluir DTD**: Sim
            - **Validar estrutura**: Sim
            - **Compactar XML**: Não
            """)
            
            # Configurações de tributos
            st.subheader("💰 Alíquotas Padrão")
            
            col_trib1, col_trib2 = st.columns(2)
            
            with col_trib1:
                ii_aliquota = st.number_input("II (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.1)
                ipi_aliquota = st.number_input("IPI (%)", min_value=0.0, max_value=100.0, value=3.25, step=0.1)
            
            with col_trib2:
                pis_aliquota = st.number_input("PIS (%)", min_value=0.0, max_value=100.0, value=2.1, step=0.1)
                cofins_aliquota = st.number_input("COFINS (%)", min_value=0.0, max_value=100.0, value=9.65, step=0.1)
            
            # Salvar configurações
            if st.button("💾 Salvar Configurações"):
                config_salvar = {
                    "ii_aliquota": ii_aliquota,
                    "ipi_aliquota": ipi_aliquota,
                    "pis_aliquota": pis_aliquota,
                    "cofins_aliquota": cofins_aliquota,
                    "mapeamento_ncm": mapeamento_ncm_dict
                }
                
                # Salvar em arquivo
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(config_salvar, f, indent=2)
                    f.flush()
                    
                    # Criar link de download
                    with open(f.name, 'r') as config_file:
                        config_content = config_file.read()
                    
                    st.markdown(create_download_link(
                        config_content,
                        "config_conversor_duimp.json",
                        "📥 Baixar Configurações"
                    ), unsafe_allow_html=True)
                
                st.success("Configurações salvas com sucesso!")
        
        # Logs e debug
        st.markdown("---")
        st.subheader("📋 Logs do Sistema")
        
        if st.button("🔄 Gerar Log de Exemplo"):
            log_content = f"""
            SISTEMA DE CONVERSÃO DUIMP - LOG
            ================================
            Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Versão: 1.0.0
            
            ESTATÍSTICAS:
            - Arquivos processados: {len(uploaded_files) if 'uploaded_files' in locals() else 0}
            - Itens totais: {total_itens if 'total_itens' in locals() else 0}
            - Tempo total: {sum([r['stats']['tempo_processamento'] for r in resultados]) if 'resultados' in locals() else 0:.2f}s
            
            CONFIGURAÇÕES ATIVAS:
            - Usar PyMuPDF: {config['usar_pymupdf']}
            - Máximo de itens: {config['max_itens']}
            - Gerar Excel: {config['gerar_excel']}
            """
            
            st.code(log_content)

# Rodar aplicativo
if __name__ == "__main__":
    main()
