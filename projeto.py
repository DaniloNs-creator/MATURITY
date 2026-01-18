import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Configuração da página
st.set_page_config(page_title="Extrator DUIMP HAFELE", layout="wide")

# --- FUNÇÕES DE LIMPEZA E EXTRAÇÃO ---

def clean_number(num_str):
    """
    Converte string brasileira (ex: '1.065,1600000') para float (1065.16).
    """
    if not num_str:
        return 0.0
    try:
        # Remove pontos de milhar e troca vírgula por ponto
        cleaned = num_str.replace('.', '').replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def extract_taxes_from_text(content):
    """
    Função especializada para extrair os impostos baseada no dump de texto fornecido.
    Procura o valor numérico exato que antecede a frase chave.
    """
    taxes = {
        'II': 0.0,
        'IPI': 0.0,
        'PIS': 0.0,
        'COFINS': 0.0,
        'ICMS': 0.0
    }

    # Recorte: Vamos trabalhar apenas com a parte do texto referente aos tributos para evitar falsos positivos
    if "CALCULOS DOS TRIBUTOS - MERCADORIA" in content:
        # Pega tudo do cabeçalho de tributos até o fim do item
        tax_section = content.split("CALCULOS DOS TRIBUTOS - MERCADORIA")[1]
    else:
        return taxes # Retorna zerado se não achar a seção

    # --- 1. Extração de II, IPI, PIS, COFINS ---
    # Padrão identificado no seu texto:
    # NOME DO IMPOSTO (ex: II) -> quebra de linha -> vários textos -> VALOR -> "Valor A Recolher"
    
    for tax_name in ['II', 'IPI', 'PIS', 'COFINS']:
        # Regex Explicado:
        # 1. f"{tax_name}\n" -> Encontra o cabeçalho do imposto (ex: "II" seguido de enter)
        # 2. .*? -> Pega qualquer texto no meio (non-greedy)
        # 3. ([\d\.]+,\d+) -> CAPTURA o número (ex: 1.065,1600000)
        # 4. \s+Valor A Recolher -> Que esteja IMEDIATAMENTE antes da frase "Valor A Recolher"
        
        pattern = re.compile(rf'{tax_name}\n.*?([\d\.]+,\d+)\s+Valor A Recolher', re.DOTALL)
        match = pattern.search(tax_section)
        
        if match:
            taxes[tax_name] = clean_number(match.group(1))

    # --- 2. Extração de ICMS ---
    # Padrão identificado: "0,00 0,00 Valor Devido Base de Cálculo"
    # O primeiro número é o Valor Devido, o segundo é a Base. Queremos o primeiro.
    
    # Regex Explicado:
    # 1. ([\d\.]+,\d+) -> Captura o primeiro valor (Valor Devido)
    # 2. \s+ -> Espaço
    # 3. [\d\.]+,\d+ -> Ignora o segundo valor (Base de Cálculo)
    # 4. \s+Valor Devido Base de Cálculo -> Âncora do texto
    
    icms_pattern = re.search(r'([\d\.]+,\d+)\s+[\d\.]+,\d+\s+Valor Devido Base de Cálculo', tax_section)
    if icms_pattern:
        taxes['ICMS'] = clean_number(icms_pattern.group(1))

    return taxes

def process_pdf_duimp(pdf_file):
    full_text = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Divide o texto pelos itens (Adições)
    splitter = re.compile(r'(ITENS DA DUIMP - \d+)')
    parts = splitter.split(full_text)

    data = []

    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            header = parts[i]       # Ex: ITENS DA DUIMP - 00001
            content = parts[i+1]    # Conteúdo do item
            
            row = {}
            row['Item'] = header.replace('ITENS DA DUIMP - ', '').strip()
            
            # Extração de Dados Básicos (Partnumber, Descrição, NCM)
            pn_match = re.search(r'CÓDIGO INTERNO \(PARTNUMBER\)\n(.+)', content)
            row['Partnumber'] = pn_match.group(1).strip() if pn_match else ""
            
            desc_match = re.search(r'DENOMINACAO DO PRODUTO\n(.+)', content)
            row['Descrição'] = desc_match.group(1).strip() if desc_match else ""
            
            ncm_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', content)
            row['NCM'] = ncm_match.group(1) if ncm_match else ""
            
            # --- NOVA LÓGICA DE IMPOSTOS ---
            taxes = extract_taxes_from_text(content)
            
            row['II (R$)'] = taxes['II']
            row['IPI (R$)'] = taxes['IPI']
            row['PIS (R$)'] = taxes['PIS']
            row['COFINS (R$)'] = taxes['COFINS']
            row['ICMS (R$)'] = taxes['ICMS']
            
            row['Total Tributos (R$)'] = sum(taxes.values())
            
            data.append(row)

    return pd.DataFrame(data)

# --- INTERFACE STREAMLIT ---

st.title("📑 Extrator DUIMP HAFELE (Versão Regex Estrita)")
st.markdown("Importe o PDF para gerar o relatório de impostos por item.")

uploaded_file = st.file_uploader("Carregue o PDF da DUIMP", type="pdf")

if uploaded_file:
    with st.spinner("Analisando PDF..."):
        try:
            df = process_pdf_duimp(uploaded_file)
            
            if not df.empty:
                st.success(f"Processamento concluído! {len(df)} itens extraídos.")
                
                # Métricas
                total_geral = df['Total Tributos (R$)'].sum()
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Tributos", f"R$ {total_geral:,.2f}")
                col2.metric("Total II", f"R$ {df['II (R$)'].sum():,.2f}")
                col3.metric("Total IPI", f"R$ {df['IPI (R$)'].sum():,.2f}")
                
                # Exibição
                st.dataframe(
                    df.style.format({
                        'II (R$)': '{:,.2f}',
                        'IPI (R$)': '{:,.2f}',
                        'PIS (R$)': '{:,.2f}',
                        'COFINS (R$)': '{:,.2f}',
                        'ICMS (R$)': '{:,.2f}',
                        'Total Tributos (R$)': '{:,.2f}',
                    }),
                    use_container_width=True
                )
                
                # Download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Tributos')
                
                st.download_button(
                    label="📥 Baixar Excel",
                    data=buffer.getvalue(),
                    file_name="tributos_duimp_final.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.warning("Nenhum item encontrado. Verifique o arquivo.")
                
        except Exception as e:
            st.error(f"Erro: {e}")
