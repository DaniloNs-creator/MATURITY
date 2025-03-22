import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# Função para exportar os dados para um arquivo Excel, incluindo os enunciados
def exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias, valores, fig):
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            linhas.append({"Pergunta": subpergunta, "Resposta": respostas[subitem]})
    df_respostas = pd.DataFrame(linhas)

    df_grafico = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores[:-1]})

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Respostas')
        df_grafico.to_excel(writer, index=False, sheet_name='Gráfico')

        workbook = writer.book
        worksheet = writer.sheets['Gráfico']

        img_data = BytesIO()
        fig.savefig(img_data, format='png')
        img_data.seek(0)

        worksheet.insert_image('E2', 'grafico.png', {'image_data': img_data})

    return output.getvalue()

if "formulario_preenchido" not in st.session_state:
    st.session_state.formulario_preenchido = False

if not st.session_state.formulario_preenchido:
    st.title("MATRIZ DE MATURIDADE DE COMPLIANCE  E PROCESSOS")
    st.subheader("Por favor, preencha suas informações antes de prosseguir")

    nome = st.text_input("Nome")
    email = st.text_input("E-mail")
    empresa = st.text_input("Empresa")
    telefone = st.text_input("Telefone")

    if st.button("Prosseguir"):
        if nome and email and empresa and telefone:  # Adicionado 'and' entre 'empresa' e 'telefone'
            st.session_state.nome = nome
            st.session_state.email = email
            st.session_state.empresa = empresa
            st.session_state.telefone = telefone
            st.session_state.formulario_preenchido = True
            st.success("Informações preenchidas com sucesso! Você pode prosseguir para o questionário.")
        else:
            st.error("Por favor, preencha todos os campos antes de prosseguir.")
else:
    st.title("Formulário com Itens Expansíveis e Gráfico de Radar")

    caminho_arquivo = "/workspaces/MATURITY/FORMULARIO.csv"
    try:
        perguntas_df = pd.read_csv(
            caminho_arquivo, 
            delimiter=',', 
            quoting=3, 
            on_bad_lines='skip'  # Substituído por 'on_bad_lines' para ignorar linhas com problemas
        )

        if 'classe' not in perguntas_df.columns or 'pergunta' not in perguntas_df.columns:  # Substituído 'ou' por 'or'
            st.error("Certifique-se de que o arquivo CSV contém as colunas 'classe' e 'pergunta'.")
        else:
            perguntas_hierarquicas = {}
            respostas = {}

            for _, row in perguntas_df.iterrows():
                classe = str(row['classe'])
                pergunta = row['pergunta']

                if classe.endswith(".0"):
                    perguntas_hierarquicas[classe] = {"titulo": pergunta, "subitens": {}}
                else:
                    item_principal = classe.split(".")[0] + ".0"
                    if item_principal not in perguntas_hierarquicas:
                        perguntas_hierarquicas[item_principal] = {"titulo": "", "subitens": {}}
                    perguntas_hierarquicas[item_principal]["subitens"][classe] = pergunta

            st.write("Por favor, responda às perguntas dentro de cada item:")
            for item, conteudo in perguntas_hierarquicas.items():
                with st.expander(f"{item} - {conteudo['titulo']}"):
                    for subitem, subpergunta in conteudo["subitens"].items():
                        respostas[subitem] = st.number_input(f"{subitem} - {subpergunta}", min_value=0, max_value=5, step=1)

            if st.button("Enviar Dados e Gerar Gráfico"):
                st.write(f"Obrigado, {st.session_state.nome}!")
                st.write("Respostas enviadas com sucesso!")

                categorias = []
                valores = []
                for item, conteudo in perguntas_hierarquicas.items():
                    soma_respostas = sum(respostas[subitem] for subitem in conteudo["subitens"].keys())
                    num_perguntas = len(conteudo["subitens"])
                    if num_perguntas > 0:
                        valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
                        categorias.append(conteudo["titulo"])
                        valores.append(valor_percentual)

                if categorias:
                    valores += valores[:1]
                    angulos = np.linspace(0, 2 * np.pi, len(categorias), endpoint=False).tolist()
                    angulos += angulos[:1]

                    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    ax.fill(angulos, valores, color='blue', alpha=0.25)
                    ax.plot(angulos, valores, color='blue', linewidth=2)
                    ax.set_yticks(np.arange(0, 101, step=20))
                    ax.set_xticks(angulos[:-1])
                    ax.set_xticklabels(categorias, fontsize=8)

                    st.pyplot(fig)

                    excel_data = exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias, valores, fig)
                    st.download_button(
                        label="Exportar para Excel",
                        data=excel_data,
                        file_name="respostas_e_grafico.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

    except FileNotFoundError:
        st.error(f"O arquivo {caminho_arquivo} não foi encontrado.")
    except pd.errors.ParserError as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
