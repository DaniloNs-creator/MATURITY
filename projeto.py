import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import sqlite3
from datetime import datetime, timedelta, date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from typing import List, Tuple, Optional
import io
import contextlib
import chardet
from io import BytesIO
import base64
import xml.dom.minidom
import os
import hashlib
import traceback
from pathlib import Path
import numpy as np

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Sistema de Processamento Hafele",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Namespaces para CT-e
CTE_NAMESPACES = {
    'cte': 'http://www.portalfiscal.inf.br/cte'
}

# Inicialização do estado da sessão
if 'selected_xml' not in st.session_state:
    st.session_state.selected_xml = None
if 'cte_data' not in st.session_state:
    st.session_state.cte_data = None

# --- UI PROFESSIONAL & CLEAN (MODERN SAAS STYLE) ---
def apply_clean_ui():
    st.markdown("""
    <style>
    /* Reset e Fundo Sóbrio */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }

    /* Container Principal */
    .main-box {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-top: 2rem;
    }

    /* Cabeçalhos */
    h1 {
        color: #0f172a;
        font-weight: 800;
        font-size: 2.5rem !important;
        letter-spacing: -0.025em;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #2c3e50, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    h2 {
        color: #1e293b;
        font-weight: 700;
        font-size: 1.75rem !important;
        margin: 1.5rem 0 1rem 0;
        padding-left: 10px;
        border-left: 5px solid #2563eb;
    }

    h3 {
        color: #334155;
        font-weight: 600;
        font-size: 1.25rem !important;
    }

    /* Botão Primário Estilo Profissional */
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    }

    /* Barra de Progresso Discreta */
    .stProgress > div > div > div > div {
        background-color: #2563eb;
        border-radius: 4px;
    }

    /* Inputs e Upload */
    .stFileUploader {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 20px;
        background: #f8fafc;
        transition: border-color 0.2s;
    }
    .stFileUploader:hover {
        border-color: #2563eb;
    }

    /* Alertas e Badges */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }

    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        padding: 1.8rem;
        margin-bottom: 1.8rem;
        border: 1px solid #e2e8f0;
    }

    /* Cover Container */
    .cover-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .cover-logo {
        max-width: 350px;
        margin: 0 auto 1.5rem auto;
        display: block;
        filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
    }
    .cover-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: #1e3a8a;
        text-align: center;
    }
    .cover-subtitle {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 0;
        font-weight: 500;
        text-align: center;
    }

    /* Logo Container */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    .logo-img {
        max-height: 80px;
        object-fit: contain;
    }

    /* Spinner Animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinner {
        animation: spin 2s linear infinite;
        display: inline-block;
        font-size: 24px;
    }

    /* Métricas */
    .stMetric {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
    }

    /* Dataframe */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO (DUIMP) ---
def clean_val(val):
    if not val: return "0"
    return re.sub(r'[^\d,]', '', str(val)).replace(',', '')

def format_xml_num(val, length):
    return clean_val(val).zfill(length)

def clean_partnumber(text):
    if not text: return ""
    # Remove rótulos preservando o código
    words = ["CÓDIGO", "CODIGO", "INTERNO", "PARTNUMBER", r"\(", r"\)"]
    for w in words:
        text = re.search(f"{w}(.*)", text, re.I).group(1) if re.search(w, text, re.I) else text
    return re.sub(r'\s+', ' ', text).strip().lstrip("- ").strip()

# --- EXTRAÇÃO DO PDF (DUIMP) ---
def parse_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    
    data = {"header": {}, "itens": []}
    data["header"]["processo"] = re.search(r"PROCESSO\s*#?(\d+)", text, re.I).group(1) if re.search(r"PROCESSO\s*#?(\d+)", text, re.I) else "N/A"
    data["header"]["duimp"] = re.search(r"Numero\s*[:\n]*\s*([\dBR]+)", text, re.I).group(1) if re.search(r"Numero\s*[:\n]*\s*([\dBR]+)", text, re.I) else "N/A"
    
    parts = re.split(r"ITENS DA DUIMP\s*[-–]?\s*(\d+)", text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            num = parts[i]
            block = parts[i+1]
            
            raw_desc = re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S).group(1) if re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S) else ""
            raw_pn = re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S).group(1) if re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S) else ""
            
            pn = clean_partnumber(raw_pn)
            final_desc = f"{pn} - {re.sub(r'\s+', ' ', raw_desc).strip()}" if pn else raw_desc
            
            data["itens"].append({
                "seq": num,
                "descricao": final_desc,
                "ncm": re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block).group(1).replace(".", "") if re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block) else "00000000",
                "peso": re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block) else "0",
                "qtd": re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block) else "0",
                "v_unit": re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block) else "0"
            })
    return data

# --- GERADOR XML (ESTRUTURA HAFELE OBRIGATÓRIA) ---
def generate_xml(data):
    root = ET.Element("ListaDeclaracoes")
    duimp = ET.SubElement(root, "duimp")
    
    for item in data["itens"]:
        ad = ET.SubElement(duimp, "adicao")
        
        # Estrutura obrigatória conforme arquivo enviado
        acr = ET.SubElement(ad, "acrescimo")
        ET.SubElement(acr, "codigoAcrescimo").text = "17"
        ET.SubElement(acr, "denominacao").text = "OUTROS ACRESCIMOS AO VALOR ADUANEIRO"
        ET.SubElement(acr, "moedaNegociadaCodigo").text = "978"
        ET.SubElement(acr, "valorReais").text = "000000000106601"
        
        # Tags de controle e impostos
        ET.SubElement(ad, "codigoRelacaoCompradorVendedor").text = "3"
        ET.SubElement(ad, "codigoVinculoCompradorVendedor").text = "1"
        ET.SubElement(ad, "cofinsAliquotaAdValorem").text = "00965"
        ET.SubElement(ad, "dadosMercadoriaCodigoNcm").text = item["ncm"]
        ET.SubElement(ad, "dadosMercadoriaPesoLiquido").text = format_xml_num(item["peso"], 15)
        
        # Tag Mercadoria (Onde entra a Descrição + PN)
        merc = ET.SubElement(ad, "mercadoria")
        ET.SubElement(merc, "descricaoMercadoria").text = item["descricao"]
        ET.SubElement(merc, "numeroSequencialItem").text = item["seq"].zfill(2)
        ET.SubElement(merc, "quantidade").text = format_xml_num(item["qtd"], 14)
        ET.SubElement(merc, "unidadeMedida").text = "UNIDADE"
        ET.SubElement(merc, "valorUnitario").text = format_xml_num(item["v_unit"], 20)
        
        ET.SubElement(ad, "numeroAdicao").text = item["seq"].zfill(3)
        ET.SubElement(ad, "numeroDUIMP").text = data["header"]["duimp"].replace("25BR", "")[:10]
        ET.SubElement(ad, "pisPasepAliquotaAdValorem").text = "00210"

    ET.SubElement(duimp, "importadorNome").text = "HAFELE BRASIL LTDA"
    ET.SubElement(duimp, "totalAdicoes").text = str(len(data["itens"])).zfill(3)
    ET.SubElement(duimp, "urfDespachoNome").text = "PORTO DE PARANAGUA"
    
    return root

# --- ANIMAÇÕES DE CARREGAMENTO ---
def show_loading_animation(message="Processando..."):
    """Exibe uma animação de carregamento"""
    with st.spinner(message):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.005)
            progress_bar.progress(i + 1)
        progress_bar.empty()

def show_processing_animation(message="Analisando dados..."):
    """Exibe animação de processamento"""
    placeholder = st.empty()
    with placeholder.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(f"⏳ {message}")
            spinner_placeholder = st.empty()
            spinner_chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
            for i in range(20):
                spinner_placeholder.markdown(f"<div style='text-align: center; font-size: 24px;'>{spinner_chars[i % 8]}</div>", unsafe_allow_html=True)
                time.sleep(0.05)
    placeholder.empty()

def show_success_animation(message="Concluído!"):
    """Exibe animação de sucesso"""
    success_placeholder = st.empty()
    with success_placeholder.container():
        st.success(f"✅ {message}")
        time.sleep(1.5)
    success_placeholder.empty()

# --- FUNÇÕES DO PROCESSADOR DE ARQUIVOS TXT ---
def detectar_encoding(conteudo):
    """Detecta o encoding do conteúdo do arquivo"""
    resultado = chardet.detect(conteudo)
    return resultado['encoding']

def processar_arquivo_txt(conteudo, padroes):
    """
    Processa o conteúdo do arquivo removendo linhas indesejadas e realizando substituições
    """
    try:
        substituicoes = {
            "IMPOSTO IMPORTACAO": "IMP IMPORT",
            "TAXA SICOMEX": "TX SISCOMEX",
            "FRETE INTERNACIONAL": "FRET INTER",
            "SEGURO INTERNACIONAL": "SEG INTERN"
        }
        
        encoding = detectar_encoding(conteudo)
        
        try:
            texto = conteudo.decode(encoding)
        except UnicodeDecodeError:
            texto = conteudo.decode('latin-1')
        
        linhas = texto.splitlines()
        linhas_processadas = []
        
        for linha in linhas:
            linha = linha.strip()
            if not any(padrao in linha for padrao in padroes):
                for original, substituto in substituicoes.items():
                    linha = linha.replace(original, substituto)
                linhas_processadas.append(linha)
        
        return "\n".join(linhas_processadas), len(linhas)
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        return None, 0

# --- PROCESSADOR CT-E COM EXTRAÇÃO DO PESO BRUTO E PESO BASE DE CÁLCULO ---
class CTeProcessorDirect:
    def __init__(self):
        self.processed_data = []
    
    def extract_nfe_number_from_key(self, chave_acesso):
        """Extrai o número da NF-e da chave de acesso"""
        if not chave_acesso or len(chave_acesso) != 44:
            return None
        
        try:
            numero_nfe = chave_acesso[25:34]
            return numero_nfe
        except Exception:
            return None
    
    def extract_peso_bruto(self, root):
        """Extrai o peso bruto do CT-e - BUSCA EM PESO BRUTO E PESO BASE DE CÁLCULO"""
        try:
            def find_text(element, xpath):
                try:
                    for prefix, uri in CTE_NAMESPACES.items():
                        full_xpath = xpath.replace('cte:', f'{{{uri}}}')
                        found = element.find(full_xpath)
                        if found is not None and found.text:
                            return found.text
                    
                    found = element.find(xpath.replace('cte:', ''))
                    if found is not None and found.text:
                        return found.text
                    return None
                except Exception:
                    return None
            
            # Lista de tipos de peso a serem procurados (em ordem de prioridade)
            tipos_peso = ['PESO BRUTO', 'PESO BASE DE CALCULO', 'PESO BASE CÁLCULO', 'PESO']
            
            # Busca por todas as tags infQ com namespaces
            for prefix, uri in CTE_NAMESPACES.items():
                infQ_elements = root.findall(f'.//{{{uri}}}infQ')
                for infQ in infQ_elements:
                    tpMed = infQ.find(f'{{{uri}}}tpMed')
                    qCarga = infQ.find(f'{{{uri}}}qCarga')
                    
                    if tpMed is not None and tpMed.text and qCarga is not None and qCarga.text:
                        # Verifica cada tipo de peso na ordem de prioridade
                        for tipo_peso in tipos_peso:
                            if tipo_peso in tpMed.text.upper():
                                peso = float(qCarga.text)
                                return peso, tipo_peso  # Retorna o peso e o tipo encontrado
            
            # Tentativa alternativa sem namespace
            infQ_elements = root.findall('.//infQ')
            for infQ in infQ_elements:
                tpMed = infQ.find('tpMed')
                qCarga = infQ.find('qCarga')
                
                if tpMed is not None and tpMed.text and qCarga is not None and qCarga.text:
                    for tipo_peso in tipos_peso:
                        if tipo_peso in tpMed.text.upper():
                            peso = float(qCarga.text)
                            return peso, tipo_peso
            
            return 0.0, "Não encontrado"
            
        except Exception as e:
            st.warning(f"Não foi possível extrair o peso: {str(e)}")
            return 0.0, "Erro na extração"
    
    def extract_cte_data(self, xml_content, filename):
        """Extrai dados específicos do CT-e incluindo peso bruto"""
        try:
            root = ET.fromstring(xml_content)
            
            for prefix, uri in CTE_NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            def find_text(element, xpath):
                try:
                    for prefix, uri in CTE_NAMESPACES.items():
                        full_xpath = xpath.replace('cte:', f'{{{uri}}}')
                        found = element.find(full_xpath)
                        if found is not None and found.text:
                            return found.text
                    
                    found = element.find(xpath.replace('cte:', ''))
                    if found is not None and found.text:
                        return found.text
                    return None
                except Exception:
                    return None
            
            # Extrai dados do CT-e
            nCT = find_text(root, './/cte:nCT')
            dhEmi = find_text(root, './/cte:dhEmi')
            cMunIni = find_text(root, './/cte:cMunIni')
            UFIni = find_text(root, './/cte:UFIni')
            cMunFim = find_text(root, './/cte:cMunFim')
            UFFim = find_text(root, './/cte:UFFim')
            emit_xNome = find_text(root, './/cte:emit/cte:xNome')
            vTPrest = find_text(root, './/cte:vTPrest')
            rem_xNome = find_text(root, './/cte:rem/cte:xNome')
            
            # Extrai dados do destinatário
            dest_xNome = find_text(root, './/cte:dest/cte:xNome')
            dest_CNPJ = find_text(root, './/cte:dest/cte:CNPJ')
            dest_CPF = find_text(root, './/cte:dest/cte:CPF')
            
            documento_destinatario = dest_CNPJ or dest_CPF or 'N/A'
            
            # Extrai endereço do destinatário
            dest_xLgr = find_text(root, './/cte:dest/cte:enderDest/cte:xLgr')
            dest_nro = find_text(root, './/cte:dest/cte:enderDest/cte:nro')
            dest_xBairro = find_text(root, './/cte:dest/cte:enderDest/cte:xBairro')
            dest_cMun = find_text(root, './/cte:dest/cte:enderDest/cte:cMun')
            dest_xMun = find_text(root, './/cte:dest/cte:enderDest/cte:xMun')
            dest_CEP = find_text(root, './/cte:dest/cte:enderDest/cte:CEP')
            dest_UF = find_text(root, './/cte:dest/cte:enderDest/cte:UF')
            
            # Monta endereço completo
            endereco_destinatario = ""
            if dest_xLgr:
                endereco_destinatario += f"{dest_xLgr}"
                if dest_nro:
                    endereco_destinatario += f", {dest_nro}"
                if dest_xBairro:
                    endereco_destinatario += f" - {dest_xBairro}"
                if dest_xMun:
                    endereco_destinatario += f", {dest_xMun}"
                if dest_UF:
                    endereco_destinatario += f"/{dest_UF}"
                if dest_CEP:
                    endereco_destinatario += f" - CEP: {dest_CEP}"
            
            if not endereco_destinatario:
                endereco_destinatario = "N/A"
            
            infNFe_chave = find_text(root, './/cte:infNFe/cte:chave')
            numero_nfe = self.extract_nfe_number_from_key(infNFe_chave) if infNFe_chave else None
            
            # EXTRAI O PESO BRUTO - AGORA COM BUSCA EM MÚLTIPLOS CAMPOS
            peso_bruto, tipo_peso_encontrado = self.extract_peso_bruto(root)
            
            # Formata data
            data_formatada = None
            if dhEmi:
                try:
                    try:
                        data_obj = datetime.strptime(dhEmi[:10], '%Y-%m-%d')
                    except:
                        try:
                            data_obj = datetime.strptime(dhEmi[:10], '%d/%m/%Y')
                        except:
                            data_obj = datetime.strptime(dhEmi[:10], '%d/%m/%y')
                    data_formatada = data_obj.strftime('%d/%m/%y')
                except:
                    data_formatada = dhEmi[:10]
            
            # Converte valor para decimal
            try:
                vTPrest = float(vTPrest) if vTPrest else 0.0
            except (ValueError, TypeError):
                vTPrest = 0.0
            
            return {
                'Arquivo': filename,
                'nCT': nCT or 'N/A',
                'Data Emissão': data_formatada or dhEmi or 'N/A',
                'Código Município Início': cMunIni or 'N/A',
                'UF Início': UFIni or 'N/A',
                'Código Município Fim': cMunFim or 'N/A',
                'UF Fim': UFFim or 'N/A',
                'Emitente': emit_xNome or 'N/A',
                'Valor Prestação': vTPrest,
                'Peso Bruto (kg)': peso_bruto,
                'Tipo de Peso Encontrado': tipo_peso_encontrado,
                'Remetente': rem_xNome or 'N/A',
                'Destinatário': dest_xNome or 'N/A',
                'Documento Destinatário': documento_destinatario,
                'Endereço Destinatário': endereco_destinatario,
                'Município Destino': dest_xMun or 'N/A',
                'UF Destino': dest_UF or 'N/A',
                'Chave NFe': infNFe_chave or 'N/A',
                'Número NFe': numero_nfe or 'N/A',
                'Data Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
        except Exception as e:
            st.error(f"Erro ao extrair dados do CT-e {filename}: {str(e)}")
            return None
    
    def process_single_file(self, uploaded_file):
        """Processa um único arquivo XML de CT-e"""
        try:
            file_content = uploaded_file.getvalue()
            filename = uploaded_file.name
            
            if not filename.lower().endswith('.xml'):
                return False, "Arquivo não é XML"
            
            content_str = file_content.decode('utf-8', errors='ignore')
            if 'CTe' not in content_str and 'conhecimento' not in content_str.lower():
                return False, "Arquivo não parece ser um CT-e"
            
            cte_data = self.extract_cte_data(content_str, filename)
            
            if cte_data:
                self.processed_data.append(cte_data)
                return True, f"CT-e {filename} processado com sucesso!"
            else:
                return False, f"Erro ao processar CT-e {filename}"
                
        except Exception as e:
            return False, f"Erro ao processar arquivo {filename}: {str(e)}"
    
    def process_multiple_files(self, uploaded_files):
        """Processa múltiplos arquivos XML de CT-e"""
        results = {
            'success': 0,
            'errors': 0,
            'messages': []
        }
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processando {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            success, message = self.process_single_file(uploaded_file)
            if success:
                results['success'] += 1
            else:
                results['errors'] += 1
            results['messages'].append(message)
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    def get_dataframe(self):
        """Retorna os dados processados como DataFrame"""
        if self.processed_data:
            return pd.DataFrame(self.processed_data)
        return pd.DataFrame()
    
    def clear_data(self):
        """Limpa os dados processados"""
        self.processed_data = []

# --- FUNÇÃO PARA CRIAR LINHA DE TENDÊNCIA SIMPLES SEM STATSMODELS ---
def add_simple_trendline(fig, x, y):
    """Adiciona uma linha de tendência simples usando regressão linear básica"""
    try:
        # Remove valores NaN
        mask = ~np.isnan(x) & ~np.isnan(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) > 1:
            # Regressão linear simples
            coefficients = np.polyfit(x_clean, y_clean, 1)
            polynomial = np.poly1d(coefficients)
            
            # Gera pontos para a linha de tendência
            x_trend = np.linspace(x_clean.min(), x_clean.max(), 100)
            y_trend = polynomial(x_trend)
            
            fig.add_trace(go.Scatter(
                x=x_trend, 
                y=y_trend,
                mode='lines',
                name='Linha de Tendência',
                line=dict(color='red', dash='dash'),
                opacity=0.7
            ))
    except Exception:
        # Se houver erro, simplesmente não adiciona a linha de tendência
        pass

# --- FUNÇÃO PRINCIPAL DO PROCESSADOR CT-E ---
def processador_cte():
    """Interface para o sistema de CT-e com extração do peso bruto"""
    processor = CTeProcessorDirect()
    
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    
    st.title("🚚 Processador de CT-e para Power BI")
    st.markdown("### Processa arquivos XML de CT-e e gera planilha para análise")
    
    with st.expander("ℹ️ Informações sobre a extração do Peso", expanded=True):
        st.markdown("""
        **Extração do Peso - Busca Inteligente:**
        
        O sistema agora busca o peso em **múltiplos campos** na seguinte ordem de prioridade:
        
        1. **PESO BRUTO** - Campo principal
        2. **PESO BASE DE CALCULO** - Campo alternativo 1
        3. **PESO BASE CÁLCULO** - Campo alternativo 2  
        4. **PESO** - Campo genérico
        
        **Exemplos de campos reconhecidos:**
        ```xml
        <infQ>
            <tpMed>PESO BRUTO</tpMed>
            <qCarga>319.8000</qCarga>
        </infQ>
        ```
        ```xml
        <infQ>
            <tpMed>PESO BASE DE CALCULO</tpMed>
            <qCarga>250.5000</qCarga>
        </infQ>
        ```
        
        **Resultado:** O sistema mostrará qual tipo de peso foi encontrado em cada CT-e
        """)
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "👀 Visualizar Dados", "📥 Exportar"])
    
    with tab1:
        st.header("Upload de CT-es")
        upload_option = st.radio("Selecione o tipo de upload:", 
                                ["Upload Individual", "Upload em Lote"])
        
        if upload_option == "Upload Individual":
            uploaded_file = st.file_uploader("Selecione um arquivo XML de CT-e", type=['xml'], key="single_cte")
            if uploaded_file and st.button("📊 Processar CT-e", key="process_single"):
                show_loading_animation("Analisando estrutura do XML...")
                show_processing_animation("Extraindo dados do CT-e...")
                
                success, message = processor.process_single_file(uploaded_file)
                if success:
                    show_success_animation("CT-e processado com sucesso!")
                    
                    df = processor.get_dataframe()
                    if not df.empty:
                        ultimo_cte = df.iloc[-1]
                        st.info(f"""
                        **Extração bem-sucedida:**
                        - **Peso encontrado:** {ultimo_cte['Peso Bruto (kg)']} kg
                        - **Tipo de peso:** {ultimo_cte['Tipo de Peso Encontrado']}
                        """)
                else:
                    st.error(message)
        
        else:
            uploaded_files = st.file_uploader("Selecione múltiplos arquivos XML de CT-e", 
                                            type=['xml'], 
                                            accept_multiple_files=True,
                                            key="multiple_cte")
            if uploaded_files and st.button("📊 Processar Todos", key="process_multiple"):
                show_loading_animation(f"Iniciando processamento de {len(uploaded_files)} arquivos...")
                
                results = processor.process_multiple_files(uploaded_files)
                show_success_animation("Processamento em lote concluído!")
                
                st.success(f"""
                **Processamento concluído!**  
                ✅ Sucessos: {results['success']}  
                ❌ Erros: {results['errors']}
                """)
                
                df = processor.get_dataframe()
                if not df.empty:
                    # Estatísticas dos tipos de peso encontrados
                    tipos_peso = df['Tipo de Peso Encontrado'].value_counts()
                    peso_total = df['Peso Bruto (kg)'].sum()
                    
                    st.info(f"""
                    **Estatísticas de extração:**
                    - Peso bruto total: {peso_total:,.2f} kg
                    - Peso médio por CT-e: {df['Peso Bruto (kg)'].mean():,.2f} kg
                    - Tipos de peso encontrados:
                    """)
                    
                    for tipo, quantidade in tipos_peso.items():
                        st.write(f"  - **{tipo}**: {quantidade} CT-e(s)")
                
                if results['errors'] > 0:
                    with st.expander("Ver mensagens detalhadas"):
                        for msg in results['messages']:
                            st.write(f"- {msg}")
        
        if st.button("🗑️ Limpar Dados Processados", type="secondary"):
            processor.clear_data()
            st.success("Dados limpos com sucesso!")
            time.sleep(1)
            st.rerun()
    
    with tab2:
        st.header("Dados Processados")
        df = processor.get_dataframe()
        
        if not df.empty:
            st.write(f"Total de CT-es processados: {len(df)}")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                uf_filter = st.multiselect("Filtrar por UF Início", options=df['UF Início'].unique())
            with col2:
                uf_destino_filter = st.multiselect("Filtrar por UF Destino", options=df['UF Destino'].unique())
            with col3:
                tipo_peso_filter = st.multiselect("Filtrar por Tipo de Peso", options=df['Tipo de Peso Encontrado'].unique())
            
            # Filtro de peso
            st.subheader("Filtro por Peso Bruto")
            peso_min = float(df['Peso Bruto (kg)'].min())
            peso_max = float(df['Peso Bruto (kg)'].max())
            peso_filter = st.slider("Selecione a faixa de peso (kg)", peso_min, peso_max, (peso_min, peso_max))
            
            # Aplicar filtros
            filtered_df = df.copy()
            if uf_filter:
                filtered_df = filtered_df[filtered_df['UF Início'].isin(uf_filter)]
            if uf_destino_filter:
                filtered_df = filtered_df[filtered_df['UF Destino'].isin(uf_destino_filter)]
            if tipo_peso_filter:
                filtered_df = filtered_df[filtered_df['Tipo de Peso Encontrado'].isin(tipo_peso_filter)]
            filtered_df = filtered_df[
                (filtered_df['Peso Bruto (kg)'] >= peso_filter[0]) & 
                (filtered_df['Peso Bruto (kg)'] <= peso_filter[1])
            ]
            
            # Exibir dataframe
            colunas_principais = [
                'Arquivo', 'nCT', 'Data Emissão', 'Emitente', 'Remetente', 
                'Destinatário', 'UF Início', 'UF Destino', 'Peso Bruto (kg)', 
                'Tipo de Peso Encontrado', 'Valor Prestação'
            ]
            
            st.dataframe(filtered_df[colunas_principais], use_container_width=True)
            
            with st.expander("📋 Ver todos os campos detalhados"):
                st.dataframe(filtered_df, use_container_width=True)
            
            # Estatísticas
            st.subheader("📈 Estatísticas")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Valor Prestação", f"R$ {filtered_df['Valor Prestação'].sum():,.2f}")
            col2.metric("Peso Bruto Total", f"{filtered_df['Peso Bruto (kg)'].sum():,.2f} kg")
            col3.metric("Média Peso/CT-e", f"{filtered_df['Peso Bruto (kg)'].mean():,.2f} kg")
            col4.metric("Tipos de Peso", f"{filtered_df['Tipo de Peso Encontrado'].nunique()}")
            
            # Gráficos
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("📊 Distribuição por Tipo de Peso")
                if not filtered_df.empty:
                    tipo_counts = filtered_df['Tipo de Peso Encontrado'].value_counts()
                    fig_tipo = px.pie(
                        values=tipo_counts.values,
                        names=tipo_counts.index,
                        title="Distribuição por Tipo de Peso Encontrado"
                    )
                    st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col_chart2:
                st.subheader("📈 Relação Peso x Valor")
                if not filtered_df.empty:
                    fig_relacao = px.scatter(
                        filtered_df,
                        x='Peso Bruto (kg)',
                        y='Valor Prestação',
                        title="Relação entre Peso Bruto e Valor da Prestação",
                        color='Tipo de Peso Encontrado'
                    )
                    
                    if st.checkbox("Mostrar linha de tendência", key="trendline"):
                        add_simple_trendline(fig_relacao, 
                                           filtered_df['Peso Bruto (kg)'].values, 
                                           filtered_df['Valor Prestação'].values)
                    
                    st.plotly_chart(fig_relacao, use_container_width=True)
            
        else:
            st.info("Nenhum CT-e processado ainda. Faça upload de arquivos na aba 'Upload'.")
    
    with tab3:
        st.header("Exportar para Excel")
        df = processor.get_dataframe()
        
        if not df.empty:
            st.success(f"Pronto para exportar {len(df)} registros")
            
            export_option = st.radio("Formato de exportação:", 
                                   ["Excel (.xlsx)", "CSV (.csv)"])
            
            st.subheader("Selecionar Colunas para Exportação")
            todas_colunas = df.columns.tolist()
            colunas_selecionadas = st.multiselect(
                "Selecione as colunas para exportar:",
                options=todas_colunas,
                default=todas_colunas
            )
            
            df_export = df[colunas_selecionadas] if colunas_selecionadas else df
            
            if export_option == "Excel (.xlsx)":
                show_processing_animation("Gerando arquivo Excel...")
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, sheet_name='Dados_CTe', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="📥 Baixar Planilha Excel",
                    data=output,
                    file_name="dados_cte.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            else:
                show_processing_animation("Gerando arquivo CSV...")
                
                csv = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Baixar Arquivo CSV",
                    data=csv,
                    file_name="dados_cte.csv",
                    mime="text/csv"
                )
            
            with st.expander("📋 Prévia dos dados a serem exportados"):
                st.dataframe(df_export.head(10))
                
        else:
            st.warning("Nenhum dado disponível para exportação.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL DO PROCESSADOR TXT ---
def processador_txt_tab():
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    
    st.title("📄 Processador de Arquivos TXT")
    st.markdown("""
    <div class="card">
        Remova linhas indesejadas de arquivos TXT. Carregue seu arquivo e defina os padrões a serem removidos.
    </div>
    """, unsafe_allow_html=True)
    
    # Padrões padrão para remoção
    padroes_default = ["-------", "SPED EFD-ICMS/IPI"]
    
    # Upload do arquivo
    arquivo = st.file_uploader("Selecione o arquivo TXT", type=['txt'])
    
    # Opções avançadas
    with st.expander("⚙️ Configurações avançadas", expanded=False):
        padroes_adicionais = st.text_input(
            "Padrões adicionais para remoção (separados por vírgula)",
            help="Exemplo: padrão1, padrão2, padrão3"
        )
        
        padroes = padroes_default + [
            p.strip() for p in padroes_adicionais.split(",") 
            if p.strip()
        ] if padroes_adicionais else padroes_default

    if arquivo is not None:
        if st.button("🔄 Processar Arquivo TXT"):
            try:
                show_loading_animation("Analisando arquivo TXT...")
                conteudo = arquivo.read()
                show_processing_animation("Processando linhas...")
                resultado, total_linhas = processar_arquivo_txt(conteudo, padroes)
                
                if resultado is not None:
                    show_success_animation("Arquivo processado com sucesso!")
                    
                    linhas_processadas = len(resultado.splitlines())
                    st.success(f"""
                    **Processamento concluído!**  
                    ✔️ Linhas originais: {total_linhas}  
                    ✔️ Linhas processadas: {linhas_processadas}  
                    ✔️ Linhas removidas: {total_linhas - linhas_processadas}
                    """)

                    st.subheader("Prévia do resultado")
                    st.text_area("Conteúdo processado", resultado, height=300)

                    buffer = BytesIO()
                    buffer.write(resultado.encode('utf-8'))
                    buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Baixar arquivo processado",
                        data=buffer,
                        file_name=f"processado_{arquivo.name}",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")
                st.info("Tente novamente ou verifique o arquivo.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL DO CONVERSOR DUIMP ---
def conversor_duimp_tab():
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    
    st.title("Conversor de DUIMP")
    st.markdown("Extração de dados para o layout XML Hafele.")
    
    uploaded_file = st.file_uploader("Selecione o Extrato de Conferência (PDF)", type="pdf")
    
    if uploaded_file:
        if st.button("PROCESSAR ARQUIVO"):
            with st.spinner("Extraindo dados..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.005)
                    progress.progress(i + 1)
                
                try:
                    res = parse_pdf(uploaded_file)
                    if res["itens"]:
                        xml_root = generate_xml(res)
                        xml_output = minidom.parseString(ET.tostring(xml_root, 'utf-8')).toprettyxml(indent="    ")
                        
                        st.success("Arquivo processado com sucesso.")
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total de Itens", len(res["itens"]))
                        col2.metric("Nº Processo", res["header"]["processo"])
                        
                        st.markdown("---")
                        st.markdown("**Validação de Descrição (Item 1):**")
                        st.text(res["itens"][0]["descricao"])
                        
                        st.download_button(
                            label="BAIXAR XML COMPATÍVEL",
                            data=xml_output,
                            file_name=f"DUIMP_{res['header']['processo']}.xml",
                            mime="text/xml"
                        )
                    else:
                        st.error("Nenhum item identificado no PDF.")
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- APLICAÇÃO PRINCIPAL ---
def main():
    """Função principal que gerencia o fluxo da aplicação."""
    apply_clean_ui()
    
    # Header com logo e título
    st.markdown("""
    <div class="cover-container">
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/DaniloNs-creator/final/main/haefele_logo.png" 
                 alt="Hafele Logo" 
                 class="cover-logo">
        </div>
        <h1 class="cover-title">Sistema de Processamento Hafele</h1>
        <p class="cover-subtitle">Processamento integrado de DUIMP, TXT e CT-e para análise de dados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cria abas
    tab1, tab2, tab3 = st.tabs(["📄 Conversor DUIMP", "📄 Processador TXT", "🚚 Processador CT-e"])
    
    with tab1:
        conversor_duimp_tab()
    
    with tab2:
        processador_txt_tab()
    
    with tab3:
        processador_cte()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")
        st.code(traceback.format_exc())
