import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests  # Adicionado para baixar o arquivo remoto

st.set_page_config(layout='wide')

def calcular_porcentagem_grupo(grupo, perguntas_hierarquicas, respostas):
    soma_respostas = sum(respostas[subitem] for subitem in perguntas_hierarquicas[grupo]["subitens"].keys())
    num_perguntas = len(perguntas_hierarquicas[grupo]["subitens"])
    valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
    return valor_percentual

def exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias, valores, valores_normalizados):
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            linhas.append({"Pergunta": subpergunta, "Resposta": respostas[subitem]})

    df_respostas = pd.DataFrame(linhas)
    df_grafico = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
    df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Respostas')
        df_grafico.to_excel(writer, index=False, sheet_name='Gráfico')
        df_grafico_normalizado.to_excel(writer, index=False, sheet_name='Gráfico Normalizado')
    return output.getvalue()

if "formulario_preenchido" not in st.session_state:
    st.session_state.formulario_preenchido = False
if "grupo_atual" not in st.session_state:
    st.session_state.grupo_atual = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}

if not st.session_state.formulario_preenchido:
    st.title("MATRIZ DE MATURIDADE DE COMPLIANCE E PROCESSOS")
    st.subheader("Por favor, preencha suas informações antes de prosseguir")

    nome = st.text_input("Nome")
    email = st.text_input("E-mail")
    empresa = st.text_input("Empresa")
    telefone = st.text_input("Telefone")
    if st.button("Prosseguir"):
        if nome and email and empresa and telefone:  # Corrigido: Adicionado 'and' entre 'empresa' e 'telefone'
            st.session_state.nome = nome
            st.session_state.email = email
            st.session_state.empresa = empresa
            st.session_state.telefone = telefone
            st.session_state.formulario_preenchido = True
            st.success("Informações preenchidas com sucesso! Você pode prosseguir para o questionário.")
        else:
            st.error("Por favor, preencha todos os campos antes de prosseguir.")
