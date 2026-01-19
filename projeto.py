import streamlit as st
import pandas as pd
import pdfplumber
import re
import os
import logging
import tempfile
from typing import Dict, List, Optional

# --- Configuração de Logging e Página ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Análise DUIMP/Invoice Pro",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Profissional ---
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #0f172a; font-weight: 800; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    .sub-header { font-size: 1.5rem; color: #334155; font-weight: 600; margin-top: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #2563eb; }
    .metric-label { font-size: 0.9rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

class AdvancedPDFParser:
    """
    Parser avançado utilizando expressões regulares com flags DOTALL
    para capturar blocos de texto multilinha entre seções conhecidas.
    """
    
    def __init__(self):
        self.documento = {'itens': [], 'totais': {}}

    def parse_pdf(self, pdf_path: str) -> Dict:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                # Concatena todas as páginas para tratar itens que quebram de página
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            
            # Normalização básica
            full_text = self._normalize_text(full_text)
            self._process_text(full_text)
            return self.documento
        except Exception as e:
            logger.error(f"Erro fatal no parsing: {e}")
            raise

    def _normalize_text(self, text: str) -> str:
        # Remove caracteres de controle estranhos, mas mantém quebras de linha essenciais
        return text

    def _process_text(self, text: str):
        # Regex Mestre: Busca o padrão inicial de um item (Item | Integração | NCM)
        # Ex: "74 8302.42.00 193" (Item espaço NCM espaço Codigo)
        # O padrão abaixo procura: Inicio de linha ou quebra, Digitos (Item), Espaço, NCM, Espaço
        item_pattern = r'(?:^|\n)(\d+)\s+.*?\s+(\d{4}\.\d{2}\.\d{2})\s+(\d+)\s'
        
        matches = list(re.finditer(item_pattern, text))
        
        for i, match in enumerate(matches):
            start = match.start()
            # O fim deste item é o início do próximo, ou o fim do texto
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            block_text = text[start:end]
            
            # Dados capturados no cabeçalho do item (Item, NCM, Codigo Produto)
            item_num = match.group(1)
            ncm = match.group(2)
            cod_prod_header = match.group(3)
            
            item_data = self._extract_fields_from_block(block_text, item_num, ncm, cod_prod_header)
            if item_data:
                self.documento['itens'].append(item_data)

        self._calculate_totals()

    def _extract_fields_from_block(self, text: str, item_num: str, ncm: str, cod_header: str) -> Dict:
        """
        Extrai dados usando 'âncoras' de texto. Procura o texto entre a chave e a próxima seção.
        """
        item = {
            # Campos Chave
            'numero_item': item_num,
            'ncm': ncm,
            'codigo_produto_duimp': cod_header,
            
            # Campos Solicitados (Novos e Corrigidos)
            'codigo_interno': '',
            'pais_origem': '',
            'aplicacao': '',
            'fatura_invoice': '',
            'condicao_venda': '',
            'descricao_completa': '',
            'marca': '',
            
            # Valores Numéricos
            'quantidade': 0.0,
            'peso_liquido': 0.0,
            'valor_total': 0.0,
            'total_impostos': 0.0,
            
            # Impostos Detalhados
            'ii_valor': 0.0, 'ipi_valor': 0.0, 'pis_valor': 0.0, 'cofins_valor': 0.0,
            'frete': 0.0, 'seguro': 0.0
        }

        # --- TÁTICA AVANÇADA DE EXTRAÇÃO (Blocos Multilinha) ---

        # 1. CÓDIGO INTERNO (Correção Crítica)
        # Procura por "Código interno", pega tudo até chegar em "FABRICANTE" ou "Conhecido"
        # O re.DOTALL (.) permite que o ponto capture quebras de linha (\n)
        cod_interno_match = re.search(r'Código interno\s*(.*?)\s*(?:FABRICANTE|Conhecido|Pais)', text, re.IGNORECASE | re.DOTALL)
        if cod_interno_match:
            # Limpa quebras de linha e espaços extras do resultado
            raw_code = cod_interno_match.group(1).replace('\n', '').strip()
            item['codigo_interno'] = raw_code

        # 2. PAIS DE ORIGEM
        # Procura "Pais Origem", pega o texto até "CARACTERIZAÇÃO" ou nova linha
        pais_match = re.search(r'Pais Origem\s*(.*?)\s*(?:CARACTERIZAÇÃO|\n)', text, re.IGNORECASE)
        if pais_match:
            item['pais_origem'] = pais_match.group(1).strip()

        # 3. FATURA / INVOICE
        # Geralmente está na primeira linha ou próximo ao cabeçalho do item
        # Procura padrão numérico grande próximo a "Fatura" ou no topo
        invoice_match = re.search(r'Fatura/Invoice\s*([\d\w]+)', text, re.IGNORECASE)
        if invoice_match:
            item['fatura_invoice'] = invoice_match.group(1).strip()

        # 4. APLICAÇÃO
        app_match = re.search(r'Aplicação\s*(.*?)\s*(?:Condição|Qtde)', text, re.IGNORECASE)
        if app_match:
            item['aplicacao'] = app_match.group(1).strip()

        # 5. CONDIÇÃO DE VENDA
        cond_venda_match = re.search(r'Cond\. Venda\s*([A-Z]{3})', text, re.IGNORECASE)
        if cond_venda_match:
            item['condicao_venda'] = cond_venda_match.group(1).strip()

        # 6. DESCRIÇÃO E MARCA
        desc_match = re.search(r'DENOMINACAO DO PRODUTO\s*(.*?)\s*DESCRICAO', text, re.IGNORECASE | re.DOTALL)
        if desc_match:
            item['descricao_completa'] = desc_match.group(1).replace('\n', ' ').strip()
            
        marca_match = re.search(r'MARCA\s*([^\.]+)', text, re.IGNORECASE)
        if marca_match:
            item['marca'] = marca_match.group(1).strip()

        # --- Extração de Valores Numéricos (Mantida e Reforçada) ---
        
        # Quantidade
        qtd_match = re.search(r'Qtde Unid\. Comercial\s+([\d\.,]+)', text)
        if qtd_match: item['quantidade'] = self._parse_float(qtd_match.group(1))

        # Peso
        peso_match = re.search(r'Peso Líquido.*?([\d\.,]+)', text)
        if peso_match: item['peso_liquido'] = self._parse_float(peso_match.group(1))

        # Valor Total (MLE/Mercadoria)
        vlr_total_match = re.search(r'Valor Tot\. Cond Venda\s+([\d\.,]+)', text)
        if vlr_total_match: item['valor_total'] = self._parse_float(vlr_total_match.group(1))

        # Frete e Seguro
        frete_match = re.search(r'Frete Internac\. \(R\$\)\s+([\d\.,]+)', text)
        if frete_match: item['frete'] = self._parse_float(frete_match.group(1))
        
        seguro_match = re.search(r'Seguro Internac\. \(R\$\)\s+([\d\.,]+)', text)
        if seguro_match: item['seguro'] = self._parse_float(seguro_match.group(1))

        # --- IMPOSTOS (Busca Resiliente) ---
        # Procura o padrão "Imposto ... Valor Devido (R$) X.XXX,XX"
        taxes = {
            'ii_valor': r'II.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'ipi_valor': r'IPI.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'pis_valor': r'PIS.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
            'cofins_valor': r'COFINS.*?Valor Devido \(R\$\)\s*([\d\.,]+)'
        }
        
        for key, pattern in taxes.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                item[key] = self._parse_float(match.group(1))
            else:
                # Fallback: Tenta achar apenas o rótulo do imposto e pega o primeiro número grande depois
                pass

        item['total_impostos'] = item['ii_valor'] + item['ipi_valor'] + item['pis_valor'] + item['cofins_valor']

        return item

    def _parse_float(self, value_str: str) -> float:
        if not value_str: return 0.0
        try:
            return float(value_str.replace('.', '').replace(',', '.'))
        except:
            return 0.0

    def _calculate_totals(self):
        # Soma simples para dashboard
        self.documento['totais'] = {
            'valor_total_mercadoria': sum(i['valor_total'] for i in self.documento['itens']),
            'total_impostos': sum(i['total_impostos'] for i in self.documento['itens'])
        }

# --- Interface Streamlit ---

def main():
    st.markdown('<h1 class="main-header">🚀 Extrator DUIMP/Invoice Pro</h1>', unsafe_allow_html=True)
    
    st.info("💡 **Novidades na Versão Pro:** Captura inteligente de Código Interno (Partnumber), Pais de Origem, Aplicação e Invoice, independente da formatação do PDF.")

    uploaded_file = st.sidebar.file_uploader("📂 Arraste seu PDF aqui", type=['pdf'])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            parser = AdvancedPDFParser()
            
            with st.spinner("🔍 Executando extração avançada..."):
                doc = parser.parse_pdf(tmp_path)
            
            # --- Métricas ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(doc['itens'])}</div>
                    <div class="metric-label">Itens Extraídos</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">R$ {doc['totais']['valor_total_mercadoria']:,.2f}</div>
                    <div class="metric-label">Valor Total Mercadoria</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">R$ {doc['totais']['total_impostos']:,.2f}</div>
                    <div class="metric-label">Total de Impostos</div>
                </div>""", unsafe_allow_html=True)

            # --- DataFrame ---
            if doc['itens']:
                df = pd.DataFrame(doc['itens'])
                
                # Seleção e renomeação de colunas para exibição final
                cols_order = [
                    'numero_item', 'codigo_interno', 'codigo_produto_duimp', 'descricao_completa', 
                    'ncm', 'pais_origem', 'aplicacao', 'fatura_invoice', 
                    'quantidade', 'valor_total', 'total_impostos',
                    'ii_valor', 'ipi_valor', 'pis_valor', 'cofins_valor'
                ]
                
                # Garante que colunas existem
                display_cols = [c for c in cols_order if c in df.columns]
                
                st.markdown('<h2 class="sub-header">📊 Detalhamento dos Itens</h2>', unsafe_allow_html=True)
                st.dataframe(
                    df[display_cols].style.format({
                        'valor_total': 'R$ {:,.2f}',
                        'total_impostos': 'R$ {:,.2f}',
                        'ii_valor': 'R$ {:,.2f}',
                        'pis_valor': 'R$ {:,.2f}',
                        'cofins_valor': 'R$ {:,.2f}',
                        'ipi_valor': 'R$ {:,.2f}',
                        'quantidade': '{:,.2f}'
                    }),
                    use_container_width=True,
                    height=500
                )

                # --- Exportação ---
                csv = df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(
                    label="💾 Baixar Relatório Completo (CSV)",
                    data=csv,
                    file_name="extrato_duimp_pro.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.warning("Nenhum item encontrado. Verifique se o PDF está no formato padrão de DUIMP/Invoice.")

        except Exception as e:
            st.error(f"Erro ao processar: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    main()
