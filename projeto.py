import streamlit as st
import pandas as pd
from lxml import etree
import os
from datetime import datetime
import base64
import zipfile
import io
from io import BytesIO
import tempfile
import plotly.express as px

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
        background-color: #f8f9fa;
    }
    .stApp {
        background-color: white;
    }
    .reportview-container {
        background-color: white;
    }
    
    /* Estilos dos botões */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #ced4da;
        background-color: #f8f9fa;
        color: #495057;
        font-weight: 500;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
    }
    .stButton>button:hover {
        background-color: #e9ecef;
        color: #212529;
        border-color: #adb5bd;
    }
    
    /* Estilos das abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 0 20px;
        border-radius: 8px 8px 0 0;
        background-color: #e9ecef;
        color: #495057;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0d6efd;
        color: white;
    }
    
    /* Estilos dos cards */
    .card {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        border: 1px solid #dee2e6;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #0d6efd;
    }
    
    /* Estilos da sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Estilos da tabela */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #0d6efd;
        color: white;
        padding: 10px;
        text-align: left;
    }
    td {
        padding: 8px 10px;
        border-bottom: 1px solid #dee2e6;
    }
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    /* Estilos do cabeçalho */
    .header {
        background-color: #0d6efd;
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Funções para processamento dos XMLs
def parse_xml(xml_file):
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
        
        # Namespaces
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Dados básicos da NFe
        inf_nfe = root.find('.//nfe:infNFe', ns)
        ide = inf_nfe.find('nfe:ide', ns)
        emit = inf_nfe.find('nfe:emit', ns)
        dest = inf_nfe.find('nfe:dest', ns)
        total = inf_nfe.find('nfe:total', ns)
        
        # Informações da nota
        nfe_data = {
            'chave': inf_nfe.get('Id')[3:],  # Remove 'NFe' do início
            'numero': ide.find('nfe:nNF', ns).text,
            'serie': ide.find('nfe:serie', ns).text,
            'data_emissao': ide.find('nfe:dhEmi', ns).text,
            'emitente_cnpj': emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else emit.find('nfe:CPF', ns).text,
            'emitente_nome': emit.find('nfe:xNome', ns).text,
            'destinatario_cnpj': dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else dest.find('nfe:CPF', ns).text,
            'destinatario_nome': dest.find('nfe:xNome', ns).text,
            'valor_total': float(total.find('nfe:ICMSTot/nfe:vNF', ns).text)
        }
        
        # Itens da NFe
        itens = []
        for det in inf_nfe.findall('nfe:det', ns):
            item = det.find('nfe:prod', ns)
            imposto = det.find('nfe:imposto', ns)
            
            # ICMS
            icms = imposto.find('nfe:ICMS/*', ns) if imposto.find('nfe:ICMS', ns) is not None else None
            
            # IPI
            ipi = imposto.find('nfe:IPI/nfe:IPITrib', ns) if imposto.find('nfe:IPI', ns) is not None else None
            
            # PIS
            pis = imposto.find('nfe:PIS/*', ns) if imposto.find('nfe:PIS', ns) is not None else None
            
            # COFINS
            cofins = imposto.find('nfe:COFINS/*', ns) if imposto.find('nfe:COFINS', ns) is not None else None
            
            item_data = {
                'numero_item': det.get('nItem'),
                'codigo': item.find('nfe:cProd', ns).text,
                'descricao': item.find('nfe:xProd', ns).text,
                'ncm': item.find('nfe:NCM', ns).text,
                'cfop': item.find('nfe:CFOP', ns).text,
                'unidade': item.find('nfe:uCom', ns).text,
                'quantidade': float(item.find('nfe:qCom', ns).text),
                'valor_unitario': float(item.find('nfe:vUnCom', ns).text),
                'valor_total': float(item.find('nfe:vProd', ns).text),
                'icms_orig': icms.find('nfe:orig', ns).text if icms is not None else None,
                'icms_cst': icms.find('nfe:CST', ns).text if icms is not None and icms.find('nfe:CST', ns) is not None else icms.find('nfe:CSOSN', ns).text if icms is not None else None,
                'icms_bc': float(icms.find('nfe:vBC', ns).text) if icms is not None and icms.find('nfe:vBC', ns) is not None else 0.0,
                'icms_p': float(icms.find('nfe:pICMS', ns).text) if icms is not None and icms.find('nfe:pICMS', ns) is not None else 0.0,
                'icms_v': float(icms.find('nfe:vICMS', ns).text) if icms is not None and icms.find('nfe:vICMS', ns) is not None else 0.0,
                'icms_bc_st': float(icms.find('nfe:vBCST', ns).text) if icms is not None and icms.find('nfe:vBCST', ns) is not None else 0.0,
                'icms_p_st': float(icms.find('nfe:pICMSST', ns).text) if icms is not None and icms.find('nfe:pICMSST', ns) is not None else 0.0,
                'icms_v_st': float(icms.find('nfe:vICMSST', ns).text) if icms is not None and icms.find('nfe:vICMSST', ns) is not None else 0.0,
                'ipi_cst': ipi.find('nfe:CST', ns).text if ipi is not None else None,
                'ipi_bc': float(ipi.find('nfe:vBC', ns).text) if ipi is not None and ipi.find('nfe:vBC', ns) is not None else 0.0,
                'ipi_p': float(ipi.find('nfe:pIPI', ns).text) if ipi is not None and ipi.find('nfe:pIPI', ns) is not None else 0.0,
                'ipi_v': float(ipi.find('nfe:vIPI', ns).text) if ipi is not None and ipi.find('nfe:vIPI', ns) is not None else 0.0,
                'pis_cst': pis.find('nfe:CST', ns).text if pis is not None else None,
                'pis_bc': float(pis.find('nfe:vBC', ns).text) if pis is not None and pis.find('nfe:vBC', ns) is not None else 0.0,
                'pis_p': float(pis.find('nfe:pPIS', ns).text) if pis is not None and pis.find('nfe:pPIS', ns) is not None else 0.0,
                'pis_v': float(pis.find('nfe:vPIS', ns).text) if pis is not None and pis.find('nfe:vPIS', ns) is not None else 0.0,
                'cofins_cst': cofins.find('nfe:CST', ns).text if cofins is not None else None,
                'cofins_bc': float(cofins.find('nfe:vBC', ns).text) if cofins is not None and cofins.find('nfe:vBC', ns) is not None else 0.0,
                'cofins_p': float(cofins.find('nfe:pCOFINS', ns).text) if cofins is not None and cofins.find('nfe:pCOFINS', ns) is not None else 0.0,
                'cofins_v': float(cofins.find('nfe:vCOFINS', ns).text) if cofins is not None and cofins.find('nfe:vCOFINS', ns) is not None else 0.0
            }
            itens.append(item_data)
        
        return {'nfe': nfe_data, 'itens': itens}
    except Exception as e:
        st.error(f"Erro ao processar o arquivo XML: {str(e)}")
        return None

def processar_arquivos(uploaded_files):
    notas_fiscais = []
    itens_notas = []
    
    for uploaded_file in uploaded_files:
        try:
            # Salvar o arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Processar o XML
            resultado = parse_xml(tmp_path)
            
            if resultado:
                notas_fiscais.append(resultado['nfe'])
                for item in resultado['itens']:
                    item['chave'] = resultado['nfe']['chave']
                    itens_notas.append(item)
            
            # Remover o arquivo temporário
            os.unlink(tmp_path)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
    
    return notas_fiscais, itens_notas

# Funções para cálculo dos impostos
def calcular_icms(itens):
    # Agrupar por CFOP e CST
    df = pd.DataFrame(itens)
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Cálculo do ICMS normal
    icms_normal = df.groupby(['cfop', 'icms_cst']).agg({
        'valor_total': 'sum',
        'icms_bc': 'sum',
        'icms_v': 'sum'
    }).reset_index()
    
    icms_normal = icms_normal.rename(columns={
        'valor_total': 'Valor Total',
        'icms_bc': 'Base de Cálculo ICMS',
        'icms_v': 'Valor ICMS'
    })
    
    # Cálculo do ICMS ST
    icms_st = df[df['icms_v_st'] > 0].groupby(['cfop', 'icms_cst']).agg({
        'icms_bc_st': 'sum',
        'icms_v_st': 'sum'
    }).reset_index()
    
    if not icms_st.empty:
        icms_st = icms_st.rename(columns={
            'icms_bc_st': 'Base de Cálculo ST',
            'icms_v_st': 'Valor ST'
        })
    else:
        icms_st = pd.DataFrame(columns=['cfop', 'icms_cst', 'Base de Cálculo ST', 'Valor ST'])
    
    # Cálculo do DIFAL (para operações interestaduais)
    difal = df[(df['icms_cst'].isin(['60', '10'])) & (df['icms_v_st'] == 0)].copy()
    
    if not difal.empty:
        # Simulação de cálculo do DIFAL (fórmula simplificada)
        difal['DIFAL'] = difal.apply(lambda x: (x['icms_bc'] * 0.12) - x['icms_v'], axis=1)
        
        difal_result = difal.groupby(['cfop', 'icms_cst']).agg({
            'icms_bc': 'sum',
            'DIFAL': 'sum'
        }).reset_index()
        
        difal_result = difal_result.rename(columns={
            'icms_bc': 'Base de Cálculo DIFAL',
            'DIFAL': 'Valor DIFAL'
        })
    else:
        difal_result = pd.DataFrame(columns=['cfop', 'icms_cst', 'Base de Cálculo DIFAL', 'Valor DIFAL'])
    
    return icms_normal, icms_st, difal_result

def calcular_ipi(itens):
    df = pd.DataFrame(itens)
    
    if df.empty:
        return pd.DataFrame()
    
    ipi = df[df['ipi_v'] > 0].groupby(['cfop', 'ipi_cst']).agg({
        'valor_total': 'sum',
        'ipi_bc': 'sum',
        'ipi_v': 'sum'
    }).reset_index()
    
    ipi = ipi.rename(columns={
        'valor_total': 'Valor Total',
        'ipi_bc': 'Base de Cálculo IPI',
        'ipi_v': 'Valor IPI'
    })
    
    return ipi

def calcular_pis_cofins(itens):
    df = pd.DataFrame(itens)
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # PIS
    pis = df[df['pis_v'] > 0].groupby(['cfop', 'pis_cst']).agg({
        'valor_total': 'sum',
        'pis_bc': 'sum',
        'pis_v': 'sum'
    }).reset_index()
    
    pis = pis.rename(columns={
        'valor_total': 'Valor Total',
        'pis_bc': 'Base de Cálculo PIS',
        'pis_v': 'Valor PIS'
    })
    
    # COFINS
    cofins = df[df['cofins_v'] > 0].groupby(['cfop', 'cofins_cst']).agg({
        'valor_total': 'sum',
        'cofins_bc': 'sum',
        'cofins_v': 'sum'
    }).reset_index()
    
    cofins = cofins.rename(columns={
        'valor_total': 'Valor Total',
        'cofins_bc': 'Base de Cálculo COFINS',
        'cofins_v': 'Valor COFINS'
    })
    
    return pis, cofins

# Função para gerar relatório consolidado
def gerar_relatorio_consolidado(notas_fiscais, icms_normal, icms_st, difal, ipi, pis, cofins):
    relatorio = {
        'Resumo Geral': {
            'Quantidade de Notas Fiscais': len(notas_fiscais),
            'Valor Total das Notas': sum(nf['valor_total'] for nf in notas_fiscais),
            'Período das Notas': f"{min(nf['data_emissao'][:10] for nf in notas_fiscais)} a {max(nf['data_emissao'][:10] for nf in notas_fiscais)}"
        },
        'ICMS': {
            'Valor Total ICMS Normal': icms_normal['Valor ICMS'].sum() if not icms_normal.empty else 0,
            'Valor Total ICMS ST': icms_st['Valor ST'].sum() if not icms_st.empty else 0,
            'Valor Total DIFAL': difal['Valor DIFAL'].sum() if not difal.empty else 0
        },
        'IPI': {
            'Valor Total IPI': ipi['Valor IPI'].sum() if not ipi.empty else 0
        },
        'PIS': {
            'Valor Total PIS': pis['Valor PIS'].sum() if not pis.empty else 0
        },
        'COFINS': {
            'Valor Total COFINS': cofins['Valor COFINS'].sum() if not cofins.empty else 0
        }
    }
    
    return relatorio

# Interface do Streamlit
def main():
    # Inicializar variáveis de sessão
    if 'notas_fiscais' not in st.session_state:
        st.session_state.notas_fiscais = []
    if 'itens_notas' not in st.session_state:
        st.session_state.itens_notas = []
    
    # Sidebar - Upload de arquivos
    with st.sidebar:
        st.markdown("## Configurações")
        uploaded_files = st.file_uploader("Carregar XMLs de NFe", type=['xml'], accept_multiple_files=True)
        
        if uploaded_files and st.button("Processar XMLs"):
            with st.spinner("Processando arquivos..."):
                notas_fiscais, itens_notas = processar_arquivos(uploaded_files)
                st.session_state.notas_fiscais = notas_fiscais
                st.session_state.itens_notas = itens_notas
                st.success(f"{len(notas_fiscais)} notas fiscais processadas com sucesso!")
        
        if st.session_state.notas_fiscais:
            st.markdown("---")
            st.markdown("### Relatórios Disponíveis")
            st.markdown(f"**Notas Processadas:** {len(st.session_state.notas_fiscais)}")
            st.markdown(f"**Itens Processados:** {len(st.session_state.itens_notas)}")
            
            # Botão para exportar dados
            if st.button("Exportar Dados para Excel"):
                with st.spinner("Gerando arquivo Excel..."):
                    # Criar um arquivo Excel com múltiplas abas
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        pd.DataFrame(st.session_state.notas_fiscais).to_excel(writer, sheet_name='Notas Fiscais', index=False)
                        pd.DataFrame(st.session_state.itens_notas).to_excel(writer, sheet_name='Itens', index=False)
                        
                        # Adicionar abas para cada imposto
                        icms_normal, icms_st, difal = calcular_icms(st.session_state.itens_notas)
                        if not icms_normal.empty:
                            icms_normal.to_excel(writer, sheet_name='ICMS Normal', index=False)
                        if not icms_st.empty:
                            icms_st.to_excel(writer, sheet_name='ICMS ST', index=False)
                        if not difal.empty:
                            difal.to_excel(writer, sheet_name='DIFAL', index=False)
                        
                        ipi = calcular_ipi(st.session_state.itens_notas)
                        if not ipi.empty:
                            ipi.to_excel(writer, sheet_name='IPI', index=False)
                        
                        pis, cofins = calcular_pis_cofins(st.session_state.itens_notas)
                        if not pis.empty:
                            pis.to_excel(writer, sheet_name='PIS', index=False)
                        if not cofins.empty:
                            cofins.to_excel(writer, sheet_name='COFINS', index=False)
                    
                    output.seek(0)
                    st.download_button(
                        label="Baixar Arquivo Excel",
                        data=output,
                        file_name="apuracao_fiscal.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    
    # Página principal
    st.markdown("""
    <div class="header">
        <div class="header-title">Sistema de Apuração Fiscal</div>
        <div class="header-subtitle">ICMS | IPI | PIS | COFINS | DIFAL | ST</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navegação por abas
    tabs = st.tabs(["🏠 Início", "📊 ICMS", "🏭 IPI", "💰 PIS", "💵 COFINS", "📈 Consolidador"])
    
    with tabs[0]:  # Página inicial
        st.markdown("""
        <div class="card">
            <div class="card-title">Bem-vindo ao Sistema de Apuração Fiscal</div>
            <p>Este sistema permite a apuração dos impostos ICMS, IPI, PIS e COFINS com base nos XMLs de Notas Fiscais Eletrônicas (Modelo 55).</p>
            <p>Para começar, carregue os arquivos XML no menu lateral e clique em "Processar XMLs".</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.notas_fiscais:
            st.markdown("### Resumo das Notas Processadas")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Notas", len(st.session_state.notas_fiscais))
            with col2:
                total_valor = sum(nf['valor_total'] for nf in st.session_state.notas_fiscais)
                st.metric("Valor Total", f"R$ {total_valor:,.2f}")
            with col3:
                datas = [nf['data_emissao'][:10] for nf in st.session_state.notas_fiscais]
                st.metric("Período", f"{min(datas)} a {max(datas)}")
            
            # Gráfico de barras com valores por data
            df_notas = pd.DataFrame(st.session_state.notas_fiscais)
            df_notas['data'] = pd.to_datetime(df_notas['data_emissao'].str[:10])
            df_grouped = df_notas.groupby('data')['valor_total'].sum().reset_index()
            
            fig = px.bar(df_grouped, x='data', y='valor_total', 
                         title='Valor Total por Data de Emissão',
                         labels={'data': 'Data', 'valor_total': 'Valor Total (R$)'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela com as notas fiscais
            st.dataframe(df_notas[['chave', 'numero', 'serie', 'data_emissao', 'emitente_nome', 'destinatario_nome', 'valor_total']], 
                         hide_index=True, use_container_width=True)
    
    with tabs[1]:  # ICMS
        st.markdown("""
        <div class="card">
            <div class="card-title">Apuração do ICMS</div>
            <p>Esta seção apresenta a apuração do Imposto sobre Circulação de Mercadorias e Serviços (ICMS), incluindo operações normais, substituição tributária e DIFAL.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.itens_notas:
            icms_normal, icms_st, difal = calcular_icms(st.session_state.itens_notas)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ICMS Normal", f"R$ {icms_normal['Valor ICMS'].sum():,.2f}")
            with col2:
                st.metric("ICMS ST", f"R$ {icms_st['Valor ST'].sum():,.2f}" if not icms_st.empty else "R$ 0,00")
            with col3:
                st.metric("DIFAL", f"R$ {difal['Valor DIFAL'].sum():,.2f}" if not difal.empty else "R$ 0,00")
            
            st.markdown("#### ICMS Normal")
            st.dataframe(icms_normal, hide_index=True, use_container_width=True)
            
            st.markdown("#### ICMS Substituição Tributária")
            if not icms_st.empty:
                st.dataframe(icms_st, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma operação com substituição tributária encontrada.")
            
            st.markdown("#### DIFAL - Diferencial de Alíquotas")
            if not difal.empty:
                st.dataframe(difal, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma operação com DIFAL encontrada.")
        else:
            st.warning("Nenhum dado disponível. Por favor, carregue e processe os XMLs primeiro.")
    
    with tabs[2]:  # IPI
        st.markdown("""
        <div class="card">
            <div class="card-title">Apuração do IPI</div>
            <p>Esta seção apresenta a apuração do Imposto sobre Produtos Industrializados (IPI).</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.itens_notas:
            ipi = calcular_ipi(st.session_state.itens_notas)
            
            st.metric("Total IPI", f"R$ {ipi['Valor IPI'].sum():,.2f}" if not ipi.empty else "R$ 0,00")
            
            if not ipi.empty:
                st.dataframe(ipi, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma operação com IPI encontrada.")
        else:
            st.warning("Nenhum dado disponível. Por favor, carregue e processe os XMLs primeiro.")
    
    with tabs[3]:  # PIS
        st.markdown("""
        <div class="card">
            <div class="card-title">Apuração do PIS</div>
            <p>Esta seção apresenta a apuração do Programa de Integração Social (PIS).</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.itens_notas:
            pis, _ = calcular_pis_cofins(st.session_state.itens_notas)
            
            st.metric("Total PIS", f"R$ {pis['Valor PIS'].sum():,.2f}" if not pis.empty else "R$ 0,00")
            
            if not pis.empty:
                st.dataframe(pis, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma operação com PIS encontrada.")
        else:
            st.warning("Nenhum dado disponível. Por favor, carregue e processe os XMLs primeiro.")
    
    with tabs[4]:  # COFINS
        st.markdown("""
        <div class="card">
            <div class="card-title">Apuração do COFINS</div>
            <p>Esta seção apresenta a apuração da Contribuição para o Financiamento da Seguridade Social (COFINS).</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.itens_notas:
            _, cofins = calcular_pis_cofins(st.session_state.itens_notas)
            
            st.metric("Total COFINS", f"R$ {cofins['Valor COFINS'].sum():,.2f}" if not cofins.empty else "R$ 0,00")
            
            if not cofins.empty:
                st.dataframe(cofins, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma operação com COFINS encontrada.")
        else:
            st.warning("Nenhum dado disponível. Por favor, carregue e processe os XMLs primeiro.")
    
    with tabs[5]:  # Consolidador
        st.markdown("""
        <div class="card">
            <div class="card-title">Relatório Consolidado</div>
            <p>Esta seção apresenta um resumo consolidado de todos os impostos apurados.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.itens_notas:
            icms_normal, icms_st, difal = calcular_icms(st.session_state.itens_notas)
            ipi = calcular_ipi(st.session_state.itens_notas)
            pis, cofins = calcular_pis_cofins(st.session_state.itens_notas)
            
            relatorio = gerar_relatorio_consolidado(
                st.session_state.notas_fiscais,
                icms_normal, icms_st, difal,
                ipi, pis, cofins
            )
            
            # Resumo Geral
            st.markdown("### Resumo Geral")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Notas Fiscais", relatorio['Resumo Geral']['Quantidade de Notas Fiscais'])
                st.metric("Período", relatorio['Resumo Geral']['Período das Notas'])
            with col2:
                st.metric("Valor Total", f"R$ {relatorio['Resumo Geral']['Valor Total das Notas']:,.2f}")
            
            # Resumo por Imposto
            st.markdown("### Resumo por Imposto")
            
            # ICMS
            with st.expander("ICMS"):
                cols = st.columns(3)
                with cols[0]:
                    st.metric("ICMS Normal", f"R$ {relatorio['ICMS']['Valor Total ICMS Normal']:,.2f}")
                with cols[1]:
                    st.metric("ICMS ST", f"R$ {relatorio['ICMS']['Valor Total ICMS ST']:,.2f}")
                with cols[2]:
                    st.metric("DIFAL", f"R$ {relatorio['ICMS']['Valor Total DIFAL']:,.2f}")
            
            # IPI
            with st.expander("IPI"):
                st.metric("Total IPI", f"R$ {relatorio['IPI']['Valor Total IPI']:,.2f}")
            
            # PIS e COFINS
            with st.expander("PIS e COFINS"):
                cols = st.columns(2)
                with cols[0]:
                    st.metric("Total PIS", f"R$ {relatorio['PIS']['Valor Total PIS']:,.2f}")
                with cols[1]:
                    st.metric("Total COFINS", f"R$ {relatorio['COFINS']['Valor Total COFINS']:,.2f}")
            
            # Gráfico de pizza com a distribuição dos impostos
            impostos = {
                'ICMS Normal': relatorio['ICMS']['Valor Total ICMS Normal'],
                'ICMS ST': relatorio['ICMS']['Valor Total ICMS ST'],
                'DIFAL': relatorio['ICMS']['Valor Total DIFAL'],
                'IPI': relatorio['IPI']['Valor Total IPI'],
                'PIS': relatorio['PIS']['Valor Total PIS'],
                'COFINS': relatorio['COFINS']['Valor Total COFINS']
            }
            
            df_impostos = pd.DataFrame.from_dict(impostos, orient='index', columns=['Valor']).reset_index()
            df_impostos = df_impostos.rename(columns={'index': 'Imposto'})
            df_impostos = df_impostos[df_impostos['Valor'] > 0]
            
            if not df_impostos.empty:
                fig = px.pie(df_impostos, values='Valor', names='Imposto', 
                             title='Distribuição dos Valores de Impostos',
                             hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível. Por favor, carregue e processe os XMLs primeiro.")

if __name__ == "__main__":
    main()
