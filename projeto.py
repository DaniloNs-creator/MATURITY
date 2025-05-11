import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests
import plotly.graph_objects as go
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json

# Configuração da página com layout amplo e ícone
st.set_page_config(page_title="Maturity Reali Consultoria", layout='wide', page_icon="⚖️")

# CSS personalizado para animações e estilos
st.markdown("""
<style>
    /* Estilos gerais */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f8f9fa;
    }
    
    /* Cabeçalho personalizado */
    .header {
        background: linear-gradient(135deg, #2c3e50, #3498db);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Cards de perguntas */
    .question-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border-left: 4px solid #3498db;
    }
    
    .question-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    /* Botões principais */
    .stButton>button {
        border: none;
        border-radius: 25px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    
    /* Botão primário */
    button[kind="primary"] {
        background: linear-gradient(135deg, #3498db, #2c3e50);
        color: white;
        animation: pulse 2s infinite;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2c3e50, #3498db);
        animation: none;
    }
    
    /* Botão secundário */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        color: #2c3e50;
    }
    
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #e9ecef, #dee2e6);
    }
    
    /* Botão de enviar email */
    .stButton>button:contains("ENVIAR POR EMAIL") {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
    }
    
    .stButton>button:contains("ENVIAR POR EMAIL"):hover {
        background: linear-gradient(135deg, #c0392b, #e74c3c);
    }
    
    /* Botão de salvar progresso */
    .stButton>button:contains("Salvar Progresso") {
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        color: white;
    }
    
    .stButton>button:contains("Salvar Progresso"):hover {
        background: linear-gradient(135deg, #27ae60, #2ecc71);
    }
    
    /* Sidebar estilizada */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50, #34495e);
        color: white;
    }
    
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        margin-bottom: 0.5rem;
        text-align: left;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        background: rgba(255,255,255,0.1);
        color: white;
        border: none;
    }
    
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255,255,255,0.2);
    }
    
    [data-testid="stSidebar"] .stButton>button[aria-pressed="true"] {
        background: linear-gradient(135deg, #3498db, #2980b9) !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* Tabs na sidebar */
    [data-testid="stSidebar"] .stTabs [role="tab"] {
        color: white;
        padding: 0.5rem 1rem;
    }
    
    [data-testid="stSidebar"] .stTabs [role="tab"][aria-selected="true"] {
        background: rgba(255,255,255,0.2);
        border-radius: 6px;
    }
    
    /* Animações */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out forwards;
    }
    
    /* Alertas personalizados */
    .stAlert {
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* Gráficos */
    .stPlotlyChart {
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        background: white;
        padding: 1rem;
    }
    
    /* Tabelas */
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* Texto de destaque */
    .highlight {
        background: linear-gradient(90deg, rgba(52,152,219,0.2), transparent);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .header h1 {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Mapeamento das respostas de texto para valores numéricos
mapeamento_respostas = {
    "Selecione": 0,
    "Não Possui": 1,
    "Insatisfatório": 2,
    "Controlado": 3,
    "Eficiente": 4,
    "Otimizado": 5
}

# Verificar se o pacote kaleido está instalado
try:
    import kaleido
except ImportError:
    st.error("O pacote 'kaleido' é necessário para exportar gráficos como imagens. Por favor, instale-o executando: pip install -U kaleido")
    st.stop()

# Função para salvar respostas no arquivo
def salvar_respostas(nome, email, respostas):
    try:
        dados = {"nome": nome, "email": email, "respostas": respostas}
        with open(f"respostas_{email}.json", "w") as arquivo:
            json.dump(dados, arquivo)
        st.success("Respostas salvas com sucesso! Você pode continuar mais tarde.")
    except Exception as e:
        st.error(f"Erro ao salvar respostas: {e}")

# Função para carregar respostas do arquivo
def carregar_respostas(email):
    try:
        with open(f"respostas_{email}.json", "r") as arquivo:
            dados = json.load(arquivo)
        return dados.get("respostas", {})
    except FileNotFoundError:
        st.warning("Nenhum progresso salvo encontrado para este e-mail.")
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar respostas: {e}")
        return {}

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

def exportar_questionario(respostas, perguntas_hierarquicas):
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            linhas.append({"Pergunta": subpergunta, "Resposta": respostas[subitem]})

    df_respostas = pd.DataFrame(linhas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Questionário')
    return output.getvalue()

def enviar_email(destinatario, arquivo_questionario, fig_original, fig_normalizado):
    servidor_smtp = "smtplw.com.br"
    porta = 587
    user = "reali14"
    senha = "Profile8464Rea"
    remetente = "profile@realiconsultoria.com.br"

    destinatarios = [destinatario, "sousadanilo601@outlook.com"]

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = "Relatório de Análise"

    grupo_atual_nome = grupos[st.session_state.grupo_atual]
    respostas_numericas = {k: mapeamento_respostas[v] for k, v in st.session_state.respostas.items()}
    soma_respostas = sum(respostas_numericas[subitem] for subitem in perguntas_hierarquicas[grupo_atual_nome]["subitens"].keys())
    num_perguntas = len(perguntas_hierarquicas[grupo_atual_nome]["subitens"])
    if num_perguntas > 0:
        valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
        nivel_atual = ""
        if valor_percentual < 26:
            nivel_atual = "INICIAL"
        elif valor_percentual < 51:
            nivel_atual = "ORGANIZAÇÃO"
        elif valor_percentual < 71:
            nivel_atual = "CONSOLIDAÇÃO"
        elif valor_percentual < 90:
            nivel_atual = "OTIMIZAÇÃO"
        elif valor_percentual >= 91:
            nivel_atual = "EXCELÊNCIA"

        proximos_blocos = grupos[st.session_state.grupo_atual + 1:] if st.session_state.grupo_atual + 1 < len(grupos) else []
        proximos_blocos_texto = ", ".join(proximos_blocos) if proximos_blocos else "Nenhum bloco restante."

        tabela_html = """
        <table border="1" style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left;">Nível</th>
                    <th style="padding: 8px; text-align: left;">Descrição</th>
                    <th style="padding: 8px; text-align: center;">Atual</th>
                </tr>
            </thead>
            <tbody>
        """
        
        niveis = [
            {"Nível": "INICIAL", "Descrição": "A organização opera de forma desestruturada, sem processos claramente definidos ou formalizados...", "Atual": "✔️" if nivel_atual == "INICIAL" else ""},
            {"Nível": "ORGANIZAÇÃO", "Descrição": "A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada...", "Atual": "✔️" if nivel_atual == "ORGANIZAÇÃO" else ""},
            {"Nível": "CONSOLIDAÇÃO", "Descrição": "Os processos são formalmente documentados e seguidos de maneira estruturada...", "Atual": "✔️" if nivel_atual == "CONSOLIDAÇÃO" else ""},
            {"Nível": "OTIMIZAÇÃO", "Descrição": "Os processos estão plenamente integrados e gerenciados de maneira eficiente...", "Atual": "✔️" if nivel_atual == "OTIMIZAÇÃO" else ""},
            {"Nível": "EXCELÊNCIA", "Descrição": "A organização alcança um nível de referência, caracterizado por uma cultura de melhoria contínua e inovação...", "Atual": "✔️" if nivel_atual == "EXCELÊNCIA" else ""}
        ]
        
        for nivel in niveis:
            tabela_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{nivel['Nível']}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{nivel['Descrição']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{nivel['Atual']}</td>
                </tr>
            """
        
        tabela_html += """
            </tbody>
        </table>
        """

        corpo = f"""
        <p>Prezado(a) {st.session_state.nome},</p>
        <p>Segue abaixo os gráficos de radar gerados pela Matriz de Maturidade:</p>
        <p><b>Gráfico de Radar - Nível Atual:</b></p>
        <img src="cid:fig_original" alt="Gráfico Original" style="width:600px;">
        <p><b>Gráfico de Radar - Normalizado:</b></p>
        <img src="cid:fig_normalizado" alt="Gráfico Normalizado" style="width:600px;">
        <p>Em anexo, você encontrará o questionário preenchido.</p>
        <hr>
        <h3>Relatório de Progresso</h3>
        <p>Você completou o Bloco <b>{grupo_atual_nome}</b>. Os resultados indicam que o seu nível de maturidade neste bloco é classificado como: <b>{nivel_atual}</b>.</p>
        <p>Para aprofundarmos a análise e oferecermos insights mais estratégicos, recomendamos que você complete também:</p>
        <p><b>{proximos_blocos_texto}</b></p>
        
        <h3>Trilha de Níveis de Maturidade</h3>
        {tabela_html}
        
        <p>Nossos consultores especializados receberão este relatório e entrarão em contato para agendar uma discussão personalizada. Juntos, identificaremos oportunidades de melhoria e traçaremos os próximos passos para otimizar os processos da sua organização.</p>
        """
        msg.attach(MIMEText(corpo, 'html'))

    anexo = MIMEBase('application', 'octet-stream')
    anexo.set_payload(arquivo_questionario)
    encoders.encode_base64(anexo)
    anexo.add_header('Content-Disposition', f'attachment; filename="questionario_preenchido.xlsx"')
    msg.attach(anexo)

    try:
        if fig_original is not None:
            img_original = BytesIO()
            fig_original.write_image(img_original, format="png", engine="kaleido")
            img_original.seek(0)
            img_original_mime = MIMEBase('image', 'png', filename="grafico_original.png")
            img_original_mime.set_payload(img_original.read())
            encoders.encode_base64(img_original_mime)
            img_original_mime.add_header('Content-ID', '<fig_original>')
            img_original_mime.add_header('Content-Disposition', 'inline', filename="grafico_original.png")
            msg.attach(img_original_mime)
        else:
            raise ValueError("Gráfico Original não foi gerado.")

        if fig_normalizado is not None:
            img_normalizado = BytesIO()
            fig_normalizado.write_image(img_normalizado, format="png", engine="kaleido")
            img_normalizado.seek(0)
            img_normalizado_mime = MIMEBase('image', 'png', filename="grafico_normalizado.png")
            img_normalizado_mime.set_payload(img_normalizado.read())
            encoders.encode_base64(img_normalizado_mime)
            img_normalizado_mime.add_header('Content-ID', '<fig_normalizado>')
            img_normalizado_mime.add_header('Content-Disposition', 'inline', filename="grafico_normalizado.png")
            msg.attach(img_normalizado_mime)
        else:
            raise ValueError("Gráfico Normalizado não foi gerado.")
    except Exception as e:
        st.error(f"Erro ao gerar imagens dos gráficos: {e}")
        return False

    try:
        with smtplib.SMTP(servidor_smtp, porta) as server:
            server.set_debuglevel(1)
            server.ehlo()
            server.starttls()
            server.login(user, senha)
            server.sendmail(remetente, destinatarios, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError as e:
        st.error(f"Erro de autenticação: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Erro detalhado: {str(e)}")
        return False

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
        name='Gráfico Original',
        fillcolor='rgba(52, 152, 219, 0.6)',
        line=dict(color='rgba(52, 152, 219, 1)')
    ))
    fig_original.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Gráfico de Radar - Nível Atual",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Gráfico Normalizado
    valores_normalizados_fechado = valores_normalizados + valores_normalizados[:1]
    fig_normalizado = go.Figure()
    fig_normalizado.add_trace(go.Scatterpolar(
        r=valores_normalizados_fechado,
        theta=categorias_original,
        fill='toself',
        name='Gráfico Normalizado',
        fillcolor='rgba(46, 204, 113, 0.6)',
        line=dict(color='rgba(46, 204, 113, 1)')
    ))
    fig_normalizado.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Gráfico de Radar - Normalizado",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_original, fig_normalizado

