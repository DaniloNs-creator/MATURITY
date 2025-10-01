import streamlit as st
import pandas as pd
import tabula
from io import BytesIO

# Configura a página
st.set_page_config(page_title="PDF para Excel", layout="wide")
st.title("📄 Conversor de PDF para Excel")

# Widget para upload de arquivo
uploaded_file = st.file_uploader("Faça o upload do seu PDF", type="pdf")

if uploaded_file is not None:
    # Lê o PDF usando tabula. O resultado é uma lista de DataFrames.
    try:
        # Usa BytesIO para passar o arquivo em memória para o tabula
        pdf_bytes = uploaded_file.read()
        dfs = tabula.read_pdf(BytesIO(pdf_bytes), pages='all', multiple_tables=True)
        
        # Verifica se tabelas foram encontradas
        if not dfs:
            st.warning("Nenhuma tabela foi encontrada neste PDF.")
        else:
            st.success(f"Foram encontradas {len(dfs)} tabela(s) no PDF.")
            
            # Exibe uma prévia de cada tabela encontrada
            for i, df in enumerate(dfs):
                st.subheader(f"Prévia da Tabela {i+1}")
                st.dataframe(df)
                
                # Adiciona uma linha em branco entre as tabelas
                st.write("---")
            
            # Combina todas as tabelas em um único DataFrame
            # (Se você preferir cada tabela em uma planilha diferente, comente a linha abaixo)
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Prepara o arquivo Excel para download
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                combined_df.to_excel(writer, sheet_name="Tabelas_Consolidadas", index=False)
            
            # Configura o botão de download
            st.download_button(
                label="📥 Baixar Arquivo Excel",
                data=output.getvalue(),
                file_name="tabelas_convertidas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Ocorreu um erro durante a conversão: {e}")
else:
    st.info("👆 Por favor, faça o upload de um arquivo PDF para começar.")