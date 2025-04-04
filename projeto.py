import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests

st.set_page_config(layout='wide')

# Mapeamento das respostas de texto para valores numéricos
mapeamento_respostas = {
    "Selecione": 0,  # Adicionando "Selecione" como valor padrão
    "Não iniciado": 1,
    "Inicial": 2,
    "Em andamento": 3,
    "Avançado": 4,
    "Completamente implementado": 5
}

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
    url_arquivo = "https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/FOMULARIO.txt"
    try:
        response = requests.get(url_arquivo)
        response.raise_for_status()

        lines = response.text.splitlines()
        data = []
        grupo_atual = None
        for line in lines:
            parts = line.strip().split(';')
            if len(parts) >= 2:
                classe = parts[0].strip()
                pergunta = parts[1].strip()

                if classe.isdigit():
                    grupo_atual = f"{classe} - {pergunta}"
                else:
                    if grupo_atual:
                        data.append({'grupo': grupo_atual, 'classe': classe, 'pergunta': pergunta})

        perguntas_df = pd.DataFrame(data)

        if perguntas_df.empty or not {'grupo', 'classe', 'pergunta'}.issubset(perguntas_df.columns):
            st.error("Certifique-se de que o arquivo TXT contém as colunas 'grupo', 'classe' e 'pergunta'.")
            st.write("Conteúdo do arquivo processado:", perguntas_df.head())
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
            
            # Criando navegação por grupos
            with st.sidebar:
                st.title("Navegação por Grupos")
                tab1, tab2, tab3, tab4 = st.tabs(["FINANCEIRA", "GESTÃO", "GOVERNANÇA", "SETORES"])
                
                with tab1:
                    if st.button("Eficiência de Gestão"):
                        st.session_state.grupo_atual = 0
                
                with tab2:
                    if st.button("Estruturas"):
                        st.session_state.grupo_atual = 1
                
                with tab3:
                    if st.button("Gestão de Processos"):
                        st.session_state.grupo_atual = 2
                    if st.button("Gestão de Riscos"):
                        st.session_state.grupo_atual = 3
                    if st.button("Compliance"):
                        st.session_state.grupo_atual = 4
                    if st.button("Canal de Denúncias"):
                        st.session_state.grupo_atual = 5
                    if st.button("Governança Corporativa"):
                        st.session_state.grupo_atual = 6
                
                with tab4:
                    if st.button("Recursos Humanos"):
                        st.session_state.grupo_atual = 7
                    if st.button("Tecnologia da Informação"):
                        st.session_state.grupo_atual = 8
                    if st.button("Compras"):
                        st.session_state.grupo_atual = 9
                    if st.button("Estoques"):
                        st.session_state.grupo_atual = 10
                    if st.button("Contabilidade e Controle Financeiro"):
                        st.session_state.grupo_atual = 11
                    if st.button("Logística e Distribuição"):
                        st.session_state.grupo_atual = 12

            grupo_atual = st.session_state.grupo_atual

            # Textos introdutórios para cada grupo
            TEXTO_GRUPO1 = """
            O preenchimento de uma Matriz de Maturidade de Gestão Financeira é essencial para avaliar a eficiência dos processos financeiros, identificar lacunas e estruturar um plano de melhoria contínua. Ela permite medir o nível de controle sobre orçamento, fluxo de caixa, investimentos e riscos, fornecendo uma visão clara da saúde financeira da empresa. Além disso, facilita a tomada de decisões estratégicas, ajudando a mitigar riscos, otimizar recursos e garantir a sustentabilidade do negócio a longo prazo. Empresas que utilizam essa matriz conseguem se adaptar melhor a mudanças e aprimorar sua competitividade.
            """
            TEXTO_GRUPO2 = """
            A avaliação da maturidade da estrutura de uma organização é um processo essencial para entender o nível de desenvolvimento e a eficácia das práticas de governança, gestão de riscos, compliance e processos organizacionais. Trata-se de um diagnóstico completo que permite identificar pontos fortes, fragilidades e oportunidades de melhoria em diferentes áreas estratégicas.
            """
            TEXTO_GRUPO3 = """
            O preenchimento desta seção permite avaliar a maturidade do programa de Compliance, garantindo que a organização esteja em conformidade com regulamentações e boas práticas éticas. Ajuda a prevenir riscos legais, fortalecer a cultura organizacional e demonstrar compromisso com a integridade corporativa.
            """
            TEXTO_GRUPO4 = """
            Responder a estas perguntas auxilia na identificação, monitoramento e mitigação de riscos que podem impactar a operação. Com uma gestão de riscos eficiente, a empresa minimiza perdas, melhora a tomada de decisão e se prepara para desafios internos e externos, garantindo maior resiliência operacional.
            """
            TEXTO_GRUPO5 = """
            Esta seção permite avaliar a eficiência e a padronização dos processos internos. Um bom gerenciamento de processos melhora a produtividade, reduz desperdícios e assegura entregas consistentes. Além disso, facilita a implementação de melhorias contínuas e a adaptação a novas exigências do mercado.
            """
            TEXTO_GRUPO6 = """
            A governança bem estruturada assegura transparência, ética e eficiência na gestão da empresa. Com este diagnóstico, é possível fortalecer a tomada de decisão, alinhar os interesses das partes interessadas e garantir um crescimento sustentável, reduzindo riscos e aumentando a confiança dos stakeholders.
            """
            TEXTO_GRUPO7 = """
            Esta seção mede a maturidade da gestão de pessoas, garantindo que a empresa valorize seus colaboradores e mantenha um ambiente produtivo e inclusivo. Um RH eficiente melhora a retenção de talentos, impulsiona a inovação e alinha os funcionários à cultura e estratégia organizacional.
            """
            TEXTO_GRUPO8 = """
            Responder a estas perguntas ajuda a avaliar o nível de digitalização e segurança da empresa. Uma TI bem estruturada melhora a eficiência operacional, protege dados sensíveis e impulsiona a inovação, garantindo que a organização esteja preparada para desafios tecnológicos e competitivos.
            """
            TEXTO_GRUPO9 = """
            Esta seção permite identificar boas práticas e oportunidades de melhoria na gestão financeira. Com um controle eficiente, a empresa assegura sustentabilidade, reduz riscos de inadimplência e fraudes, melhora a liquidez e otimiza investimentos, garantindo saúde financeira e crescimento sustentável.
            """
            TEXTO_GRUPO10 = """
            O diagnóstico nesta área assegura que as compras sejam estratégicas, alinhadas às necessidades da empresa e aos melhores preços e prazos. Com processos estruturados, a organização reduz custos, melhora a qualidade dos insumos e fortalece a relação com fornecedores confiáveis.
            """
            TEXTO_GRUPO11 = """
            Avaliar a gestão de estoques permite reduzir desperdícios, evitar faltas e garantir uma operação eficiente. Com controle adequado, a empresa melhora a previsibilidade, reduz custos de armazenagem e assegura disponibilidade de produtos, otimizando o fluxo operacional.
            """
            TEXTO_GRUPO12 = """
            Responder a estas perguntas possibilita otimizar a cadeia logística, garantindo entregas ágeis e redução de custos operacionais. Um bom planejamento melhora o nível de serviço, evita atrasos e assegura eficiência no transporte, impactando positivamente a satisfação do cliente.
            """
            TEXTO_GRUPO13 = """
            Esta seção avalia a transparência e conformidade da contabilidade empresarial. Um controle rigoroso das demonstrações financeiras assegura a correta apuração de resultados, garantindo confiança e credibilidade junto a investidores e órgãos reguladores.
            """

            # Lista de perguntas obrigatórias
            perguntas_obrigatorias = [
                "1.02", "1.06", "1.42", "1.03", "1.13", "1.14", "1.30", "1.12", "1.19", "1.25", "1.41", "1.43", "1.27", "1.35", "1.45", "1.20",
                "2.10", "2.01", "2.16", "2.23", "2.05", "2.08", "2.25", "2.29", "2.21", "2.22",
                "3.01", "3.04", "3.08", "3.11", "3.29", "3.38", "3.40", "3.42", "3.43",
                "5.01", "5.03", "5.04", "5.07", "5.10", "5.32", "5.35", "5.40"
            ]

            # Grupos obrigatórios (4, 6, 7, 8, 9, 10, 11, 12, 13)
            grupos_obrigatorios = [
                "4 - Gestão de Riscos",
                "6 - Governança Corporativa",
                "7 - Recursos Humanos",
                "8 - Tecnologia da Informação",
                "9 - Compras",
                "10 - Estoques",
                "11 - Contabilidade e Controle Financeiro",
                "12 - Logística e Distribuição",
                "13 - Contabilidade e Controle Financeiro"
            ]

            if grupo_atual < len(grupos):
                grupo = grupos[grupo_atual]

                # Exibe o texto introdutório correspondente ao grupo atual
                if grupo.startswith("1 -"):
                    st.markdown(TEXTO_GRUPO1)
                elif grupo.startswith("2 -"):
                    st.markdown(TEXTO_GRUPO2)
                elif grupo.startswith("3 -"):
                    st.markdown(TEXTO_GRUPO3)
                elif grupo.startswith("4 -"):
                    st.markdown(TEXTO_GRUPO4)
                elif grupo.startswith("5 -"):
                    st.markdown(TEXTO_GRUPO5)
                elif grupo.startswith("6 -"):
                    st.markdown(TEXTO_GRUPO6)
                elif grupo.startswith("7 -"):
                    st.markdown(TEXTO_GRUPO7)
                elif grupo.startswith("8 -"):
                    st.markdown(TEXTO_GRUPO8)
                elif grupo.startswith("9 -"):
                    st.markdown(TEXTO_GRUPO9)
                elif grupo.startswith("10 -"):
                    st.markdown(TEXTO_GRUPO10)
                elif grupo.startswith("11 -"):
                    st.markdown(TEXTO_GRUPO11)
                elif grupo.startswith("12 -"):
                    st.markdown(TEXTO_GRUPO12)
                elif grupo.startswith("13 -"):
                    st.markdown(TEXTO_GRUPO13)

                st.write(f"### {perguntas_hierarquicas[grupo]['titulo']}")
                
                # Verifica se todas as perguntas obrigatórias foram respondidas
                todas_obrigatorias_preenchidas = True
                obrigatorias_no_grupo = []
                
                for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
                    if subitem in perguntas_obrigatorias:
                        obrigatorias_no_grupo.append(subitem)
                        if st.session_state.respostas.get(subitem, "Selecione") == "Selecione":
                            todas_obrigatorias_preenchidas = False

                for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
                    if subitem not in st.session_state.respostas:
                        st.session_state.respostas[subitem] = "Selecione"  # Inicializa com "Selecione"

                    # Adiciona destaque em negrito para perguntas obrigatórias
                    if subitem in perguntas_obrigatorias:
                        pergunta_label = f"**{subitem} - {subpergunta}** (OBRIGATÓRIO)"  # Destaca em negrito
                    else:
                        pergunta_label = f"{subitem} - {subpergunta}"

                    resposta = st.selectbox(
                        pergunta_label,
                        options=list(mapeamento_respostas.keys()),
                        index=list(mapeamento_respostas.keys()).index(st.session_state.respostas[subitem])
                    )
                    st.session_state.respostas[subitem] = resposta

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Voltar"):
                        if st.session_state.grupo_atual > 0:
                            st.session_state.grupo_atual -= 1
                with col2:
                    if st.button("Prosseguir"):
                        # Verifica se todas as perguntas obrigatórias do grupo atual foram respondidas
                        obrigatorias_no_grupo = [
                            subitem for subitem in perguntas_hierarquicas[grupo]["subitens"].keys()
                            if subitem in perguntas_obrigatorias
                        ]
                        todas_obrigatorias_preenchidas = all(
                            st.session_state.respostas.get(subitem, "Selecione") != "Selecione"
                            for subitem in obrigatorias_no_grupo
                        )

                        # Verifica se todos os grupos obrigatórios foram completamente preenchidos
                        grupos_obrigatorios_completos = True
                        grupos_incompletos = []
                        for grupo_obrigatorio in grupos_obrigatorios:
                            if grupo_obrigatorio in perguntas_hierarquicas:
                                for subitem in perguntas_hierarquicas[grupo_obrigatorio]["subitens"].keys():
                                    if st.session_state.respostas.get(subitem, "Selecione") == "Selecione":
                                        grupos_obrigatorios_completos = False
                                        grupos_incompletos.append(grupo_obrigatorio)
                                        break

                        if not todas_obrigatorias_preenchidas:
                            st.error(f"Por favor, responda todas as perguntas obrigatórias deste grupo antes de prosseguir: {', '.join(obrigatorias_no_grupo)}")
                        elif not grupos_obrigatorios_completos:
                            st.error(f"Os seguintes grupos obrigatórios não foram completamente preenchidos: {', '.join(set(grupos_incompletos))}")
                        else:
                            # Avança para o próximo grupo
                            st.session_state.grupo_atual += 1
                            st.success("Você avançou para o próximo grupo.")

                            # Exibe o nível do usuário após preencher o grupo atual
                            respostas = {k: mapeamento_respostas[v] for k, v in st.session_state.respostas.items()}
                            total_respostas = sum(respostas.values())
                            total_perguntas = len(respostas)
                            if total_perguntas > 0:
                                nivel_percentual = (total_respostas / (total_perguntas * 5)) * 100
                                if nivel_percentual < 26:
                                    st.warning("SEU NÍVEL ATUAL É: INICIAL")
                                    st.info("""
                                    **NIVEL DE MATURIDADE INICIAL:** 
                                    Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados. 
                                    As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada. 
                                    A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
                                    """)
                                elif nivel_percentual < 51:
                                    st.warning("SEU NÍVEL ATUAL É: REPETITIVO")
                                    st.info("""
                                    **NIVEL DE MATURIDADE ORGANIZAÇÃO:** 
                                    A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada. 
                                    Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada. 
                                    As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
                                    """)
                                elif nivel_percentual < 71:
                                    st.warning("SEU NÍVEL ATUAL É: DEFINIDO")
                                    st.info("""
                                    **NIVEL DE MATURIDADE CONSOLIDAÇÃO:** 
                                    A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada. 
                                    Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual. 
                                    A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas. 
                                    Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
                                    """)
                                elif nivel_percentual < 90:
                                    st.warning("SEU NÍVEL ATUAL É: GERENCIADO")
                                    st.info("""
                                    **NIVEL DE MATURIDADE OTIMIZAÇÃO:** 
                                    Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho. 
                                    A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades. 
                                    A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional. 
                                    O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
                                    """)
                                elif nivel_percentual >= 91:
                                    st.success("SEU NÍVEL ATUAL É: OTIMIZADO")
                                    st.info("""
                                    **NIVEL DE MATURIDADE EXCELÊNCIA:** 
                                    A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação. 
                                    Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico. 
                                    Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório. 
                                    O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
                                    """)
            else:
                st.write("### Todas as perguntas foram respondidas!")
                if st.button("Gerar Gráfico"):
                    # Verifica se todas as perguntas obrigatórias foram respondidas
                    todas_obrigatorias_respondidas = True
                    obrigatorias_nao_respondidas = []
                    
                    for pergunta in perguntas_obrigatorias:
                        if st.session_state.respostas.get(pergunta, "Selecione") == "Selecione":
                            todas_obrigatorias_respondidas = False
                            obrigatorias_nao_respondidas.append(pergunta)
                    
                    # Verifica se todos os grupos obrigatórios foram completamente respondidos
                    grupos_obrigatorios_completos = True
                    grupos_incompletos = []
                    
                    for grupo_obrigatorio in grupos_obrigatorios:
                        if grupo_obrigatorio in perguntas_hierarquicas:
                            for subitem in perguntas_hierarquicas[grupo_obrigatorio]["subitens"].keys():
                                if st.session_state.respostas.get(subitem, "Selecione") == "Selecione":
                                    grupos_obrigatorios_completos = False
                                    grupos_incompletos.append(grupo_obrigatorio)
                                    break
                    
                    if not todas_obrigatorias_respondidas or not grupos_obrigatorios_completos:
                        mensagem_erro = []
                        if not todas_obrigatorias_respondidas:
                            mensagem_erro.append(f"Perguntas obrigatórias não respondidas: {', '.join(obrigatorias_nao_respondidas)}")
                        if not grupos_obrigatorios_completos:
                            mensagem_erro.append(f"Grupos obrigatórios incompletos: {', '.join(set(grupos_incompletos))}")
                        st.error(" | ".join(mensagem_erro))
                    else:
                        respostas = {k: mapeamento_respostas[v] for k, v in st.session_state.respostas.items()}
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
                                    total_porcentagem = df_grafico_original['Porcentagem'].sum()
                                    df_grafico_original.loc['Total'] = ['Total', total_porcentagem]
                                    st.dataframe(df_grafico_original)

                                    if total_porcentagem < 26:
                                        st.warning("SEU NIVEL É INICIAL")
                                    elif total_porcentagem < 51:
                                        st.warning("SEU NIVEL É REPETITIVO")
                                    elif total_porcentagem < 71:
                                        st.warning("SEU NIVEL É DEFINIDO")
                                    elif total_porcentagem < 90:
                                        st.warning("SEU NIVEL É GERENCIADO")
                                    elif total_porcentagem >= 91:
                                        st.success("SEU NIVEL É OTIMIZADO")
                                with col2:
                                    st.plotly_chart(fig_normalizado, use_container_width=True)
                                    st.write("### Gráfico 2")
                                    df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
                                    st.dataframe(df_grafico_normalizado)
                                excel_data = exportar_para_excel_completo(st.session_state.respostas, perguntas_hierarquicas, categorias[:-1], valores[:-1], valores_normalizados[:-1])
                                st.download_button(
                                    label="Exportar para Excel",
                                    data=excel_data,
                                    file_name="respostas_e_grafico.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                )
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