def exibir_tabela_niveis_maturidade(nivel_atual):
    niveis = [
        {
            "Nível": "INICIAL",
            "Descrição": (
                "A organização opera de forma desestruturada, sem processos claramente definidos ou formalizados. "
                "As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, "
                "tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada. "
                "A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais "
                "e elevado risco de não conformidade regulatória."
            )
        },
        {
            "Nível": "ORGANIZAÇÃO",
            "Descrição": (
                "A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada. "
                "Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência "
                "na execução continue limitada. As atividades ainda dependem fortemente da experiência individual, e a governança sobre "
                "os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos."
            )
        },
        {
            "Nível": "CONSOLIDAÇÃO",
            "Descrição": (
                "Os processos são formalmente documentados e seguidos de maneira estruturada. Existe uma clareza maior sobre as responsabilidades "
                "e papéis, o que reduz a dependência do conhecimento individual. A implementação de controles internos começa a ganhar robustez, "
                "permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas. Indicadores de desempenho são introduzidos, permitindo "
                "um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento."
            )
        },
        {
            "Nível": "OTIMIZAÇÃO",
            "Descrição": (
                "Os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho. "
                "A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades. "
                "A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional. "
                "O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo."
            )
        },
        {
            "Nível": "EXCELÊNCIA",
            "Descrição": (
                "A organização alcança um nível de referência, caracterizado por uma cultura de melhoria contínua e inovação. Os processos são constantemente "
                "avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico. Há uma integração "
                "plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório. "
                "O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor."
            )
        }
    ]
    
    for nivel in niveis:
        nivel["Atual"] = "✔️" if nivel["Nível"] == nivel_atual else ""

    df_niveis = pd.DataFrame(niveis)
    df_niveis = df_niveis.reset_index(drop=True)
    styled_table = df_niveis.style.set_properties(
        **{'font-size': '10px', 'white-space': 'nowrap'}, subset=['Nível']
    ).set_properties(
        **{'background-color': '#f8f9fa'}, subset=pd.IndexSlice[df_niveis[df_niveis['Atual'] == '✔️'].index, :]
    )

    st.write("### Trilha de Níveis de Maturidade")
    st.table(styled_table)

