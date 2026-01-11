import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
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
import time
import os
import hashlib
import xml.dom.minidom
import traceback
from pathlib import Path
import numpy as np

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Sistema de Processamento Avançado",
    page_icon="⚡",
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

# --- CSS PROFISSIONAL E ANIMADO ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* Paleta de cores clean - Azul Profissional */
        :root {
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --gradient-primary: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            --gradient-success: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
        }
        
        /* Reset e configurações base */
        .stApp {
            background-color: var(--background);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Container principal responsivo */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        
        /* Header com gradiente */
        .main-header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 3rem 2rem;
            background: var(--gradient-primary);
            border-radius: 20px;
            color: white;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 20px 20px;
            animation: float 20s linear infinite;
        }
        
        .main-title {
            font-size: 3.2rem !important;
            font-weight: 800;
            margin-bottom: 0.5rem;
            position: relative;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .main-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }
        
        /* Abas personalizadas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: var(--surface);
            padding: 8px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            background: white;
            border-radius: 8px;
            padding: 0 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--gradient-primary) !important;
            color: white !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }
        
        .stTabs [aria-selected="false"]:hover {
            border-color: var(--primary);
            transform: translateY(-1px);
        }
        
        /* Cards com efeito glassmorphism */
        .glass-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }
        
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.12);
        }
        
        /* Botões premium */
        .stButton > button {
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 0.85rem 2rem;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: 0.5s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3);
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }
        
        /* Animações avançadas */
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px) scale(0.95); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }
        
        @keyframes float {
            0% { transform: translate(0, 0) rotate(0deg); }
            100% { transform: translate(100px, 100px) rotate(360deg); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        /* Loaders sofisticados */
        .processing-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4rem;
            text-align: center;
            background: var(--surface);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin: 2rem 0;
        }
        
        .spinner-3d {
            width: 80px;
            height: 80px;
            border: 8px solid rgba(37, 99, 235, 0.1);
            border-top: 8px solid var(--primary);
            border-bottom: 8px solid var(--primary);
            border-radius: 50%;
            animation: spin 1.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
            margin-bottom: 1.5rem;
            position: relative;
        }
        
        .spinner-3d::after {
            content: '';
            position: absolute;
            top: -8px;
            left: -8px;
            right: -8px;
            bottom: -8px;
            border: 4px solid transparent;
            border-top: 4px solid rgba(37, 99, 235, 0.2);
            border-radius: 50%;
            animation: spin 2s linear infinite;
        }
        
        .particles {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary-light);
            border-radius: 50%;
            animation: float 15s infinite linear;
        }
        
        /* Estatísticas premium */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2.5rem 0;
        }
        
        .stat-card {
            background: var(--surface);
            border-radius: 16px;
            padding: 1.8rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            border: 1px solid rgba(37, 99, 235, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--gradient-primary);
        }
        
        .stat-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
        }
        
        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0.5rem 0;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.95rem;
            font-weight: 500;
        }
        
        /* File uploader premium */
        .upload-zone {
            border: 3px dashed #cbd5e1;
            border-radius: 20px;
            padding: 4rem 2rem;
            text-align: center;
            background: rgba(255, 255, 255, 0.7);
            transition: all 0.3s ease;
            cursor: pointer;
            margin: 2rem 0;
        }
        
        .upload-zone:hover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.03);
            transform: scale(1.01);
        }
        
        .upload-zone.dragover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.1);
            transform: scale(1.02);
        }
        
        /* Progress bar premium */
        .stProgress > div > div > div {
            background: var(--gradient-primary);
            border-radius: 10px;
            height: 12px;
        }
        
        .stProgress > div > div {
            background: rgba(37, 99, 235, 0.1);
            border-radius: 10px;
            height: 12px;
        }
        
        /* Tooltips e popups */
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background: var(--text-primary);
            color: white;
            text-align: center;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.9rem;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        
        /* Expandable sections */
        .expander-content {
            background: var(--surface);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-left: 4px solid var(--primary);
        }
        
        /* Footer premium */
        .footer {
            text-align: center;
            margin-top: 4rem;
            padding: 3rem 2rem;
            color: var(--text-secondary);
            background: var(--surface);
            border-radius: 20px;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.05);
            position: relative;
            overflow: hidden;
        }
        
        .footer::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
        }
        
        /* Responsividade avançada */
        @media (max-width: 1024px) {
            .main-title {
                font-size: 2.5rem !important;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 640px) {
            .main-title {
                font-size: 2rem !important;
            }
            
            .main-header {
                padding: 2rem 1rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .glass-card {
                padding: 1.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                padding: 0 16px;
                font-size: 0.9rem;
            }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            :root {
                --background: #0f172a;
                --surface: #1e293b;
                --text-primary: #f1f5f9;
                --text-secondary: #cbd5e1;
            }
            
            .glass-card {
                background: rgba(30, 41, 59, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .upload-zone {
                background: rgba(30, 41, 59, 0.5);
                border-color: #475569;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# --- ANIMAÇÕES DE CARREGAMENTO ---
def show_loading_animation(message="Processando..."):
    """Exibe uma animação de carregamento premium"""
    with st.spinner(""):
        placeholder = st.empty()
        with placeholder.container():
            st.markdown(f"""
            <div class="processing-container fade-in">
                <div class="spinner-3d"></div>
                <h3 style="margin-bottom: 0.5rem;">{message}</h3>
                <p style="color: var(--text-secondary);">Por favor, aguarde enquanto processamos seu arquivo</p>
                <div class="particles">
                    {''.join([f'<div class="particle" style="animation-delay: {i*0.1}s; left: {random.randint(10, 90)}%; top: {random.randint(10, 90)}%;"></div>' for i in range(15)])}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        progress_bar.empty()
        placeholder.empty()

def show_processing_animation(message="Analisando dados..."):
    """Exibe animação de processamento premium"""
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div class="processing-container pulse">
            <div class="spinner-3d" style="border-top-color: var(--warning); border-bottom-color: var(--warning);"></div>
            <h3 style="margin-bottom: 0.5rem;">{message}</h3>
            <p style="color: var(--warning); font-weight: 500;">⏳ Esta operação pode levar alguns segundos</p>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(2)
    placeholder.empty()

def show_success_animation(message="Concluído!"):
    """Exibe animação de sucesso premium"""
    success_placeholder = st.empty()
    with success_placeholder.container():
        st.markdown(f"""
        <div class="processing-container" style="border: 2px solid var(--success);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
            <h3 style="color: var(--success);">{message}</h3>
            <p style="color: var(--text-secondary);">Operação realizada com sucesso!</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
    success_placeholder.empty()

# --- FUNÇÕES DO GERADOR XML DUIMP ---
def clean_text(text):
    if not text: return ""
    text = text.replace('\n', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def format_xml_number(value, length=15):
    if not value: return "0" * length
    clean = re.sub(r'[^\d,]', '', str(value)).replace(',', '')
    return clean.zfill(length)

def safe_extract(pattern, text, group=1):
    """Extrai texto ignorando erros de sintaxe de regex mal formada."""
    try:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(group).strip()
    except Exception as e:
        print(f"Erro no regex: {e}")
    return ""

def clean_partnumber(text):
    """Remove rótulos e limpa o código interno."""
    if not text: return ""
    for word in ["CÓDIGO", "CODIGO", "INTERNO", "PARTNUMBER", "PRODUTO", r"\(", r"\)"]:
        text = re.sub(word, "", text, flags=re.IGNORECASE)
    
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.lstrip("- ").strip()
    return text

def parse_pdf(pdf_file):
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() or "" + "\n"

    data = {"header": {}, "itens": []}

    # Cabeçalho
    data["header"]["processo"] = safe_extract(r"PROCESSO\s*#?(\d+)", full_text)
    data["header"]["duimp"] = safe_extract(r"Numero\s*[:\n]*\s*([\dBR]+)", full_text)
    data["header"]["cnpj"] = safe_extract(r"CNPJ\s*[:\n]*\s*([\d\./-]+)", full_text).replace('.', '').replace('/', '').replace('-', '')
    data["header"]["importador"] = "HAFELE BRASIL LTDA"

    # Itens
    raw_itens = re.split(r"ITENS DA DUIMP\s*[-–]?\s*(\d+)", full_text)

    if len(raw_itens) > 1:
        for i in range(1, len(raw_itens), 2):
            num_item = raw_itens[i]
            content = raw_itens[i+1]

            desc_pura = safe_extract(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", content)
            desc_pura = clean_text(desc_pura)

            raw_code = safe_extract(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO|VALOR|NCM)", content)
            codigo_limpo = clean_partnumber(raw_code)

            descricao_final = f"{codigo_limpo} - {desc_pura}" if codigo_limpo else desc_pura

            item = {
                "numero_adicao": num_item.zfill(3),
                "descricao": descricao_final,
                "ncm": safe_extract(r"NCM\s*[:\n]*\s*([\d\.]+)", content).replace(".", "") or "00000000",
                "quantidade": safe_extract(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", content) or "0",
                "valor_unitario": safe_extract(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", content) or "0",
                "valor_total": safe_extract(r"Valor Tot\. Cond Venda\s*[:\n]*\s*([\d\.,]+)", content) or "0",
                "peso_liquido": safe_extract(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", content) or "0",
                "pis": safe_extract(r"PIS.*?Valor Devido.*?([\d\.,]+)", content) or "0",
                "cofins": safe_extract(r"COFINS.*?Valor Devido.*?([\d\.,]+)", content) or "0",
            }
            data["itens"].append(item)
            
    return data

def create_xml(data):
    root = ET.Element("ListaDeclaracoes")
    duimp = ET.SubElement(root, "duimp")

    for item in data["itens"]:
        adicao = ET.SubElement(duimp, "adicao")
        
        ET.SubElement(adicao, "cideValorAliquotaEspecifica").text = "0"*11
        ET.SubElement(adicao, "cideValorDevido").text = "0"*15
        ET.SubElement(adicao, "cideValorRecolher").text = "0"*15
        ET.SubElement(adicao, "codigoRelacaoCompradorVendedor").text = "3"
        ET.SubElement(adicao, "codigoVinculoCompradorVendedor").text = "1"
        ET.SubElement(adicao, "cofinsAliquotaAdValorem").text = "00965"
        ET.SubElement(adicao, "cofinsAliquotaValorRecolher").text = format_xml_number(item["cofins"], 15)
        ET.SubElement(adicao, "condicaoVendaIncoterm").text = "FCA"
        ET.SubElement(adicao, "condicaoVendaMoedaCodigo").text = "978"
        ET.SubElement(adicao, "condicaoVendaValorMoeda").text = format_xml_number(item["valor_total"], 15)
        ET.SubElement(adicao, "dadosMercadoriaAplicacao").text = "REVENDA"
        ET.SubElement(adicao, "dadosMercadoriaCodigoNcm").text = item["ncm"]
        ET.SubElement(adicao, "dadosMercadoriaCondicao").text = "NOVA"
        ET.SubElement(adicao, "dadosMercadoriaPesoLiquido").text = format_xml_number(item["peso_liquido"], 15)
        
        mercadoria = ET.SubElement(adicao, "mercadoria")
        ET.SubElement(mercadoria, "descricaoMercadoria").text = item["descricao"]
        ET.SubElement(mercadoria, "numeroSequencialItem").text = item["numero_adicao"][-2:]
        ET.SubElement(mercadoria, "quantidade").text = format_xml_number(item["quantidade"], 14)
        ET.SubElement(mercadoria, "unidadeMedida").text = "UNIDADE"
        ET.SubElement(mercadoria, "valorUnitario").text = format_xml_number(item["valor_unitario"], 20)
        
        ET.SubElement(adicao, "numeroAdicao").text = item["numero_adicao"]
        duimp_nr = data["header"]["duimp"].replace("25BR", "")[:10]
        ET.SubElement(adicao, "numeroDUIMP").text = duimp_nr
        ET.SubElement(adicao, "pisPasepAliquotaAdValorem").text = "00210"
        ET.SubElement(adicao, "pisPasepAliquotaValorRecolher").text = format_xml_number(item["pis"], 15)
        ET.SubElement(adicao, "relacaoCompradorVendedor").text = "Fabricante é desconhecido"
        ET.SubElement(adicao, "vinculoCompradorVendedor").text = "Não há vinculação entre comprador e vendedor."

    ET.SubElement(duimp, "armazenamentoRecintoAduaneiroNome").text = "TCP - TERMINAL DE CONTEINERES DE PARANAGUA S/A"
    ET.SubElement(duimp, "importadorNome").text = data["header"]["importador"]
    ET.SubElement(duimp, "importadorNumero").text = data["header"]["cnpj"]
    info = ET.SubElement(duimp, "informacaoComplementar")
    info.text = f"PROCESSO: {data['header']['processo']}"
    ET.SubElement(duimp, "numeroDUIMP").text = data["header"]["duimp"]
    ET.SubElement(duimp, "totalAdicoes").text = str(len(data["itens"])).zfill(3)

    return root

def gerador_xml_duimp():
    """Interface para o Gerador de XML DUIMP"""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); font-size: 2.5rem; margin-bottom: 0.5rem;">📄 Gerador XML DUIMP Pro</h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            Transforme extratos PDF da DUIMP em XML estruturado com validação automática
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    file = st.file_uploader(
        "Selecione o Extrato PDF da DUIMP",
        type="pdf",
        help="Arraste e solte ou clique para selecionar o arquivo PDF"
    )
    
    if file:
        st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-value">{file.name[:15]}...</div>
                <div class="stat-label">Arquivo</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            size_mb = len(file.getvalue()) / (1024 * 1024)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">⚖️</div>
                <div class="stat-value">{size_mb:.2f} MB</div>
                <div class="stat-label">Tamanho</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value" style="color: var(--success);">Pronto</div>
                <div class="stat-label">Status</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🚀 Processar e Gerar XML", type="primary", use_container_width=True):
            try:
                show_loading_animation("Analisando estrutura do PDF...")
                res = parse_pdf(file)
                
                if res["itens"]:
                    show_processing_animation("Gerando estrutura XML...")
                    xml_data = create_xml(res)
                    xml_str = ET.tostring(xml_data, 'utf-8')
                    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
                    
                    show_success_animation("Processamento concluído com sucesso!")
                    
                    # Estatísticas do resultado
                    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">📦</div>
                            <div class="stat-value">{len(res["itens"])}</div>
                            <div class="stat-label">Itens</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">🔢</div>
                            <div class="stat-value">#{res["header"]["processo"]}</div>
                            <div class="stat-label">Processo</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">🏷️</div>
                            <div class="stat-value">{res["header"]["duimp"][:10]}...</div>
                            <div class="stat-label">DUIMP</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">🏢</div>
                            <div class="stat-value">{res["header"]["cnpj"][:8]}...</div>
                            <div class="stat-label">CNPJ</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Preview do primeiro item
                    with st.expander("📋 Visualizar Primeiro Item", expanded=True):
                        st.markdown('<div class="expander-content">', unsafe_allow_html=True)
                        st.write("**Descrição:**", res["itens"][0]["descricao"])
                        st.write("**NCM:**", res["itens"][0]["ncm"])
                        st.write("**Quantidade:**", res["itens"][0]["quantidade"])
                        st.write("**Valor Total:**", f"R$ {float(res['itens'][0]['valor_total'].replace('.', '').replace(',', '.')):,.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Botão de download
                    st.markdown('<br>', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([1,2,1])
                    with col2:
                        st.download_button(
                            label="📥 Baixar Arquivo XML",
                            data=pretty,
                            file_name=f"DUIMP_{res['header']['processo']}.xml",
                            mime="text/xml",
                            use_container_width=True,
                            help="Clique para baixar o arquivo XML gerado"
                        )
                    
                else:
                    st.error("⚠️ Não foram encontrados itens válidos no PDF.")
                    st.info("Verifique se o documento contém a estrutura esperada da DUIMP.")
                    
            except Exception as e:
                st.error(f"❌ Erro no processamento: {str(e)}")
                st.markdown('<div class="expander-content" style="border-left-color: var(--error);">', unsafe_allow_html=True)
                st.write("**Detalhes do erro:**", str(e))
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FUNÇÕES DO PROCESSADOR DE ARQUIVOS ---
def processador_txt():
    """Interface para o Processador de TXT"""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); font-size: 2.5rem; margin-bottom: 0.5rem;">📄 Processador de Arquivos TXT</h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            Remova linhas indesejadas de arquivos TXT com substituições inteligentes
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    def detectar_encoding(conteudo):
        """Detecta o encoding do conteúdo do arquivo"""
        resultado = chardet.detect(conteudo)
        return resultado['encoding']

    def processar_arquivo(conteudo, padroes):
        """Processa o conteúdo do arquivo"""
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

    # Configurações
    padroes_default = ["-------", "SPED EFD-ICMS/IPI"]
    
    # Upload do arquivo
    arquivo = st.file_uploader("Selecione o arquivo TXT", type=['txt'], key="txt_uploader")
    
    # Opções avançadas
    with st.expander("⚙️ Configurações Avançadas", expanded=False):
        padroes_adicionais = st.text_input(
            "Padrões adicionais para remoção (separados por vírgula)",
            help="Exemplo: padrão1, padrão2, padrão3",
            key="padroes_adicionais"
        )
        
        padroes = padroes_default + [
            p.strip() for p in padroes_adicionais.split(",") 
            if p.strip()
        ] if padroes_adicionais else padroes_default

    if arquivo is not None:
        if st.button("🔄 Processar Arquivo TXT", type="primary", use_container_width=True):
            try:
                show_loading_animation("Analisando arquivo TXT...")
                conteudo = arquivo.read()
                show_processing_animation("Processando linhas...")
                resultado, total_linhas = processar_arquivo(conteudo, padroes)
                
                if resultado is not None:
                    show_success_animation("Arquivo processado com sucesso!")
                    
                    linhas_processadas = len(resultado.splitlines())
                    
                    # Estatísticas
                    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">📊</div>
                            <div class="stat-value">{total_linhas}</div>
                            <div class="stat-label">Linhas Originais</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">✅</div>
                            <div class="stat-value">{linhas_processadas}</div>
                            <div class="stat-label">Linhas Processadas</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-icon">🗑️</div>
                            <div class="stat-value">{total_linhas - linhas_processadas}</div>
                            <div class="stat-label">Linhas Removidas</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Prévia
                    st.subheader("📋 Prévia do Resultado")
                    st.text_area("Conteúdo processado", resultado, height=300, key="resultado_preview")
                    
                    # Download
                    buffer = BytesIO()
                    buffer.write(resultado.encode('utf-8'))
                    buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Baixar arquivo processado",
                        data=buffer,
                        file_name=f"processado_{arquivo.name}",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")
                st.info("Tente novamente ou verifique o arquivo.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- PROCESSADOR CT-E ---
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
        """Extrai o peso bruto do CT-e"""
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
            
            tipos_peso = ['PESO BRUTO', 'PESO BASE DE CALCULO', 'PESO BASE CÁLCULO', 'PESO']
            
            for prefix, uri in CTE_NAMESPACES.items():
                infQ_elements = root.findall(f'.//{{{uri}}}infQ')
                for infQ in infQ_elements:
                    tpMed = infQ.find(f'{{{uri}}}tpMed')
                    qCarga = infQ.find(f'{{{uri}}}qCarga')
                    
                    if tpMed is not None and tpMed.text and qCarga is not None and qCarga.text:
                        for tipo_peso in tipos_peso:
                            if tipo_peso in tpMed.text.upper():
                                peso = float(qCarga.text)
                                return peso, tipo_peso
            
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
            
            peso_bruto, tipo_peso_encontrado = self.extract_peso_bruto(root)
            
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

def add_simple_trendline(fig, x, y):
    """Adiciona uma linha de tendência simples usando regressão linear básica"""
    try:
        mask = ~np.isnan(x) & ~np.isnan(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) > 1:
            coefficients = np.polyfit(x_clean, y_clean, 1)
            polynomial = np.poly1d(coefficients)
            
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
        pass

def processador_cte():
    """Interface para o sistema de CT-e com extração do peso bruto"""
    processor = CTeProcessorDirect()
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); font-size: 2.5rem; margin-bottom: 0.5rem;">🚚 Processador de CT-e para Power BI</h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            Processa arquivos XML de CT-e e gera planilha para análise
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("ℹ️ Informações sobre a extração do Peso", expanded=True):
        st.markdown("""
        <div class="expander-content">
        **Extração do Peso - Busca Inteligente:**
        
        O sistema busca o peso em **múltiplos campos** na seguinte ordem de prioridade:
        
        1. **PESO BRUTO** - Campo principal
        2. **PESO BASE DE CALCULO** - Campo alternativo 1
        3. **PESO BASE CÁLCULO** - Campo alternativo 2  
        4. **PESO** - Campo genérico
        
        **Resultado:** O sistema mostrará qual tipo de peso foi encontrado em cada CT-e
        </div>
        """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "👀 Visualizar Dados", "📥 Exportar"])
    
    with tab1:
        st.header("Upload de CT-es")
        upload_option = st.radio("Selecione o tipo de upload:", 
                                ["Upload Individual", "Upload em Lote"])
        
        if upload_option == "Upload Individual":
            uploaded_file = st.file_uploader("Selecione um arquivo XML de CT-e", type=['xml'], key="single_cte")
            if uploaded_file and st.button("📊 Processar CT-e", type="primary", key="process_single", use_container_width=True):
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
            if uploaded_files and st.button("📊 Processar Todos", type="primary", key="process_multiple", use_container_width=True):
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
        
        if st.button("🗑️ Limpar Dados Processados", type="secondary", use_container_width=True):
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
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            else:
                show_processing_animation("Gerando arquivo CSV...")
                
                csv = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Baixar Arquivo CSV",
                    data=csv,
                    file_name="dados_cte.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with st.expander("📋 Prévia dos dados a serem exportados"):
                st.dataframe(df_export.head(10))
                
        else:
            st.warning("Nenhum dado disponível para exportação.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- APLICAÇÃO PRINCIPAL ---
def main():
    """Função principal que gerencia o fluxo da aplicação."""
    inject_custom_css()
    
    # Header premium
    st.markdown("""
    <div class="main-header fade-in">
        <h1 class="main-title">⚡ Sistema de Processamento Avançado</h1>
        <p class="main-subtitle">
            Solução completa para processamento de documentos TXT, CT-e e DUIMP XML
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Processador TXT", 
        "🚚 Processador CT-e", 
        "📊 Gerador XML DUIMP",
        "📋 Dashboard"
    ])
    
    with tab1:
        processador_txt()
    
    with tab2:
        processador_cte()
    
    with tab3:
        gerador_xml_duimp()
    
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: var(--primary); font-size: 2.5rem; margin-bottom: 0.5rem;">📋 Dashboard de Atividades</h1>
            <p style="color: var(--text-secondary); font-size: 1.1rem;">
                Visão geral das funcionalidades disponíveis no sistema
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-value">Processador TXT</div>
                <div class="stat-label">
                    • Remoção de linhas indesejadas<br>
                    • Substituições inteligentes<br>
                    • Suporte a múltiplos encodings
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-icon">🚚</div>
                <div class="stat-value">Processador CT-e</div>
                <div class="stat-label">
                    • Extração de peso bruto<br>
                    • Busca inteligente em múltiplos campos<br>
                    • Exportação para Power BI
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">Gerador XML DUIMP</div>
                <div class="stat-label">
                    • Conversão PDF para XML<br>
                    • Validação automática<br>
                    • Estruturação de dados
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Instruções de uso
        with st.expander("📖 Guia Rápido de Uso", expanded=True):
            st.markdown("""
            <div class="expander-content">
            ### 🔧 Como utilizar o sistema:
            
            **1. Processador TXT:**
            - Selecione um arquivo TXT para processar
            - Configure os padrões de remoção desejados
            - Clique em "Processar" para limpar o arquivo
            
            **2. Processador CT-e:**
            - Faça upload de arquivos XML de CT-e
            - Visualize os dados extraídos
            - Exporte para Excel ou CSV
            
            **3. Gerador XML DUIMP:**
            - Carregue o extrato PDF da DUIMP
            - O sistema converte automaticamente para XML
            - Baixe o arquivo XML estruturado
            
            ### 💡 Dicas:
            - Use o modo "Upload em Lote" para processar múltiplos arquivos
            - Configure filtros avançados para análise específica
            - Exporte sempre que possível para backup dos dados
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer premium
    st.markdown("""
    <div class="footer fade-in">
        <div style="max-width: 800px; margin: 0 auto;">
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">
                ⚡ Sistema de Processamento Avançado
            </h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                Solução completa para processamento de documentos empresariais<br>
                Versão 2.0 | Desenvolvido com tecnologia Streamlit
            </p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
                <div style="padding: 0.5rem 1rem; background: rgba(37, 99, 235, 0.1); border-radius: 8px;">
                    <small>📄 TXT Processing</small>
                </div>
                <div style="padding: 0.5rem 1rem; background: rgba(37, 99, 235, 0.1); border-radius: 8px;">
                    <small>🚚 CT-e Extraction</small>
                </div>
                <div style="padding: 0.5rem 1rem; background: rgba(37, 99, 235, 0.1); border-radius: 8px;">
                    <small>📊 XML Generation</small>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")
        st.code(traceback.format_exc())
