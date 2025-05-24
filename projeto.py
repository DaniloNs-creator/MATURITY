import pandas as pd
import os
import streamlit as st
from streamlit.components.v1 import html
import glob
import time
import io
from pathlib import Path

# Configuração da página para remover a barra lateral
st.set_page_config(
    page_title="Consolidador de Planilhas",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado com animações e efeitos profissionais
custom_css = """
<style>
[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="collapsedControl"] {
    display: none !important;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
    70% { box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
    100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}

body {
    background: linear-gradient(270deg, #e8f5e9, #c8e6c9, #a5d6a7, #81c784);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
}

.stApp {
    background-color: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
    padding: 2.5rem;
    max-width: 850px;
    margin: 2rem auto;
    border: 1px solid rgba(255, 255, 255, 0.3);
    animation: float 6s ease-in-out infinite;
}

.stButton>button {
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
    color: white;
    border: none;
    padding: 18px 36px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 18px;
    margin: 8px 0;
    cursor: pointer;
    border-radius: 30px;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 6px 12px rgba(46, 125, 50, 0.3);
    font-weight: 600;
    width: 100%;
    max-width: 350px;
    position: relative;
    overflow: hidden;
    text-transform: uppercase;
    letter-spacing: 1px;
    z-index: 1;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #43A047 0%, #1B5E20 100%);
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 12px 20px rgba(46, 125, 50, 0.4);
    animation: pulse 1.5s infinite;
}

.stButton>button:active {
    transform: translateY(2px) scale(0.98);
    box-shadow: 0 4px 8px rgba(46, 125, 50, 0.4);
    transition: all 0.1s;
}

.stButton>button:after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
    z-index: -1;
}

.stButton>button:focus:not(:active)::after {
    animation: ripple 1s ease-out;
}

@keyframes ripple {
    0% {
        transform: scale(0, 0);
        opacity: 0.5;
    }
    100% {
        transform: scale(50, 50);
        opacity: 0;
    }
}

.stButton>button::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    z-index: -2;
    background: linear-gradient(135deg, #4CAF50, #81C784, #A5D6A7, #C8E6C9);
    background-size: 400%;
    border-radius: 32px;
    opacity: 0;
    transition: 0.5s;
}

.stButton>button:hover::before {
    opacity: 1;
    animation: gradientBG 3s linear infinite;
}

.title {
    color: #2E7D32;
    text-align: center;
    margin-bottom: 2.5rem;
    font-weight: 800;
    font-size: 2.5rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    position: relative;
    display: inline-block;
    width: 100%;
}

.title::after {
    content: '';
    display: block;
    width: 100px;
    height: 4px;
    background: linear-gradient(90deg, #4CAF50, transparent);
    margin: 10px auto;
    border-radius: 2px;
}

.success-message {
    background: linear-gradient(135deg, rgba(200, 230, 201, 0.9), rgba(165, 214, 167, 0.9));
    color: #1B5E20;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-top: 1.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-left: 5px solid #2E7D32;
    animation: slideIn 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
    transform-origin: top center;
}

@keyframes slideIn {
    0% {
        opacity: 0;
        transform: perspective(500px) rotateX(-30deg) translateY(-20px);
    }
    100% {
        opacity: 1;
        transform: perspective(500px) rotateX(0deg) translateY(0);
    }
}

.card {
    transition: all 0.3s ease;
    cursor: pointer;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}

.stSpinner>div>div {
    border-color: #4CAF50 transparent transparent transparent !important;
}

.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 200px;
    background-color: #2E7D32;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 14px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}

.progress-container {
    width: 100%;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    margin-top: 10px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #81C784);
    border-radius: 3px;
    width: 0%;
    transition: width 0.3s ease;
    animation: progressAnimation 2s ease-in-out infinite;
}

@keyframes progressAnimation {
    0% { width: 0%; }
    50% { width: 100%; }
    100% { width: 0%; left: 100%; }
}

.button-loading .progress-container {
    display: block;
}

.button-loading button {
    pointer-events: none;
    opacity: 0.8;
}

.button-to-progress {
    transition: all 0.5s ease;
    height: 60px;
    padding: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.button-to-progress::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
    width: var(--progress-width, 0%);
    transition: width 0.3s ease;
}

.button-to-progress span {
    position: relative;
    z-index: 1;
    color: white;
}

.btn-extrair {
    background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%) !important;
    box-shadow: 0 6px 12px rgba(230, 74, 25, 0.3) !important;
}

.btn-extrair:hover {
    background: linear-gradient(135deg, #F4511E 0%, #D84315 100%) !important;
    box-shadow: 0 12px 20px rgba(230, 74, 25, 0.4) !important;
}

@media (max-width: 768px) {
    .stApp {
        padding: 1.5rem;
        margin: 1rem;
        border-radius: 15px;
    }
    
    .title {
        font-size: 2rem;
    }
    
    .stButton>button {
        padding: 15px 30px;
        font-size: 16px;
    }
}

.contas-sem-depara-info {
    background: rgba(255, 243, 224, 0.8);
    border-left: 4px solid #FF9800;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin: 1.5rem 0;
    font-size: 0.95rem;
}
</style>
"""

# Função para obter o caminho da pasta Documents do usuário
def get_user_documents_path():
    return str(Path.home() / "Documents")

# Função para ler arquivos de uma pasta
def ler_arquivos_pasta(pasta, extensoes=['*.xlsx', '*.xls', '*.csv']):
    arquivos = []
    for ext in extensoes:
        arquivos.extend(glob.glob(os.path.join(pasta, ext)))
    return arquivos

# Função para criar um arquivo Excel em memória
def criar_excel_em_memoria(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Contas sem depara')
    output.seek(0)
    return output

# Função para processar as planilhas
def processar_planilhas(progress_bar, button_placeholder):
    try:
        # Obter o caminho da pasta Documents do usuário
        documents_path = get_user_documents_path()
        
        # Caminhos das pastas
        import_path = os.path.join(documents_path, 'import')
        import2_path = os.path.join(documents_path, 'import2')
        download_path = os.path.join(documents_path, 'download')
        
        # Atualizar progresso
        progress_bar.progress(5, text="Criando pasta de destino...")
        time.sleep(0.5)
        
        # Criar pasta download se não existir
        os.makedirs(download_path, exist_ok=True)
        
        # Verificar se as pastas existem
        if not os.path.exists(import_path):
            st.error(f"Pasta não encontrada: {import_path}")
            return None, None
        if not os.path.exists(import2_path):
            st.error(f"Pasta não encontrada: {import2_path}")
            return None, None
        
        progress_bar.progress(15, text="Lendo arquivos da pasta import...")
        time.sleep(0.5)
        
        # Ler arquivos da pasta import
        import_files = ler_arquivos_pasta(import_path)
        if not import_files:
            st.error(f"Nenhuma planilha encontrada na pasta: {import_path}")
            return None, None
        
        # Ler e concatenar todas as planilhas da pasta import
        dfs_import = []
        total_files = len(import_files)
        
        for i, filename in enumerate(import_files):
            try:
                progress_percent = 15 + int((i / total_files) * 30)
                progress_bar.progress(progress_percent, text=f"Processando arquivo {i+1} de {total_files}...")
                
                if filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                else:
                    df = pd.read_excel(filename)
                
                # Verificar se as colunas necessárias existem
                required_cols = ['Data', 'conta', 'valor', 'valor2']
                if not all(col in df.columns for col in required_cols):
                    st.warning(f"Arquivo {os.path.basename(filename)} não contém todas as colunas necessárias {required_cols}")
                    continue
                
                dfs_import.append(df[required_cols])
            except Exception as e:
                st.warning(f"Erro ao ler arquivo {filename}: {str(e)}")
                continue
        
        if not dfs_import:
            st.error("Nenhum arquivo válido encontrado na pasta import")
            return None, None
        
        progress_bar.progress(50, text="Concatenando dados...")
        time.sleep(0.5)
        
        df_import = pd.concat(dfs_import, ignore_index=True)
        
        progress_bar.progress(60, text="Lendo arquivos da pasta import2...")
        time.sleep(0.5)
        
        # Ler arquivos da pasta import2
        import2_files = ler_arquivos_pasta(import2_path)
        if not import2_files:
            st.error(f"Nenhuma planilha encontrada na pasta: {import2_path}")
            return None, None
        
        # Ler a primeira planilha encontrada na pasta import2
        filename = import2_files[0]
        try:
            if filename.endswith('.csv'):
                df_import2 = pd.read_csv(filename)
            else:
                df_import2 = pd.read_excel(filename)
        except Exception as e:
            st.error(f"Erro ao ler arquivo {filename}: {str(e)}")
            return None, None
        
        # Verificar se as colunas necessárias existem
        if not all(col in df_import2.columns for col in ['conta', 'conta contabil']):
            st.error(f"Arquivo {os.path.basename(filename)} não contém as colunas necessárias ('conta', 'conta contabil')")
            return None, None
        
        progress_bar.progress(70, text="Mesclando dados...")
        time.sleep(0.5)
        
        # Fazer o merge das planilhas
        df_final = pd.merge(
            df_import,
            df_import2[['conta', 'conta contabil']],
            on='conta',
            how='left'
        )
        
        # Criar dataframe com contas sem depara (NAN)
        contas_sem_depara = df_final[df_final['conta contabil'].isna()].copy()
        contas_sem_depara = contas_sem_depara[['conta', 'Data', 'valor', 'valor2']]
        contas_sem_depara = contas_sem_depara.drop_duplicates(subset=['conta'])
        
        progress_bar.progress(80, text="Processando colunas...")
        time.sleep(0.5)
        
        # Selecionar e renomear colunas
        df_final = df_final[['Data', 'conta contabil', 'valor', 'valor2']]
        df_final.columns = ['Data', 'conta contabil', 'valor', 'valor2']
        
        # Remover os pontos da coluna 'conta contabil'
        df_final['conta contabil'] = df_final['conta contabil'].astype(str).str.replace('.', '', regex=False)
        
        # Remover linhas com conta contabil vazia
        df_final = df_final.dropna(subset=['conta contabil'])
        
        progress_bar.progress(90, text="Salvando arquivos...")
        time.sleep(0.5)
        
        # Salvar a planilha consolidada em arquivos de 1000 linhas cada
        total_linhas = len(df_final)
        num_arquivos = (total_linhas // 1000) + (1 if total_linhas % 1000 != 0 else 0)
        
        for i in range(num_arquivos):
            inicio = i * 1000
            fim = (i + 1) * 1000
            parte = df_final.iloc[inicio:fim]
            
            output_path = os.path.join(download_path, f"planilha_consolidada_parte_{i+1}.xlsx")
            parte.to_excel(output_path, index=False)
        
        progress_bar.progress(100, text="Processamento concluído!")
        time.sleep(0.5)
        
        success_message = f"""
        <div class="success-message">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <h3 style="margin-top: 10px; margin-bottom: 5px;">Processamento concluído com sucesso!</h3>
            <p style="margin: 5px 0;">Total de linhas processadas: <strong>{total_linhas}</strong></p>
            <p style="margin: 5px 0;">Arquivos gerados: <strong>{num_arquivos}</strong></p>
            <p style="margin: 5px 0;">Salvo em: <strong>{download_path}</strong></p>
        </div>
        """
        st.markdown(success_message, unsafe_allow_html=True)
        
        # Restaurar o botão original após a conclusão
        with button_placeholder:
            if st.button('🚀 INICIAR PROCESSAMENTO', key='importar_again', help="Clique para importar e consolidar as planilhas"):
                st.session_state.processing = True
        
        return df_final, contas_sem_depara
        
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")
        progress_bar.empty()
        # Restaurar o botão original em caso de erro
        with button_placeholder:
            if st.button('🚀 INICIAR PROCESSAMENTO', key='importar_again', help="Clique para importar e consolidar as planilhas"):
                st.session_state.processing = True
        return None, None

# Interface do aplicativo
def main():
    # Aplicar o CSS
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Título do aplicativo
    st.markdown('<h1 class="title">📊 Importador de Lançamentos DOMINIO</h1>', unsafe_allow_html=True)
    
    # Descrição
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2.5rem; color: #455A64; font-size: 1.1rem; line-height: 1.6;">
        Esta ferramenta consolida automaticamente planilhas de diferentes formatos<br>
        em um único arquivo padronizado para análise.
    </div>
    """, unsafe_allow_html=True)
    
    # Container principal com efeito de card
    with st.container():
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); border-radius: 15px; padding: 2rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
            <h3 style="color: #2E7D32; text-align: center; margin-bottom: 1.5rem;">Instruções</h3>
            <ol style="color: #455A64; padding-left: 1.5rem;">
                <li style="margin-bottom: 0.5rem;">Certifique-se que os arquivos estão nas pastas corretas (Documents/import e Documents/import2)</li>
                <li style="margin-bottom: 0.5rem;">Clique no botão abaixo para iniciar o processamento</li>
                <li style="margin-bottom: 0.5rem;">Aguarde até a conclusão do processo</li>
                <li>Os arquivos consolidados serão salvos automaticamente na pasta Documents/download</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Espaçamento
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Botão centralizado com efeitos especiais
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        button_placeholder = st.empty()
        
        if 'processing' not in st.session_state:
            st.session_state.processing = False
            st.session_state.contas_sem_depara = None
        
        if not st.session_state.processing:
            if button_placeholder.button('🚀 INICIAR PROCESSAMENTO', key='importar', help="Clique para importar e consolidar as planilhas"):
                st.session_state.processing = True
                st.rerun()
        else:
            # Criar uma barra de progresso
            progress_bar = st.progress(0, text="Preparando para processar...")
            
            # Chamar a função de processamento com a barra de progresso
            df_final, contas_sem_depara = processar_planilhas(progress_bar, button_placeholder)
            
            # Armazenar contas sem depara na sessão
            if contas_sem_depara is not None:
                st.session_state.contas_sem_depara = contas_sem_depara
            
            # Remover a barra de progresso após um breve delay
            time.sleep(1)
            progress_bar.empty()
            st.session_state.processing = False
    
    # Seção para extrair contas sem depara (sem mostrar a tabela)
    if st.session_state.get('contas_sem_depara') is not None and not st.session_state.contas_sem_depara.empty:
        st.markdown("---")
        
        num_contas_sem_depara = len(st.session_state.contas_sem_depara)
        
        # Mensagem informativa sobre contas sem depara
        st.markdown(f"""
        <div class="contas-sem-depara-info">
            <strong>⚠️ Foram encontradas {num_contas_sem_depara} contas sem correspondência no depara.</strong><br>
            Você pode baixar a lista completa clicando no botão abaixo.
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para baixar contas sem depara
        excel_file = criar_excel_em_memoria(st.session_state.contas_sem_depara)
        st.download_button(
            label="📥 EXTRAIR CONTAS SEM DEPARA",
            data=excel_file,
            file_name="contas_sem_depara.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download_contas_sem_depara',
            help="Clique para baixar todas as contas que não foram encontradas no depara",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
