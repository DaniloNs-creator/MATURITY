import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import time
from typing import List, Dict, Any

# ==============================================================================
# CONFIGURAÇÃO GERAL DA APLICAÇÃO
# ==============================================================================
st.set_page_config(
    page_title="Processador DUIMP Enterprise",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para visual mais profissional
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #007bff;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# NÚCLEO DE PROCESSAMENTO (ENGINE)
# ==============================================================================

class DuimpExtractorEngine:
    """
    Motor de processamento robusto para Declarações Únicas de Importação (DUIMP).
    Utiliza estratégia de 'Text Stream' para mitigar quebras de página em itens longos.
    """

    def __init__(self):
        # Padrões Regex Compilados (Otimizados para Siscomex/DUIMP)
        self.PATTERNS = {
            # Captura início de um bloco de item: "Nº Adição 1 Nº do Item 1"
            'ITEM_START': re.compile(r'N[ºo°]\s*Adição\s*(\d+)\s*N[ºo°]\s*do\s*Item\s*(\d+)', re.IGNORECASE),
            
            # Captura Código do Produto (Part Number)
            'PROD_CODE': re.compile(r'Código\s*(?:do)?\s*Produto\s*[:\s]*([0-9\.]+)', re.IGNORECASE),
            
            # Captura Descrição (busca texto entre a label e a próxima label comum como NCM ou Unidade)
            'DESC_COMPLETA': re.compile(r'Descrição\s*Complementar\s*\n(.*?)(?=\n\s*(?:NCM|Unidade|Condição|País)|$)', re.IGNORECASE | re.DOTALL),
            
            # Captura valores monetários de impostos (considerando formatação R$ 1.000,00)
            'TAX_II': re.compile(r'II\s*.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'TAX_IPI': re.compile(r'IPI\s*.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'TAX_PIS': re.compile(r'PIS\s*.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'TAX_COFINS': re.compile(r'COFINS\s*.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
        }

    @staticmethod
    def _parse_currency(value_str: str) -> float:
        """Converte string monetária brasileira para float de forma segura."""
        if not value_str:
            return 0.0
        try:
            # Remove caracteres invisíveis e espaços
            clean_str = value_str.strip()
            # Remove separador de milhar e substitui decimal
            clean_str = clean_str.replace('.', '').replace(',', '.')
            return float(clean_str)
        except (ValueError, AttributeError):
            return 0.0

    def extract_full_text(self, pdf_file) -> str:
        """
        Extrai texto de todas as páginas e concatena com marcadores.
        Isso é crucial para itens que quebram de uma página para outra.
        """
        full_text = []
        with pdfplumber.open(pdf_file) as pdf:
            total = len(pdf.pages)
            progress_bar = st.progress(0)
            status = st.empty()
            
            for i, page in enumerate(pdf.pages):
                # Feedback visual para o usuário
                if i % 10 == 0:
                    prog = int((i / total) * 100)
                    progress_bar.progress(prog)
                    status.text(f"Lendo página {i+1} de {total}...")
                
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            progress_bar.progress(100)
            status.empty()
            
        return "\n".join(full_text)

    def process_data(self, raw_text: str) -> pd.DataFrame:
        """Processa o texto bruto concatenado e estrutura os dados."""
        
        # Divide o texto bruto em blocos baseados no padrão de início de item
        # O split cria uma lista onde cada elemento é um bloco de texto de um item
        # Usamos regex split mantendo os grupos de captura (Adição e Item)
        
        # Adiciona um marcador especial para facilitar o split
        text_with_markers = self.PATTERNS['ITEM_START'].sub(r'__ITEM_START__\1|\2\n', raw_text)
        blocks = text_with_markers.split('__ITEM_START__')
        
        extracted_items = []
        
        # Pula o primeiro bloco se for cabeçalho geral (antes do item 1)
        for block in blocks[1:]:
            try:
                # O bloco começa com "Adição|Item\nResto do texto..."
                header_line, content = block.split('\n', 1)
                num_adicao, num_item = header_line.split('|')
                
                item_data = {
                    'Adição': int(num_adicao),
                    'Item': int(num_item),
                    'Código Produto': None,
                    'Descrição': None,
                    'II (R$)': 0.0,
                    'IPI (R$)': 0.0,
                    'PIS (R$)': 0.0,
                    'COFINS (R$)': 0.0,
                    'Check Impostos': 0.0
                }

                # Extração de Campos usando o conteúdo do bloco
                
                # Código
                match_cod = self.PATTERNS['PROD_CODE'].search(content)
                if match_cod:
                    item_data['Código Produto'] = match_cod.group(1)

                # Descrição
                match_desc = self.PATTERNS['DESC_COMPLETA'].search(content)
                if match_desc:
                    # Limpa quebras de linha excessivas na descrição
                    desc_clean = re.sub(r'\s+', ' ', match_desc.group(1)).strip()
                    item_data['Descrição'] = desc_clean
                
                # Impostos (Itera sobre as chaves de impostos)
                tax_map = {
                    'TAX_II': 'II (R$)',
                    'TAX_IPI': 'IPI (R$)',
                    'TAX_PIS': 'PIS (R$)',
                    'TAX_COFINS': 'COFINS (R$)'
                }
                
                total_impostos_item = 0.0
                for pattern_key, df_col in tax_map.items():
                    match_tax = self.PATTERNS[pattern_key].search(content)
                    if match_tax:
                        val = self._parse_currency(match_tax.group(1))
                        item_data[df_col] = val
                        total_impostos_item += val
                
                item_data['Check Impostos'] = total_impostos_item
                extracted_items.append(item_data)

            except Exception as e:
                # Log de erro silencioso para não parar o loop, mas poderia ser exibido em modo debug
                continue

        return pd.DataFrame(extracted_items)

# ==============================================================================
# INTERFACE DO USUÁRIO (FRONTEND)
# ==============================================================================

def main():
    st.title("🛡️ Extrator DUIMP Pro")
    st.markdown("### Automação de Conferência Aduaneira")
    st.markdown("""
    Esta ferramenta foi projetada para ler arquivos PDF de DUIMP complexos (100+ páginas), 
    garantindo que itens quebrados entre páginas sejam capturados corretamente.
    """)

    # Sidebar de Controle
    with st.sidebar:
        st.header("Entrada de Dados")
        uploaded_file = st.file_uploader(
            "Carregar PDF da DUIMP", 
            type=['pdf'], 
            help="Arraste o arquivo 'Extrato de conferencia' aqui."
        )
        
        st.divider()
        st.info("💡 **Dica Profissional:** Verifique se o PDF é legível (texto selecionável) e não uma imagem escaneada.")

    if uploaded_file:
        processor = DuimpExtractorEngine()
        
        try:
            # Etapa 1: Leitura (IO Intensive)
            with st.spinner("🔄 Lendo arquivo e mapeando estrutura (isso pode levar alguns segundos)..."):
                raw_text = processor.extract_full_text(uploaded_file)
            
            # Etapa 2: Processamento (CPU Intensive)
            with st.spinner("⚙️ Processando lógica de itens e cálculos tributários..."):
                df_result = processor.process_data(raw_text)
            
            # Validação se dados foram extraídos
            if df_result.empty:
                st.error("⚠️ Não foi possível identificar itens. O layout do arquivo pode ser diferente do padrão Siscomex DUIMP.")
                st.stop()

            # Etapa 3: Exibição de Resultados
            st.success(f"✅ Processamento concluído! {len(df_result)} itens mapeados com sucesso.")
            
            # KPIs Tributários
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total II", f"R$ {df_result['II (R$)'].sum():,.2f}")
            kpi2.metric("Total IPI", f"R$ {df_result['IPI (R$)'].sum():,.2f}")
            kpi3.metric("Total PIS/COFINS", f"R$ {(df_result['PIS (R$)'].sum() + df_result['COFINS (R$)'].sum()):,.2f}")
            kpi4.metric("Valor Total Tributos", f"R$ {df_result['Check Impostos'].sum():,.2f}")

            # Filtros Dinâmicos
            st.divider()
            col_search, col_filter = st.columns([2, 1])
            with col_search:
                search_term = st.text_input("🔍 Buscar na Descrição ou Código:", "")
            
            if search_term:
                df_display = df_result[
                    df_result['Descrição'].str.contains(search_term, case=False, na=False) | 
                    df_result['Código Produto'].str.contains(search_term, case=False, na=False)
                ]
            else:
                df_display = df_result

            # Grid de Dados
            st.dataframe(
                df_display,
                column_config={
                    "Adição": st.column_config.NumberColumn("Adição", format="%d"),
                    "Item": st.column_config.NumberColumn("Item", format="%d"),
                    "II (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "IPI (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "PIS (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "COFINS (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Check Impostos": st.column_config.NumberColumn("Total Item", format="R$ %.2f"),
                },
                use_container_width=True,
                height=500
            )

            # Exportação
            st.divider()
            st.subheader("📤 Exportar Relatório")
            
            # Gerar Excel em memória
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Itens DUIMP')
                
                # Formatação Excel
                workbook = writer.book
                worksheet = writer.sheets['Itens DUIMP']
                money_fmt = workbook.add_format({'num_format': '#,##0.00'})
                
                worksheet.set_column('E:I', 15, money_fmt) # Colunas de valores
                worksheet.set_column('D:D', 50) # Coluna Descrição Larga
                
            st.download_button(
                label="Baixar Planilha Completa (.xlsx)",
                data=output.getvalue(),
                file_name="Relatorio_Analitico_DUIMP.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

        except Exception as e:
            st.error(f"Erro Crítico no Sistema: {str(e)}")
            # Em produção, aqui entraria um log handler
            
if __name__ == "__main__":
    main()
