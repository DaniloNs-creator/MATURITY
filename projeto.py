import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests
import plotly.graph_objects as go
import base64  # Para converter imagens em base64

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

# Verificar se o pacote kaleido está instalado
try:
    import kaleido
except ImportError:
    st.error("O pacote 'kaleido' é necessário para exportar gráficos como imagens. Por favor, instale-o executando: pip install -U kaleido")
    st.stop()

# Função para verificar se todas as perguntas obrigatórias foram respondidas
def verificar_obrigatorias_preenchidas(grupo, perguntas_hierarquicas, perguntas_obrigatorias, respostas):
    obrigatorias_no_grupo = [
        subitem for subitem in perguntas_hierarquicas[grupo]["subitens"].keys()
        if subitem in perguntas_obrigatorias
    ]
    todas_preenchidas = all(
        respostas.get(subitem, "Selecione") != "Selecione"
        for subitem in obrigatorias_no_grupo
    )
    return todas_preenchidas, obrigatorias_no_grupo

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

def exportar_graficos_e_respostas(respostas, perguntas_hierarquicas, categorias, valores, valores_normalizados, fig_original, fig_normalizado):
    # Exportar respostas e gráficos para Excel
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            linhas.append({"Pergunta": subpergunta, "Resposta": respostas[subitem]})

    df_respostas = pd.DataFrame(linhas)
    df_grafico = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
    df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})

    # Salvar gráficos como imagens usando kaleido
    img_original = BytesIO()
    fig_original.write_image(img_original, format="png", engine="kaleido")
    img_original.seek(0)

    img_normalizado = BytesIO()
    fig_normalizado.write_image(img_normalizado, format="png", engine="kaleido")
    img_normalizado.seek(0)

    # Criar arquivo Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Respostas')
        df_grafico.to_excel(writer, index=False, sheet_name='Gráfico')
        df_grafico_normalizado.to_excel(writer, index=False, sheet_name='Gráfico Normalizado')

        # Adicionar imagens ao Excel
        workbook = writer.book
        worksheet = workbook.add_worksheet('Gráficos')
        writer.sheets['Gráficos'] = worksheet
        worksheet.insert_image('B2', 'grafico_original.png', {'image_data': img_original})
        worksheet.insert_image('B20', 'grafico_normalizado.png', {'image_data': img_normalizado})

    return output.getvalue()

def gerar_graficos_radar(perguntas_hierarquicas, respostas):
    respostas_numericas = {k: mapeamento_respostas[v] for k, v in respostas.items()}
    categorias = []
    valores = []
    valores_normalizados = []
    
    for item, conteudo in perguntas_hierarquicas.items():
        soma_respostas = sum(respostas_numericas[subitem] for subitem in conteudo["subitens"].keys())
        num_perguntas = len(conteudo["subitens"])
        if num_perguntas > 0:
            valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
            valor_normalizado = (soma_respostas / valor_percentual) * 100 if valor_percentual > 0 else 0
            categorias.append(conteudo["titulo"])
            valores.append(valor_percentual)
            valores_normalizados.append(valor_normalizado)
    
    if len(categorias) != len(valores) or len(categorias) != len(valores_normalizados):
        st.error("Erro: As listas de categorias e valores têm tamanhos diferentes.")
        return None, None
    
    # Gráfico Original
    valores_original = valores + valores[:1]
    categorias_original = categorias + categorias[:1]
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
        showlegend=False,
        title="Gráfico de Radar - Nível Atual"
    )
    
    # Gráfico Normalizado
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
        showlegend=False,
        title="Gráfico de Radar - Normalizado"
    )
    
    return fig_original, fig_normalizado