else:
    url_arquivo = "https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/FOMULARIO.txt"  # URL raw do GitHub
    try:
        # Baixando o arquivo .txt
        response = requests.get(url_arquivo)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida

        # Processando as linhas para criar um DataFrame
        lines = response.text.splitlines()
        data = []
        grupo_atual = None
        for line in lines:
            # Separa as colunas usando o delimitador ";"
            parts = line.strip().split(';')
            if len(parts) >= 2:  # Verifica se há pelo menos duas colunas
                classe = parts[0].strip()
                pergunta = parts[1].strip()

                # Verifica se a linha é um título de grupo (número inteiro seguido de um texto)
                if classe.isdigit():
                    grupo_atual = f"{classe} - {pergunta}"  # Formato: "1 - Eficiência de Gestão"
                else:
                    # Adiciona a pergunta ao grupo atual
                    if grupo_atual:
                        data.append({'grupo': grupo_atual, 'classe': classe, 'pergunta': pergunta})

        # Criar o DataFrame
        perguntas_df = pd.DataFrame(data)

        # Verificar se as colunas necessárias estão presentes
        if perguntas_df.empty or not {'grupo', 'classe', 'pergunta'}.issubset(perguntas_df.columns):
            st.error("Certifique-se de que o arquivo TXT contém as colunas 'grupo', 'classe' e 'pergunta'.")
            st.write("Conteúdo do arquivo processado:", perguntas_df.head())  # Exibe uma amostra para depuração
        else:
            perguntas_hierarquicas = {}
            for _, row in perguntas_df.iterrows():
                grupo = row['grupo']
                classe = str(row['classe'])
                pergunta = row['pergunta']

                if grupo not in perguntas_hierarquicas:
                    perguntas_hierarquicas[grupo] = {"titulo": grupo, "subitens": {}}

                perguntas_hierarquicas[grupo]["subitens"][classe] = pergunta

            grupos = list(perguntas_hierarquicas.keys())
            grupo_atual = st.session_state.grupo_atual

            if grupo_atual < len(grupos):
                grupo = grupos[grupo_atual]
                st.write(f"### {perguntas_hierarquicas[grupo]['titulo']}")
                for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
                    if subitem not in st.session_state.respostas:
                        st.session_state.respostas[subitem] = 0
                    st.session_state.respostas[subitem] = st.number_input(
                        f"{subitem} - {subpergunta}",
                        min_value=0,
                        max_value=5,
                        step=1,
                        value=st.session_state.respostas[subitem]
                    )

                # Verifica se o botão "Prosseguir" foi clicado
                if st.button("Prosseguir"):
                    # Verifica se o grupo atual é "1 - Eficiência de Gestão"
                    if grupo == "1 - Eficiência de Gestão":
                        valor_percentual_grupo1 = calcular_porcentagem_grupo(grupo, perguntas_hierarquicas, st.session_state.respostas)
                        if valor_percentual_grupo1 < 25:
                            st.error("Não foi possível prosseguir. O resultado do Grupo 1 - Eficiência de Gestão é menor que 25.")
                        else:
                            st.session_state.grupo_atual += 1
                    elif grupo == "2 - Estruturas":  # Substitua pelo nome real do Grupo 2
                        valor_percentual_grupo1 = calcular_porcentagem_grupo("1 - Eficiência de Gestão", perguntas_hierarquicas, st.session_state.respostas)
                        valor_percentual_grupo2 = calcular_porcentagem_grupo(grupo, perguntas_hierarquicas, st.session_state.respostas)
                        soma_percentual = valor_percentual_grupo1 + valor_percentual_grupo2

                        if soma_percentual <= 50:
                            st.error("Não é possível prosseguir. A soma dos Grupos 1 e 2 é menor ou igual a 50.")
                        else:
                            st.session_state.grupo_atual += 1
                    else:
                        st.session_state.grupo_atual += 1
            else:
                st.write("### Todas as perguntas foram respondidas!")
                if st.button("Gerar Gráfico"):
                    respostas = st.session_state.respostas
                    categorias = []
                    valores = []
                    valores_normalizados = []
                    soma_total_respostas = sum(respostas.values())
                    for item, conteudo in perguntas_hierarquicas.items():
                        soma_respostas = sum(respostas[subitem] for subitem in conteudo["subitens"].keys())
                        num_perguntas = len(conteudo["subitens"])
                        if num_perguntas > 0:
                            valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
                            valor_normalizado = (soma_respostas / valor_percentual) * 100 if valor_percentual > 0 else 0
                            categorias.append(conteudo["titulo"])
                            valores.append(valor_percentual)
                            valores_normalizados.append(valor_normalizado)
                    if len(categorias) != len(valores) or len(categorias) != len(valores_normalizados):
                        st.error("Erro: As listas de categorias e valores têm tamanhos diferentes.")
                    else:
                        if categorias:
                            valores_original = valores + valores[:1]
                            categorias_original = categorias + categorias[:1]
                            import plotly.graph_objects as go
                            fig_original = go.Figure()
                            fig_original.add_trace(go.Scatterpolar(
                                r=valores_original,
                                theta=categorias_original,
                                fill='toself',
                                name='Gráfico Original'
                            ))
                            fig_original.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )),
                                showlegend=False
                            )
                            valores_normalizados_fechado = valores_normalizados + valores_normalizados[:1]
                            fig_normalizado = go.Figure()
                            fig_normalizado.add_trace(go.Scatterpolar(
                                r=valores_normalizados_fechado,
                                theta=categorias_original,
                                fill='toself',
                                name='Gráfico Normalizado'
                            ))
                            fig_normalizado.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )),
                                showlegend=False
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                st.plotly_chart(fig_original, use_container_width=True)
                                st.write("### Gráfico 1")
                                df_grafico_original = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
                                st.dataframe(df_grafico_original)
                            with col2:
                                st.plotly_chart(fig_normalizado, use_container_width=True)
                                st.write("### Gráfico 2")
                                df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
                                st.dataframe(df_grafico_normalizado)
                            excel_data = exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias[:-1], valores[:-1], valores_normalizados[:-1])
                            st.download_button(
                                label="Exportar para Excel",
                                data=excel_data,
                                file_name="respostas_e_grafico.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
