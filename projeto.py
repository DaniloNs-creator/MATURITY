import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Configuração da página para dar mais espaço à tabela
st.set_page_config(page_title="Extrator DUIMP HAFELE", layout="wide")

def clean_number(num_str):
    """
    Converte string numérica brasileira (1.234,5678) para float (1234.5678).
    Retorna 0.0 se falhar.
    """
    if not num_str:
        return 0.0
    try:
        # Remove pontos de milhar e substitui vírgula decimal por ponto
        cleaned = num_str.replace('.', '').replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def extract_tax_value(tax_name, text_block):
    """
    Busca o valor 'A Recolher' para um imposto específico dentro do bloco de texto do item.
    Lógica: Encontra o cabeçalho do imposto (ex: 'II') e busca o padrão numérico 
    imediatamente antes da frase 'Valor A Recolher'.
    """
    try:
        # 1. Isolar o bloco do imposto específico (do nome do imposto até o próximo rótulo ou fim)
        # O regex busca, por exemplo, de "II" até o próximo imposto ou fim do bloco
        pattern_block = re.compile(rf'{tax_name}\n(.*?)(?=\n[A-Z]{{2,}}|\Z)', re.DOTALL)
        match_block = pattern_block.search(text_block)
        
        if match_block:
            content = match_block.group(1)
            # 2. Dentro desse bloco, buscar o valor associado a "Valor A Recolher"
            # O padrão no seu PDF é: "134,0800000 Valor A Recolher"
            val_match = re.search(r'([\d\.]+,\d+)\s+Valor A Recolher', content)
            if val_match:
                return clean_number(val_match.group(1))
    except Exception:
        return 0.0
    return 0.0

def extract_icms(text_block):
    """
    Extrai dados do ICMS que tem um formato ligeiramente diferente no rodapé do item.
    Padrão: 0,00 0,00 Valor Devido Base de Cálculo
    """
    try:
        # Busca a seção de ICMS
        if "INFORMAÇÕES DO ICMS DA MERCADORIA" in text_block:
            # Tenta capturar a linha de valores
            # Procura por dois números seguidos de "Valor Devido Base de Cálculo"
            match = re.search(r'([\d\.]+,\d+)\s+([\d\.]+,\d+)\s+Valor Devido Base de Cálculo', text_block)
            if match:
                valor_devido = clean_number(match.group(1))
                base_calculo = clean_number(match.group(2))
                return valor_devido, base_calculo
    except:
        pass
    return 0.0, 0.0

def process_pdf(pdf_file):
    full_text = ""
    
    # Leitura do PDF
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Dividir o texto em Itens (Adições)
    # O padrão do cabeçalho é "ITENS DA DUIMP - {numero}"
    # Usamos regex split para manter o delimitador e reconstruir a lista
    splitter = re.compile(r'(ITENS DA DUIMP - \d+)')
    parts = splitter.split(full_text)

    data_rows = []

    # Iterar sobre as partes (pula o preâmbulo do PDF)
    # A lista parts fica: [TextoInicial, "ITENS... - 01", Conteudo01, "ITENS... - 02", Conteudo02...]
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            header = parts[i]       # Ex: ITENS DA DUIMP - 00001
            content = parts[i+1]    # O texto contendo dados do produto e impostos
            
            row = {}
            
            # --- DADOS BÁSICOS DO ITEM ---
            row['Item'] = header.replace('ITENS DA DUIMP - ', '').strip()
            
            # Partnumber
            pn_match = re.search(r'CÓDIGO INTERNO \(PARTNUMBER\)\n(.+)', content)
            row['Partnumber'] = pn_match.group(1).strip() if pn_match else ""
            
            # Descrição
            desc_match = re.search(r'DENOMINACAO DO PRODUTO\n(.+)', content)
            row['Descrição'] = desc_match.group(1).strip() if desc_match else ""
            
            # NCM
            ncm_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', content)
            row['NCM'] = ncm_match.group(1) if ncm_match else ""
            
            # Valor Aduaneiro/Mercadoria (Aproximado pelo Valor Tot Cond Venda ou Base Calculo II)
            # Vamos tentar pegar a Base de Cálculo do II que é o valor aduaneiro para imposto
            base_ii_match = re.search(r'II\n.*?([\d\.]+,\d+)\s+Base de Cálculo - Específica', content, re.DOTALL)
            if not base_ii_match:
                 base_ii_match = re.search(r'II\n.*?([\d\.]+,\d+)\s+Base de Cálculo', content, re.DOTALL)
            
            row['Valor Aduaneiro (R$)'] = clean_number(base_ii_match.group(1)) if base_ii_match else 0.0

            # --- EXTRAÇÃO DE TRIBUTOS ---
            # Cortamos o texto para focar na área de impostos
            if "CALCULOS DOS TRIBUTOS - MERCADORIA" in content:
                tax_section = content.split("CALCULOS DOS TRIBUTOS - MERCADORIA")[1]
                
                # Extrair II, IPI, PIS, COFINS
                row['II a Recolher'] = extract_tax_value('II', tax_section)
                row['IPI a Recolher'] = extract_tax_value('IPI', tax_section)
                row['PIS a Recolher'] = extract_tax_value('PIS', tax_section)
                row['COFINS a Recolher'] = extract_tax_value('COFINS', tax_section)
                
                # Extrair ICMS
                val_icms, base_icms = extract_icms(tax_section)
                row['ICMS a Recolher'] = val_icms
                row['ICMS Base Calc'] = base_icms
                
                # Total de Impostos da Linha
                row['Total Tributos Item'] = (row['II a Recolher'] + row['IPI a Recolher'] + 
                                              row['PIS a Recolher'] + row['COFINS a Recolher'] + 
                                              row['ICMS a Recolher'])
            else:
                # Caso não ache a seção de tributos (ex: item isento ou erro de leitura)
                row['II a Recolher'] = 0.0
                row['IPI a Recolher'] = 0.0
                row['PIS a Recolher'] = 0.0
                row['COFINS a Recolher'] = 0.0
                row['ICMS a Recolher'] = 0.0
                row['Total Tributos Item'] = 0.0

            data_rows.append(row)

    return pd.DataFrame(data_rows)

