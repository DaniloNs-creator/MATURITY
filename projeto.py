import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

# --- Funções de Extração (Ajustadas para o novo PDF) ---

def parse_linha_evento(linha):
    """
    Tenta extrair informações de uma linha de evento.
    Esta função é complexa devido à variação no espaçamento e colunas.
    """
    # Padrão de data é um bom ponto de referência
    match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
    if not match_data:
        return None

    data_evento = match_data.group(1)
    partes = linha.split(data_evento)
    
    parte_esquerda = partes[0].strip()
    parte_direita = partes[1].strip()

    # Na parte direita, os valores numéricos estão no final
    valores = re.findall(r'[\d.,]+', parte_direita)
    valor_total = "0,00"
    if valores:
        # O último valor numérico geralmente é o Valor Total da coparticipação
        valor_total = valores[-1]

    # Na parte esquerda, temos a descrição e o executor
    # O executor geralmente é um nome em maiúsculas precedido por um código de guia (número longo)
    match_guia_executor = re.search(r'\d{7,}\s+(.*)', parte_esquerda)
    if match_guia_executor:
        executor = match_guia_executor.group(1).strip()
        descricao = parte_esquerda.split(match_guia_executor.group(0))[0].strip()
    else:
        # Se não encontrar um guia claro, a lógica fica mais simples
        executor = "N/A"
        descricao = parte_esquerda
        # Tenta pegar o último conjunto de palavras em maiúsculas como o executor
        palavras_maiusculas = re.findall(r'([A-Z][A-Z\s]+[A-Z])', parte_esquerda)
        if palavras_maiusculas:
            executor = palavras_maiusculas[-1].strip()
            # Remove o nome do executor da descrição para limpá-la
            descricao = descricao.replace(executor, '').strip()


    return {
        "Descricao": descricao,
        "Executor": executor,
        "Data": data_evento,
        "Valor_Total_Coparticipacao": valor_total
    }


def extrair_dados_pdf(arquivo_pdf):
    """
    Função principal para extrair e processar os dados de todas as páginas do PDF.
    """
    registros = []
    
    contexto = {
        "familia": None,
        "responsavel": None,
        "matricula_funcional": None,
        "beneficiario_atual": None,
        "modulo_atual": "Não Identificado" # Valor padrão
    }

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text(x_tolerance=2, y_tolerance=2)
            if not texto:
                continue

            linhas = texto.split('\n')
            
            for linha in linhas:
                # 1. Identifica a Família
                match_familia = re.search(r"^\s*Familia:\s*(\d+)", linha)
                if match_familia:
                    contexto["familia"] = match_familia.group(1)
                    # Reseta o responsável ao encontrar uma nova família
                    contexto["responsavel"] = None
                    contexto["matricula_funcional"] = None
                    continue

                # 2. Identifica o Responsável e a Matrícula
                match_responsavel = re.search(r"^\s*Responsável:\s*(.*?)(?:\s*Matricula Funcional:\s*(.*))?$", linha)
                if match_responsavel:
                    contexto["responsavel"] = match_responsavel.group(1).strip()
                    contexto["matricula_funcional"] = match_responsavel.group(2).strip() if match_responsavel.group(2) else "N/A"
                    continue

                # 3. Identifica um novo Beneficiário (pode ser o titular ou dependente)
                match_beneficiario = re.search(r"^\s*BENEFICIARIO:\s*\S+\s*Nome:\s*(.*)", linha)
                if match_beneficiario:
                    contexto["beneficiario_atual"] = match_beneficiario.group(1).strip()
                    continue
                # Às vezes o nome do beneficiário aparece em outra linha
                if "BENEFICIÁRIO:" in linha and "Nome:" not in linha:
                    # O nome pode estar na próxima linha
                    # Essa lógica pode ser complexa, então vamos focar no padrão principal.
                    pass


                # 4. Identifica o Módulo do plano
                if "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%" in linha:
                    contexto["modulo_atual"] = "NR PJ NAC AMB HOSP ENF OBST COPARTICIPACAO 25%"
                    continue

                # 5. Tenta identificar e extrair dados de uma linha de evento
                # A condição é que já tenhamos um beneficiário identificado
                if contexto["beneficiario_atual"] and re.search(r'\d{2}/\d{2}/\d{4}', linha):
                    dados_evento = parse_linha_evento(linha)
                    if dados_evento:
                        registro_completo = {
                            "Familia": contexto["familia"],
                            "Responsavel": contexto["responsavel"],
                            "Matricula_Funcional": contexto["matricula_funcional"],
                            "Beneficiario_Utilizacao": contexto["beneficiario_atual"],
                            "Modulo_Plano": contexto["modulo_atual"],
                            "Descricao_Evento": dados_evento["Descricao"],
                            "Executor": dados_evento["Executor"],
                            "Data_Evento": dados_evento["Data"],
                            "Valor_Coparticipacao": dados_evento["Valor_Total_Coparticipacao"]
                        }
                        registros.append(registro_completo)

    if not registros:
        return pd.DataFrame() # Retorna DF vazio se nada for encontrado

    df = pd.DataFrame(registros)
    return df


def to_excel(df):
    """
    Converte um DataFrame para um arquivo Excel em memória.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato_Detalhado')
        # Auto-ajuste da largura das colunas para melhor visualização
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            writer.sheets['Extrato_Detalhado'].set_column(col_idx, col_idx, column_width)
    processed_data = output.getvalue()
    return processed_data

# --- Interface do Streamlit (UI) ---

st.set_page_config(page_title="Conversor de Faturamento Unimed", layout="wide")

st.title("📄 Conversor de Demonstrativo de Faturamento Unimed")
st.markdown("""
Esta aplicação foi **ajustada para ler o layout específico do arquivo `Unimed - Demonstrativo de Faturamento`**. 
Ela extrai os dados de utilização de cada beneficiário e os organiza em uma tabela.

**Instruções:**
1.  Faça o upload do seu arquivo PDF.
2.  Aguarde o processamento.
3.  Visualize os dados extraídos na tela.
4.  Clique no botão para baixar o relatório completo em formato Excel.
""")

uploaded_file = st.file_uploader(
    "Escolha o seu arquivo PDF de faturamento", 
    type="pdf"
)

if uploaded_file is not None:
    with st.spinner('Analisando o PDF e extraindo os dados... Isso pode demorar um pouco.'):
        try:
            df_extraido = extrair_dados_pdf(uploaded_file)
            
            if not df_extraido.empty:
                st.success(f"🎉 Processamento concluído! Foram encontrados {len(df_extraido)} registros de eventos.")
                
                st.dataframe(df_extraido)
                
                excel_file = to_excel(df_extraido)
                
                st.download_button(
                    label="📥 Baixar Relatório em Excel",
                    data=excel_file,
                    file_name=f"faturamento_unimed_{uploaded_file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Não foram encontrados registros de eventos no formato esperado. Verifique se o arquivo PDF é o correto ou se o layout não foi alterado.")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
            st.error("Este erro pode ocorrer se a estrutura do PDF for muito diferente da amostra fornecida.")
