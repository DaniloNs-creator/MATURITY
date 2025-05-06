import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import base64
from io import BytesIO
import zipfile

# Configuração da página
st.set_page_config(
    page_title="Sistema de Apuração Fiscal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Criar arquivo CSS se não existir
if not os.path.exists("style.css"):
    with open("style.css", "w") as f:
        f.write("""
/* Estilos gerais */
body {
    font-family: 'Arial', sans-serif;
    color: #333;
    background-color: #f5f5f5;
}

/* Cabeçalho */
.header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Títulos */
h1, h2, h3 {
    color: #2c3e50;
}

/* Abas */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    padding: 8px 20px;
    border-radius: 4px 4px 0 0;
    background-color: #ecf0f1;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #3498db !important;
    color: white !important;
}

/* Cards */
.card {
    background-color: white;
    border-radius: 5px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Botões */
.stButton>button {
    background-color: #3498db;
    color: white;
    border-radius: 4px;
    border: none;
    padding: 8px 16px;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    background-color: #2980b9;
}

/* Tabelas */
.dataframe {
    width: 100%;
}

/* Sidebar */
.sidebar .sidebar-content {
    background-color: #2c3e50;
    color: white;
}

/* Mensagens de sucesso */
.stAlert {
    border-radius: 5px;
}
""")

local_css("style.css")

# Função para exibir a capa
def mostrar_capa():
    st.markdown("""
    <div class="header">
        <h1 style="color:white; text-align:center;">Sistema de Apuração Fiscal</h1>
        <h3 style="color:white; text-align:center;">ICMS | IPI | PIS | COFINS</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/477/477103.png", width=200)
    
    st.markdown("""
    <div style="text-align:center; margin-top:2rem;">
        <p>Este sistema permite a apuração dos impostos ICMS, IPI, PIS e COFINS com base nos arquivos XMLs das notas fiscais.</p>
        <p>Desenvolvido de acordo com os manuais da EFD ICMS IPI e EFD Contribuições.</p>
    </div>
    """, unsafe_allow_html=True)

# Funções para processamento dos XMLs
def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Namespaces comuns em XMLs de NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Extrair informações básicas
        inf_nfe = root.find('.//nfe:infNFe', ns)
        if inf_nfe is None:
            ns = {'': 'http://www.portalfiscal.inf.br/nfe'}
            inf_nfe = root.find('.//infNFe', ns)
        
        ide = inf_nfe.find('.//nfe:ide', ns) or inf_nfe.find('.//ide', ns)
        emit = inf_nfe.find('.//nfe:emit', ns) or inf_nfe.find('.//emit', ns)
        dest = inf_nfe.find('.//nfe:dest', ns) or inf_nfe.find('.//dest', ns)
        total = inf_nfe.find('.//nfe:total', ns) or inf_nfe.find('.//total', ns)
        
        # Extrair valores dos impostos
        icms_total = total.find('.//nfe:ICMSTot', ns) or total.find('.//ICMSTot', ns)
        ipi_total = total.find('.//nfe:IPITot', ns) or total.find('.//IPITot', ns)
        pis_total = total.find('.//nfe:PISTot', ns) or total.find('.//PISTot', ns)
        cofins_total = total.find('.//nfe:COFINSTot', ns) or total.find('.//COFINSTot', ns)
        
        # Criar dicionário com os dados
        dados = {
            'Chave_NFe': inf_nfe.get('Id', '')[3:] if 'Id' in inf_nfe.attrib else '',
            'Numero': ide.find('.//nfe:nNF', ns).text if ide.find('.//nfe:nNF', ns) is not None else ide.find('.//nNF', ns).text,
            'Data_Emissao': ide.find('.//nfe:dhEmi', ns).text if ide.find('.//nfe:dhEmi', ns) is not None else ide.find('.//dhEmi', ns).text,
            'Emitente_CNPJ': emit.find('.//nfe:CNPJ', ns).text if emit.find('.//nfe:CNPJ', ns) is not None else emit.find('.//CNPJ', ns).text,
            'Emitente_Nome': emit.find('.//nfe:xNome', ns).text if emit.find('.//nfe:xNome', ns) is not None else emit.find('.//xNome', ns).text,
            'Destinatario_CNPJ': dest.find('.//nfe:CNPJ', ns).text if dest.find('.//nfe:CNPJ', ns) is not None else (dest.find('.//nfe:CPF', ns).text if dest.find('.//nfe:CPF', ns) is not None else ''),
            'Destinatario_Nome': dest.find('.//nfe:xNome', ns).text if dest.find('.//nfe:xNome', ns) is not None else dest.find('.//xNome', ns).text,
            'Valor_Total': total.find('.//nfe:vNF', ns).text if total.find('.//nfe:vNF', ns) is not None else total.find('.//vNF', ns).text,
            'Valor_ICMS': icms_total.find('.//nfe:vICMS', ns).text if icms_total is not None and icms_total.find('.//nfe:vICMS', ns) is not None else (icms_total.find('.//vICMS', ns).text if icms_total is not None and icms_total.find('.//vICMS', ns) is not None else '0'),
            'Valor_IPI': ipi_total.find('.//nfe:vIPI', ns).text if ipi_total is not None and ipi_total.find('.//nfe:vIPI', ns) is not None else (ipi_total.find('.//vIPI', ns).text if ipi_total is not None and ipi_total.find('.//vIPI', ns) is not None else '0'),
            'Valor_PIS': pis_total.find('.//nfe:vPIS', ns).text if pis_total is not None and pis_total.find('.//nfe:vPIS', ns) is not None else (pis_total.find('.//vPIS', ns).text if pis_total is not None and pis_total.find('.//vPIS', ns) is not None else '0'),
            'Valor_COFINS': cofins_total.find('.//nfe:vCOFINS', ns).text if cofins_total is not None and cofins_total.find('.//nfe:vCOFINS', ns) is not None else (cofins_total.find('.//vCOFINS', ns).text if cofins_total is not None and cofins_total.find('.//vCOFINS', ns) is not None else '0'),
        }
        
        return dados
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {xml_file.name}: {str(e)}")
        return None

def processar_arquivos(uploaded_files):
    dados = []
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.xml'):
            dados_xml = parse_xml(uploaded_file)
            if dados_xml:
                dados.append(dados_xml)
        elif uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.xml'):
                        with zip_ref.open(file_info) as xml_file:
                            dados_xml = parse_xml(BytesIO(xml_file.read()))
                            if dados_xml:
                                dados.append(dados_xml)
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Converter valores para float
        colunas_valores = ['Valor_Total', 'Valor_ICMS', 'Valor_IPI', 'Valor_PIS', 'Valor_COFINS']
        for col in colunas_valores:
            df[col] = df[col].astype(float)
        
        # Converter data
        df['Data_Emissao'] = pd.to_datetime(df['Data_Emissao']).dt.date
        
        return df
    else:
        return None

# Funções para cálculos fiscais
def calcular_icms(df):
    if df is None or df.empty:
        return None
    
    # Agrupar por mês/ano
    df['Periodo'] = df['Data_Emissao'].apply(lambda x: x.strftime('%m/%Y'))
    
    # Calcular totais
    resumo_icms = df.groupby('Periodo').agg({
        'Valor_Total': 'sum',
        'Valor_ICMS': 'sum'
    }).reset_index()
    
    # Adicionar cálculos específicos do ICMS conforme manual EFD ICMS IPI
    resumo_icms['ICMS_Devido'] = resumo_icms['Valor_ICMS']
    resumo_icms['ICMS_Retido'] = 0  # Exemplo, pode ser calculado com base em outras informações
    resumo_icms['ICMS_Diferencial'] = 0  # Exemplo para alíquotas diferencial
    resumo_icms['ICMS_ST'] = 0  # Exemplo para substituição tributária
    resumo_icms['ICMS_Total'] = resumo_icms['ICMS_Devido'] + resumo_icms['ICMS_ST'] - resumo_icms['ICMS_Retido']
    
    return resumo_icms

def calcular_ipi(df):
    if df is None or df.empty:
        return None
    
    df['Periodo'] = df['Data_Emissao'].apply(lambda x: x.strftime('%m/%Y'))
    
    resumo_ipi = df.groupby('Periodo').agg({
        'Valor_Total': 'sum',
        'Valor_IPI': 'sum'
    }).reset_index()
    
    # Adicionar cálculos específicos do IPI
    resumo_ipi['IPI_Devido'] = resumo_ipi['Valor_IPI']
    resumo_ipi['IPI_Creditos'] = 0  # Exemplo de créditos
    resumo_ipi['IPI_Total'] = resumo_ipi['IPI_Devido'] - resumo_ipi['IPI_Creditos']
    
    return resumo_ipi

def calcular_pis_cofins(df, tipo='PIS'):
    if df is None or df.empty:
        return None
    
    coluna = 'Valor_PIS' if tipo == 'PIS' else 'Valor_COFINS'
    
    df['Periodo'] = df['Data_Emissao'].apply(lambda x: x.strftime('%m/%Y'))
    
    resumo = df.groupby('Periodo').agg({
        'Valor_Total': 'sum',
        coluna: 'sum'
    }).reset_index()
    
    # Adicionar cálculos específicos conforme manual EFD Contribuições
    resumo[f'{tipo}_Devido'] = resumo[coluna]
    resumo[f'{tipo}_Creditos'] = 0  # Exemplo de créditos
    resumo[f'{tipo}_Total'] = resumo[f'{tipo}_Devido'] - resumo[f'{tipo}_Creditos']
    
    return resumo

# Função para download dos resultados
def get_table_download_link(df, filename):
    csv = df.to_csv(index=False, sep=';', decimal=',')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Baixar arquivo CSV</a>'
    return href

# Interface principal
def main():
    # Mostrar capa inicial
    mostrar_capa()
    
    # Upload de arquivos
    st.sidebar.header("Configurações")
    uploaded_files = st.sidebar.file_uploader(
        "Carregue os arquivos XML ou ZIP com XMLs", 
        type=['xml', 'zip'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        with st.spinner('Processando arquivos...'):
            df = processar_arquivos(uploaded_files)
        
        if df is not None:
            st.success(f"{len(df)} notas fiscais processadas com sucesso!")
            
            # Exibir abas para cada imposto
            tab1, tab2, tab3, tab4 = st.tabs(["ICMS", "IPI", "PIS", "COFINS"])
            
            with tab1:
                st.header("Apuração de ICMS")
                resumo_icms = calcular_icms(df)
                
                if resumo_icms is not None:
                    # Formatar valores em R$
                    for col in resumo_icms.columns:
                        if col != 'Periodo':
                            resumo_icms[col] = resumo_icms[col].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    st.dataframe(resumo_icms, use_container_width=True)
                    
                    # Gráfico
                    st.subheader("Evolução Mensal do ICMS")
                    df_graf = calcular_icms(df)
                    df_graf['Periodo'] = pd.to_datetime(df_graf['Periodo'], format='%m/%Y')
                    st.line_chart(df_graf.set_index('Periodo')['ICMS_Total'])
                    
                    # Download
                    st.markdown(get_table_download_link(resumo_icms, "apuracao_icms.csv"), unsafe_allow_html=True)
            
            with tab2:
                st.header("Apuração de IPI")
                resumo_ipi = calcular_ipi(df)
                
                if resumo_ipi is not None:
                    # Formatar valores em R$
                    for col in resumo_ipi.columns:
                        if col != 'Periodo':
                            resumo_ipi[col] = resumo_ipi[col].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    st.dataframe(resumo_ipi, use_container_width=True)
                    
                    # Gráfico
                    st.subheader("Evolução Mensal do IPI")
                    df_graf = calcular_ipi(df)
                    df_graf['Periodo'] = pd.to_datetime(df_graf['Periodo'], format='%m/%Y')
                    st.line_chart(df_graf.set_index('Periodo')['IPI_Total'])
                    
                    # Download
                    st.markdown(get_table_download_link(resumo_ipi, "apuracao_ipi.csv"), unsafe_allow_html=True)
            
            with tab3:
                st.header("Apuração de PIS")
                resumo_pis = calcular_pis_cofins(df, 'PIS')
                
                if resumo_pis is not None:
                    # Formatar valores em R$
                    for col in resumo_pis.columns:
                        if col != 'Periodo':
                            resumo_pis[col] = resumo_pis[col].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    st.dataframe(resumo_pis, use_container_width=True)
                    
                    # Gráfico
                    st.subheader("Evolução Mensal do PIS")
                    df_graf = calcular_pis_cofins(df, 'PIS')
                    df_graf['Periodo'] = pd.to_datetime(df_graf['Periodo'], format='%m/%Y')
                    st.line_chart(df_graf.set_index('Periodo')['PIS_Total'])
                    
                    # Download
                    st.markdown(get_table_download_link(resumo_pis, "apuracao_pis.csv"), unsafe_allow_html=True)
            
            with tab4:
                st.header("Apuração de COFINS")
                resumo_cofins = calcular_pis_cofins(df, 'COFINS')
                
                if resumo_cofins is not None:
                    # Formatar valores em R$
                    for col in resumo_cofins.columns:
                        if col != 'Periodo':
                            resumo_cofins[col] = resumo_cofins[col].apply(lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    st.dataframe(resumo_cofins, use_container_width=True)
                    
                    # Gráfico
                    st.subheader("Evolução Mensal do COFINS")
                    df_graf = calcular_pis_cofins(df, 'COFINS')
                    df_graf['Periodo'] = pd.to_datetime(df_graf['Periodo'], format='%m/%Y')
                    st.line_chart(df_graf.set_index('Periodo')['COFINS_Total'])
                    
                    # Download
                    st.markdown(get_table_download_link(resumo_cofins, "apuracao_cofins.csv"), unsafe_allow_html=True)
            
            # Exibir dados brutos
            st.sidebar.subheader("Dados das Notas Fiscais")
            if st.sidebar.checkbox("Mostrar dados completos"):
                st.subheader("Dados Completos das Notas Fiscais")
                st.dataframe(df, use_container_width=True)
                
                # Download dos dados completos
                st.sidebar.markdown(get_table_download_link(df, "dados_completos_nf.csv"), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
