import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_and_process_pdf(pdf_file):
    """
    Função para extrair e processar dados de um PDF da Unimed,
    organizando-os em um DataFrame do pandas.
    """
    all_events = []
    current_family_data = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            # Use regex para encontrar informações de família
            family_match = re.search(r"Família: (\d+)", text)
            responsible_match = re.search(r"Responsável: (.+)", text)
            total_family_match = re.search(r"Total Familia: ([\d.,]+)", text)

            if family_match and responsible_match:
                current_family_data = {
                    "Família": family_match.group(1),
                    "Responsável": responsible_match.group(1).strip()
                }
            
            # Encontre a tabela de eventos na página
            tables = page.extract_tables()
            
            for table in tables:
                if table and "Descrição" in table[0]:
                    # Processa a tabela de eventos
                    header = [item.replace("\n", " ") for item in table[0]]
                    df = pd.DataFrame(table[1:], columns=header)
                    
                    # Adiciona as informações da família a cada linha de evento
                    if current_family_data:
                        df["Família"] = current_family_data.get("Família")
                        df["Responsável"] = current_family_data.get("Responsável")
                    
                    all_events.append(df)
                    
    if all_events:
        # Concatena todos os DataFrames de eventos em um único DataFrame
        final_df = pd.concat(all_events, ignore_index=True)
        # Reorganiza as colunas
        cols = ["Família", "Responsável", "Descrição", "Evento", "Grau", "Guia", "Executor", "Data", "Qtd.", "VE", "UI", "TX", "Valor Total", "INSS Base"]
        final_df = final_df.reindex(columns=cols)
        
        # Converte a coluna de valores para numérico
        final_df['Valor Total'] = final_df['Valor Total'].str.replace('.', '').str.replace(',', '.').astype(float)
        final_df['INSS Base'] = final_df['INSS Base'].str.replace('.', '').str.replace(',', '.').astype(float)
        
        return final_df
    else:
        return None

# Configuração do Streamlit
st.set_page_config(page_title="Conversor PDF para Excel", layout="wide")

st.title("Conversor de Demonstrativo de Faturamento da Unimed")
st.markdown("---")
st.markdown("Faça o upload do seu arquivo PDF para extrair e converter a tabela de eventos para um arquivo Excel.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        # Lê o PDF como um objeto de arquivo
        pdf_bytes = uploaded_file.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
        
        # Chama a função de extração
        df_events = extract_and_process_pdf(pdf_buffer)
        
        if df_events is not None:
            st.success("Arquivo processado com sucesso!")
            st.dataframe(df_events)
            
            # Prepara o DataFrame para download
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_events.to_excel(writer, index=False, sheet_name='Eventos')
            excel_buffer.seek(0)
            
            st.download_button(
                label="Baixar arquivo Excel",
                data=excel_buffer,
                file_name="demonstrativo_unimed_eventos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Não foi possível encontrar a tabela de 'Eventos' no arquivo PDF. Verifique se o formato corresponde ao esperado.")