# --- INTERFACE DO USUÁRIO ---

st.title("📑 Extrator de Tributos DUIMP (Padrão HAFELE)")
st.markdown("Importe o PDF da DUIMP para gerar o DataFrame com Partnumber, NCM e discriminação detalhada de impostos (II, IPI, PIS, COFINS, ICMS).")

uploaded_file = st.file_uploader("Carregar arquivo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processando dados e calculando impostos..."):
        try:
            df = process_pdf(uploaded_file)
            
            if not df.empty:
                # Formatação para exibição (apenas visual)
                st.success("Dados extraídos com sucesso!")
                
                # Métricas Gerais
                total_trib = df['Total Tributos Item'].sum()
                total_aduaneiro = df['Valor Aduaneiro (R$)'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Itens Processados", len(df))
                c2.metric("Total Valor Aduaneiro", f"R$ {total_aduaneiro:,.2f}")
                c3.metric("Total Tributos", f"R$ {total_trib:,.2f}")
                
                # Exibir DataFrame
                st.dataframe(
                    df.style.format({
                        'Valor Aduaneiro (R$)': 'R$ {:,.2f}',
                        'II a Recolher': 'R$ {:,.2f}',
                        'IPI a Recolher': 'R$ {:,.2f}',
                        'PIS a Recolher': 'R$ {:,.2f}',
                        'COFINS a Recolher': 'R$ {:,.2f}',
                        'ICMS a Recolher': 'R$ {:,.2f}',
                        'Total Tributos Item': 'R$ {:,.2f}',
                    }),
                    use_container_width=True,
                    height=500
                )
                
                # Botões de Download
                col_d1, col_d2 = st.columns(2)
                
                # Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Tributos')
                    # Ajuste automático de colunas (básico)
                    worksheet = writer.sheets['Tributos']
                    worksheet.set_column(0, len(df.columns) - 1, 15)
                    
                with col_d1:
                    st.download_button(
                        label="📥 Baixar em Excel (.xlsx)",
                        data=buffer.getvalue(),
                        file_name="tributos_duimp_hafele.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                
                # CSV
                with col_d2:
                    csv = df.to_csv(index=False, sep=';', decimal=',')
                    st.download_button(
                        label="📥 Baixar em CSV",
                        data=csv,
                        file_name="tributos_duimp_hafele.csv",
                        mime="text/csv"
                    )

            else:
                st.warning("Não foi possível identificar itens no PDF. Verifique se o arquivo segue o padrão informado.")
                
        except Exception as e:
            st.error(f"Ocorreu um erro no processamento: {e}")
