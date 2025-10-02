import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

# --- Funções de Extração ---

def extrair_dados_pdf(arquivo_pdf):
    """
    Função principal para extrair e processar os dados de todas as páginas do PDF.
    """
    registros = []
    
    # Contexto que persiste entre as linhas e páginas
    contexto = {
        "familia": None,
        "responsavel": None,
        "beneficiario_atual": None,
        "modulo_atual": None
    }

    with pdfplumber.open(arquivo_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            
            if not texto:
                continue

            linhas = texto.split('\n')
            
            for linha in linhas:
                # 1. Tenta identificar a Família
                match_familia = re.search(r"Família:\s*(\S+)", linha)
                if match_familia:
                    contexto["familia"] = match_familia.group(1).strip()
                    continue

                # 2. Tenta identificar o Responsável
                match_responsavel = re.search(r"Responsável:\s*(.*)", linha)
                if match_responsavel:
                    contexto["responsavel"] = match_responsavel.group(1).strip()
                    continue

                # 3. Tenta identificar um novo Beneficiário (Titular ou Dependente)
                match_beneficiario = re.search(r"BENEFICIÁRIO:\s*\d+\s*Nome:\s*(.*)", linha)
                if match_beneficiario:
                    contexto["beneficiario_atual"] = match_beneficiario.group(1).strip()
                    # Reseta o módulo ao encontrar um novo beneficiário
                    contexto["modulo_atual"] = None
                    continue

                # 4. Tenta identificar o Módulo (Plano com coparticipação)
                # Assumimos que o módulo vem logo após a linha do beneficiário
                if contexto["beneficiario_atual"] and not contexto["modulo_atual"]:
                    # Ex: PL NAC AMB HOSP ENF OBST COPARTICIPACAO 25%
                    # A lógica aqui é pegar uma linha que parece ser um plano
                    if "COPARTICIPACAO" in linha or "PL NAC" in linha:
                         contexto["modulo_atual"] = linha.strip()
                         continue
                
                # 5. Tenta identificar a linha de um evento/procedimento
                # Ex: CONSULTA EM CLINICA P/S DO AD 11.04.2012 O+ 85764022 MONIELE CAROLINA MEIRA DO ROSARIO ...
                # Esta regex é um pouco mais complexa para capturar os dados da tabela
                # (Descrição) (Data) (Tipo Sanguineo?) (Código) (Prestador) ... (Valor)
                match_evento = re.search(
                    r"^(?P<evento>.+?)\s+"  # Descrição do evento
                    r"(?P<data>\d{2}\.\d{2}\.\d{4})\s+"  # Data no formato DD.MM.YYYY
                    r"(?P<tipo_sangue>\S+)\s+"  # Tipo sanguíneo ou similar
                    r"(?P<codigo>\d+)\s+"  # Código
                    r"(?P<prestador>.+?)\s+"  # Nome do prestador
                    r"(\S+\s+){5}" # Pula 5 colunas que não precisamos capturar individualmente
                    r"(?P<valor_total>\d+,\d{2})$", # Valor no formato XX,XX no final da linha
                    linha
                )

                if match_evento and contexto["beneficiario_atual"]:
                    dados_evento = match_evento.groupdict()
                    
                    # Monta o registro completo
                    registro_completo = {
                        "Família": contexto["familia"],
                        "Responsável": contexto["responsavel"],
                        "Beneficiário (Dependente)": contexto["beneficiario_atual"],
                        "Módulo (Plano)": contexto["modulo_atual"],
                        "Evento": dados_evento.get("evento", "").strip(),
                        "Data Início": dados_evento.get("data", "").strip(),
                        "Prestador": dados_evento.get("prestador", "").strip(),
                        "Valor Total": dados_evento.get("valor_total", "").strip()
                    }
                    registros.append(registro_completo)

    return pd.DataFrame(registros)


def to_excel(df):
    """
    Converte um DataFrame para um arquivo Excel em memória.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato')
    processed_data = output.getvalue()
    return processed_data

# --- Interface do Streamlit ---

st.set_page_config(page_title="Conversor de Extrato para Excel", layout="wide")

st.title("📄 Conversor de Extrato PDF para Excel")
st.markdown("""
Esta aplicação extrai os dados de extratos de utilização (como o da imagem de exemplo) de um arquivo PDF.
Faça o upload do seu arquivo para processar as informações de:

- **Família e Responsável (Titular)**
- **Beneficiários (Dependentes)**
- **Módulo do Plano (com informação de coparticipação)**
- **Eventos (consultas, exames, etc.)**

O resultado será uma tabela organizada que você poderá baixar como um arquivo Excel.
""")

uploaded_file = st.file_uploader(
    "Escolha o seu arquivo PDF de extrato (69 PG ou similar)", 
    type="pdf"
)

if uploaded_file is not None:
    with st.spinner('Processando o PDF... Isso pode levar alguns segundos.'):
        try:
            df_extraido = extrair_dados_pdf(uploaded_file)
            
            if not df_extraido.empty:
                st.success("🎉 Arquivo processado com sucesso!")
                st.dataframe(df_extraido)
                
                # Geração do arquivo Excel para download
                excel_file = to_excel(df_extraido)
                
                st.download_button(
                    label="📥 Baixar Dados em Excel",
                    data=excel_file,
                    file_name=f"extrato_processado_{uploaded_file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Não foram encontrados dados no formato esperado no arquivo PDF. Verifique se o arquivo está correto.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.error("O layout do PDF pode ser diferente do esperado. O código foi baseado na imagem de exemplo fornecida.")

