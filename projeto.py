import streamlit as st
import pandas as pd
import pdfplumber
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import io
import chardet
import traceback
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Häfele | Data Hub Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PROFISSIONAL UNIFICADO ---
def apply_ui_style():
    st.markdown("""
    <style>
        /* Fundo e Fonte Principal */
        .stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Inter', sans-serif; }
        
        /* Cabeçalho Häfele Style */
        .header-box {
            background: #ffffff;
            padding: 2rem;
            border-radius: 12px;
            border-left: 10px solid #0054a6;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            text-align: left;
        }
        .hafele-logo { max-width: 180px; margin-bottom: 1rem; }
        
        /* Containers de Conteúdo */
        .content-card {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin-bottom: 1rem;
        }

        /* Botões Enterprise */
        .stButton > button {
            background-color: #2563eb !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 0.6rem 2rem !important;
            font-weight: 500 !important;
            border: none !important;
            transition: 0.3s;
        }
        .stButton > button:hover { background-color: #1d4ed8 !important; transform: translateY(-1px); }

        /* Estilização de métricas */
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #0054a6; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSES E LOGICA DE PROCESSAMENTO ---

class DataEngine:
    """Motor de processamento central para TXT, CTe e DUIMP"""

    # --- MÉTODO 1: TXT CLEANER ---
    @staticmethod
    def clean_txt(content, patterns_to_remove):
        substitutions = {
            "IMPOSTO IMPORTACAO": "IMP IMPORT",
            "TAXA SICOMEX": "TX SISCOMEX",
            "FRETE INTERNACIONAL": "FRET INTER",
            "SEGURO INTERNACIONAL": "SEG INTERN"
        }
        enc = chardet.detect(content[:10000])['encoding'] or 'latin-1'
        text = content.decode(enc)
        
        lines = text.splitlines()
        processed = []
        for line in lines:
            if not any(p in line for p in patterns_to_remove):
                temp = line
                for k, v in substitutions.items():
                    temp = temp.replace(k, v)
                processed.append(temp)
        return "\n".join(processed), len(lines)

    # --- MÉTODO 2: DUIMP CONVERTER (LAYOUT HAFELE) ---
    @staticmethod
    def parse_duimp_pdf(pdf_file):
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
                num, block = parts[i], parts[i+1]
                # Limpeza PartNumber
                raw_pn = re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S).group(1) if re.search(r"PARTNUMBER\)\s*(.*?)\s*(?:PAIS|FABRICANTE|CONDICAO)", block, re.S) else ""
                pn = re.sub(r'(C[ÓO]DIGO|INTERNO|PARTNUMBER|\(|\))', '', raw_pn, flags=re.I).strip().lstrip("- ").strip()
                
                raw_desc = re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S).group(1) if re.search(r"DENOMINACAO DO PRODUTO\s+(.*?)\s+C[ÓO]DIGO", block, re.S) else ""
                
                data["itens"].append({
                    "seq": num,
                    "descricao": f"{pn} - {re.sub(r'\s+', ' ', raw_desc).strip()}" if pn else raw_desc,
                    "ncm": re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block).group(1).replace(".", "") if re.search(r"NCM\s*[:\n]*\s*([\d\.]+)", block) else "00000000",
                    "peso": re.sub(r'[^\d,]', '', re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Peso Líquido \(KG\)\s*[:\n]*\s*([\d\.,]+)", block) else "0").replace(',', ''),
                    "qtd": re.sub(r'[^\d,]', '', re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Qtde Unid\. Comercial\s*[:\n]*\s*([\d\.,]+)", block) else "0").replace(',', ''),
                    "v_unit": re.sub(r'[^\d,]', '', re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block).group(1) if re.search(r"Valor Unit Cond Venda\s*[:\n]*\s*([\d\.,]+)", block) else "0").replace(',', '')
                })
        return data

    @staticmethod
    def build_duimp_xml(data):
        root = ET.Element("ListaDeclaracoes")
        duimp = ET.SubElement(root, "duimp")
        for item in data["itens"]:
            ad = ET.SubElement(duimp, "adicao")
            acr = ET.SubElement(ad, "acrescimo")
            ET.SubElement(acr, "codigoAcrescimo").text = "17"
            ET.SubElement(acr, "denominacao").text = "OUTROS ACRESCIMOS AO VALOR ADUANEIRO"
            ET.SubElement(acr, "moedaNegociadaCodigo").text = "978"
            ET.SubElement(acr, "valorReais").text = "000000000106601"
            ET.SubElement(ad, "dadosMercadoriaCodigoNcm").text = item["ncm"]
            ET.SubElement(ad, "dadosMercadoriaPesoLiquido").text = item["peso"].zfill(15)
            merc = ET.SubElement(ad, "mercadoria")
            ET.SubElement(merc, "descricaoMercadoria").text = item["descricao"]
            ET.SubElement(merc, "numeroSequencialItem").text = item["seq"].zfill(2)
            ET.SubElement(merc, "quantidade").text = item["qtd"].zfill(14)
            ET.SubElement(merc, "valorUnitario").text = item["v_unit"].zfill(20)
            ET.SubElement(ad, "numeroDUIMP").text = data["header"]["duimp"].replace("25BR", "")[:10]
        ET.SubElement(duimp, "importadorNome").text = "HAFELE BRASIL LTDA"
        return root

    # --- MÉTODO 3: CTE MASSIVE PROCESSOR (UP TO 1M) ---
    @staticmethod
    def process_cte_massive(files):
        data_list = []
        ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}
        progress_bar = st.progress(0)
        status = st.empty()
        total = len(files)
        
        for idx, file in enumerate(files):
            try:
                root = ET.fromstring(file.read())
                def find_t(path):
                    found = root.find(f'.//{{{ns["cte"]}}}{path}')
                    if found is None: found = root.find(f'.//{path}')
                    return found.text if found is not None else ""
                
                # Busca de peso inteligente
                peso_val, tipo_p = 0.0, "N/A"
                for infQ in root.findall(f'.//{{{ns["cte"]}}}infQ') or root.findall('.//infQ'):
                    tpMed = infQ.find(f'{{{ns["cte"]}}}tpMed') or infQ.find('tpMed')
                    qCarga = infQ.find(f'{{{ns["cte"]}}}qCarga') or infQ.find('qCarga')
                    if tpMed is not None and qCarga is not None:
                        if any(x in tpMed.text.upper() for x in ['PESO BRUTO', 'PESO BASE', 'PESO']):
                            peso_val = float(qCarga.text or 0)
                            tipo_p = tpMed.text.upper()
                            break

                data_list.append({
                    "nCT": find_t('nCT'),
                    "Emissao": find_t('dhEmi')[:10],
                    "Emitente": find_t('emit/xNome')[:40],
                    "Destinatario": find_t('dest/xNome')[:40],
                    "Peso_KG": peso_val,
                    "Tipo_Peso": tipo_p,
                    "Valor": float(find_t('vTPrest') or 0),
                    "Chave": find_t('infNFe/chave')
                })
                
                if (idx + 1) % 500 == 0 or (idx + 1) == total:
                    progress_bar.progress((idx + 1) / total)
                    status.text(f"Processando: {idx+1}/{total}")
            except: continue
            
        return pd.DataFrame(data_list)

# --- APLICAÇÃO ---

def main():
    apply_ui_style()
    engine = DataEngine()

    st.markdown(f"""
    <div class="header-box">
        <img src="https://raw.githubusercontent.com/DaniloNs-creator/final/7ea6ab2a610ef8f0c11be3c34f046e7ff2cdfc6a/haefele_logo.png" class="hafele-logo">
        <h1>Data Management Hub</h1>
        <p>Unificação de Processos: TXT Cleaner | Massive CT-e | DUIMP Official Layout</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚚 Processamento CT-e (Escala)", "📄 Conversor DUIMP PDF/XML", "📝 Limpeza de TXT"])

    # TAB 1: CT-E MASSIVO
    with tab1:
        st.subheader("Processamento de CT-e para Power BI")
        uploaded_ctes = st.file_uploader("Upload XMLs de CT-e (Suporta Lotes de até 1 milhão)", type="xml", accept_multiple_files=True)
        if uploaded_ctes and st.button("🚀 Processar CT-es"):
            df_cte = engine.process_cte_massive(uploaded_ctes)
            st.success(f"Processado {len(df_cte)} arquivos com sucesso!")
            st.dataframe(df_cte.head(50), use_container_width=True)
            
            csv = df_cte.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Base Consolidada (CSV)", csv, "base_cte_consolidada.csv", "text/csv")

    # TAB 2: DUIMP (LAYOUT HAFELE)
    with tab2:
        st.subheader("Conversor DUIMP (Layout Oficial)")
        pdf_duimp = st.file_uploader("Selecione o PDF de Conferência", type="pdf")
        if pdf_duimp and st.button("🛠️ Gerar XML Häfele"):
            data_duimp = engine.parse_duimp_pdf(pdf_duimp)
            xml_res = engine.build_duimp_xml(data_duimp)
            xml_str = minidom.parseString(ET.tostring(xml_res, 'utf-8')).toprettyxml(indent="    ")
            
            st.info(f"Processo: {data_duimp['header']['processo']} | Itens: {len(data_duimp['itens'])}")
            st.download_button("📥 Baixar XML Oficial", xml_str, f"DUIMP_{data_duimp['header']['processo']}.xml", "text/xml")
            with st.expander("Prévia da Descrição (Item 1)"):
                st.code(data_duimp['itens'][0]['descricao'])

    # TAB 3: TXT CLEANER
    with tab3:
        st.subheader("Limpeza de Arquivos TXT/Sped")
        txt_file = st.file_uploader("Selecione o arquivo TXT", type="txt")
        if txt_file and st.button("🪄 Limpar Linhas"):
            res_txt, total = engine.clean_txt(txt_file.read(), ["-------", "SPED EFD-ICMS/IPI"])
            st.success(f"Processado! Linhas originais: {total}")
            st.download_button("📥 Baixar TXT Limpo", res_txt, f"CLEAN_{txt_file.name}", "text/plain")

if __name__ == "__main__":
    main()
