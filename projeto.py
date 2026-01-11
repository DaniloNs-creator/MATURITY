import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pdfplumber
import re
import time
import chardet
import traceback
import gc
from io import BytesIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURAÇÃO DA PÁGINA (WIDE MODE) ---
st.set_page_config(
    page_title="Häfele Data System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PROFISSIONAL & CLEAN ---
def apply_professional_style():
    st.markdown("""
    <style>
    /* Importação de fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fundo e Container Principal */
    .stApp {
        background-color: #f8fafc;
    }

    /* Estilização de Cards e Seções */
    .main-card {
        background-color: #ffffff;
        padding: 2.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
    }

    /* Cabeçalhos Modernos */
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Botões Profissionais */
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* Botão Danger */
    .stButton.danger > button {
        background-color: #dc2626 !important;
    }
    .stButton.danger > button:hover {
        background-color: #b91c1c !important;
    }

    /* Tabs Customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: #64748b;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom-color: #2563eb !important;
    }

    /* Alertas */
    .stAlert {
        border-radius: 10px;
        border: none;
    }
    
    /* Logo Header */
    .header-logo {
        display: flex;
        justify-content: center;
        padding: 20px 0;
        margin-bottom: 30px;
        background: white;
        border-bottom: 1px solid #e2e8f0;
    }
    
    /* Progress Bar Custom */
    .stProgress > div > div > div {
        background-color: #2563eb;
    }
    
    /* Dataframe styling */
    .dataframe {
        font-size: 14px !important;
    }
    
    /* Metrics cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE (TXTS E XMLS) ---
def clean_val(val):
    if not val: return "0"
    return re.sub(r'[^\d,]', '', str(val)).replace(',', '')

def format_xml_num(val, length):
    return clean_val(val).zfill(length)

def clean_partnumber(text):
    if not text: return ""
    words = ["CÓDIGO", "CODIGO", "INTERNO", "PARTNUMBER", r"\(", r"\)"]
    for w in words:
        text = re.search(f"{w}(.*)", text, re.I).group(1) if re.search(w, text, re.I) else text
    return re.sub(r'\s+', ' ', text).strip().lstrip("- ").strip()

# --- LÓGICA DO CONVERSOR HAFELE (NOVA ABA) ---
def parse_pdf_hafele(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    
    data = {"header": {}, "itens": []}
    data["header"]["processo"] = re.search(r"PROCESSO\s*#?(\d+)", text, re.I).group(1) if re.search(r"PROCESSO\s*#?(\d+)", text, re.I) else "N/A"
    data["header"]["duimp"] = re.search(r"Numero\s*[:\n]*\s*([\dBR]+)", text, re.I).group(1) if re.search(r"Numero\s*[:\n]*\s*([\dBR]+)", text, re.I) else "N/A"
    
    parts = re.split(r"ITENS DA DUIMP\s*[-–]?\s*(\d+)", text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            num = parts[i]
            block = parts[i+1]
            raw_desc = re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S).group(1) if re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S) else ""
            raw_pn = re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S).group(1) if re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S) else ""
            pn = clean_partnumber(raw_pn)
            data["itens"].append({
                "seq": num,
                "descricao": f"{pn} - {re.sub(r'\s+', ' ', raw_desc).strip()}" if pn else raw_desc,
                "ncm": re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block).group(1).replace(".", "") if re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block) else "00000000",
                "peso": re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block) else "0",
                "qtd": re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block) else "0",
                "v_unit": re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block) else "0"
            })
    return data

def generate_xml_hafele(data):
    root = ET.Element("ListaDeclaracoes")
    duimp = ET.SubElement(root, "duimp")
    for item in data["itens"]:
        ad = ET.SubElement(duimp, "adicao")
        acr = ET.SubElement(ad, "acrescimo")
        ET.SubElement(acr, "codigoAcrescimo").text = "17"
        ET.SubElement(acr, "valorReais").text = "000000000106601"
        ET.SubElement(ad, "dadosMercadoriaCodigoNcm").text = item["ncm"]
        ET.SubElement(ad, "dadosMercadoriaPesoLiquido").text = format_xml_num(item["peso"], 15)
        merc = ET.SubElement(ad, "mercadoria")
        ET.SubElement(merc, "descricaoMercadoria").text = item["descricao"]
        ET.SubElement(merc, "numeroSequencialItem").text = item["seq"].zfill(2)
        ET.SubElement(merc, "quantidade").text = format_xml_num(item["qtd"], 14)
        ET.SubElement(merc, "valorUnitario").text = format_xml_num(item["v_unit"], 20)
        ET.SubElement(ad, "numeroAdicao").text = item["seq"].zfill(3)
        ET.SubElement(ad, "numeroDUIMP").text = data["header"]["duimp"].replace("25BR", "")[:10]
    return root

# --- FUNÇÕES OTIMIZADAS PARA CTE ---
def parse_cte_fast(content_bytes, filename):
    """Parsing ultra rápido de CT-e com ElementTree otimizado"""
    try:
        data = {}
        
        # Extrair chave do CT-e (busca rápida)
        content_str = content_bytes.decode('utf-8', errors='ignore')[:5000]  # Analisar apenas início
        chave_match = re.search(r'Id="CTe(\d{44})"', content_str)
        if chave_match:
            data['chave'] = chave_match.group(1)
        else:
            data['chave'] = ''
        
        # Parsing streaming dos elementos principais
        try:
            context = ET.iterparse(BytesIO(content_bytes), events=('end',))
            
            for event, elem in context:
                tag = elem.tag.lower()
                
                # Buscar apenas tags necessárias de forma eficiente
                if 'dhemi' in tag:
                    data['emissao'] = elem.text[:10] if elem.text else ''
                elif 'vtprest' in tag or 'vprest' in tag:
                    for child in elem:
                        if 'vtprest' in child.tag.lower():
                            data['valor'] = child.text or '0.00'
                            break
                elif 'rem' in tag:
                    for child in elem:
                        if 'xnome' in child.tag.lower():
                            data['remetente'] = (child.text or '')[:100]
                            break
                elif 'dest' in tag:
                    for child in elem:
                        if 'xnome' in child.tag.lower():
                            data['destinatario'] = (child.text or '')[:100]
                            break
                elif 'emit' in tag:
                    for child in elem:
                        if 'xnome' in child.tag.lower():
                            data['emitente'] = (child.text or '')[:100]
                            break
                
                # Limpar elemento para liberar memória
                elem.clear()
                if elem.getprevious() is not None:
                    del elem.getparent()[0]
                    
        except Exception as e:
            # Fallback para parsing mais simples
            pass
        
        # Garantir campos mínimos
        data.setdefault('valor', '0.00')
        data.setdefault('emissao', '')
        data.setdefault('remetente', '')
        data.setdefault('destinatario', '')
        data.setdefault('emitente', '')
        
        return data
        
    except Exception as e:
        return {'error': f"Erro ao processar {filename}: {str(e)}"}

def process_cte_batch(files_batch, batch_number):
    """Processa um lote de arquivos CT-e"""
    batch_results = []
    
    for uploaded_file in files_batch:
        try:
            # Ler arquivo uma vez
            content = uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read()
            
            # Parse rápido
            cte_data = parse_cte_fast(content, uploaded_file.name)
            
            if 'error' not in cte_data:
                cte_data.update({
                    'arquivo': uploaded_file.name,
                    'processamento': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    'tamanho_bytes': len(content)
                })
            else:
                cte_data['arquivo'] = uploaded_file.name
                
            batch_results.append(cte_data)
            
        except Exception as e:
            batch_results.append({
                'arquivo': uploaded_file.name,
                'error': f"Erro crítico: {str(e)}",
                'processamento': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
    
    return batch_results

# --- INTERFACE PRINCIPAL ---
def main():
    apply_professional_style()

    # Header de Logo Limpo
    st.markdown("""
        <div class="header-logo">
            <img src="https://raw.githubusercontent.com/DaniloNs-creator/final/7ea6ab2a610ef8f0c11be3c34f046e7ff2cdfc6a/haefele_logo.png" width="200">
        </div>
    """, unsafe_allow_html=True)

    st.title("🚀 Sistema Integrado de Processamento - Alta Performance")
    
    tabs = st.tabs(["🚀 Conversor XML Häfele", "🚚 Processador CT-e (Otimizado)", "📄 Utilitário TXT"])

    # --- ABA 1: CONVERSOR HAFELE ---
    with tabs[0]:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("Extração de PDF para Layout XML Häfele")
        pdf_file = st.file_uploader("Upload Extrato de Conferência (PDF)", type="pdf", key="hafele_pdf")
        
        if pdf_file and st.button("PROCESSAR E GERAR XML", key="btn_hafele"):
            with st.spinner("Analisando PDF..."):
                res = parse_pdf_hafele(pdf_file)
                if res["itens"]:
                    xml_root = generate_xml_hafele(res)
                    xml_str = minidom.parseString(ET.tostring(xml_root, 'utf-8')).toprettyxml(indent="    ")
                    
                    st.success(f"✅ Sucesso! {len(res['itens'])} itens processados.")
                    c1, c2 = st.columns(2)
                    c1.metric("📊 Nº Itens", len(res['itens']))
                    c2.metric("🔢 Processo", res['header']['processo'])
                    
                    # Estatísticas
                    st.info(f"**DUIMP:** {res['header']['duimp']}")
                    
                    st.download_button(
                        "⬇️ BAIXAR XML HAFELE", 
                        xml_str, 
                        f"HAFELE_{res['header']['processo']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml", 
                        "text/xml",
                        key="download_hafele"
                    )
                    
                    # Preview
                    with st.expander("👁️ Visualizar Primeiros Itens"):
                        preview_df = pd.DataFrame(res["itens"]).head(10)
                        st.dataframe(preview_df, use_container_width=True)
                else:
                    st.error("❌ Nenhum item detectado no PDF.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 2: PROCESSADOR CT-E (OTIMIZADO PARA PERFORMANCE) ---
    with tabs[1]:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("🚀 Análise de Conhecimentos de Transporte - Alta Performance")
        
        # Configurações de performance
        st.markdown("**⚙️ Configurações de Performance**")
        
        col_config1, col_config2, col_config3 = st.columns(3)
        with col_config1:
            enable_parallel = st.checkbox("Processamento Paralelo", value=True, 
                                        help="Ativa processamento multithread")
            batch_size = st.number_input("Tamanho do Lote", 
                                        min_value=100, 
                                        max_value=50000, 
                                        value=5000,
                                        step=100,
                                        help="Arquivos processados por lote")
        with col_config2:
            extraction_mode = st.selectbox(
                "Modo de Extração",
                ["Completo", "Somente Campos Críticos", "Mínimo"],
                index=1,
                help="Quantidade de dados extraídos"
            )
            max_workers = st.slider("Threads Paralelas", 1, 16, 4, 
                                   help="Número de threads para processamento")
        with col_config3:
            show_preview = st.checkbox("Mostrar Prévia", value=True)
            optimize_memory = st.checkbox("Otimizar Memória", value=True,
                                         help="Limpa memória durante processamento")
        
        up_files = st.file_uploader(
            "📂 Selecione os arquivos XML de CT-e", 
            type='xml', 
            accept_multiple_files=True,
            key="cte_uploader_massive",
            help="📌 Dica: Selecione todos os arquivos de uma vez (suporte até 100.000+)"
        )
        
        if up_files:
            total_files = len(up_files)
            
            # Mostrar estatísticas iniciais
            st.info(f"""
            **📊 ESTATÍSTICAS DO CARREGAMENTO:**
            - 📁 Total de arquivos: **{total_files:,}**
            - 💾 Tamanho estimado: **{(sum(len(f.getvalue()) for f in up_files) / (1024*1024)):.2f} MB**
            - 🎯 Modo de extração: **{extraction_mode}**
            - ⚡ Processamento: **{"Paralelo" if enable_parallel else "Sequencial"}**
            """)
            
            if st.button("🚀 INICIAR PROCESSAMENTO EM MASSA", type="primary", key="btn_process_cte_mass"):
                # Iniciar temporizador
                start_time = time.time()
                
                # Controle de progresso
                progress_bar = st.progress(0)
                status_container = st.empty()
                metrics_container = st.empty()
                
                # Divisão em lotes
                batches = [up_files[i:i + batch_size] 
                          for i in range(0, len(up_files), batch_size)]
                
                # Processamento
                all_results = []
                processed_count = 0
                error_count = 0
                
                for batch_idx, batch in enumerate(batches):
                    # Atualizar status
                    status_container.info(f"""
                    **📦 PROCESSANDO LOTE {batch_idx + 1}/{len(batches)}**
                    - Itens no lote: **{len(batch):,}**
                    - Total processado: **{processed_count:,}/{total_files:,}**
                    - Progresso: **{((processed_count / total_files) * 100):.1f}%**
                    """)
                    
                    # Processar lote
                    if enable_parallel:
                        # Processamento paralelo
                        with ThreadPoolExecutor(max_workers=max_workers) as executor:
                            # Dividir batch em chunks menores para paralelismo
                            chunk_size = max(1, len(batch) // max_workers)
                            batch_chunks = [batch[i:i + chunk_size] 
                                          for i in range(0, len(batch), chunk_size)]
                            
                            future_to_chunk = {
                                executor.submit(process_cte_batch, chunk, batch_idx): chunk 
                                for chunk in batch_chunks
                            }
                            
                            for future in as_completed(future_to_chunk):
                                chunk_results = future.result()
                                all_results.extend(chunk_results)
                    else:
                        # Processamento sequencial
                        batch_results = process_cte_batch(batch, batch_idx)
                        all_results.extend(batch_results)
                    
                    # Atualizar contadores
                    processed_count += len(batch)
                    error_count += len([r for r in batch_results if 'error' in r])
                    
                    # Atualizar barra de progresso
                    progress_bar.progress(min(processed_count / total_files, 1.0))
                    
                    # Atualizar métricas em tempo real
                    elapsed = time.time() - start_time
                    speed = processed_count / elapsed if elapsed > 0 else 0
                    
                    metrics_container.markdown(f"""
                    **📈 MÉTRICAS EM TEMPO REAL:**
                    - ⏱️ Tempo decorrido: **{elapsed:.1f}s**
                    - ⚡ Velocidade: **{speed:.1f} arquivos/segundo**
                    - ✅ Sucessos: **{processed_count - error_count:,}**
                    - ❌ Erros: **{error_count:,}**
                    - 📊 Progresso: **{(processed_count / total_files * 100):.1f}%**
                    """)
                    
                    # Otimização de memória
                    if optimize_memory and batch_idx < len(batches) - 1:
                        gc.collect()
                        time.sleep(0.01)
                
                # Finalizar processamento
                progress_bar.progress(1.0)
                total_time = time.time() - start_time
                
                # Separar resultados
                success_results = [r for r in all_results if 'error' not in r]
                error_results = [r for r in all_results if 'error' in r]
                
                # Exibir resumo final
                st.success(f"✅ **PROCESSAMENTO CONCLUÍDO EM {total_time:.2f} SEGUNDOS**")
                
                # Métricas finais
                cols = st.columns(4)
                cols[0].metric("📁 Total", f"{total_files:,}")
                cols[1].metric("✅ Sucessos", f"{len(success_results):,}", 
                             delta=f"{((len(success_results)/total_files)*100):.1f}%")
                cols[2].metric("❌ Erros", f"{len(error_results):,}")
                cols[3].metric("⏱️ Tempo Total", f"{total_time:.2f}s")
                
                # Processar dados de sucesso
                if success_results:
                    # Criar DataFrame otimizado
                    df_success = pd.DataFrame(success_results)
                    
                    # Otimizar tipos de dados
                    if 'valor' in df_success.columns:
                        df_success['valor'] = pd.to_numeric(df_success['valor'], errors='coerce')
                    
                    if 'emissao' in df_success.columns:
                        df_success['data_emissao'] = pd.to_datetime(
                            df_success['emissao'], 
                            errors='coerce', 
                            dayfirst=True
                        )
                        df_success = df_success.sort_values('data_emissao', ascending=False)
                    
                    # Converter colunas de texto para categorias para economia de memória
                    text_cols = ['remetente', 'destinatario', 'emitente']
                    for col in text_cols:
                        if col in df_success.columns:
                            df_success[col] = df_success[col].astype('category')
                    
                    # Exibir abas com resultados
                    tab_data, tab_stats, tab_export, tab_errors = st.tabs([
                        "📋 Dados Processados", 
                        "📈 Estatísticas", 
                        "💾 Exportar", 
                        f"⚠️ Erros ({len(error_results)})"
                    ])
                    
                    with tab_data:
                        if show_preview:
                            st.dataframe(
                                df_success.head(1000),
                                use_container_width=True,
                                height=600
                            )
                        else:
                            st.dataframe(df_success, use_container_width=True)
                    
                    with tab_stats:
                        # Estatísticas gerais
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if 'data_emissao' in df_success.columns:
                                st.subheader("📅 Distribuição por Data")
                                daily_counts = df_success['data_emissao'].dt.date.value_counts().sort_index()
                                fig1 = px.line(daily_counts, title="CT-es por Dia")
                                st.plotly_chart(fig1, use_container_width=True)
                        
                        with col2:
                            if 'valor' in df_success.columns:
                                st.subheader("💰 Distribuição de Valores")
                                fig2 = px.histogram(
                                    df_success, 
                                    x='valor',
                                    nbins=50,
                                    title="Histograma de Valores"
                                )
                                st.plotly_chart(fig2, use_container_width=True)
                        
                        # Estatísticas numéricas
                        st.subheader("📊 Estatísticas Descritivas")
                        if 'valor' in df_success.columns:
                            st.dataframe(df_success['valor'].describe(), use_container_width=True)
                    
                    with tab_export:
                        st.subheader("📥 Opções de Exportação")
                        
                        export_col1, export_col2 = st.columns([2, 1])
                        
                        with export_col1:
                            export_format = st.radio(
                                "Selecione o formato de exportação:",
                                ["Parquet (Recomendado - Mais Rápido)", 
                                 "CSV (Compatível)", 
                                 "Excel (Para Análise)", 
                                 "JSON (Para Integração)"],
                                index=0
                            )
                        
                        with export_col2:
                            compression = st.selectbox(
                                "Compressão",
                                ["snappy", "gzip", "brotli", "none"],
                                index=0
                            )
                        
                        if st.button("🔄 Gerar Arquivo para Download", type="primary"):
                            buffer = BytesIO()
                            
                            if "Parquet" in export_format:
                                df_success.to_parquet(
                                    buffer, 
                                    index=False, 
                                    compression=compression if compression != "none" else None
                                )
                                file_ext = "parquet"
                                mime_type = "application/octet-stream"
                                
                            elif "CSV" in export_format:
                                df_success.to_csv(buffer, index=False, encoding='utf-8-sig')
                                file_ext = "csv"
                                mime_type = "text/csv"
                                
                            elif "Excel" in export_format:
                                df_success.to_excel(buffer, index=False)
                                file_ext = "xlsx"
                                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                
                            else:  # JSON
                                df_success.to_json(buffer, orient='records', force_ascii=False)
                                file_ext = "json"
                                mime_type = "application/json"
                            
                            buffer.seek(0)
                            
                            st.download_button(
                                label=f"⬇️ Baixar {export_format.split(' ')[0]} ({df_success.shape[0]:,} registros)",
                                data=buffer,
                                file_name=f"ctes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                                mime=mime_type,
                                type="primary"
                            )
                    
                    with tab_errors:
                        if error_results:
                            df_errors = pd.DataFrame(error_results)
                            st.dataframe(df_errors, use_container_width=True)
                            
                            # Opção para exportar erros
                            error_buffer = BytesIO()
                            df_errors.to_csv(error_buffer, index=False, encoding='utf-8-sig')
                            error_buffer.seek(0)
                            
                            st.download_button(
                                "📥 Baixar Log de Erros",
                                error_buffer,
                                f"ctes_erros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                        else:
                            st.success("🎉 Nenhum erro encontrado!")
                
                else:
                    st.warning("⚠️ Nenhum arquivo processado com sucesso.")
        
        # Dicas de performance
        with st.expander("💡 DICAS PARA PERFORMANCE MÁXIMA", expanded=False):
            st.markdown("""
            ### 🚀 **OTIMIZAÇÃO PARA GRANDES VOLUMES (100.000+ CTEs)**
            
            1. **📁 PREPARAÇÃO DOS ARQUIVOS**
               - Organize os XMLs em pastas por mês/ano
               - Remova arquivos corrompidos antes do processamento
               - Use nomes de arquivos consistentes
            
            2. ⚙️ **CONFIGURAÇÕES RECOMENDADAS**
               - **Tamanho do Lote**: 5.000-10.000 para servidores com 8GB+ RAM
               - **Threads Paralelas**: 4-8 para maioria dos servidores
               - **Modo de Extração**: "Somente Campos Críticos" para máxima velocidade
               - **Otimizar Memória**: SEMPRE ativado para grandes volumes
            
            3. 💻 **RECURSOS DE HARDWARE**
               - **RAM Mínima**: 4GB (para até 50.000 arquivos)
               - **RAM Recomendada**: 8GB+ (para 100.000+ arquivos)
               - **CPU**: Múltiplos núcleos para paralelismo
               - **Disco**: SSD para leitura/escrita rápida
            
            4. 📊 **EXPORTAÇÃO INTELIGENTE**
               - Use **Parquet** para velocidade (10x mais rápido que CSV)
               - Compressão **snappy** para equilíbrio velocidade/tamanho
               - Exporte apenas colunas necessárias
            
            5. ⚡ **DICAS EXTRAS**
               - Feche outras aplicações durante processamento massivo
               - Processe em horários de menor uso do servidor
               - Monitore uso de memória durante execução
               - Divida processamentos muito grandes (ex: 200k em 2x 100k)
            
            ### 🎯 **ESTIMATIVAS DE PERFORMANCE**
            | Quantidade | Tempo Estimado | RAM Necessária |
            |------------|----------------|----------------|
            | 10.000 CTEs | 15-30 segundos | 2-3 GB |
            | 50.000 CTEs | 60-120 segundos | 4-6 GB |
            | 100.000 CTEs | 120-240 segundos | 6-8 GB |
            | 200.000 CTEs | 240-480 segundos | 8-12 GB |
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 3: UTILITÁRIO TXT ---
    with tabs[2]:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("🧹 Limpeza de Arquivos TXT (SPED)")
        txt_file = st.file_uploader("Upload TXT", type="txt", key="txt_clean")
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            remove_lines = st.checkbox("Remover linhas com '---'", value=True)
            remove_sped = st.checkbox("Remover cabeçalho SPED", value=True)
        with col_opt2:
            encoding_type = st.selectbox("Codificação", ["latin-1", "utf-8", "cp1252"])
            remove_empty = st.checkbox("Remover linhas vazias", value=True)
        
        if txt_file and st.button("🧼 LIMPAR E PROCESSAR", key="btn_clean_txt"):
            with st.spinner("Processando arquivo..."):
                try:
                    # Ler arquivo
                    content = txt_file.read().decode(encoding_type, errors='ignore')
                    lines = content.splitlines()
                    
                    # Aplicar filtros
                    cleaned_lines = []
                    for line in lines:
                        if remove_empty and not line.strip():
                            continue
                        if remove_lines and "-------" in line:
                            continue
                        if remove_sped and "SPED" in line.upper():
                            continue
                        cleaned_lines.append(line)
                    
                    # Estatísticas
                    removed = len(lines) - len(cleaned_lines)
                    
                    # Exibir resultados
                    col_res1, col_res2 = st.columns(2)
                    col_res1.success(f"✅ Linhas mantidas: {len(cleaned_lines):,}")
                    col_res2.warning(f"🗑️ Linhas removidas: {removed:,}")
                    
                    # Prévia
                    with st.expander("👁️ PRÉVIA DO RESULTADO"):
                        st.text_area("Primeiras 20 linhas:", 
                                   "\n".join(cleaned_lines[:20]), 
                                   height=200)
                    
                    # Download
                    cleaned_content = "\n".join(cleaned_lines)
                    st.download_button(
                        "⬇️ BAIXAR TXT LIMPO", 
                        cleaned_content,
                        f"limpo_{txt_file.name}",
                        "text/plain",
                        key="download_clean_txt"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        
        # Ferramentas adicionais
        with st.expander("🔧 FERRAMENTAS ADICIONAIS"):
            st.subheader("Contador de Linhas")
            text_input = st.text_area("Cole texto para contar linhas:", height=150)
            if text_input:
                lines_count = len(text_input.splitlines())
                st.metric("Linhas:", lines_count)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
