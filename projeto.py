import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import os
from io import BytesIO
import zipfile
import base64

# Configuração inicial da página
st.set_page_config(
    page_title="Sistema de Apuração Fiscal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    /* Estilos gerais */
    .main {
        background-color: #f5f5f5;
    }
    
    /* Cabeçalhos */
    h1, h2, h3 {
        color: #2c3e50;
    }
    
    /* Botões */
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        margin: 5px;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 20px;
        background-color: #ecf0f1;
        border-radius: 5px 5px 0 0;
        gap: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3498db;
        color: white;
    }
    
    /* Cards */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
        color: white;
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    
    /* Tabelas */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    th {
        background-color: #3498db;
        color: white;
    }
    
    tr:hover {
        background-color: #f5f5f5;
    }
    
    /* Capa */
    .cover {
        text-align: center;
        padding: 50px 0;
        background: linear-gradient(135deg, #3498db, #2c3e50);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .cover h1 {
        color: white;
        font-size: 3em;
    }
    
    .cover p {
        font-size: 1.2em;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            padding: 0 10px;
            font-size: 0.8em;
        }
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares para processamento dos XMLs
def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Namespace da NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Extrair dados básicos
        inf_nfe = root.find('.//nfe:infNFe', ns)
        if inf_nfe is None:
            # Tentar outro namespace (alguns XMLs podem ter diferenças)
            ns = {'ns2': 'http://www.portalfiscal.inf.br/nfe'}
            inf_nfe = root.find('.//ns2:infNFe', ns)
        
        ide = inf_nfe.find('.//nfe:ide', ns)
        emit = inf_nfe.find('.//nfe:emit', ns)
        dest = inf_nfe.find('.//nfe:dest', ns)
        total = inf_nfe.find('.//nfe:total', ns)
        dets = inf_nfe.findall('.//nfe:det', ns)
        
        # Dados da NFe
        nfe_data = {
            'chave': inf_nfe.get('Id')[3:],  # Remover 'NFe' do início
            'numero': ide.find('nfe:nNF', ns).text,
            'serie': ide.find('nfe:serie', ns).text,
            'data_emissao': ide.find('nfe:dhEmi', ns).text,
            'emitente_cnpj': emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else '',
            'destinatario_cnpj': dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else '',
            'valor_total': total.find('.//nfe:vNF', ns).text,
            'itens': []
        }
        
        # Processar cada item
        for det in dets:
            prod = det.find('nfe:prod', ns)
            imposto = det.find('nfe:imposto', ns)
            
            # ICMS
            icms = imposto.find('nfe:ICMS', ns)
            icms_node = None
            for node in icms:
                if node.tag.endswith('ICMS00') or node.tag.endswith('ICMS10') or node.tag.endswith('ICMS20') or \
                   node.tag.endswith('ICMS30') or node.tag.endswith('ICMS40') or node.tag.endswith('ICMS51') or \
                   node.tag.endswith('ICMS60') or node.tag.endswith('ICMS70') or node.tag.endswith('ICMS90') or \
                   node.tag.endswith('ICMSPart') or node.tag.endswith('ICMSST'):
                    icms_node = node
                    break
            
            # IPI
            ipi = imposto.find('nfe:IPI', ns)
            ipi_node = None
            if ipi is not None:
                for node in ipi:
                    if node.tag.endswith('IPITrib') or node.tag.endswith('IPINT'):
                        ipi_node = node
                        break
            
            # PIS
            pis = imposto.find('nfe:PIS', ns)
            pis_node = None
            if pis is not None:
                for node in pis:
                    if node.tag.endswith('PISAliq') or node.tag.endswith('PISQtde') or node.tag.endswith('PISNT') or node.tag.endswith('PISOutr'):
                        pis_node = node
                        break
            
            # COFINS
            cofins = imposto.find('nfe:COFINS', ns)
            cofins_node = None
            if cofins is not None:
                for node in cofins:
                    if node.tag.endswith('COFINSAliq') or node.tag.endswith('COFINSQtde') or node.tag.endswith('COFINSNT') or node.tag.endswith('COFINSOutr'):
                        cofins_node = node
                        break
            
            item_data = {
                'numero_item': det.get('nItem'),
                'codigo': prod.find('nfe:cProd', ns).text,
                'descricao': prod.find('nfe:xProd', ns).text,
                'cfop': prod.find('nfe:CFOP', ns).text,
                'ncm': prod.find('nfe:NCM', ns).text,
                'quantidade': prod.find('nfe:qCom', ns).text,
                'valor_unitario': prod.find('nfe:vUnCom', ns).text,
                'valor_total': prod.find('nfe:vProd', ns).text,
                'icms': {
                    'orig': icms_node.find('nfe:orig', ns).text if icms_node is not None and icms_node.find('nfe:orig', ns) is not None else '',
                    'cst': icms_node.find('nfe:CST', ns).text if icms_node is not None and icms_node.find('nfe:CST', ns) is not None else '',
                    'modBC': icms_node.find('nfe:modBC', ns).text if icms_node is not None and icms_node.find('nfe:modBC', ns) is not None else '',
                    'vBC': icms_node.find('nfe:vBC', ns).text if icms_node is not None and icms_node.find('nfe:vBC', ns) is not None else '0',
                    'pICMS': icms_node.find('nfe:pICMS', ns).text if icms_node is not None and icms_node.find('nfe:pICMS', ns) is not None else '0',
                    'vICMS': icms_node.find('nfe:vICMS', ns).text if icms_node is not None and icms_node.find('nfe:vICMS', ns) is not None else '0',
                    'modBCST': icms_node.find('nfe:modBCST', ns).text if icms_node is not None and icms_node.find('nfe:modBCST', ns) is not None else '',
                    'pMVAST': icms_node.find('nfe:pMVAST', ns).text if icms_node is not None and icms_node.find('nfe:pMVAST', ns) is not None else '0',
                    'pRedBCST': icms_node.find('nfe:pRedBCST', ns).text if icms_node is not None and icms_node.find('nfe:pRedBCST', ns) is not None else '0',
                    'vBCST': icms_node.find('nfe:vBCST', ns).text if icms_node is not None and icms_node.find('nfe:vBCST', ns) is not None else '0',
                    'pICMSST': icms_node.find('nfe:pICMSST', ns).text if icms_node is not None and icms_node.find('nfe:pICMSST', ns) is not None else '0',
                    'vICMSST': icms_node.find('nfe:vICMSST', ns).text if icms_node is not None and icms_node.find('nfe:vICMSST', ns) is not None else '0',
                    'vBCSTRet': icms_node.find('nfe:vBCSTRet', ns).text if icms_node is not None and icms_node.find('nfe:vBCSTRet', ns) is not None else '0',
                    'vICMSSTRet': icms_node.find('nfe:vICMSSTRet', ns).text if icms_node is not None and icms_node.find('nfe:vICMSSTRet', ns) is not None else '0',
                    'pRedBC': icms_node.find('nfe:pRedBC', ns).text if icms_node is not None and icms_node.find('nfe:pRedBC', ns) is not None else '0',
                    'pBCOp': icms_node.find('nfe:pBCOp', ns).text if icms_node is not None and icms_node.find('nfe:pBCOp', ns) is not None else '0',
                    'UFST': icms_node.find('nfe:UFST', ns).text if icms_node is not None and icms_node.find('nfe:UFST', ns) is not None else '',
                },
                'ipi': {
                    'cst': ipi_node.find('nfe:CST', ns).text if ipi_node is not None and ipi_node.find('nfe:CST', ns) is not None else '',
                    'vBC': ipi_node.find('nfe:vBC', ns).text if ipi_node is not None and ipi_node.find('nfe:vBC', ns) is not None else '0',
                    'pIPI': ipi_node.find('nfe:pIPI', ns).text if ipi_node is not None and ipi_node.find('nfe:pIPI', ns) is not None else '0',
                    'vIPI': ipi_node.find('nfe:vIPI', ns).text if ipi_node is not None and ipi_node.find('nfe:vIPI', ns) is not None else '0',
                },
                'pis': {
                    'cst': pis_node.find('nfe:CST', ns).text if pis_node is not None and pis_node.find('nfe:CST', ns) is not None else '',
                    'vBC': pis_node.find('nfe:vBC', ns).text if pis_node is not None and pis_node.find('nfe:vBC', ns) is not None else '0',
                    'pPIS': pis_node.find('nfe:pPIS', ns).text if pis_node is not None and pis_node.find('nfe:pPIS', ns) is not None else '0',
                    'vPIS': pis_node.find('nfe:vPIS', ns).text if pis_node is not None and pis_node.find('nfe:vPIS', ns) is not None else '0',
                },
                'cofins': {
                    'cst': cofins_node.find('nfe:CST', ns).text if cofins_node is not None and cofins_node.find('nfe:CST', ns) is not None else '',
                    'vBC': cofins_node.find('nfe:vBC', ns).text if cofins_node is not None and cofins_node.find('nfe:vBC', ns) is not None else '0',
                    'pCOFINS': cofins_node.find('nfe:pCOFINS', ns).text if cofins_node is not None and cofins_node.find('nfe:pCOFINS', ns) is not None else '0',
                    'vCOFINS': cofins_node.find('nfe:vCOFINS', ns).text if cofins_node is not None and cofins_node.find('nfe:vCOFINS', ns) is not None else '0',
                }
            }
            
            nfe_data['itens'].append(item_data)
        
        return nfe_data
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {xml_file.name}: {str(e)}")
        return None

def processar_xmls(uploaded_files, cnpj_empresa):
    nfes = []
    for uploaded_file in uploaded_files:
        nfe_data = parse_xml(uploaded_file)
        if nfe_data:
            nfes.append(nfe_data)
    
    # Separar NFes de entrada e saída
    nfe_entrada = [nfe for nfe in nfes if nfe['destinatario_cnpj'] == cnpj_empresa]
    nfe_saida = [nfe for nfe in nfes if nfe['emitente_cnpj'] == cnpj_empresa]
    
    return nfe_entrada, nfe_saida

def calcular_icms(nfe_entrada, nfe_saida):
    # Inicializar totais
    totais = {
        'credito': 0.0,
        'debito': 0.0,
        'st': 0.0,
        'difal': 0.0,
        'a_pagar': 0.0,
        'detalhes': []
    }
    
    # Processar NFes de entrada (créditos)
    for nfe in nfe_entrada:
        for item in nfe['itens']:
            icms = item['icms']
            
            # Verificar se é operação que gera crédito (CST 00, 10, 20, 30, 40, 51, 60, 70, 90)
            if icms['cst'] in ['00', '10', '20', '30', '40', '51', '60', '70', '90']:
                valor_credito = float(icms['vICMS'])
                totais['credito'] += valor_credito
                
                # Detalhes para exibição
                totais['detalhes'].append({
                    'tipo': 'Crédito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': icms['cst'],
                    'valor': valor_credito
                })
            
            # ICMS ST (crédito para o destinatário)
            if icms['vICMSST'] != '0' and float(icms['vICMSST']) > 0:
                valor_st = float(icms['vICMSST'])
                totais['st'] += valor_st
                
                totais['detalhes'].append({
                    'tipo': 'ST',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': icms['cst'],
                    'valor': valor_st
                })
    
    # Processar NFes de saída (débitos)
    for nfe in nfe_saida:
        for item in nfe['itens']:
            icms = item['icms']
            
            # Verificar se é operação que gera débito (CST 00, 10, 20, 30, 40, 51, 60, 70, 90)
            if icms['cst'] in ['00', '10', '20', '30', '40', '51', '60', '70', '90']:
                valor_debito = float(icms['vICMS'])
                totais['debito'] += valor_debito
                
                # Detalhes para exibição
                totais['detalhes'].append({
                    'tipo': 'Débito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': icms['cst'],
                    'valor': valor_debito
                })
            
            # ICMS ST (débito para o emitente)
            if icms['vICMSST'] != '0' and float(icms['vICMSST']) > 0:
                valor_st = float(icms['vICMSST'])
                totais['st'] += valor_st
                
                totais['detalhes'].append({
                    'tipo': 'ST',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': icms['cst'],
                    'valor': valor_st
                })
            
            # DIFAL (para operações interestaduais)
            if nfe['destinatario_cnpj'] and nfe['emitente_cnpj'] != nfe['destinatario_cnpj']:
                # Simulação simples do DIFAL (na prática, é mais complexo)
                if icms['cst'] in ['00', '10', '20', '90']:
                    valor_difal = float(icms['vICMS']) * 0.4  # Exemplo: 40% do ICMS
                    totais['difal'] += valor_difal
                    
                    totais['detalhes'].append({
                        'tipo': 'DIFAL',
                        'chave': nfe['chave'],
                        'item': item['numero_item'],
                        'cfop': item['cfop'],
                        'cst': icms['cst'],
                        'valor': valor_difal
                    })
    
    # Calcular total a pagar
    totais['a_pagar'] = totais['debito'] - totais['credito'] + totais['st'] + totais['difal']
    
    return totais

def calcular_ipi(nfe_entrada, nfe_saida):
    totais = {
        'credito': 0.0,
        'debito': 0.0,
        'a_pagar': 0.0,
        'detalhes': []
    }
    
    # Processar NFes de entrada (créditos)
    for nfe in nfe_entrada:
        for item in nfe['itens']:
            ipi = item['ipi']
            
            # Verificar se é operação tributada (CST 00, 49, 50, 99)
            if ipi['cst'] in ['00', '49', '50', '99'] and float(ipi['vIPI']) > 0:
                valor_credito = float(ipi['vIPI'])
                totais['credito'] += valor_credito
                
                totais['detalhes'].append({
                    'tipo': 'Crédito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': ipi['cst'],
                    'valor': valor_credito
                })
    
    # Processar NFes de saída (débitos)
    for nfe in nfe_saida:
        for item in nfe['itens']:
            ipi = item['ipi']
            
            # Verificar se é operação tributada (CST 00, 49, 50, 99)
            if ipi['cst'] in ['00', '49', '50', '99'] and float(ipi['vIPI']) > 0:
                valor_debito = float(ipi['vIPI'])
                totais['debito'] += valor_debito
                
                totais['detalhes'].append({
                    'tipo': 'Débito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': ipi['cst'],
                    'valor': valor_debito
                })
    
    # Calcular total a pagar
    totais['a_pagar'] = totais['debito'] - totais['credito']
    
    return totais

def calcular_pis(nfe_entrada, nfe_saida):
    totais = {
        'credito': 0.0,
        'debito': 0.0,
        'a_pagar': 0.0,
        'detalhes': []
    }
    
    # Processar NFes de entrada (créditos)
    for nfe in nfe_entrada:
        for item in nfe['itens']:
            pis = item['pis']
            
            # Verificar se é operação tributada (CST 01, 02, 05)
            if pis['cst'] in ['01', '02', '05'] and float(pis['vPIS']) > 0:
                valor_credito = float(pis['vPIS'])
                totais['credito'] += valor_credito
                
                totais['detalhes'].append({
                    'tipo': 'Crédito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': pis['cst'],
                    'valor': valor_credito
                })
    
    # Processar NFes de saída (débitos)
    for nfe in nfe_saida:
        for item in nfe['itens']:
            pis = item['pis']
            
            # Verificar se é operação tributada (CST 01, 02, 05)
            if pis['cst'] in ['01', '02', '05'] and float(pis['vPIS']) > 0:
                valor_debito = float(pis['vPIS'])
                totais['debito'] += valor_debito
                
                totais['detalhes'].append({
                    'tipo': 'Débito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': pis['cst'],
                    'valor': valor_debito
                })
    
    # Calcular total a pagar
    totais['a_pagar'] = totais['debito'] - totais['credito']
    
    return totais

def calcular_cofins(nfe_entrada, nfe_saida):
    totais = {
        'credito': 0.0,
        'debito': 0.0,
        'a_pagar': 0.0,
        'detalhes': []
    }
    
    # Processar NFes de entrada (créditos)
    for nfe in nfe_entrada:
        for item in nfe['itens']:
            cofins = item['cofins']
            
            # Verificar se é operação tributada (CST 01, 02, 05)
            if cofins['cst'] in ['01', '02', '05'] and float(cofins['vCOFINS']) > 0:
                valor_credito = float(cofins['vCOFINS'])
                totais['credito'] += valor_credito
                
                totais['detalhes'].append({
                    'tipo': 'Crédito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': cofins['cst'],
                    'valor': valor_credito
                })
    
    # Processar NFes de saída (débitos)
    for nfe in nfe_saida:
        for item in nfe['itens']:
            cofins = item['cofins']
            
            # Verificar se é operação tributada (CST 01, 02, 05)
            if cofins['cst'] in ['01', '02', '05'] and float(cofins['vCOFINS']) > 0:
                valor_debito = float(cofins['vCOFINS'])
                totais['debito'] += valor_debito
                
                totais['detalhes'].append({
                    'tipo': 'Débito',
                    'chave': nfe['chave'],
                    'item': item['numero_item'],
                    'cfop': item['cfop'],
                    'cst': cofins['cst'],
                    'valor': valor_debito
                })
    
    # Calcular total a pagar
    totais['a_pagar'] = totais['debito'] - totais['credito']
    
    return totais

# Página inicial
def mostrar_capa():
    st.markdown("""
    <div class="cover">
        <h1>Sistema de Apuração Fiscal</h1>
        <p>ICMS | IPI | PIS | COFINS</p>
        <p>Conforme Manual EFD ICMS/IPI e EFD Contribuições</p>
        <p>Versão atualizada conforme legislação vigente</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ## Como usar o sistema:
    1. Insira o CNPJ da empresa no campo ao lado
    2. Faça o upload dos arquivos XML das Notas Fiscais
    3. Navegue pelas abas para visualizar a apuração de cada imposto
    4. Consulte os detalhes de créditos, débitos e valores a pagar
    """)

# Página principal
def main():
    # Sidebar com configurações
    with st.sidebar:
        st.title("Configurações")
        cnpj_empresa = st.text_input("CNPJ da Empresa (somente números)", max_chars=14)
        
        st.markdown("---")
        st.header("Upload de Arquivos")
        uploaded_files = st.file_uploader("Selecione os arquivos XML", type=["xml"], accept_multiple_files=True)
        
        if uploaded_files and cnpj_empresa:
            st.success(f"{len(uploaded_files)} arquivo(s) carregado(s) para o CNPJ {cnpj_empresa}")
        
        st.markdown("---")
        st.header("Navegação")
        imposto_selecionado = st.radio(
            "Selecione o imposto para apuração:",
            ["ICMS", "IPI", "PIS", "COFINS"],
            index=0
        )
    
    # Conteúdo principal
    if not cnpj_empresa:
        mostrar_capa()
        return
    
    if not uploaded_files:
        st.warning("Por favor, faça o upload dos arquivos XML para continuar.")
        return
    
    # Processar XMLs
    nfe_entrada, nfe_saida = processar_xmls(uploaded_files, cnpj_empresa)
    
    if not nfe_entrada and not nfe_saida:
        st.error("Nenhuma nota fiscal válida encontrada para o CNPJ informado.")
        return
    
    # Resumo geral
    st.header("Resumo Geral")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("NF-e de Entrada", len(nfe_entrada))
    
    with col2:
        st.metric("NF-e de Saída", len(nfe_saida))
    
    # Abas de apuração
    tab1, tab2, tab3, tab4 = st.tabs(["ICMS", "IPI", "PIS", "COFINS"])
    
    with tab1:
        st.header("Apuração de ICMS")
        icms_totais = calcular_icms(nfe_entrada, nfe_saida)
        
        # Métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Créditos", f"R$ {icms_totais['credito']:,.2f}")
        
        with col2:
            st.metric("Débitos", f"R$ {icms_totais['debito']:,.2f}")
        
        with col3:
            st.metric("ST", f"R$ {icms_totais['st']:,.2f}")
        
        with col4:
            st.metric("DIFAL", f"R$ {icms_totais['difal']:,.2f}")
        
        with col5:
            st.metric("Total a Pagar", f"R$ {icms_totais['a_pagar']:,.2f}", delta_color="inverse")
        
        # Detalhes
        st.subheader("Detalhes das Operações")
        df_icms = pd.DataFrame(icms_totais['detalhes'])
        if not df_icms.empty:
            st.dataframe(df_icms)
        else:
            st.info("Nenhuma operação de ICMS encontrada nos arquivos.")
    
    with tab2:
        st.header("Apuração de IPI")
        ipi_totais = calcular_ipi(nfe_entrada, nfe_saida)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Créditos", f"R$ {ipi_totais['credito']:,.2f}")
        
        with col2:
            st.metric("Débitos", f"R$ {ipi_totais['debito']:,.2f}")
        
        with col3:
            st.metric("Total a Pagar", f"R$ {ipi_totais['a_pagar']:,.2f}", delta_color="inverse")
        
        # Detalhes
        st.subheader("Detalhes das Operações")
        df_ipi = pd.DataFrame(ipi_totais['detalhes'])
        if not df_ipi.empty:
            st.dataframe(df_ipi)
        else:
            st.info("Nenhuma operação de IPI encontrada nos arquivos.")
    
    with tab3:
        st.header("Apuração de PIS")
        pis_totais = calcular_pis(nfe_entrada, nfe_saida)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Créditos", f"R$ {pis_totais['credito']:,.2f}")
        
        with col2:
            st.metric("Débitos", f"R$ {pis_totais['debito']:,.2f}")
        
        with col3:
            st.metric("Total a Pagar", f"R$ {pis_totais['a_pagar']:,.2f}", delta_color="inverse")
        
        # Detalhes
        st.subheader("Detalhes das Operações")
        df_pis = pd.DataFrame(pis_totais['detalhes'])
        if not df_pis.empty:
            st.dataframe(df_pis)
        else:
            st.info("Nenhuma operação de PIS encontrada nos arquivos.")
    
    with tab4:
        st.header("Apuração de COFINS")
        cofins_totais = calcular_cofins(nfe_entrada, nfe_saida)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Créditos", f"R$ {cofins_totais['credito']:,.2f}")
        
        with col2:
            st.metric("Débitos", f"R$ {cofins_totais['debito']:,.2f}")
        
        with col3:
            st.metric("Total a Pagar", f"R$ {cofins_totais['a_pagar']:,.2f}", delta_color="inverse")
        
        # Detalhes
        st.subheader("Detalhes das Operações")
        df_cofins = pd.DataFrame(cofins_totais['detalhes'])
        if not df_cofins.empty:
            st.dataframe(df_cofins)
        else:
            st.info("Nenhuma operação de COFINS encontrada nos arquivos.")
    
    # Botão para exportar resultados
    st.markdown("---")
    st.header("Exportar Resultados")
    
    if st.button("Gerar Relatório Completo"):
        # Criar um arquivo Excel com todas as apurações
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Resumo geral
            resumo_data = {
                'Imposto': ['ICMS', 'IPI', 'PIS', 'COFINS'],
                'Créditos': [
                    icms_totais['credito'],
                    ipi_totais['credito'],
                    pis_totais['credito'],
                    cofins_totais['credito']
                ],
                'Débitos': [
                    icms_totais['debito'],
                    ipi_totais['debito'],
                    pis_totais['debito'],
                    cofins_totais['debito']
                ],
                'Total a Pagar': [
                    icms_totais['a_pagar'],
                    ipi_totais['a_pagar'],
                    pis_totais['a_pagar'],
                    cofins_totais['a_pagar']
                ]
            }
            pd.DataFrame(resumo_data).to_excel(writer, sheet_name='Resumo', index=False)
            
            # Detalhes por imposto
            if not df_icms.empty:
                df_icms.to_excel(writer, sheet_name='ICMS Detalhes', index=False)
            if not df_ipi.empty:
                df_ipi.to_excel(writer, sheet_name='IPI Detalhes', index=False)
            if not df_pis.empty:
                df_pis.to_excel(writer, sheet_name='PIS Detalhes', index=False)
            if not df_cofins.empty:
                df_cofins.to_excel(writer, sheet_name='COFINS Detalhes', index=False)
        
        # Configurar o download
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="apuracao_fiscal.xlsx">Clique aqui para baixar o relatório completo</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
