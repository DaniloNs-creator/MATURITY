import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Extrai dados de um arquivo PDF da Unimed e retorna um DataFrame do pandas.
    """
    all_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        text_content = ""
        for page in pdf.pages:
            text_content += page.extract_text()
    
    # Divide o texto em blocos de família usando "Família: " como delimitador
    family_blocks = re.split(r'Família: (\d+)', text_content)
    
    # O primeiro item é o cabeçalho do documento, não é um bloco de família
    for i in range(1, len(family_blocks), 2):
        family_id = family_blocks[i].strip()
        block_text = family_blocks[i+1]
        
        # Encontra o nome do responsável
        responsible_match = re.search(r'Responsável: (.+)', block_text)
        responsible_name = responsible_match.group(1).strip() if responsible_match else 'Não encontrado'

        # Pega a Coparticipação do módulo. O documento mostra "COPARTICIPACAO 25%"
        coparticipation = "25%" 

        # Encontra todos os nomes de beneficiários e dependentes no bloco
        beneficiary_names = re.findall(r'Nome: (.+)', block_text)

        # A primeira pessoa na lista é o responsável
        beneficiary_names = [name for name in beneficiary_names if name.strip() != responsible_name.strip()]
        
        # Cria uma linha para o responsável
        all_data.append({
            'Família': family_id,
            'Tipo de Beneficiário': 'Responsável',
            'Nome': responsible_name,
            'Coparticipação': coparticipation
        })

        # Adiciona os dependentes (se houver)
        for name in beneficiary_names:
            all_data.append({
                'Família': family_id,
                'Tipo de Beneficiário': 'Dependente',
                'Nome': name.strip(),
                'Coparticipação': coparticipation
            })
            
    df = pd.DataFrame(all_data)
    return df

st.set_page_config(page_title="Conversor PDF Unimed para Excel")

st.title("Conversor de Demonstração Unimed")
st.markdown("Faça o upload do demonstrativo de faturamento PDF para extrair e converter dados em uma planilha Excel.")

# Widget de upload de arquivo
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.success("Arquivo enviado com sucesso!")

    # Extrair e processar os dados
    df_result = extract_data_from_pdf(uploaded_file)
    
    # Exibir a tabela com os dados extraídos
    st.subheader("Dados Extraídos")
    st.dataframe(df_result)

    # Botão de download do arquivo Excel
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

