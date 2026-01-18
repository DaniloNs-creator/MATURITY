import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Configuração da página
st.set_page_config(page_title="Extrator DUIMP HAFELE", layout="wide")

# --- FUNÇÕES AUXILIARES ---

def clean_number(num_str):
    """
    Converte string numérica brasileira (ex: '1.065,1600000') para float (1065.16).
    Retorna 0.0 se a string for vazia ou inválida.
    """
    if not num_str:
        return 0.0
    try:
        # Remove ponto de milhar e troca vírgula por ponto
        cleaned = num_str.replace('.', '').replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def extract_federal_tax(tax_name, text_block):
    """
    Extrai o 'Valor A Recolher' de impostos federais (II, IPI, PIS, COFINS).
    Padrão identificado:
       [NOME IMPOSTO]
       ...
       [VALOR] Valor A Recolher
    """
    try:
        # 1. Localiza o bloco que começa com o Nome do Imposto (ex: "II")
        # e vai até o próximo imposto ou fim da seção, para evitar pegar valores errados.
        # O regex (?=\n[A-Z]+|\Z) olha para frente para parar antes do próximo título.
        pattern = re.compile(rf'{tax_name}\n(.*?)(?=\n[A-Z]+|\Z)', re.DOTALL)
        match = pattern.search(text_block)
        
        if match:
            block_content = match.group(1)
            # 2. Dentro desse bloco, busca o número antes da frase "Valor A Recolher"
            val_match = re.search(r'([\d\.]+,\d+)\s+Valor A Recolher', block_content)
            if val_match:
                return clean_number(val_match.group(1))
    except Exception:
        return 0.0
    return 0.0

def extract_icms(text_block):
    """
    Extrai o ICMS baseado no padrão:
    '0,00 0,00 Valor Devido Base de Cálculo'
    O primeiro número é o Valor Devido, o segundo é a Base.
    """
    try:
        if "INFORMAÇÕES DO ICMS DA MERCADORIA" in text_block:
            # Pega a linha exata que contém "Valor Devido Base de Cálculo"
            # Captura dois grupos numéricos antes dessa frase
            match = re.search(r'([\d\.]+,\d+)\s+([\d\.]+,\d+)\s+Valor Devido Base de Cálculo', text_block)
            if match:
                valor_devido = clean_number(match.group(1))
                return valor_devido
    except Exception:
        return 0.0
    return 0.0

def process_pdf_duimp(pdf_file):
    """Lê o PDF e estrutura os dados em DataFrame."""
    full_text = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Divide o texto pelos itens (Adições)
    # Padrão: "ITENS DA DUIMP - 00001", "ITENS DA DUIMP - 00002", etc.
    splitter = re.compile(r'(ITENS DA DUIMP - \d+)')
    parts = splitter.split(full_text)

    data = []

    # O split gera uma lista onde os índices ímpares são os cabeçalhos e pares o conteúdo
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            header = parts[i]       # Ex: ITENS DA DUIMP - 00001
            content = parts[i+1]    # Texto do item
            
            row = {}
            
            # Identificação do Item
            row['Item'] = header.replace('ITENS DA DUIMP - ', '').strip()
            
            # Dados do Produto (Partnumber, Descrição, NCM)
            pn_match = re.search(r'CÓDIGO INTERNO \(PARTNUMBER\)\n(.+)', content)
            row['Partnumber'] = pn_match.group(1).strip() if pn_match else ""
            
            desc_match = re.search(r'DENOMINACAO DO PRODUTO\n(.+)', content)
            row['Descrição'] = desc_match.group(1).strip() if desc_match else ""
            
            ncm_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', content)
            row['NCM'] = ncm_match.group(1) if ncm_match else ""
            
            # --- EXTRAÇÃO DE IMPOSTOS ---
            # Cortamos o texto para focar apenas na parte de tributos para evitar ruído
            if "CALCULOS DOS TRIBUTOS - MERCADORIA" in content:
                tax_section = content.split("CALCULOS DOS TRIBUTOS - MERCADORIA")[1]
                
                # Federais
                row['II (R$)'] = extract_federal_tax('II', tax_section)
                row['IPI (R$)'] = extract_federal_tax('IPI', tax_section)
                row['PIS (R$)'] = extract_federal_tax('PIS', tax_section)
                row['COFINS (R$)'] = extract_federal_tax('COFINS', tax_section)
                
                # Estadual
                row['ICMS (R$)'] = extract_icms(tax_section)
                
                # Totalizador
                row['Total Tributos (R$)'] = (
                    row['II (R$)'] + row['IPI (R$)'] + 
                    row['PIS (R$)'] + row['COFINS (R$)'] + 
                    row['ICMS (R$)']
                )
            else:
                # Caso não tenha seção de tributos (ex: item cancelado ou atípico)
                row['II (R$)'] = 0.0
                row['IPI (R$)'] = 0.0
                row['PIS (R$)'] = 0.0
                row['COFINS (R$)'] = 0.0
                row['ICMS (R$)'] = 0.0
                row['Total Tributos (R$)'] = 0.0
                
            data.append(row)

    return pd.DataFrame(data)

# --- INTERFACE STREAMLIT ---

st.title("📑 Extrator DUIMP HAFELE")
st.markdown("""
Este app processa o PDF padrão da DUIMP e gera uma tabela com os impostos discriminados por item.
""")

uploaded_file = st.file_uploader("Carregue o PDF da DUIMP", type="pdf")

if uploaded_file:
    with st.spinner("Lendo PDF e calculando impostos..."):
        try:
            df = process_pdf_duimp(uploaded_file)
            
            if not df.empty:
                st.success(f"Processamento concluído! {len(df)} itens encontrados.")
                
                # Métricas de Resumo
                col1, col2, col3 = st.columns(3)
                total_trib = df['Total Tributos (R$)'].sum()
                total_ii = df['II (R$)'].sum()
                total_ipi = df['IPI (R$)'].sum()
                
                col1.metric("Total Tributos (Todos)", f"R$ {total_trib:,.2f}")
                col2.metric("Total II", f"R$ {total_ii:,.2f}")
                col3.metric("Total IPI", f"R$ {total_ipi:,.2f}")
                
                # Visualização da Tabela
                st.dataframe(
                    df.style.format({
                        'II (R$)': '{:,.2f}',
                        'IPI (R$)': '{:,.2f}',
                        'PIS (R$)': '{:,.2f}',
                        'COFINS (R$)': '{:,.2f}',
                        'ICMS (R$)': '{:,.2f}',
                        'Total Tributos (R$)': '{:,.2f}',
                    }),
                    use_container_width=True,
                    height=500
                )
                
                # Botão de Download Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Tributos')
                    # Ajuste de largura das colunas
                    worksheet = writer.sheets['Tributos']
                    worksheet.set_column(0, 1, 10) # Item
                    worksheet.set_column(1, 2, 15) # Partnumber
                    worksheet.set_column(2, 3, 40) # Descrição
                    worksheet.set_column(3, 10, 15) # Valores
                
                st.download_button(
                    label="📥 Baixar Tabela em Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="tributos_duimp.xlsx",
                    mime="application/vnd.ms-excel"
                )
                
            else:
                st.warning("O PDF foi lido, mas nenhum item foi identificado. Verifique se é o arquivo correto.")
                
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
