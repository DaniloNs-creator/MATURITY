import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Configuração da página
st.set_page_config(page_title="Extrator HAFELE DUIMP", layout="wide")

def convert_br_number(num_str):
    """Converte string '1.234,56' para float 1234.56"""
    if not num_str:
        return 0.0
    try:
        # Remove pontos de milhar e troca vírgula por ponto
        clean_str = num_str.replace('.', '').replace(',', '.')
        return float(clean_str)
    except:
        return 0.0

def extract_data_from_pdf(pdf_file):
    all_text = ""
    
    # 1. Extração do texto bruto do PDF
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"

    # 2. Lógica de Parsing baseada no padrão fixo
    # O padrão indica que cada item começa com "ITENS DA DUIMP - {numero}"
    # Vamos dividir o texto nesses blocos
    
    # Regex para encontrar o início de cada item
    item_splitter = re.compile(r'(ITENS DA DUIMP - \d+)')
    parts = item_splitter.split(all_text)
    
    items_data = []
    
    # O split gera: [Texto Inicial, "ITENS... - 01", Conteudo 01, "ITENS... - 02", Conteudo 02...]
    # Vamos pular o preâmbulo e iterar de 2 em 2 (marcador + conteúdo)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            header = parts[i]   # Ex: ITENS DA DUIMP - 00001
            content = parts[i+1] # Todo o texto do item até o próximo
            
            # Dicionário para armazenar os dados deste item
            item = {}
            
            # --- Extração via Regex ---
            
            # 1. Número do Item
            item['Item'] = header.replace('ITENS DA DUIMP - ', '').strip()
            
            # 2. Código Produto (Partnumber)
            # Padrão: CÓDIGO INTERNO (PARTNUMBER)\n{codigo} Código interno
            partnumber_match = re.search(r'CÓDIGO INTERNO \(PARTNUMBER\)\n(.+?)\s', content)
            item['Partnumber'] = partnumber_match.group(1).strip() if partnumber_match else "N/A"
            
            # 3. Denominação
            desc_match = re.search(r'DENOMINACAO DO PRODUTO\n(.+)', content)
            item['Descrição'] = desc_match.group(1).strip() if desc_match else "N/A"
            
            # 4. NCM
            # Padrão: costuma aparecer na linha de integração, ex: 3926.30.00
            ncm_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', content)
            item['NCM'] = ncm_match.group(1) if ncm_match else "N/A"
            
            # 5. Quantidade
            # Padrão: {numero} Qtde Unid. Comercial
            qty_match = re.search(r'([\d\.]+,\d+)\s+Qtde Unid\. Comercial', content)
            item['Qtde'] = convert_br_number(qty_match.group(1)) if qty_match else 0
            
            # 6. Unidade
            # Padrão: {UNIDADE} Unidade Comercial
            unit_match = re.search(r'([A-Z]+)\s+Unidade Comercial', content)
            item['Unid'] = unit_match.group(1) if unit_match else ""
            
            # 7. Valor Unitário
            # Padrão: {valor} Valor Unit Cond Venda
            vlr_unit_match = re.search(r'([\d\.]+,\d+)\s+Valor Unit Cond Venda', content)
            item['Vlr Unit'] = convert_br_number(vlr_unit_match.group(1)) if vlr_unit_match else 0
            
            # 8. Valor Total
            # Padrão: {valor} Valor Tot. Cond Venda
            vlr_tot_match = re.search(r'([\d\.]+,\d+)\s+Valor Tot\. Cond Venda', content)
            item['Vlr Total (Moeda)'] = convert_br_number(vlr_tot_match.group(1)) if vlr_tot_match else 0

            # 9. Impostos (II, IPI, PIS, COFINS)
            # A lógica é procurar a string do imposto e capturar o valor próximo a "Valor A Recolher"
            # O texto costuma ter: {valor} Valor A Recolher (R$)
            
            def get_tax(tax_name, text_block):
                # Procura o bloco do imposto específico e depois o valor a recolher dentro dele
                # Regex simplificado assumindo que a ordem é mantida no bloco
                try:
                    # Pega o trecho que começa com o nome do imposto até a próxima quebra de linha dupla ou outro imposto
                    tax_block_match = re.search(f'{tax_name}\n(.+?)(?=\n[A-Z]|\Z)', text_block, re.DOTALL)
                    if tax_block_match:
                        block = tax_block_match.group(1)
                        # Busca o valor que antecede "Valor A Recolher"
                        val_match = re.search(r'([\d\.]+,\d+)\s+Valor A Recolher', block)
                        return convert_br_number(val_match.group(1)) if val_match else 0.0
                except:
                    return 0.0
                return 0.0

            # Como o texto é contínuo, vamos cortar o texto apenas na parte de CÁLCULOS DOS TRIBUTOS para evitar pegar o resumo
            tributos_part = content.split('CALCULOS DOS TRIBUTOS - MERCADORIA')
            if len(tributos_part) > 1:
                trib_content = tributos_part[1]
                item['II (R$)'] = get_tax('II', trib_content)
                item['IPI (R$)'] = get_tax('IPI', trib_content)
                item['PIS (R$)'] = get_tax('PIS', trib_content)
                item['COFINS (R$)'] = get_tax('COFINS', trib_content)
            else:
                item['II (R$)'] = 0.0
                item['IPI (R$)'] = 0.0
                item['PIS (R$)'] = 0.0
                item['COFINS (R$)'] = 0.0

            items_data.append(item)
            
    return pd.DataFrame(items_data)

# --- Interface Streamlit ---

st.title("📄 Extrator de PDF HAFELE (Padrão DUIMP)")
st.markdown("""
Este aplicativo converte o PDF de conferência da DUIMP (formato padrão Hafele) 
em uma tabela Excel/CSV para análise.
""")

uploaded_file = st.file_uploader("Arraste o PDF aqui", type="pdf")

if uploaded_file is not None:
    with st.spinner('Lendo e processando o PDF...'):
        try:
            df = extract_data_from_pdf(uploaded_file)
            
            if not df.empty:
                st.success(f"Sucesso! {len(df)} itens extraídos.")
                
                # Exibir métricas rápidas
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Itens", len(df))
                col2.metric("Valor Total (Moeda)", f"{df['Vlr Total (Moeda)'].sum():,.2f}")
                col3.metric("Total II (R$)", f"{df['II (R$)'].sum():,.2f}")
                
                # Exibir Tabela
                st.dataframe(df, use_container_width=True)
                
                # Botão de Download Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='DUIMP')
                
                st.download_button(
                    label="📥 Baixar como Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"duimp_extraida.xlsx",
                    mime="application/vnd.ms-excel"
                )
                
                # Botão de Download CSV
                csv = df.to_csv(index=False, sep=';', decimal=',')
                st.download_button(
                    label="📥 Baixar como CSV",
                    data=csv,
                    file_name="duimp_extraida.csv",
                    mime="text/csv"
                )
                
            else:
                st.warning("O PDF foi lido, mas nenhum item foi encontrado. Verifique se o arquivo está no formato padrão correto.")
                
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
