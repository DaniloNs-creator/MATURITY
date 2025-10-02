import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

# --- Funções de Extração (Versão Robusta) ---

def extrair_dados_pdf(arquivo_pdf):
    """
    Função principal e robusta para extrair e processar os dados de todas as páginas do PDF.
    Lida com nomes em múltiplas linhas e formatos de tabela variados.
    """
    registros = []
    
    # Contexto que persiste entre as linhas e páginas
    contexto = {
        "familia": None,
        "responsavel": None,
        "matricula_funcional": None,
        "beneficiario_atual": None,
        "modulo_atual": "Não Identificado"
    }
    
    # Flag para ajudar a capturar nomes em duas linhas
    aguardando_nome_beneficiario = False

    with pdfplumber.open(arquivo_pdf) as pdf:
        full_text = "".join([page.extract_text(x_tolerance=2) or "" for page in pdf.pages])

    linhas = full_text.split('\n')
    
    for i, linha in enumerate(linhas):
        # Limpa espaços extras
        linha = linha.strip()
        if not linha:
            continue

        # 1. Identifica a Família
        match_familia = re.search(r"^\s*Familia:\s*(\d+)", linha)
        if match_familia:
            contexto["familia"] = match_familia.group(1)
            contexto["responsavel"] = None # Reseta para garantir a nova atribuição
            continue

        # 2. Identifica o Responsável e a Matrícula
        match_responsavel = re.search(r"^\s*Responsável:\s*(.*?)(?:\s*Matrícula Funcional:\s*(.*))?$", linha)
        if match_responsavel:
            contexto["responsavel"] = match_responsavel.group(1).strip()
            contexto["matricula_funcional"] = match_responsavel.group(2).strip() if match_responsavel.group(2) else "N/A"
            continue

        # 3. Lógica para capturar o nome do Beneficiário (lida com 1 ou 2 linhas)
        if aguardando_nome_beneficiario:
            match_nome = re.search(r"^\s*Nome:\s*(.*)", linha)
            if match_nome:
                contexto["beneficiario_atual"] = match_nome.group(1).strip()
            aguardando_nome_beneficiario = False # Reseta a flag independentemente do resultado

        match_beneficiario = re.search(r"^\s*BENEFICIARIO:\s*(\S+)", linha)
        if match_beneficiario:
            # Caso 1: Nome na mesma linha
            match_nome_na_linha = re.search(r"Nome:\s*(.*)", linha)
            if match_nome_na_linha:
                contexto["beneficiario_atual"] = match_nome_na_linha.group(1).strip()
                aguardando_nome_beneficiario = False
            else:
                # Caso 2: Nome na próxima linha
                aguardando_nome_beneficiario = True
            continue

        # 4. Identifica o Módulo do plano
        if "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%" in linha:
            contexto["modulo_atual"] = "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%"
            continue
        
        # 5. Lógica para identificar e extrair uma linha de evento
        # Um evento tem uma data (dd/mm/yyyy) e valores monetários.
        # Também não deve ser uma linha de cabeçalho ou totalização.
        if (re.search(r'\d{2}/\d{2}/\d{4}', linha) and 
            not linha.startswith("Total Eventos:") and
            not linha.startswith("Emissão") and
            contexto["beneficiario_atual"]):

            # Regex simplificada e mais flexível para capturar as partes principais
            # Padrão: (Qualquer coisa no início) (Data) (Qualquer coisa no meio) (Valor Final)
            match_evento = re.search(r"^(.*?)\s+(\d{2}/\d{2}/\d{4})\s+.*\s+([\d.,]+)\s*$", linha)
            
            if match_evento:
                descricao_completa = match_evento.group(1).strip()
                data = match_evento.group(2).strip()
                valor = match_evento.group(3).strip()
                
                # Tenta extrair o Executor de forma mais inteligente
                # Geralmente é um nome próprio em maiúsculas no final da descrição
                executor = "N/A"
                # Remove códigos e palavras-chave para isolar a descrição e o executor
                descricao_limpa = re.sub(r'\d{1,2}\.\d{3}\.\d{5}\s+\w{3}\s+\d{7,}\s+', '', descricao_completa)
                
                # Procura por sequências de palavras em maiúsculas que pareçam um nome
                possiveis_executores = re.findall(r'([A-Z\s]{5,}[A-Z])', descricao_limpa)
                if possiveis_executores:
                    executor = possiveis_executores[-1].strip()
                    descricao = descricao_limpa.replace(executor, "").strip()
                else:
                    descricao = descricao_limpa

                registro_completo = {
                    "Familia": contexto["familia"],
                    "Responsavel": contexto["responsavel"],
                    "Matricula_Funcional": contexto["matricula_funcional"],
                    "Beneficiario_Utilizacao": contexto["beneficiario_atual"],
                    "Modulo_Plano": contexto["modulo_atual"],
                    "Descricao_Evento": descricao,
                    "Executor": executor,
                    "Data_Evento": data,
                    "Valor_Coparticipacao": valor
                }
                registros.append(registro_completo)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)
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
Esta aplicação foi **corrigida e aprimorada** para ler o layout do arquivo de faturamento que você forneceu. 
Ela agora consegue lidar com nomes de beneficiários em linhas separadas e com a formatação variada da tabela de eventos.

**Instruções:**
1.  Faça o upload do seu arquivo PDF.
2.  Aguarde o processamento.
3.  Visualize os dados extraídos e baixe o relatório completo em Excel.
""")

uploaded_file = st.file_uploader(
    "Escolha o seu arquivo PDF de faturamento", 
    type="pdf"
)

if uploaded_file is not None:
    with st.spinner('Analisando o PDF e extraindo os dados... Este processo pode levar alguns segundos.'):
        try:
            df_extraido = extrair_dados_pdf(uploaded_file)
            
            if not df_extraido.empty:
                st.success(f"🎉 Processamento concluído! Foram encontrados {len(df_extraido)} registros de eventos.")
                st.dataframe(df_extraido)
                
                excel_file = to_excel(df_extraido)
                
                st.download_button(
                    label="📥 Baixar Relatório em Excel",
                    data=excel_file,
                    file_name=f"faturamento_unimed_processado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhum registro de evento foi encontrado no formato esperado. O PDF pode estar vazio ou ter um layout completamente diferente.")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
            st.error("Se o erro persistir, o layout do PDF pode ter mudado significativamente.")