def mostrar_nivel_maturidade(total_porcentagem):
    if total_porcentagem < 26:
        nivel_atual = "INICIAL"
        st.warning("SEU NÍVEL ATUAL É: INICIAL")
        st.info("""
        **NIVEL DE MATURIDADE INICIAL:** 
        Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados. 
        As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada. 
        A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
        """)
    elif total_porcentagem < 51:
        nivel_atual = "ORGANIZAÇÃO"
        st.warning("SEU NÍVEL ATUAL É: ORGANIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:** 
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada. 
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada. 
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif total_porcentagem < 71:
        nivel_atual = "CONSOLIDAÇÃO"
        st.warning("SEU NÍVEL ATUAL É: CONSOLIDAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:** 
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada. 
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual. 
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas. 
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif total_porcentagem < 90:
        nivel_atual = "OTIMIZAÇÃO"
        st.warning("SEU NÍVEL ATUAL É: OTIMIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:** 
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho. 
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades. 
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional. 
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif total_porcentagem >= 91:
        nivel_atual = "EXCELÊNCIA"
        st.success("SEU NÍVEL ATUAL É: EXCELÊNCIA")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:** 
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação. 
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico. 
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório. 
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)
    
    exibir_tabela_niveis_maturidade(nivel_atual)

def mostrar_nivel_atual_por_grupo(grupo, valor_percentual):
    if valor_percentual < 26:
        nivel_atual = "INICIAL"
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: INICIAL")
        st.info("""
        **NIVEL DE MATURIDADE INICIAL:**
        Neste estágio, a organização opera de forma desestruturada, sem processos claramente definidos ou formalizados.
        As atividades são executadas de maneira reativa, sem padronização ou diretrizes estabelecidas, tornando a execução dependente do conhecimento tácito de indivíduos, em vez de uma abordagem institucionalizada.
        A ausência de controle efetivo e a inexistência de mecanismos de monitoramento resultam em vulnerabilidades operacionais e elevado risco de não conformidade regulatória.
        """)
    elif valor_percentual < 51:
        nivel_atual = "ORGANIZAÇÃO"
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: ORGANIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:**
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada.
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada.
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif valor_percentual < 71:
        nivel_atual = "CONSOLIDAÇÃO"
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: CONSOLIDAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:**
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada.
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual.
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas.
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif valor_percentual < 90:
        nivel_atual = "OTIMIZAÇÃO"
        st.warning(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: OTIMIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:**
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho.
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades.
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional.
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif valor_percentual >= 91:
        nivel_atual = "EXCELÊNCIA"
        st.success(f"SEU NÍVEL ATUAL NO GRUPO '{grupo}' É: EXCELÊNCIA")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:**
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação.
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico.
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório.
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)
    
    exibir_tabela_niveis_maturidade(nivel_atual)

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
        st.warning("SEU NÍVEL ATUAL É: ORGANIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE ORGANIZAÇÃO:**
        A organização começa a estabelecer processos básicos, ainda que de maneira incipiente e pouco estruturada.
        Algumas diretrizes são documentadas e há um esforço para replicar práticas em diferentes áreas, embora a consistência na execução continue limitada.
        As atividades ainda dependem fortemente da experiência individual, e a governança sobre os processos é mínima, resultando em baixa previsibilidade e dificuldade na identificação e mitigação de riscos sistêmicos.
        """)
    elif soma_percentual < 71:
        st.warning("SEU NÍVEL ATUAL É: CONSOLIDAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE CONSOLIDAÇÃO:**
        A organização atinge um nível de maturidade em que os processos são formalmente documentados e seguidos de maneira estruturada.
        Existe uma clareza maior sobre as responsabilidades e papéis, o que reduz a dependência do conhecimento individual.
        A implementação de controles internos começa a ganhar robustez, permitindo um maior alinhamento com as diretrizes regulatórias e estratégicas.
        Indicadores de desempenho são introduzidos, permitindo um acompanhamento inicial da eficácia operacional, embora a cultura de melhoria contínua ainda esteja em desenvolvimento.
        """)
    elif soma_percentual < 90:
        st.warning("SEU NÍVEL ATUAL É: OTIMIZAÇÃO")
        st.info("""
        **NIVEL DE MATURIDADE OTIMIZAÇÃO:**
        Neste estágio, os processos estão plenamente integrados e gerenciados de maneira eficiente, com monitoramento contínuo e análise sistemática de desempenho.
        A organização adota mecanismos formais de governança e controle, utilizando métricas para avaliação e aprimoramento das atividades.
        A mitigação de riscos torna-se mais eficaz, com a implementação de políticas proativas para conformidade regulatória e excelência operacional.
        O aprendizado organizacional é fomentado, garantindo a adaptação rápida a mudanças no ambiente interno e externo.
        """)
    elif soma_percentual >= 91:
        st.success("SEU NÍVEL ATUAL É: EXCELÊNCIA")
        st.info("""
        **NIVEL DE MATURIDADE EXCELÊNCIA:**
        A organização alcança um nível de maturidade de referência, caracterizado por uma cultura de melhoria contínua e inovação.
        Os processos são constantemente avaliados e aprimorados com base em análise de dados e benchmarking, garantindo máxima eficiência e alinhamento estratégico.
        Há uma integração plena entre tecnologia, governança e gestão de riscos, promovendo uma operação resiliente e altamente adaptável às mudanças do mercado e do cenário regulatório.
        O comprometimento com a excelência e a sustentabilidade impulsiona a organização a atuar como referência no setor.
        """)

# Inicialização do estado da sessão
if "formulario_preenchido" not in st.session_state:
    st.session_state.formulario_preenchido = False
if "grupo_atual" not in st.session_state:
    st.session_state.grupo_atual = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}
if "mostrar_graficos" not in st.session_state:
    st.session_state.mostrar_graficos = False

# Inicializar as variáveis fig_original e fig_normalizado para evitar erros
fig_original = None
fig_normalizado = None

if not st.session_state.formulario_preenchido:
    # Layout do formulário inicial
    st.markdown("""
    <div class="header">
        <h1>DIAGNÓSTICO DE GESTÃO, GOVERNANÇA E CONTROLES</h1>
        <p>Preencha suas informações abaixo para iniciar o diagnóstico</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/logo.png", width=300)
        
        with st.form("form_inicial"):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            empresa = st.text_input("Empresa")
            telefone = st.text_input("Telefone")
            
            if st.form_submit_button("Prosseguir"):
                if nome and email and empresa and telefone:
                    st.session_state.nome = nome
                    st.session_state.email = email
                    st.session_state.empresa = empresa
                    st.session_state.telefone = telefone
                    st.session_state.formulario_preenchido = True
                    st.session_state.respostas = carregar_respostas(email)
                    st.success("Informações preenchidas com sucesso! Você pode prosseguir para o questionário.")
                else:
                    st.error("Por favor, preencha todos os campos antes de prosseguir.")

        st.markdown("""
        <div class="highlight">
            <h4>Como funciona o diagnóstico:</h4>
            <p>Esta ferramenta avalia o nível de maturidade da sua empresa em três dimensões estratégicas:</p>
            <ul>
                <li><strong>Gestão</strong>: Estrutura organizacional e eficiência financeira</li>
                <li><strong>Governança</strong>: Processos, riscos, compliance e canal de denúncias</li>
                <li><strong>Áreas Operacionais</strong>: RH, TI, Compras, Estoques, Contabilidade e Logística</li>
            </ul>
            <p>A análise integrada desses aspectos permitirá identificar pontos fortes e oportunidades de melhoria.</p>
        </div>
        """, unsafe_allow_html=True)
            
    with col2:
        st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/foto.jpg", use_container_width=True)
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
            
            # Sidebar com navegação
            with st.sidebar:
                st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/logo.png")
                st.title("Navegação por Grupos")
                
                tab1, tab2, tab3 = st.tabs(["GESTÃO", "GOVERNANÇA", "SETORES"])
                
                with tab1:
                    if st.button("**Estruturas**" if st.session_state.grupo_atual == 1 else "Estruturas"):
                        st.session_state.grupo_atual = 1
                    if st.button("**Eficiência de Gestão**" if st.session_state.grupo_atual == 0 else "Eficiência de Gestão"):
                        st.session_state.grupo_atual = 0
                
                with tab2:
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
                
                with tab3:
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

                st.markdown("""
                <div style="margin-top: 2rem; font-size: 0.9rem; color: #95a5a6;">
                    <p><strong>Recomendação:</strong> Inicie pela aba 'Gestão', depois 'Governança' e finalmente 'Setores' para uma análise mais eficiente.</p>
                    <p>Você também pode navegar diretamente para qualquer área específica conforme suas prioridades.</p>
                </div>
                """, unsafe_allow_html=True)

            grupo_atual = st.session_state.grupo_atual

            # Textos introdutórios para cada grupo
            TEXTO_GRUPO1 = """
            <div class="highlight">
                <h4>Gestão Financeira</h4>
                <p>O preenchimento desta matriz é essencial para avaliar a eficiência dos processos financeiros, identificar lacunas e estruturar um plano de melhoria contínua. Ela permite medir o nível de controle sobre orçamento, fluxo de caixa, investimentos e riscos, fornecendo uma visão clara da saúde financeira da empresa.</p>
            </div>
            """
            TEXTO_GRUPO2 = """
            <div class="highlight">
                <h4>Estrutura Organizacional</h4>
                <p>A avaliação da maturidade da estrutura de uma organização é um processo essencial para entender o nível de desenvolvimento e a eficácia das práticas de governança, gestão de riscos, compliance e processos organizacionais.</p>
            </div>
            """
            TEXTO_GRUPO3 = """
            <div class="highlight">
                <h4>Compliance</h4>
                <p>O preenchimento desta seção permite avaliar a maturidade do programa de Compliance, garantindo que a organização esteja em conformidade com regulamentações e boas práticas éticas. Ajuda a prevenir riscos legais e fortalecer a cultura organizacional.</p>
            </div>
            """
            TEXTO_GRUPO4 = """
            <div class="highlight">
                <h4>Gestão de Riscos</h4>
                <p>Responder a estas perguntas auxilia na identificação, monitoramento e mitigação de riscos que podem impactar a operação. Com uma gestão de riscos eficiente, a empresa minimiza perdas e melhora a tomada de decisão.</p>
            </div>
            """
            TEXTO_GRUPO5 = """
            <div class="highlight">
                <h4>Gestão de Processos</h4>
                <p>Esta seção permite avaliar a eficiência e a padronização dos processos internos. Um bom gerenciamento de processos melhora a produtividade, reduz desperdícios e assegura entregas consistentes.</p>
            </div>
            """
            TEXTO_GRUPO6 = """
            <div class="highlight">
                <h4>Governança Corporativa</h4>
                <p>A governança bem estruturada assegura transparência, ética e eficiência na gestão da empresa. Com este diagnóstico, é possível fortalecer a tomada de decisão e alinhar os interesses das partes interessadas.</p>
            </div>
            """
            TEXTO_GRUPO7 = """
            <div class="highlight">
                <h4>Recursos Humanos</h4>
                <p>Esta seção mede a maturidade da gestão de pessoas, garantindo que a empresa valorize seus colaboradores e mantenha um ambiente produtivo e inclusivo.</p>
            </div>
            """
            TEXTO_GRUPO8 = """
            <div class="highlight">
                <h4>Tecnologia da Informação</h4>
                <p>Responder a estas perguntas ajuda a avaliar o nível de digitalização e segurança da empresa. Uma TI bem estruturada melhora a eficiência operacional e protege dados sensíveis.</p>
            </div>
            """
            TEXTO_GRUPO9 = """
            <div class="highlight">
                <h4>Controle Financeiro</h4>
                <p>Esta seção permite identificar boas práticas e oportunidades de melhoria na gestão financeira. Com um controle eficiente, a empresa assegura sustentabilidade e reduz riscos.</p>
            </div>
            """
            TEXTO_GRUPO10 = """
            <div class="highlight">
                <h4>Compras</h4>
                <p>O diagnóstico nesta área assegura que as compras sejam estratégicas, alinhadas às necessidades da empresa e aos melhores preços e prazos.</p>
            </div>
            """
            TEXTO_GRUPO11 = """
            <div class="highlight">
                <h4>Estoques</h4>
                <p>Avaliar a gestão de estoques permite reduzir desperdícios, evitar faltas e garantir uma operação eficiente.</p>
            </div>
            """
            TEXTO_GRUPO12 = """
            <div class="highlight">
                <h4>Logística</h4>
                <p>Responder a estas perguntas possibilita otimizar a cadeia logística, garantindo entregas ágeis e redução de custos operacionais.</p>
            </div>
            """
            TEXTO_GRUPO13 = """
            <div class="highlight">
                <h4>Contabilidade</h4>
                <p>Esta seção avalia a transparência e conformidade da contabilidade empresarial. Um controle rigoroso das demonstrações financeiras assegura a correta apuração de resultados.</p>
            </div>
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

            # Grupos obrigatórios
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
                    st.markdown(TEXTO_GRUPO1, unsafe_allow_html=True)
                elif grupo.startswith("2 -"):
                    st.markdown(TEXTO_GRUPO2, unsafe_allow_html=True)
                elif grupo.startswith("3 -"):
                    st.markdown(TEXTO_GRUPO3, unsafe_allow_html=True)
                elif grupo.startswith("4 -"):
                    st.markdown(TEXTO_GRUPO4, unsafe_allow_html=True)
                elif grupo.startswith("5 -"):
                    st.markdown(TEXTO_GRUPO5, unsafe_allow_html=True)
                elif grupo.startswith("6 -"):
                    st.markdown(TEXTO_GRUPO6, unsafe_allow_html=True)
                elif grupo.startswith("7 -"):
                    st.markdown(TEXTO_GRUPO7, unsafe_allow_html=True)
                elif grupo.startswith("8 -"):
                    st.markdown(TEXTO_GRUPO8, unsafe_allow_html=True)
                elif grupo.startswith("9 -"):
                    st.markdown(TEXTO_GRUPO9, unsafe_allow_html=True)
                elif grupo.startswith("10 -"):
                    st.markdown(TEXTO_GRUPO10, unsafe_allow_html=True)
                elif grupo.startswith("11 -"):
                    st.markdown(TEXTO_GRUPO11, unsafe_allow_html=True)
                elif grupo.startswith("12 -"):
                    st.markdown(TEXTO_GRUPO12, unsafe_allow_html=True)
                elif grupo.startswith("13 -"):
                    st.markdown(TEXTO_GRUPO13, unsafe_allow_html=True)

                st.write(f"### {perguntas_hierarquicas[grupo]['titulo']}")
                
                # Inicializa respostas se não existirem
                for subitem in perguntas_hierarquicas[grupo]["subitens"].keys():
                    if subitem not in st.session_state.respostas:
                        st.session_state.respostas[subitem] = "Selecione"

                # Dividindo as perguntas em blocos de 10
                subitens = list(perguntas_hierarquicas[grupo]["subitens"].items())
                blocos = [subitens[i:i + 10] for i in range(0, len(subitens), 10)]

                for idx, bloco in enumerate(blocos):
                    with st.expander(f"Bloco {idx + 1} de perguntas", expanded=idx==0):
                        for subitem, subpergunta in bloco:
                            if subitem in perguntas_obrigatorias:
                                pergunta_label = f"**:red[{subitem} - {subpergunta}]** (OBRIGATÓRIO)"
                            else:
                                pergunta_label = f"{subitem} - {subpergunta}"

                            resposta = st.selectbox(
                                pergunta_label,
                                options=list(mapeamento_respostas.keys()),
                                index=list(mapeamento_respostas.keys()).index(st.session_state.respostas[subitem])
                            )
                            st.session_state.respostas[subitem] = resposta

                # Botões de navegação
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Voltar", key="voltar"):
                        if st.session_state.grupo_atual > 0:
                            st.session_state.grupo_atual -= 1
                            st.session_state.mostrar_graficos = False
                            st.rerun()
                with col2:
                    if st.button("Prosseguir", key="prosseguir"):
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
                            st.session_state.grupo_atual += 1
                            st.session_state.mostrar_graficos = False
                            st.success("Você avançou para o próximo grupo.")
                            st.rerun()
                with col3:
                    if st.button("Salvar Progresso", key="salvar"):
                        salvar_respostas(st.session_state.nome, st.session_state.email, st.session_state.respostas)
                    
                    if st.button("Gerar Gráficos", key="graficos"):
                        st.session_state.mostrar_graficos = True
                        st.rerun()

                    if st.session_state.mostrar_graficos:
                        fig_original, fig_normalizado = gerar_graficos_radar(perguntas_hierarquicas, st.session_state.respostas)
                        if fig_original is None or fig_normalizado is None:
                            st.error("Os gráficos não foram gerados corretamente. Verifique os dados de entrada.")
                        else:
                            if st.button("ENVIAR POR EMAIL", key="email"):
                                excel_data = exportar_questionario(st.session_state.respostas, perguntas_hierarquicas)
                                if enviar_email(st.session_state.email, excel_data, fig_original, fig_normalizado):
                                    st.success("Relatório enviado com sucesso para o email informado!")

                if st.session_state.mostrar_graficos:
                    # Mensagem de Relatório de Progresso
                    grupo_atual_nome = grupos[st.session_state.grupo_atual]
                    respostas_numericas = {k: mapeamento_respostas[v] for k, v in st.session_state.respostas.items()}
                    soma_respostas = sum(respostas_numericas[subitem] for subitem in perguntas_hierarquicas[grupo_atual_nome]["subitens"].keys())
                    num_perguntas = len(perguntas_hierarquicas[grupo_atual_nome]["subitens"])
                    if num_perguntas > 0:
                        valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
                        nivel_atual = ""
                        if valor_percentual < 26:
                            nivel_atual = "INICIAL"
                        elif valor_percentual < 51:
                            nivel_atual = "ORGANIZAÇÃO"
                        elif valor_percentual < 71:
                            nivel_atual = "CONSOLIDAÇÃO"
                        elif valor_percentual < 90:
                            nivel_atual = "OTIMIZAÇÃO"
                        elif valor_percentual >= 91:
                            nivel_atual = "EXCELÊNCIA"

                        proximos_blocos = grupos[st.session_state.grupo_atual + 1:] if st.session_state.grupo_atual + 1 < len(grupos) else []
                        proximos_blocos_texto = ", ".join(proximos_blocos) if proximos_blocos else "Nenhum bloco restante."

                        st.markdown(f"""
                        <div class="highlight">
                            <h3>Relatório de Progresso</h3>
                            <p>Você completou o Bloco <strong>{grupo_atual_nome}</strong>. Os resultados indicam que o seu nível de maturidade neste bloco é classificado como: <strong>{nivel_atual}</strong>.</p>
                            <p>Para aprofundarmos a análise e oferecermos insights mais estratégicos, recomendamos que você complete também:</p>
                            <p><strong>{proximos_blocos_texto}</strong></p>
                            <p>Nossos consultores especializados receberão este relatório e entrarão em contato para agendar uma discussão personalizada.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Gerar gráficos
                    fig_original, fig_normalizado = gerar_graficos_radar(perguntas_hierarquicas, st.session_state.respostas)
                    if fig_original and fig_normalizado:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(fig_original, use_container_width=True)
                        with col2:
                            st.plotly_chart(fig_normalizado, use_container_width=True)

                        # Calcular e exibir o nível atual apenas para o grupo atual
                        mostrar_nivel_atual_por_grupo(grupo_atual_nome, valor_percentual)
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
                                        name='Gráfico Original',
                                        fillcolor='rgba(52, 152, 219, 0.6)',
                                        line=dict(color='rgba(52, 152, 219, 1)')
                                    ))
                                    fig_original.update_layout(
                                        polar=dict(
                                            radialaxis=dict(
                                                visible=True,
                                                range=[0, 100]
                                            )),
                                        showlegend=False,
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)'
                                    )
                                    valores_normalizados_fechado = valores_normalizados + valores_normalizados[:1]
                                    fig_normalizado = go.Figure()
                                    fig_normalizado.add_trace(go.Scatterpolar(
                                        r=valores_normalizados_fechado,
                                        theta=categorias_original,
                                        fill='toself',
                                        name='Gráfico Normalizado',
                                        fillcolor='rgba(46, 204, 113, 0.6)',
                                        line=dict(color='rgba(46, 204, 113, 1)')
                                    ))
                                    fig_normalizado.update_layout(
                                        polar=dict(
                                            radialaxis=dict(
                                                visible=True,
                                                range=[0, 100]
                                            )),
                                        showlegend=False,
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)'
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
                                            st.warning("SEU NIVEL É ORGANIZAÇÃO")
                                        elif total_porcentagem < 71:
                                            st.warning("SEU NIVEL É CONSOLIDAÇÃO")
                                        elif total_porcentagem < 90:
                                            st.warning("SEU NIVEL É OTIMIZAÇÃO")
                                        elif total_porcentagem >= 91:
                                            st.success("SEU NIVEL É EXCELÊNCIA")
                                    with col2:
                                        st.plotly_chart(fig_normalizado, use_container_width=True)
                                        st.write("### Gráfico 2")
                                        df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
                                        st.dataframe(df_grafico_normalizado)
                                    
                                    mostrar_nivel_maturidade(total_porcentagem)
                                    
                                    excel_data = exportar_questionario(st.session_state.respostas, perguntas_hierarquicas)
                                    st.download_button(
                                        label="Exportar para Excel",
                                        data=excel_data,
                                        file_name="questionario_preenchido.xlsx",
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
            st.session_state.respostas[subitem] = "Selecione"
