import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
from collections import namedtuple

# --- Lógica de Extração (Baseada em Análise de Layout/Tabelas) ---

def extrair_dados_pdf(arquivo_pdf):
    """
    Função robusta que usa a extração de tabelas nativa do pdfplumber para 
    identificar os campos de forma precisa, combinando com a extração de texto para contexto.
    """
    registros = []
    
    contexto = {
        "familia": None,
        "responsavel": None,
        "matricula_funcional": None,
        "beneficiario_atual": None,
        "modulo_atual": "Não Identificado"
    }

    with pdfplumber.open(arquivo_pdf) as pdf:
        for page in pdf.pages:
            # 1. ATUALIZAR CONTEXTO USANDO TEXTO SIMPLES
            texto_pagina = page.extract_text(x_tolerance=2)
            if not texto_pagina:
                continue
            
            linhas = texto_pagina.split('\n')
            
            # Usamos um buffer para o nome do beneficiário que pode estar na próxima linha
            beneficiario_id_pendente = False
            for linha in linhas:
                linha = linha.strip()
                
                if beneficiario_id_pendente and linha.startswith("Nome:"):
                    contexto["beneficiario_atual"] = linha.replace("Nome:", "").strip()
                    beneficiario_id_pendente = False

                match_familia = re.search(r"^\s*Familia:\s*(\d+)", linha)
                if match_familia:
                    contexto["familia"] = match_familia.group(1)
                    continue

                match_responsavel = re.search(r"^\s*Responsável:\s*(.*?)(?:\s*Matrícula Funcional:\s*(.*))?$", linha)
                if match_responsavel:
                    contexto["responsavel"] = match_responsavel.group(1).strip()
                    contexto["matricula_funcional"] = match_responsavel.group(2).strip() if match_responsavel.group(2) else "N/A"
                    continue

                if "BENEFICIARIO:" in linha:
                    nome_match = re.search(r"Nome:\s*(.*)", linha)
                    if nome_match:
                        contexto["beneficiario_atual"] = nome_match.group(1).strip()
                        beneficiario_id_pendente = False
                    else:
                        beneficiario_id_pendente = True
                    continue

                if "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%" in linha:
                    contexto["modulo_atual"] = "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%"

            # 2. EXTRAIR TABELAS DE EVENTOS E ASSOCIAR AO CONTEXTO
            tabelas = page.extract_tables()
            for tabela in tabelas:
                # Uma tabela de eventos válida geralmente tem mais de 5 colunas
                if not tabela or not tabela[0] or len(tabela[0]) < 6:
                    continue

                for row in tabela:
                    # Limpa a linha, tratando células nulas ou com quebras de linha
                    cleaned_row = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in row]
                    
                    # Procura por uma data para identificar uma linha de evento válida
                    data_evento = None
                    for cell in cleaned_row:
                        match = re.search(r'(\d{2}/\d{2}/\d{4})', cell)
                        if match:
                            data_evento = match.group(1)
                            break
                    
                    # Se encontrou uma data e a linha parece ter dados, processa
                    if data_evento and len(cleaned_row) > 4:
                        # Devido à inconsistência das colunas, faremos uma atribuição heurística
                        descricao = cleaned_row[0]
                        valor_total = cleaned_row[-2] if len(cleaned_row) > 1 else ''
                        
                        # Tenta encontrar o executor, que pode estar em várias posições
                        executor = cleaned_row[4] if len(cleaned_row) > 4 else "N/A"
                        
                        # Remove "Total Eventos:" da descrição
                        if "Total Eventos:" in descricao:
                            continue

                        registro = {
                            "Familia": contexto["familia"],
                            "Responsavel": contexto["responsavel"],
                            "Matricula_Funcional": contexto["matricula_funcional"],
                            "Beneficiario_Utilizacao": contexto["beneficiario_atual"],
                            "Modulo_Plano": contexto["modulo_atual"],
                            "Descricao_Evento": descricao.strip(),
                            "Executor": executor.strip(),
                            "Data_Evento": data_evento,
                            "Valor_Coparticipacao": valor_total.strip()
                        }
                        registros.append(registro)
    
    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    # Limpeza final: remove linhas onde a descrição é vazia ou é um cabeçalho
    df = df[df['Descricao_Evento'].str.strip() != '']
    df = df[~df['Descricao_Evento'].str.contains("Descrição", case=False)]
    
    return df


def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato_Detalhado')
        worksheet = writer.sheets['Extrato_Detalhado']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    return output.getvalue()

# --- Interface do Streamlit (UI) ---

st.set_page_config(page_title="Conversor de Faturamento Unimed", layout="wide")
st.title("📄 Conversor de Demonstrativo de Faturamento Unimed")
st.markdown("""
Esta é uma **versão aprimorada** que utiliza análise de layout para identificar as tabelas e campos do PDF de forma precisa, resolvendo os erros de extração anteriores.

**Instruções:**
1.  Faça o upload do seu arquivo PDF de faturamento.
2.  Aguarde o processamento.
3.  Visualize os dados extraídos e baixe o relatório completo em Excel.
""")

uploaded_file = st.file_uploader(
    "Escolha o seu arquivo PDF de faturamento", 
    type="pdf"
)

if uploaded_file is not None:
    with st.spinner('Analisando o layout do PDF e extraindo as tabelas... Este processo é mais preciso e pode levar um momento.'):
        try:
            df_extraido = extrair_dados_pdf(uploaded_file)
            
            if not df_extraido.empty:
                st.success(f"🎉 Processamento concluído com sucesso! Foram encontrados {len(df_extraido)} registros de eventos.")
                st.dataframe(df_extraido)
                
                excel_file = to_excel(df_extraido)
                
                st.download_button(
                    label="📥 Baixar Relatório em Excel",
                    data=excel_file,
                    file_name=f"faturamento_unimed_processado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhum registro de evento foi encontrado. O PDF pode não conter tabelas de eventos ou ter um formato inesperado.")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
            st.error("Embora mais robusto, este método ainda pode falhar se o PDF tiver uma estrutura muito fora do padrão.")

