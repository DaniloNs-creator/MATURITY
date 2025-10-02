import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_all_data_from_pdf(pdf_file):
    """
    Extrai todas as informações mapeadas do arquivo PDF da Unimed,
    retornando DataFrames para cada seção.
    """
    faturas_df = None
    resumo_faturamento_df = None
    all_events_df = None
    
    # Dicionário para armazenar informações do cabeçalho
    header_data = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        # Extração da primeira página para cabeçalho, faturas e resumo
        first_page_text = pdf.pages[0].extract_text()
        
        # 1. Extrair informações do cabeçalho
        competence_match = re.search(r"Competência: (.+)", first_page_text)
        if competence_match:
            header_data["Competência"] = competence_match.group(1).strip()
            
        cnpj_match = re.search(r"CNPJ: (.+)", first_page_text)
        if cnpj_match:
            header_data["CNPJ"] = cnpj_match.group(1).strip()
        
        # 2. Extrair a tabela de Faturas
        faturas_tables = pdf.pages[0].extract_tables()
        for table in faturas_tables:
            if table and any("Fatura" in cell for cell in table[0]):
                headers = [h.replace("\n", " ") for h in table[0]]
                faturas_df = pd.DataFrame(table[1:], columns=headers)
                faturas_df = faturas_df.rename(columns={"Valor Bruto ": "Valor Bruto"})
                break
                
        # 3. Extrair Resumo do Faturamento
        resumo_match = re.search(r"RESUMO DO FATURAMENTO\n\n(.+?)(?=\nFamília:|\nTotal de Faturas:)", first_page_text, re.DOTALL)
        if resumo_match:
            resumo_text = resumo_match.group(1)
            resumo_lines = resumo_text.strip().split('\n')
            resumo_data = {}
            for line in resumo_lines:
                parts = line.rsplit(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    resumo_data[key] = value
            resumo_faturamento_df = pd.DataFrame([resumo_data]).transpose().reset_index()
            resumo_faturamento_df.columns = ["Item", "Valor"]
            
        # 4. Extrair tabelas de eventos de todas as páginas
        all_events = []
        for page in pdf.pages:
            text = page.extract_text()
            family_match = re.search(r"Família: (\d+)", text)
            responsible_match = re.search(r"Responsável: (.+)", text)
            current_family_data = {}
            
            if family_match and responsible_match:
                current_family_data = {
                    "Família": family_match.group(1),
                    "Responsável": responsible_match.group(1).strip()
                }

            tables = page.extract_tables()
            for table in tables:
                if table and "Descrição" in table[0]:
                    header = [item.replace("\n", " ") for item in table[0]]
                    df = pd.DataFrame(table[1:], columns=header)
                    if current_family_data:
                        df["Família"] = current_family_data.get("Família")
                        df["Responsável"] = current_family_data.get("Responsável")
                    all_events.append(df)
                    
        if all_events:
            all_events_df = pd.concat(all_events, ignore_index=True)
            # Limpeza e conversão de dados
            all_events_df.columns = all_events_df.columns.str.replace('.', '').str.strip()
            all_events_df['Valor Total'] = all_events_df['Valor Total'].str.replace('.', '').str.replace(',', '.').astype(float)
            all_events_df['INSS Base'] = all_events_df['INSS Base'].str.replace('.', '').str.replace(',', '.').astype(float)
            all_events_df['Qtd. VE'] = all_events_df['Qtd. VE'].str.replace(',', '.').astype(float)
            
    return header_data, faturas_df, resumo_faturamento_df, all_events_df

# Configuração do Streamlit
st.set_page_config(page_title="Conversor PDF para Excel", layout="wide")

st.title("Conversor de Demonstrativo de Faturamento da Unimed")
st.markdown("---")
st.markdown("Faça o upload do seu arquivo PDF para extrair todas as informações e convertê-las para um arquivo Excel com múltiplas abas.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        pdf_bytes = uploaded_file.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
        
        # Chama a função de extração
        header_info, df_faturas, df_resumo, df_eventos = extract_all_data_from_pdf(pdf_buffer)
        
        if df_faturas is not None or df_resumo is not None or df_eventos is not None:
            st.success("Arquivo processado com sucesso!")
            
            st.subheader("Informações do Cabeçalho")
            st.write(header_info)
            
            st.subheader("Tabela de Faturas")
            if df_faturas is not None:
                st.dataframe(df_faturas)
            
            st.subheader("Resumo do Faturamento")
            if df_resumo is not None:
                st.dataframe(df_resumo)
                
            st.subheader("Detalhes de Eventos (Primeiras 10 linhas)")
            if df_eventos is not None:
                st.dataframe(df_eventos.head(10))
            
            # Prepara o DataFrame para download em um arquivo Excel com várias abas
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Cria uma aba com informações do cabeçalho
                header_df = pd.DataFrame(header_info.items(), columns=['Campo', 'Valor'])
                header_df.to_excel(writer, index=False, sheet_name='Informações do Cabeçalho')

                # Escreve cada DataFrame em uma aba diferente
                if df_faturas is not None:
                    df_faturas.to_excel(writer, index=False, sheet_name='Faturas')
                if df_resumo is not None:
                    df_resumo.to_excel(writer, index=False, sheet_name='Resumo de Faturamento')
                if df_eventos is not None:
                    df_eventos.to_excel(writer, index=False, sheet_name='Detalhes de Eventos')
                    
            excel_buffer.seek(0)
            
            st.download_button(
                label="Baixar arquivo Excel com todas as abas",
                data=excel_buffer,
                file_name="demonstrativo_unimed_completo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Não foi possível extrair dados do arquivo PDF. Verifique se o formato corresponde ao esperado.")
