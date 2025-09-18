import streamlit as st
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Formulário de Desligamento",
    layout="wide"
)

# --- Main Application ---
st.title("Formulário de Solicitação de Desligamento")

# Using a form to group all the widgets
with st.form("desligamento_form"):
    
    # --- Section: Uso do Solicitante ---
    st.header("Uso do Solicitante")
    
    # Row 1
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Empresa/Posto", value="CORREIOS")
    with col2:
        st.text_input("Diretoria/Gerência Solicitante", value="CAMBÉ")
    with col3:
        st.text_input("Área / Centro custo", value="19.980.000.003")

    # Row 2
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Nome do Colaborador", value="ADRIANA MARTINS DE OLIVEIRA")
    with col2:
        st.text_input("Cargo", value="AUXILIAR OPERACIONAL")
    with col3:
        st.text_input("Chapa", value="007529")

    # Row 3
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Preposto")
    with col2:
        st.checkbox("Portador de Deficiência")

    st.divider()

    # --- Section: Motivo e Aviso Prévio ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Motivo do Desligamento")
        motivo = st.radio(
            "Selecione o motivo:",
            ["Sem justa causa", "Com justa causa", "Pedido de demissão", "Período de Experiência"],
            index=2,
            label_visibility="collapsed"
        )

    with col2:
        st.subheader("Aviso Prévio")
        aviso = st.radio(
            "Selecione o tipo de aviso:",
            ["Aviso prévio indenizado", "Aviso prévio trabalhado", "Pedido dispensa do aviso"],
            index=1,
            label_visibility="collapsed"
        )
        data_aviso = st.date_input("Início do aviso", value=datetime.date(2025, 8, 2))
        
    st.divider()

    # --- Section: Informação sobre Débitos ---
    st.header("Informação sobre Débitos")

    # Uniforme
    st.write("**Uniforme**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox("N/A")
    with col2:
        st.checkbox("Devolvido (ficha anexa)")
    with col3:
        desconto_uniforme = st.text_input("Descontar R$", key="uniforme_desconto")

    # Crachá
    st.write("**Crachá**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox("Devolvido", key="cracha_dev")
    with col2:
        st.checkbox("Não devolvido", key="cracha_nao_dev")
    with col3:
        desconto_cracha = st.text_input("Descontar R$", key="cracha_desconto")

    # Cartão Bancário
    st.write("**Cartão Bancário**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox("Devolvido", key="cartao_dev")
    with col2:
        st.checkbox("Não devolvido", key="cartao_nao_dev")
    with col3:
        desconto_cartao = st.text_input("Descontar R$", key="cartao_desconto")

    # Cartão de Ponto
    st.write("**Cartão de Ponto**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.checkbox("Anexo")
    with col2:
        st.checkbox("No final do contrato")
    with col3:
        st.checkbox("Ocorrências")
    with col4:
        st.checkbox("ver obs.")

    st.divider()

    # --- Section: Uso do Departamento de Pessoal ---
    st.header("Uso do Departamento de Pessoal")
    
    col1, col2 = st.columns(2)
    with col1:
        autorizado = st.radio("Desligamento autorizado", ["Sim", "Não"])
    
    with col2:
        st.write("**Estabilidade por:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.checkbox("CIPA")
            st.checkbox("Acidente Trabalho")
        with c2:
            st.checkbox("Férias")
            st.checkbox("Auxílio Doença")
        with c3:
            st.checkbox("Aposentadoria")
            st.checkbox("Convenção / Retenção")

    st.divider()
    
    # --- Section: Aprovações ---
    st.header("Aprovações")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.subheader("Supervisor")
        st.text_input("Nome", value="Camila", key="sup_nome")
        st.text_area("Rubrica", height=50, key="sup_rubrica", placeholder="Assinatura")
        st.date_input("Data", value=datetime.date(2025, 8, 5), key="sup_data")
    with col2:
        st.subheader("Coordenador(a)")
        st.text_input("Nome", key="coord_nome")
        st.text_area("Rubrica", height=50, key="coord_rubrica", placeholder="Assinatura")
        st.date_input("Data", key="coord_data")
    with col3:
        st.subheader("Superintendente")
        st.text_input("Nome", key="super_nome")
        st.text_area("Rubrica", height=50, key="super_rubrica", placeholder="Assinatura")
        st.date_input("Data", key="super_data")
    with col4:
        st.subheader("Diretoria")
        st.text_input("Nome", key="dir_nome")
        st.text_area("Rubrica", height=50, key="dir_rubrica", placeholder="Assinatura")
        st.date_input("Data", key="dir_data")
    with col5:
        st.subheader("Colaborador")
        st.text_input("Nome", key="colab_nome")
        st.text_area("Rubrica", height=50, key="colab_rubrica", placeholder="Assinatura")
        st.date_input("Data", key="colab_data")
        
    st.divider()

    # --- Footer and Submit Button ---
    st.text("RE,DP.0020- (PO,DP.0019)")
    
    submitted = st.form_submit_button("Enviar Formulário")
    if submitted:
        st.success("Formulário de desligamento enviado com sucesso!")

