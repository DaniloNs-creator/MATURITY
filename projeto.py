import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import time
import io
import re
import chardet
import traceback
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any, Optional

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Häfele | Data Processor", page_icon="📦", layout="wide")

def apply_custom_ui():
    st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stApp { font-family: 'Inter', sans-serif; }
        .header-container {
            background: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            border-left: 8px solid #0054a6;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .hafele-logo { max-width: 200px; margin-bottom: 1rem; }
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DE PROCESSAMENTO XML (ALTA PERFORMANCE) ---
class HighScaleCTeProcessor:
    """Processador otimizado para lidar com volumes massivos de XML (até 1M)"""
    
    NAMESPACES = {'cte': 'http://www.portalfiscal.inf.br/cte'}
    
    def __init__(self):
        if 'db_cte' not in st.session_state:
            st.session_state.db_cte = pd.DataFrame()

    def fast_extract(self, element, path):
        """Extração rápida com fallback de namespace"""
        try:
            # Tenta com namespace
            found = element.find(f'.//{{{self.NAMESPACES["cte"]}}}{path}')
            if found is None:
                # Tenta sem namespace
                found = element.find(f'.//{path}')
            return found.text if found is not None else ""
        except:
            return ""

    def get_weight_data(self, root):
        """Busca inteligente de peso em múltiplos nós"""
        tipos_peso = ['PESO BRUTO', 'PESO BASE DE CALCULO', 'PESO BASE CÁLCULO', 'PESO']
        
        # Procura em infQ
        for uri in ["", f"{{{self.NAMESPACES['cte']}}}"]:
            for infQ in root.findall(f'.//{uri}infQ'):
                tpMed = infQ.find(f'{uri}tpMed')
                qCarga = infQ.find(f'{uri}qCarga')
                
                if tpMed is not None and qCarga is not None:
                    med_text = tpMed.text.upper() if tpMed.text else ""
                    for t in tipos_peso:
                        if t in med_text:
                            return float(qCarga.text or 0), med_text
        return 0.0, "N/A"

    def process_xml_batch(self, files):
        """Processamento otimizado em lote"""
        data_list = []
        batch_size = 500 # Processa de 500 em 500 para atualizar UI
        
        total_files = len(files)
        progress_bar = st.progress(0)
        status = st.empty()

        for idx, file in enumerate(files):
            try:
                content = file.read()
                root = ET.fromstring(content)
                
                # Dados Básicos
                nCT = self.fast_extract(root, 'nCT')
                dhEmi = self.fast_extract(root, 'dhEmi')
                vTPrest = self.fast_extract(root, 'vTPrest')
                
                # Localidades
                uf_ini = self.fast_extract(root, 'UFIni')
                uf_fim = self.fast_extract(root, 'UFFim')
                
                # Envolvidos
                emit = self.fast_extract(root, 'emit/xNome')
                dest = self.fast_extract(root, 'dest/xNome')
                
                # Peso e Chave
                peso, tipo_p = self.get_weight_data(root)
                chave = self.fast_extract(root, 'infNFe/chave')
                n_nfe = chave[25:34] if len(chave) == 44 else ""

                data_list.append({
                    "nCT": nCT,
                    "Emissao": dhEmi[:10] if dhEmi else "",
                    "Emitente": emit[:30],
                    "Destinatario": dest[:30],
                    "UF_Origem": uf_ini,
                    "UF_Destino": uf_fim,
                    "Peso_KG": peso,
                    "Tipo_Peso": tipo_p,
                    "Valor_Prestacao": float(vTPrest or 0),
                    "NF_Chave": chave,
                    "NF_Numero": n_nfe,
                    "Arquivo": file.name
                })

                if (idx + 1) % batch_size == 0 or (idx + 1) == total_files:
                    progress = (idx + 1) / total_files
                    progress_bar.progress(progress)
                    status.text(f"🚀 Processado: {idx + 1} de {total_files} arquivos...")

            except Exception as e:
                continue # Pula arquivos corrompidos para não parar o lote de 1M

        new_df = pd.DataFrame(data_list)
        st.session_state.db_cte = pd.concat([st.session_state.db_cte, new_df], ignore_index=True)
        return len(new_df)

# --- ENGINE DE TEXTO (OTIMIZADO) ---
class TextProcessor:
    @staticmethod
    def clean_txt(file_content):
        substituicoes = {
            "IMPOSTO IMPORTACAO": "IMP IMPORT",
            "TAXA SICOMEX": "TX SISCOMEX",
            "FRETE INTERNACIONAL": "FRET INTER",
            "SEGURO INTERNACIONAL": "SEG INTERN"
        }
        padroes_remover = ["-------", "SPED EFD-ICMS/IPI"]
        
        # Detecção de encoding
        enc = chardet.detect(file_content[:10000])['encoding'] or 'latin-1'
        texto = file_content.decode(enc)
        
        linhas_finais = []
        for linha in texto.splitlines():
            if not any(p in linha for p in padroes_remover):
                temp = linha
                for k, v in substituicoes.items():
                    temp = temp.replace(k, v)
                linhas_finais.append(temp)
        
        return "\n".join(linhas_finais)

# --- INTERFACE PRINCIPAL ---
def main():
    apply_custom_ui()
    
    # Header Häfele Style
    st.markdown(f"""
    <div class="header-container">
        <img src="https://raw.githubusercontent.com/DaniloNs-creator/final/7ea6ab2a610ef8f0c11be3c34f046e7ff2cdfc6a/haefele_logo.png" class="hafele-logo">
        <h1>Sistema Integrado de Processamento</h1>
        <p>TXT Clean & Ultra-Scale XML CTe (Otimizado para 1.000.000+ registros)</p>
    </div>
    """, unsafe_allow_html=True)

    tab_cte, tab_txt = st.tabs(["🚚 Processamento Massivo CT-e", "📄 Limpeza de Arquivos TXT"])

    # --- ABA CT-E ---
    with tab_cte:
        proc = HighScaleCTeProcessor()
        
        col_up, col_stats = st.columns([1, 2])
        
        with col_up:
            st.subheader("Upload de Lote")
            files = st.file_uploader("Arraste milhares de XMLs aqui", type="xml", accept_multiple_files=True)
            if st.button("🚀 Iniciar Processamento de Lote"):
                if files:
                    start_time = time.time()
                    count = proc.process_xml_batch(files)
                    duration = time.time() - start_time
                    st.success(f"Finalizado! {count} arquivos processados em {duration:.2f}s")
                else:
                    st.warning("Selecione os arquivos primeiro.")

        # Dashboard de Dados
        if not st.session_state.db_cte.empty:
            df = st.session_state.db_cte
            
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total CT-e", f"{len(df):,}")
            c2.metric("Peso Total (T)", f"{df['Peso_KG'].sum()/1000:,.2f}")
            c3.metric("Valor Total", f"R$ {df['Valor_Prestacao'].sum():,.2f}")
            c4.metric("Ticket Médio", f"R$ {df['Valor_Prestacao'].mean():,.2f}")

            st.subheader("Visualização dos Dados")
            st.dataframe(df.head(100), use_container_width=True) # Mostra apenas 100 para não travar a UI
            
            # Exportação Otimizada
            st.subheader("Exportar Base Completa")
            export_format = st.selectbox("Formato", ["Excel", "CSV"])
            
            if export_format == "Excel":
                # Para 1M de linhas, o Excel tem limite de 1.048.576. 
                # Se passar disso, sugerimos CSV.
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Baixar Excel Completo", buffer.getvalue(), "base_cte.xlsx")
            else:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar CSV Completo", csv, "base_cte.csv")
            
            if st.button("🗑️ Resetar Banco de Dados"):
                st.session_state.db_cte = pd.DataFrame()
                st.rerun()

    # --- ABA TXT ---
    with tab_txt:
        st.subheader("Limpeza de Arquivos Sped/TXT")
        txt_file = st.file_uploader("Upload arquivo TXT", type="txt")
        
        if txt_file:
            if st.button("🪄 Limpar e Processar TXT"):
                content = txt_file.read()
                cleaned = TextProcessor.clean_txt(content)
                
                st.text_area("Prévia do Resultado", cleaned[:1000], height=200)
                
                st.download_button(
                    label="📥 Baixar TXT Processado",
                    data=cleaned,
                    file_name=f"CLEAN_{txt_file.name}",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()
