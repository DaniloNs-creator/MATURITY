import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_and_process_pdf(pdf_file):
    """
    Extrai dados de um PDF da Unimed e os organiza em um único DataFrame.
    """
    all_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()
        
        # Extração de informações do cabeçalho
        competence_match = re.search(r"Competência: (.+)", first_page_text)
        competencia = competence_match.group(1).strip() if competence_match else ""
        
        cnpj_match = re.search(r"CNPJ: (.+)", first_page_text)
        cnpj = cnpj_match.group(1).strip() if cnpj_match else ""
        
        # Extração da tabela de faturas
        faturas_table = next((t for t in first_page.extract_tables() if any("Fatura" in cell for cell in t[0])), None)
        if faturas_table:
            faturas_headers = [h.replace("\n", " ") for h in faturas_table[0]]
            faturas_df = pd.DataFrame(faturas_table[1:], columns=faturas_headers)
            fatura = faturas_df.iloc[0]["Fatura\n"]
            valor_bruto_fatura = faturas_df.iloc[0]["Valor Bruto\n"]
        else:
            fatura, valor_bruto_fatura = "", ""
            
        # Extração do resumo de faturamento
        resumo_match = re.search(r"RESUMO DO FATURAMENTO\n\n(.+?)(?=\nFamília:|\nTotal de Faturas:)", first_page_text, re.DOTALL)
        resumo_data = {}
        if resumo_match:
            resumo_lines = resumo_match.group(1).strip().split('\n')
            for line in resumo_lines:
                parts = line.rsplit(None, 1)
                if len(parts) == 2:
                    resumo_data[parts[0]] = parts[1]
        
        # Extração dos dados detalhados de eventos
        current_family_data = {}
        for page in pdf.pages:
            text = page.extract_text()
            family_match = re.search(r"Família: (\d+)", text)
            responsible_match = re.search(r"Responsável: (.+)", text)
            
            if family_match and responsible_match:
                current_family_data = {
                    "Família": family_match.group(1),
                    "Responsável": responsible_match.group(1).strip()
                }

            for table in page.extract_tables():
                if table and "Descrição" in table[0]:
                    headers = [h.replace("\n", " ").replace(".", "").strip() for h in table[0]]
                    df = pd.DataFrame(table[1:], columns=headers)
                    if current_family_data:
                        for idx, row in df.iterrows():
                            record = {
                                "Competencia": competencia,
                                "CNPJ": cnpj,
                                "Fatura": fatura,
                                "Valor Bruto Fatura": valor_bruto_fatura,
                                **resumo_data,
                                "Família": current_family_data.get("Família"),
                                "Responsavel": current_family_data.get("Responsavel"),
                                "Matricula Funcional": row.get("Matrícula Funcional"),
                                "Descricao": row.get("Descrição"),
                                "Evento": row.get("Evento"),
                                "Grau": row.get("Grau"),
                                "Guia": row.get("Guia"),
                                "Executor": row.get("Executor"),
                                "Data": row.get("Data"),
                                "Qtd": row.get("Qtd VE"),
                                "Valor Total": row.get("Valor Total"),
                                "INSS Base": row.get("INSS Base"),
                            }
                            all_data.append(record)
                            
    if all_data:
        return pd.DataFrame(all_data)
    return None

# Configuração do Streamlit
st.set_page_config(page_title="Conversor PDF para Excel", layout="wide")
st.title("Conversor de Demonstrativo de Faturamento Unimed")
st.markdown("---")
st.markdown("Faça o upload do seu arquivo PDF para extrair e converter a tabela de eventos para um arquivo Excel com todos os campos mapeados.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        pdf_bytes = uploaded_file.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
        
        df_completo = extract_and_process_pdf(pdf_buffer)
        
        if df_completo is not None and not df_completo.empty:
            st.success("Arquivo processado com sucesso!")
            st.dataframe(df_completo)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_completo.to_excel(writer, index=False, sheet_name='Demonstrativo Completo')
            excel_buffer.seek(0)
            
            st.download_button(
                label="Baixar arquivo Excel Completo",
                data=excel_buffer,
                file_name="demonstrativo_unimed_completo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Não foi possível extrair dados do arquivo PDF. Por favor, verifique se o formato corresponde ao esperado.")
