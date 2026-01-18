import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Configuração Profissional da Página
st.set_page_config(
    page_title="Extrator DUIMP Pro | Hafele",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS para visual profissional ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 20px;}
    .stDataFrame {border: 1px solid #e6e6e6; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE ENGENHARIA DE DADOS ---

def parse_br_float(num_str):
    """
    Converte strings numéricas complexas do padrão brasileiro/SISCOMEX para float.
    Ex: '1.065,1600000' -> 1065.16
    """
    if not num_str:
        return 0.0
    try:
        # Remove pontos de milhar e caracteres estranhos, mantém apenas dígitos e vírgula
        clean = re.sub(r'[^\d,]', '', num_str)
        # Troca vírgula por ponto
        clean = clean.replace(',', '.')
        return float(clean)
    except:
        return 0.0

def extract_header_info(full_text):
    """
    Extrai informações globais do processo (Cabeçalho do PDF).
    """
    info = {
        "Processo": "N/A",
        "Importador": "N/A",
        "Data Registro": "N/A"
    }
    
    # Regex para capturar Processo (Ex: PROCESSO #28523)
    proc_match = re.search(r'PROCESSO\s*[#:]?\s*(\d+)', full_text)
    if proc_match:
        info["Processo"] = proc_match.group(1)
        
    # Regex para Importador
    imp_match = re.search(r'IMPORTADOR\s*\n\s*"?([^"\n]+)', full_text)
    if imp_match:
        info["Importador"] = imp_match.group(1).strip()

    return info

def extract_taxes_advanced(item_text):
    """
    Extrai impostos usando lógica posicional estrita baseada no padrão do SISCOMEX.
    O padrão é: [VALOR] [Rótulo]
    """
    taxes = {
        'II': 0.0,
        'IPI': 0.0,
        'PIS': 0.0,
        'COFINS': 0.0,
        'ICMS': 0.0,
        'Taxa Siscomex': 0.0 # Se disponível no item
    }

    # Recortar apenas a seção de tributos do item
    if "CALCULOS DOS TRIBUTOS" in item_text:
        # Pega do inicio dos calculos até o fim (ou até informações do ICMS)
        tax_block = item_text.split("CALCULOS DOS TRIBUTOS")[1]
        
        # --- IMPOSTOS FEDERAIS (II, IPI, PIS, COFINS) ---
        # A estrutura é hierárquica. Procuramos o nome do imposto e depois o valor.
        # Regex: Procura o Nome do Imposto, avança até achar um número que é seguido imediatamente por "Valor A Recolher"
        
        for imposto in ['II', 'IPI', 'PIS', 'COFINS']:
            # Padrão: 
            # 1. Nome do imposto (ex: II)
            # 2. Qualquer texto (non-greedy)
            # 3. Um número formatado (ex: 134,0800000)
            # 4. A frase "Valor A Recolher"
            
            # Limitamos a busca para não invadir o próximo imposto usando lookahead ou limitadores
            pattern = re.compile(rf'{imposto}\s*\n.*?([\d\.]+,\d+)\s+Valor A Recolher', re.DOTALL)
            match = pattern.search(tax_block)
            if match:
                taxes[imposto] = parse_br_float(match.group(1))

        # --- ICMS ---
        # Padrão específico do rodapé: "0,00 0,00 Valor Devido Base de Cálculo"
        # O primeiro número é o Valor Devido.
        icms_match = re.search(r'([\d\.]+,\d+)\s+[\d\.]+,\d+\s+Valor Devido Base de Cálculo', tax_block)
        if icms_match:
            taxes['ICMS'] = parse_br_float(icms_match.group(1))
            
    return taxes

def process_full_pdf(pdf_file):
    full_text = ""
    
    # 1. Leitura Otimizada
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Extract layout=True ajuda a manter a estrutura visual, mas text puro é melhor para regex complexo
            full_text += page.extract_text() + "\n"

    # 2. Extração de Dados Globais
    header_info = extract_header_info(full_text)

    # 3. Segmentação por Item
    # O padrão "ITENS DA DUIMP - X" é o divisor mestre
    item_splitter = re.compile(r'ITENS DA DUIMP\s*-\s*(\d+)')
    
    # split retorna: [texto_pre, numero_item_1, conteudo_1, numero_item_2, conteudo_2...]
    segments = item_splitter.split(full_text)
    
    data_rows = []

    # Se tivermos segmentos, começamos do índice 1 (o 0 é o cabeçalho geral)
    if len(segments) > 1:
        # Itera de 2 em 2: (Número do Item, Conteúdo do Item)
        for i in range(1, len(segments), 2):
            item_num = segments[i]
            content = segments[i+1]
            
            row = header_info.copy() # Começa com os dados globais
            row['Item'] = item_num.zfill(3) # Padroniza 001, 002
            
            # --- EXTRAÇÃO DE DADOS DO PRODUTO ---
            
            # Partnumber
            pn = re.search(r'CÓDIGO INTERNO \(PARTNUMBER\)\s*\n(.+)', content)
            row['Partnumber'] = pn.group(1).strip() if pn else ""
            
            # Descrição (Pega a linha abaixo de DENOMINACAO e concatena se tiver mais)
            desc = re.search(r'DENOMINACAO DO PRODUTO\s*\n(.+?)(?=\n[A-Z]|\nCÓDIGO)', content, re.DOTALL)
            row['Descrição'] = desc.group(1).replace('\n', ' ').strip() if desc else ""
            
            # NCM
            ncm = re.search(r'(\d{4}\.\d{2}\.\d{2})', content)
            row['NCM'] = ncm.group(1) if ncm else ""
            
            # Quantidade Estatística
            qtde = re.search(r'([\d\.]+,\d+)\s+Qtde Unid\. Estatística', content)
            row['Qtde Estatística'] = parse_br_float(qtde.group(1)) if qtde else 0.0
            
            # Valor Aduaneiro (Base para impostos) - Geralmente é a Base de Cálculo do II
            # Procura: "II" ... "Base de Cálculo - Específica (R$)" ou "Base de Cálculo (R$)"
            # O numero vem ANTES da frase "Base de Cálculo"
            vlr_aduaneiro = re.search(r'II\s*\n.*?([\d\.]+,\d+)\s+Base de Cálculo', content, re.DOTALL)
            row['Valor Aduaneiro (R$)'] = parse_br_float(vlr_aduaneiro.group(1)) if vlr_aduaneiro else 0.0

            # --- EXTRAÇÃO DE TRIBUTOS (CHAMADA DA FUNÇÃO ESPECIALIZADA) ---
            taxes = extract_taxes_advanced(content)
            
            row.update({
                'II (R$)': taxes['II'],
                'IPI (R$)': taxes['IPI'],
                'PIS (R$)': taxes['PIS'],
                'COFINS (R$)': taxes['COFINS'],
                'ICMS (R$)': taxes['ICMS']
            })
            
            # Cálculo de Totais
            row['Total Tributos (R$)'] = (
                taxes['II'] + taxes['IPI'] + taxes['PIS'] + taxes['COFINS'] + taxes['ICMS']
            )
            
            data_rows.append(row)

    return pd.DataFrame(data_rows)

# --- APP PRINCIPAL ---

st.title("🚀 Extrator de DUIMP | Hafele Brasil")
st.markdown("### Ferramenta Profissional de Conferência Aduaneira")
st.markdown("Importe o arquivo PDF padrão da DUIMP para gerar o relatório analítico completo.")

uploaded_file = st.file_uploader("Arraste seu PDF aqui", type=['pdf'], help="Aceita apenas formato PDF nativo do sistema Hafele")

if uploaded_file:
    with st.spinner("Processando todas as páginas e extraindo dados..."):
        try:
            # Processamento
            df = process_full_pdf(uploaded_file)
            
            if not df.empty:
                st.success(f"Sucesso! Processo {df['Processo'].iloc[0]} carregado. {len(df)} itens extraídos.")
                
                # --- DASHBOARD DE RESUMO ---
                st.markdown("#### 📊 Resumo Financeiro da Importação")
                
                total_trib = df['Total Tributos (R$)'].sum()
                total_aduan = df['Valor Aduaneiro (R$)'].sum()
                
                # Layout de cartões
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Valor Aduaneiro Total", f"R$ {total_aduan:,.2f}")
                col2.metric("Total de Tributos", f"R$ {total_trib:,.2f}")
                col3.metric("Total II + IPI", f"R$ {(df['II (R$)'].sum() + df['IPI (R$)'].sum()):,.2f}")
                col4.metric("Total PIS + COFINS", f"R$ {(df['PIS (R$)'].sum() + df['COFINS (R$)'].sum()):,.2f}")
                
                st.divider()
                
                # --- VISUALIZAÇÃO DOS DADOS ---
                st.markdown("#### 📑 Detalhamento por Item")
                
                # Colunas para exibir no preview (esconde algumas para não poluir)
                cols_to_show = [
                    'Item', 'Partnumber', 'Descrição', 'NCM', 
                    'Valor Aduaneiro (R$)', 'II (R$)', 'IPI (R$)', 
                    'PIS (R$)', 'COFINS (R$)', 'ICMS (R$)', 'Total Tributos (R$)'
                ]
                
                st.dataframe(
                    df[cols_to_show].style.format({
                        'Valor Aduaneiro (R$)': 'R$ {:,.2f}',
                        'II (R$)': '{:,.2f}',
                        'IPI (R$)': '{:,.2f}',
                        'PIS (R$)': '{:,.2f}',
                        'COFINS (R$)': '{:,.2f}',
                        'ICMS (R$)': '{:,.2f}',
                        'Total Tributos (R$)': '{:,.2f}'
                    }),
                    use_container_width=True,
                    height=600
                )
                
                # --- ÁREA DE DOWNLOAD ---
                st.markdown("#### 📥 Exportação")
                
                col_d1, col_d2 = st.columns(2)
                
                # Excel Engine com formatação nativa
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Analitico_DUIMP')
                    workbook = writer.book
                    worksheet = writer.sheets['Analitico_DUIMP']
                    
                    # Formatos
                    money_fmt = workbook.add_format({'num_format': 'R$ #,##0.00'})
                    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
                    
                    # Aplicar formato nas colunas de valor (indices aproximados, ajuste conforme dataframe final)
                    # Colunas de J até O (exemplo) são valores
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_fmt)
                        if "(R$)" in value:
                             worksheet.set_column(col_num, col_num, 18, money_fmt)
                        else:
                             worksheet.set_column(col_num, col_num, 15)

                with col_d1:
                    st.download_button(
                        label="Baixar Relatório Excel (.xlsx)",
                        data=buffer.getvalue(),
                        file_name=f"DUIMP_{df['Processo'].iloc[0]}_analitico.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                    
                with col_d2:
                    csv_data = df.to_csv(index=False, sep=';', decimal=',')
                    st.download_button(
                        label="Baixar Relatório CSV",
                        data=csv_data,
                        file_name=f"DUIMP_{df['Processo'].iloc[0]}.csv",
                        mime="text/csv"
                    )
            
            else:
                st.error("ERRO CRÍTICO: O arquivo parece ser um PDF, mas o padrão 'ITENS DA DUIMP' não foi encontrado. Verifique se o arquivo não é uma imagem digitalizada.")
                
        except Exception as e:
            st.error(f"Ocorreu um erro técnico no processamento: {str(e)}")
            st.write("Detalhes para suporte técnico:", e)
