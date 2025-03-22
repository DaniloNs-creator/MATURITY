import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(layout='wide')

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

if not st.session_state.formulario_preenchido:
    st.title("MATRIZ DE MATURIDADE DE COMPLIANCE E PROCESSOS")
    st.subheader("Por favor, preencha suas informações antes de prosseguir")
    
    nome = st.text_input("Nome")
    email = st.text_input("E-mail")
    empresa = st.text_input("Empresa")
    telefone = st.text_input("Telefone")
    
    if st.button("Prosseguir"):
        if nome and email and empresa and telefone:
            st.session_state.nome = nome
            st.session_state.email = email
            st.session_state.empresa = empresa
            st.session_state.telefone = telefone
            st.session_state.formulario_preenchido = True
            st.success("Informações preenchidas com sucesso! Você pode prosseguir para o questionário.")
        else:
            st.error("Por favor, preencha todos os campos antes de prosseguir.")
else:
    st.title("Formulário")
    
    caminho_arquivo = "https://github.com/DaniloNs-creator/MATURITY/blob/main/FORMULARIO.csv"
    
    try:
        perguntas_df = pd.read_csv(caminho_arquivo)
        
        if not {'classe', 'pergunta'}.issubset(perguntas_df.columns):
            st.error("Certifique-se de que o arquivo CSV contém as colunas 'classe' e 'pergunta'.")
        else:
            perguntas_hierarquicas = {}
            respostas = st.session_state.get("respostas", {})
            etapa_atual = st.session_state.get("etapa_atual", 1)
            
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
            
            total_etapas = len(perguntas_hierarquicas)
            st.write(f"Etapa {etapa_atual} de {total_etapas}")
            
            for i, (item, conteudo) in enumerate(perguntas_hierarquicas.items(), start=1):
                if i == etapa_atual:
                    st.subheader(f"{item} - {conteudo['titulo']}")
                    for subitem, subpergunta in conteudo["subitens"].items():
                        respostas[subitem] = st.number_input(
                            f"{subitem} - {subpergunta}", 
                            min_value=0, 
                            max_value=5, 
                            step=1, 
                            value=respostas.get(subitem, 0)
                        )
                    break
            
            st.session_state.respostas = respostas
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Voltar", disabled=(etapa_atual == 1)):
                    st.session_state.etapa_atual = etapa_atual - 1
            with col2:
                if st.button("Prosseguir"):
                    if etapa_atual < total_etapas:
                        st.session_state.etapa_atual = etapa_atual + 1
                    else:
                        st.session_state.etapa_atual = 1
                        st.success("Todas as etapas foram concluídas!")
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
                                    st.write("### Tabela 1")
                                    df_grafico_original = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
                                    st.dataframe(df_grafico_original)
                                
                                with col2:
                                    st.plotly_chart(fig_normalizado, use_container_width=True)
                                    st.write("### Tabela 2")
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
