import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Extrai dados de um arquivo PDF da Unimed, identificando Família, Responsável,
    Dependentes e Coparticipação.
    """
    all_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()
    
    # Usa um regex para encontrar blocos de texto que começam com "Família: "
    family_blocks = re.split(r'(Família: \d+)', full_text)
    
    # O primeiro item do split é geralmente um cabeçalho, então o ignoramos.
    family_blocks = family_blocks[1:]
    
    for i in range(0, len(family_blocks), 2):
        family_header = family_blocks[i]
        family_content = family_blocks[i+1]
        
        family_id_match = re.search(r'Família: (\d+)', family_header)
        family_id = family_id_match.group(1).strip() if family_id_match else None
        
        # Encontra o nome do responsável
        responsible_match = re.search(r'Responsável: (.+)', family_content)
        responsible_name = responsible_match.group(1).strip() if responsible_match else None
        
        # Encontra todos os nomes de beneficiários e dependentes. 
        # Usa um lookbehind negativo para não capturar "Responsável:"
        beneficiary_names = re.findall(r'(?<!Responsável: )Nome: (.+)', family_content)
        
        # Adiciona o responsável aos dados
        if responsible_name:
            all_data.append({
                'Família': family_id,
                'Tipo de Beneficiário': 'Responsável',
                'Nome': responsible_name,
                # A coparticipação de 25% é um padrão no documento
                'Coparticipação': '25%' 
            })
        
        # Adiciona os dependentes aos dados
        for name in beneficiary_names:
            all_data.append({
                'Família': family_id,
                'Tipo de Beneficiário': 'Dependente',
                'Nome': name.strip(),
                'Coparticipação': '25%'
            })
            
    df = pd.DataFrame(all_data)
    return df

st.set_page_config(page_title="Conversor PDF Unimed para Excel")

st.title("Conversor de Demonstração Unimed")
st.markdown("Faça o upload do demonstrativo de faturamento PDF para extrair e converter dados em uma planilha Excel.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.success("Arquivo enviado com sucesso!")

    try:
        df_result = extract_data_from_pdf(uploaded_file)
        
        if not df_result.empty:
            st.subheader("Dados Extraídos")
            st.dataframe(df_result)

            st.markdown("---")
            excel_file = io.BytesIO()
            df_result.to_excel(excel_file, index=False, engine="openpyxl")
            excel_file.seek(0)
            
            st.download_button(
                label="Baixar Planilha Excel",
                data=excel_file,
                file_name="demonstrativo_unimed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Não foi possível extrair os dados. Verifique a formatação do arquivo.")
            st.info("O script busca por 'Família: [número]', 'Responsável: [Nome]' e 'Nome: [Nome]'. Certifique-se de que esses padrões estejam presentes no arquivo.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.info("Verifique se o arquivo está no formato esperado e tente novamente.")

