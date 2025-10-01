import streamlit as st
import pandas as pd
from io import BytesIO

# Configura a página
st.set_page_config(page_title="Conversor SEG 69 para Excel", page_icon="📊")
st.title("🔄 Conversor de Arquivo SEG 69 para Excel")

# Cria o uploader de arquivo
arquivo_seg69 = st.file_uploader(
    "Faça o upload do seu arquivo SEG 69",
    type=None,
    help="Carregue o arquivo no formato SEG 69 que deseja converter."
)

if arquivo_seg69 is not None:
    try:
        # Lê o conteúdo do arquivo como bytes
        bytes_data = arquivo_seg69.getvalue()
        
        st.info("Processando o arquivo SEG 69...")
        
        # Tenta decodificar os bytes para string e criar um DataFrame
        # Altere o encoding e o delimitador conforme a necessidade do seu arquivo
        stringio = BytesIO(bytes_data)
        df = pd.read_csv(stringio, delimiter=';', encoding='iso-8859-1')  # Ajuste crítico aqui
        
        # Armazena o DataFrame no session_state para acesso seguro em outros pontos do app
        st.session_state['df_processado'] = df
        
        # Exibe uma prévia dos dados
        st.subheader("Prévia dos Dados Convertidos")
        st.dataframe(df.head())
        
        # Prepara o arquivo Excel para download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Dados_SEG69', index=False)
        dados_excel = output.getvalue()
        
        # Cria o botão de download
        st.download_button(
            label="📥 Baixar Arquivo Convertido em Excel",
            data=dados_excel,
            file_name=f"dados_convertidos_{arquivo_seg69.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Conversão concluída com sucesso! Use o botão acima para baixar o arquivo.")
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.info("Dica: Verifique se o formato do arquivo é um SEG 69 válido e se a lógica de leitura (delimitador, encoding) está correta.")
else:
    st.info("👆 Aguardando o upload do arquivo SEG 69.")