def mostrar_nivel_maturidade(total_porcentagem):
    if total_porcentagem < 26:
        st.warning("SEU NÍVEL ATUAL É: INICIAL")
        st.info("""
        **NIVEL DE MATURIDADE INICIAL:** 
        Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados. 
        As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada. 
        A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
        """)
    elif total_porcentagem < 51:
        st.warning("SEU NÍVEL ATUAL É: REPETITIVO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:** 
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada. 
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada. 
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif total_porcentagem < 71:
        st.warning("SEU NÍVEL ATUAL É: DEFINIDO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:** 
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada. 
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual. 
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas. 
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif total_porcentagem < 90:
        st.warning("SEU NÍVEL ATUAL É: GERENCIADO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:** 
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho. 
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades. 
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional. 
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif total_porcentagem >= 91:
        st.success("SEU NÍVEL ATUAL É: OTIMIZADO")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:** 
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação. 
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico. 
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório. 
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)

def mostrar_nivel_atual_por_grupo(grupo, valor_percentual):
    if valor_percentual < 26:
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: INICIAL")
        st.info("""
        **NIVEL DE MATURIDADE INICIAL:**
        Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados.
        As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada.
        A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
        """)
    elif valor_percentual < 51:
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: REPETITIVO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:**
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada.
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada.
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif valor_percentual < 71:
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: DEFINIDO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:**
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada.
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual.
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas.
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif valor_percentual < 90:
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: GERENCIADO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:**
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho.
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades.
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional.
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif valor_percentual >= 91:
        st.success(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: OTIMIZADO")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:**
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação.
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico.
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório.
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)

def validar_nivel_maturidade(soma_percentual, total_porcentagem):
    if soma_percentual < 26:
        st.warning("SEU NÍVEL ATUAL É: INICIAL")
        st.info("""
        **NIVEL DE MATURIDADE INICIAL:**
        Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados.
        As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada.
        A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
        """)
    elif soma_percentual < 51:
        st.warning("SEU NÍVEL ATUAL É: REPETITIVO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:**
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada.
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada.
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif soma_percentual < 71:
        st.warning("SEU NÍVEL ATUAL É: DEFINIDO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:**
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada.
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual.
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas.
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif soma_percentual < 90:
        st.warning("SEU NÍVEL ATUAL É: GERENCIADO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:**
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho.
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades.
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional.
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif soma_percentual >= 91:
        st.success("SEU NÍVEL ATUAL É: OTIMIZADO")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:**
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação.
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico.
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório.
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)

if "formulario_preenchido" not in st.session_state:
    st.session_state.formulario_preenchido = False
if "grupo_atual" not in st.session_state:
    st.session_state.grupo_atual = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}
if "mostrar_graficos" not in st.session_state:
    st.session_state.mostrar_graficos = False

if not st.session_state.formulario_preenchido:
    # Adicionando a imagem no início com tamanho reduzido
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/logo.png", width=300)
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
    with col2:
        st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/foto.jpg", use_container_width=True)
else:
    url_arquivo = "https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/FOMULARIO.txt"
    try:
        response = requests.get(url_arquivo)
        response.raise_for_status()

        # Inicializar as variáveis para evitar erros
        categorias = []
        valores = []
        valores_normalizados = []

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
               
                # Corrigindo o caminho da imagem para o URL bruto do GitHub
                st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/logo.png")
                st.title("Navegação por Grupos")
                
                tab1, tab2, tab3, tab4 = st.tabs(["FINANCEIRA", "GESTÃO", "GOVERNANÇA", "SETORES"])
                
                with tab1:
                    if st.button("**Eficiência de Gestão**" if st.session_state.grupo_atual == 0 else "Eficiência de Gestão"):
                        st.session_state.grupo_atual = 0
                
                with tab2:
                    if st.button("**Estruturas**" if st.session_state.grupo_atual == 1 else "Estruturas"):
                        st.session_state.grupo_atual = 1
                
                with tab3:
                    if st.button("**Gestão de Processos**" if st.session_state.grupo_atual == 2 else "Gestão de Processos"):
                        st.session_state.grupo_atual = 2
                    if st.button("**Gestão de Riscos**" if st.session_state.grupo_atual == 3 else "Gestão de Riscos"):
                        st.session_state.grupo_atual = 3
                    if st.button("**Compliance**" if st.session_state.grupo_atual == 4 else "Compliance"):
                        st.session_state.grupo_atual = 4
                    if st.button("**Canal de Denúncias**" if st.session_state.grupo_atual == 5 else "Canal de Denúncias"):
                        st.session_state.grupo_atual = 5
                    if st.button("**Governança Corporativa**" if st.session_state.grupo_atual == 6 else "Governança Corporativa"):
                        st.session_state.grupo_atual = 6
                
                with tab4:
                    if st.button("**Recursos Humanos**" if st.session_state.grupo_atual == 7 else "Recursos Humanos"):
                        st.session_state.grupo_atual = 7
                    if st.button("**Tecnologia da Informação**" if st.session_state.grupo_atual == 8 else "Tecnologia da Informação"):
                        st.session_state.grupo_atual = 8
                    if st.button("**Compras**" if st.session_state.grupo_atual == 9 else "Compras"):
                        st.session_state.grupo_atual = 9
                    if st.button("**Estoques**" if st.session_state.grupo_atual == 10 else "Estoques"):
                        st.session_state.grupo_atual = 10
                    if st.button("**Contabilidade e Controle Financeiro**" if st.session_state.grupo_atual == 11 else "Contabilidade e Controle Financeiro"):
                        st.session_state.grupo_atual = 11
                    if st.button("**Logística e Distribuição**" if st.session_state.grupo_atual == 12 else "Logística e Distribuição"):
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
                "4.01", "4.02", "4.03", "4.04", "4.05", "4.06", "4.07", "4.08", "4.09","4.10",
                "5.01", "5.03", "5.04", "5.07", "5.10", "5.32", "5.35", "5.40"
                "6.01", "6.02", "6.03", "6.04", "6.05", "6.06", "6.07", "6.08", "6.09","6.10", "6.11", "6.12",
                "7.01", "7.02", "7.03", "7.04", "7.05", "7.06", "7.07", "7.08", "7.09","7.10",
                "8.01", "8.02", "8.03", "8.04", "8.05", "8.06", "8.07", "8.08", "8.09","8.10","8.11","8.12","8.13","8.14","8.15","8.16","8.17",
                "9.01", "9.02", "9.03", "9.04", "9.05", "9.06", "9.07", "9.08", "9.09","9.10",
                "10.01", "10.02", "10.03", "10.04", "10.05", "10.06", "10.07", "10.08","10.09","10.10",
                "11.01", "11.02", "11.03", "11.04", "11.05", "11.06", "11.07", "11.08","11.09","11.10",
                "12.01", "12.02", "12.03", "12.04", "12.05", "12.06", "12.07", "12.08","12.09","12.10",
                "13.01", "13.02", "13.03", "13.04", "13.05", "13.06", "13.07", "13.08","13.09","13.10"
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

                # Adicionando verificações para evitar erros ao acessar chaves inexistentes
                for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
                    if subitem not in st.session_state.respostas:
                        st.session_state.respostas[subitem] = "Selecione"  # Inicializa com "Selecione"

                for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
                    if subitem not in st.session_state.respostas:
                        st.session_state.respostas[subitem] = "Selecione"  # Inicializa com "Selecione"

                # Dividindo as perguntas em blocos de 10
                subitens = list(perguntas_hierarquicas[grupo]["subitens"].items())
                blocos = [subitens[i:i + 10] for i in range(0, len(subitens), 10)]

                for idx, bloco in enumerate(blocos):
                    with st.expander(f"Bloco {idx + 1} de perguntas"):
                        for subitem, subpergunta in bloco:
                            if subitem in perguntas_obrigatorias:
                                pergunta_label = f"**:red[{subitem} - {subpergunta}]** (OBRIGATÓRIO)"  # Destaca em vermelho
                            else:
                                pergunta_label = f"{subitem} - {subpergunta}"

                            resposta = st.selectbox(
                                pergunta_label,
                                options=list(mapeamento_respostas.keys()),
                                index=list(mapeamento_respostas.keys()).index(st.session_state.respostas[subitem])
                            )
                            st.session_state.respostas[subitem] = resposta

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Voltar"):
                        if st.session_state.grupo_atual > 0:
                            st.session_state.grupo_atual -= 1
                            st.session_state.mostrar_graficos = False
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

                        if not todas_obrigatorias_preenchidas:
                            st.error(f"Por favor, responda todas as perguntas obrigatórias deste grupo antes de prosseguir: {', '.join(obrigatorias_no_grupo)}")
                        else:
                            # Avança para o próximo grupo
                            st.session_state.grupo_atual += 1
                            st.session_state.mostrar_graficos = False
                            st.success("Você avançou para o próximo grupo.")
                with col3:
                    if st.button("Gerar Gráficos"):
                        st.session_state.mostrar_graficos = True

                if st.session_state.mostrar_graficos:
                    fig_original, fig_normalizado = gerar_graficos_radar(perguntas_hierarquicas, st.session_state.respostas)
                    
                    if fig_original and fig_normalizado:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(fig_original, use_container_width=True)
                        with col2:
                            st.plotly_chart(fig_normalizado, use_container_width=True)
                        
                        # Adicionar botão "EXPORTAR"
                        if st.button("EXPORTAR"):
                            excel_data = exportar_graficos_e_respostas(
                                st.session_state.respostas,
                                perguntas_hierarquicas,
                                categorias[:-1],
                                valores[:-1],
                                valores_normalizados[:-1],
                                fig_original,
                                fig_normalizado
                            )
                            st.download_button(
                                label="Baixar Questionário e Gráficos",
                                data=excel_data,
                                file_name="questionario_e_graficos.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                        
                        # Calcular e exibir o nível atual apenas para o grupo atual
                        grupo_atual = grupos[st.session_state.grupo_atual]
                        respostas_numericas = {k: mapeamento_respostas[v] for k, v in st.session_state.respostas.items()}
                        soma_respostas = sum(respostas_numericas[subitem] for subitem in perguntas_hierarquicas[grupo_atual]["subitens"].keys())
                        num_perguntas = len(perguntas_hierarquicas[grupo_atual]["subitens"])
                        if num_perguntas > 0:
                            valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
                            mostrar_nivel_atual_por_grupo(grupo_atual, valor_percentual)
            else:
                st.write("### Todas as perguntas foram respondidas!")
                if st.button("Gerar Gráfico Final"):
                    # Verifica se todas as perguntas obrigatórias foram respondidas
                    todas_obrigatorias_respondidas = True
                    obrigatorias_nao_respondidas = []
                    
                    for pergunta in perguntas_obrigatorias:
                        if pergunta not in st.session_state.respostas or st.session_state.respostas.get(pergunta, "Selecione") == "Selecione":
                            todas_obrigatorias_respondidas = False
                            obrigatorias_nao_respondidas.append(pergunta)
                    
                    # Verifica se todos os grupos obrigatórios foram completamente respondidos
                    grupos_obrigatorios_completos = True
                    grupos_incompletos = []
                    
                    for grupo_obrigatorio in grupos_obrigatorios:
                        if grupo_obrigatorio in perguntas_hierarquicas:
                            for subitem in perguntas_hierarquicas[grupo_obrigatorio]["subitens"].keys():
                                if subitem not in st.session_state.respostas or st.session_state.respostas.get(subitem, "Selecione") == "Selecione":
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
                        # Adicionando logs para depuração
                        try:
                            respostas = {k: mapeamento_respostas.get(v, 0) for k, v in st.session_state.respostas.items()}
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
                                    
                                    # Mostrar nível de maturidade completo
                                    mostrar_nivel_maturidade(total_porcentagem)
                                    
                                    excel_data = exportar_para_excel_completo(st.session_state.respostas, perguntas_hierarquicas, categorias[:-1], valores[:-1], valores_normalizados[:-1])
                                    st.download_button(
                                        label="Exportar para Excel",
                                        data=excel_data,
                                        file_name="respostas_e_grafico.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    )
                        except KeyError as e:
                            st.error(f"Erro ao acessar chave inexistente: {e}")
                            st.write("Estado atual das respostas:", st.session_state.respostas)
                            st.write("Perguntas obrigatórias:", perguntas_obrigatorias)
                            st.write("Perguntas hierárquicas:", perguntas_hierarquicas)
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")

# Garantir que perguntas_hierarquicas esteja definido
if 'perguntas_hierarquicas' not in locals():
    perguntas_hierarquicas = {}

# Garantir que perguntas_obrigatorias esteja definido
if 'perguntas_obrigatorias' not in locals():
    perguntas_obrigatorias = []

# Garantir que todas as perguntas obrigatórias sejam inicializadas no dicionário de respostas
for grupo, conteudo in perguntas_hierarquicas.items():
    for subitem in conteudo["subitens"].keys():
        if subitem not in st.session_state.respostas:
            st.session_state.respostas[subitem] = "Selecione"  # Inicializa com "Selecione"

# Adicionando verificações para evitar erros ao acessar chaves inexistentes
try:
    respostas = {k: mapeamento_respostas.get(v, 0) for k, v in st.session_state.respostas.items()}
except KeyError as e:
    st.error(f"Erro ao acessar chave inexistente: {e}")
    st.write("Estado atual das respostas:", st.session_state.respostas)
    st.write("Perguntas hierárquicas:", perguntas_hierarquicas)
    st.stop()

# Verificar se todas as perguntas obrigatórias estão presentes no dicionário de respostas
for pergunta in perguntas_obrigatorias:
    if pergunta not in st.session_state.respostas:
        st.session_state.respostas[pergunta] = "Selecione"  # Inicializa com "Selecione"
