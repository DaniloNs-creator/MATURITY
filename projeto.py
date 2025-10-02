import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_all_data(pdf_file):
    """
    Extrai todos os dados do PDF de forma robusta, usando regex para
    contornar a falta de tabelas detectáveis.
    """
    all_records = []

    with pdfplumber.open(pdf_file) as pdf:
        full_text = "".join([page.extract_text() for page in pdf.pages])

        # Extrai os dados do cabeçalho uma única vez
        competencia = re.search(r"Competência: (\S+)", full_text).group(1)
        cnpj = re.search(r"CNPJ: (\S+)", full_text).group(1)
        fatura = re.search(r"Fatura\n+(\d+)\n", full_text).group(1)
        valor_bruto_fatura = re.search(r"Total de Faturas:\n(.+?)\n", full_text).group(1)

        # Extrai o resumo do faturamento
        resumo_dict = {}
        resumo_match = re.search(r"RESUMO DO FATURAMENTO\n\n(.+?)(?=\nFamília:|\nTotal de Faturas:)", full_text, re.DOTALL)
        if resumo_match:
            resumo_lines = resumo_match.group(1).strip().split('\n')
            for line in resumo_lines:
                key, value = line.rsplit(None, 1)
                resumo_dict[key.strip()] = value.strip()

        # Divide o texto em blocos de família para processamento individual
        family_blocks = re.split(r"Família: (\d+)\nResponsável: (.+?)\n", full_text, flags=re.DOTALL)[1:]
        
        # Processa cada bloco de família
        for i in range(0, len(family_blocks), 3):
            family_code = family_blocks[i]
            responsible_name = family_blocks[i+1].strip()
            block_content = family_blocks[i+2]
            
            # Encontra as informações de matrícula e beneficiário
            beneficiary_info = re.findall(r"Nome: (.+?)\n.+?Matrícula Funcional: (.+?)\n", block_content, re.DOTALL)
            
            # Extrai a tabela de eventos dentro do bloco
            events_table_match = re.search(r"Descrição\n(.+?)(?=\nTotal Família:|\Z)", block_content, re.DOTALL)
            if events_table_match:
                events_text = events_table_match.group(1).strip()
                event_lines = events_text.split('\n')
                
                # Regex para extrair cada linha de evento
                event_pattern = re.compile(r"(.+?)\s+(\d\.\d+\.\d+)\s+([A-Z]+)\s+(\S+)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d,.]+)\s+([A-Z])\s+([\d,.]+)\s+([\d,.]+)")
                
                for line in event_lines:
                    match = event_pattern.search(line.strip())
                    if match:
                        # Extrai o nome do beneficiário e matrícula mais próximos
                        current_beneficiary_name = ""
                        current_matricula = ""
                        if beneficiary_info:
                            current_beneficiary_name = beneficiary_info[0][0]
                            current_matricula = beneficiary_info[0][1]

                        record = {
                            "Fatura": fatura,
                            "Competencia": competencia,
                            "CNPJ": cnpj,
                            "Valor Bruto Fatura": valor_bruto_fatura,
                            **resumo_dict,
                            "Familia": family_code,
                            "Responsavel": responsible_name,
                            "Matricula Funcional": current_matricula,
                            "Nome Beneficiario": current_beneficiary_name,
                            "Descricao": match.group(1).strip(),
                            "Evento": match.group(2),
                            "Grau": match.group(3),
                            "Guia": match.group(4),
                            "Executor": match.group(5).strip(),
                            "Data": match.group(6),
                            "Qtd": match.group(7).replace(",", "."),
                            "Valor Total Evento": match.group(9).replace(",", "."),
                            "INSS Base": match.group(10).replace(",", "."),
                        }
                        all_records.append(record)

    return pd.DataFrame(all_records)

# --- Streamlit App ---
st.set_page_config(page_title="Conversor de Faturamento Unimed", layout="wide")
st.title("Conversor de Demonstrativo de Faturamento Unimed")
st.markdown("---")
st.markdown("Faça o upload do seu arquivo PDF para extrair todos os dados em um formato de tabela única e limpa.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processando o arquivo..."):
        pdf_bytes = uploaded_file.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
        
        try:
            df_completo = extract_all_data(pdf_buffer)
            
            if not df_completo.empty:
                st.success("Arquivo processado com sucesso!")
                st.dataframe(df_completo)
                
                # Prepara o DataFrame para download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_completo.to_excel(writer, index=False, sheet_name='Demonstrativo Completo')
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Baixar arquivo Excel",
                    data=excel_buffer,
                    file_name="demonstrativo_unimed_completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Não foi possível extrair dados do arquivo PDF. Verifique se o formato corresponde ao esperado.")
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processamento: {e}")
            st.warning("O formato do PDF pode ser diferente do esperado. Por favor, tente um arquivo com a mesma estrutura.")

