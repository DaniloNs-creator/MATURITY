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

# URL DA NOVA LOGO
LOGO_URL = "https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/Branco%2C%20azul%20e%20perna%20cinza.png"

st.set_page_config(page_title="Maturity Reali Consultoria", layout='wide', page_icon="⚖️")

# CSS MESCLADO
st.markdown("""
<style>
    /* Animação para todos os botões */
    .stButton>button {
        transition: all 0.3s ease;
        transform: scale(1);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    button[kind="primary"] {
        background-color: #4CAF50;
        color: white;
        border: none;
        animation: pulse 2s infinite;
    }
    button[kind="primary"]:hover {
        background-color: #45a049;
        animation: none;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0F172A;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff, #f1f5f9);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

mapeamento_respostas = {
    "Selecione": 0,
    "Não Possui": 1,
    "Insatisfatório": 2,
    "Controlado": 3,
    "Eficiente": 4,
    "Otimizado": 5
}

try:
    import kaleido
except ImportError:
    st.error("O pacote 'kaleido' é necessário. Instale: pip install -U kaleido")
    st.stop()

def salvar_respostas(nome, email, respostas):
    try:
        dados = {"nome": nome, "email": email, "respostas": respostas}
        with open(f"respostas_{email}.json", "w") as arquivo:
            json.dump(dados, arquivo)
        st.success("Progresso salvo!")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

def carregar_respostas(email):
    try:
        with open(f"respostas_{email}.json", "r") as arquivo:
            dados = json.load(arquivo)
        return dados.get("respostas", {})
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def exportar_questionario(respostas, perguntas_hierarquicas):
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            resposta = respostas.get(subitem, "Selecione")
            if resposta != "Selecione":
                linhas.append({"Pergunta": subpergunta, "Resposta": resposta})
    df_respostas = pd.DataFrame(linhas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Questionário')
    return output.getvalue()

def enviar_email(destinatario, arquivo_questionario, fig_original, fig_normalizado):
    try:
        servidor_smtp = st.secrets["email_config"]["servidor_smtp"]
        porta = st.secrets["email_config"]["porta"]
        user = st.secrets["email_config"]["user"]
        senha = st.secrets["email_config"]["senha"]
        remetente = st.secrets["email_config"]["email"]

        destinatarios = [destinatario, "profile@realiconsultoria.com.br"]
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = ", ".join(destinatarios)
        msg['Subject'] = "Relatório de Maturidade - Reali Consultoria"

        corpo = f"<h3>Olá {st.session_state.nome},</h3><p>Segue em anexo o seu diagnóstico de maturidade.</p>"
        msg.attach(MIMEText(corpo, 'html'))

        anexo = MIMEBase('application', 'octet-stream')
        anexo.set_payload(arquivo_questionario)
        encoders.encode_base64(anexo)
        anexo.add_header('Content-Disposition', 'attachment; filename="diagnostico.xlsx"')
        msg.attach(anexo)

        with smtplib.SMTP(servidor_smtp, porta) as server:
            server.starttls()
            server.login(user, senha)
            server.sendmail(remetente, destinatarios, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

def gerar_graficos_radar(perguntas_hierarquicas, respostas):
    respostas_numericas = {k: mapeamento_respostas[v] for k, v in respostas.items()}
    categorias = []
    valores = []
    valores_normalizados = []
    
    for item, conteudo in perguntas_hierarquicas.items():
        soma_respostas = sum(respostas_numericas.get(subitem, 0) for subitem in conteudo["subitens"].keys())
        num_perguntas = len(conteudo["subitens"])
        if num_perguntas > 0:
            vp = (soma_respostas / (num_perguntas * 5)) * 100
            categorias.append(conteudo["titulo"])
            valores.append(vp)
            valores_normalizados.append(100 if vp > 0 else 0)

    fig_original = go.Figure(data=go.Scatterpolar(r=valores + valores[:1], theta=categorias + categorias[:1], fill='toself'))
    fig_original.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Nível de Maturidade Atual")
    
    fig_norm = go.Figure(data=go.Scatterpolar(r=valores_normalizados + valores_normalizados[:1], theta=categorias + categorias[:1], fill='toself'))
    fig_norm.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Gráfico Normalizado")
    
    return fig_original, fig_norm

def exibir_tabela_niveis_maturidade(nivel_atual):
    niveis = [
        {"Nível": "INICIAL", "Descrição": "Processos desestruturados e reativos."},
        {"Nível": "ORGANIZAÇÃO", "Descrição": "Processos básicos iniciando documentação."},
        {"Nível": "CONSOLIDAÇÃO", "Descrição": "Processos formalmente documentados."},
        {"Nível": "OTIMIZAÇÃO", "Descrição": "Processos integrados e gerenciados com métricas."},
        {"Nível": "EXCELÊNCIA", "Descrição": "Cultura de melhoria contínua e inovação."}
    ]
    for n in niveis: n["Atual"] = "✔️" if n["Nível"] == nivel_atual else ""
    st.table(pd.DataFrame(niveis))

def mostrar_nivel_atual_por_grupo(grupo, valor_percentual):
    if valor_percentual < 26: nivel = "INICIAL"
    elif valor_percentual < 51: nivel = "ORGANIZAÇÃO"
    elif valor_percentual < 71: nivel = "CONSOLIDAÇÃO"
    elif valor_percentual < 90: nivel = "OTIMIZAÇÃO"
    else: nivel = "EXCELÊNCIA"
    st.info(f"Nível no grupo {grupo}: {nivel}")
    exibir_tabela_niveis_maturidade(nivel)

# Inicialização de Session State
if "formulario_preenchido" not in st.session_state: st.session_state.formulario_preenchido = False
if "grupo_atual" not in st.session_state: st.session_state.grupo_atual = 0
if "respostas" not in st.session_state: st.session_state.respostas = {}
if "app_selecionado" not in st.session_state: st.session_state.app_selecionado = None
if "mostrar_graficos" not in st.session_state: st.session_state.mostrar_graficos = False

# --- TELA DE LOGIN ---
if not st.session_state.formulario_preenchido:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(LOGO_URL, width=300)
        st.header("DIAGNÓSTICO DE GESTÃO, GOVERNANÇA E CONTROLES")
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        empresa = st.text_input("Empresa")
        telefone = st.text_input("Telefone")
        if st.button("Prosseguir"):
            if nome and email and empresa and telefone:
                st.session_state.nome, st.session_state.email = nome, email
                st.session_state.formulario_preenchido = True
                st.session_state.respostas = carregar_respostas(email)
                st.rerun()
            else:
                st.error("Preencha todos os campos.")
    with col2:
        st.image("https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/foto.jpg", use_container_width=True)

# --- MENU HUB ---
elif st.session_state.app_selecionado is None:
    st.markdown("<h2 style='text-align: center;'>Selecione a Ferramenta:</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("📋 Diagnóstico de Maturidade", use_container_width=True, type="primary"):
        st.session_state.app_selecionado = "diagnostico"
        st.rerun()
    if c2.button("💎 CFO & CEO | Estrutura de Capital", use_container_width=True, type="primary"):
        st.session_state.app_selecionado = "fpa"
        st.rerun()

# --- APP 1: DIAGNÓSTICO ---
elif st.session_state.app_selecionado == "diagnostico":
    if st.button("⬅️ Menu Principal"):
        st.session_state.app_selecionado = None
        st.rerun()

    url_arquivo = "https://raw.githubusercontent.com/DaniloNs-creator/MATURITY/main/FOMULARIO.txt"
    try:
        resp = requests.get(url_arquivo)
        lines = resp.text.splitlines()
        data = []
        g_atual = None
        for l in lines:
            p = l.strip().split(';')
            if len(p) >= 2:
                if p[0].strip().isdigit(): g_atual = f"{p[0].strip()} - {p[1].strip()}"
                else: data.append({'grupo': g_atual, 'classe': p[0].strip(), 'pergunta': p[1].strip()})
        
        df = pd.DataFrame(data)
        perguntas_hierarquicas = {}
        for _, r in df.iterrows():
            if r['grupo'] not in perguntas_hierarquicas:
                perguntas_hierarquicas[r['grupo']] = {"titulo": r['grupo'], "subitens": {}}
            perguntas_hierarquicas[r['grupo']]["subitens"][str(r['classe'])] = r['pergunta']

        grupos = list(perguntas_hierarquicas.keys())

        with st.sidebar:
            st.image(LOGO_URL)
            st.title("Navegação")
            for i, g in enumerate(grupos):
                if st.button(g): 
                    st.session_state.grupo_atual = i
                    st.session_state.mostrar_graficos = False

        idx = st.session_state.grupo_atual
        if idx < len(grupos):
            gnome = grupos[idx]
            st.subheader(gnome)
            for sid, sperg in perguntas_hierarquicas[gnome]["subitens"].items():
                if sid not in st.session_state.respostas: st.session_state.respostas[sid] = "Selecione"
                st.session_state.respostas[sid] = st.selectbox(f"{sid} - {sperg}", options=list(mapeamento_respostas.keys()), index=list(mapeamento_respostas.keys()).index(st.session_state.respostas[sid]))

            c1, c2, c3 = st.columns(3)
            if c1.button("⬅️ Anterior") and idx > 0: 
                st.session_state.grupo_atual -= 1
                st.rerun()
            if c2.button("Próximo ➡️") and idx < len(grupos)-1: 
                st.session_state.grupo_atual += 1
                st.rerun()
            if c3.button("📊 Gerar e Enviar"):
                fig1, fig2 = gerar_graficos_radar(perguntas_hierarquicas, st.session_state.respostas)
                excel = exportar_questionario(st.session_state.respostas, perguntas_hierarquicas)
                if enviar_email(st.session_state.email, excel, fig1, fig2):
                    st.success("Enviado!")
                st.session_state.mostrar_graficos = True
                st.plotly_chart(fig1)

    except Exception as e:
        st.error(f"Erro ao carregar formulário: {e}")

# --- APP 2: FP&A ---
elif st.session_state.app_selecionado == "fpa":
    if st.button("⬅️ Menu Principal"):
        st.session_state.app_selecionado = None
        st.rerun()
    
    # ALTERAÇÃO DE TEXTO AQUI
    st.markdown('<div class="main-title">MATURITY ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">CFO & CEO | Painel Executivo (FP&A)</div>', unsafe_allow_html=True)
    
    aba1, aba2 = st.tabs(["📈 KPIs", "💎 EBITDA"])
    with aba1:
        st.header("Liquidez")
        ac = st.number_input("Ativo Circulante", value=0.0)
        pc = st.number_input("Passivo Circulante", value=1.0) # Evitar div zero
        st.metric("Liquidez Corrente", f"{ac/pc:.2f}x")
    with aba2:
        st.header("Cálculo EBITDA")
        ll = st.number_input("Lucro Líquido", value=0.0)
        da = st.number_input("Depreciação", value=0.0)
        st.metric("EBITDA", f"R$ {ll + da:,.2f}")

    st.markdown("<br><center><img src='" + LOGO_URL + "' width='150'></center>", unsafe_allow_html=True)
