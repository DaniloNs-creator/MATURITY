import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from dataclasses import dataclass, field
from typing import List, Optional

# ==============================================================================
# CONFIGURAÇÃO DE ALTO NÍVEL
# ==============================================================================
st.set_page_config(
    page_title="Extrator DUIMP Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS para aparência corporativa
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    h1 { color: #1e3d59; }
    .stButton>button { background-color: #ff6b6b; color: white; border-radius: 5px; }
    .stProgress > div > div > div > div { background-color: #1e3d59; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# ESTRUTURA DE DADOS (MODELO)
# ==============================================================================
@dataclass
class DuimpItem:
    """Classe que representa um único item da DUIMP com tipagem forte."""
    adicao: str = ""
    item: str = ""
    codigo: str = ""
    descricao: str = ""
    ncm: str = ""
    raw_buffer: str = "" # Buffer para acumular texto de várias páginas se necessário
    
    # Impostos
    vlr_ii: float = 0.0
    vlr_ipi: float = 0.0
    vlr_pis: float = 0.0
    vlr_cofins: float = 0.0

    def as_dict(self):
        return {
            "Adição": self.adicao,
            "Item": self.item,
            "Código Produto": self.codigo,
            "Descrição": self.descricao,
            "NCM": self.ncm,
            "II (R$)": self.vlr_ii,
            "IPI (R$)": self.vlr_ipi,
            "PIS (R$)": self.vlr_pis,
            "COFINS (R$)": self.vlr_cofins,
            "Total Tributos (R$)": self.vlr_ii + self.vlr_ipi + self.vlr_pis + self.vlr_cofins
        }

# ==============================================================================
# MOTOR DE EXTRAÇÃO (ENGINE)
# ==============================================================================
class RobustExtractor:
    def __init__(self):
        # Regex compilados para performance máxima
        # Detecta início de item: "Nº Adição: 1 ... Nº Item: 1" (com variações de espaço)
        self.RE_HEADER = re.compile(r'N[ºo°]\s*Adição\s*(\d+).*?Item\s*(\d+)', re.IGNORECASE | re.DOTALL)
        
        # Campos internos do item
        self.RE_CODIGO = re.compile(r'Código\s*Produto\s*[:\.]?\s*([\w\.-]+)', re.IGNORECASE)
        self.RE_NCM = re.compile(r'NCM\s*[:\.]?\s*(\d+)', re.IGNORECASE)
        
        # Descrição: Captura tudo após "Descrição Complementar" até encontrar uma palavra-chave de parada
        # Palavras de parada comuns em DUIMP: "NCM", "Unidade Medida", "País de Procedência"
        self.RE_DESC_START = re.compile(r'Descrição\s*Complementar', re.IGNORECASE)
        self.RE_DESC_STOP = re.compile(r'(?:NCM|Unidade\s*Medida|Condição|País)', re.IGNORECASE)

        # Impostos (formatos R$ 1.000,00)
        self.RE_TAX_II = re.compile(r'\bII\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL)
        self.RE_TAX_IPI = re.compile(r'\bIPI\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL)
        self.RE_TAX_PIS = re.compile(r'\bPIS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL)
        self.RE_TAX_COFINS = re.compile(r'\bCOFINS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL)

    def _parse_money(self, val_str: str) -> float:
        if not val_str: return 0.0
        try:
            return float(val_str.replace('.', '').replace(',', '.'))
        except:
            return 0.0

    def _finalize_item(self, item: DuimpItem) -> DuimpItem:
        """Processa o buffer de texto acumulado (raw_buffer) para extrair os dados finais."""
        text = item.raw_buffer
        
        # 1. Extrair Código
        m_cod = self.RE_CODIGO.search(text)
        if m_cod: item.codigo = m_cod.group(1)

        # 2. Extrair NCM
        m_ncm = self.RE_NCM.search(text)
        if m_ncm: item.ncm = m_ncm.group(1)

        # 3. Extrair Descrição (Lógica Avançada de Recorte)
        # Encontra onde começa a descrição
        start_match = self.RE_DESC_START.search(text)
        if start_match:
            # Pega tudo do fim do label "Descrição" até o fim do texto
            subtext = text[start_match.end():]
            # Encontra onde parar
            stop_match = self.RE_DESC_STOP.search(subtext)
            if stop_match:
                raw_desc = subtext[:stop_match.start()]
            else:
                raw_desc = subtext # Pega até o fim se não achar stop word (raro)
            
            # Limpeza: remove quebras de linha e espaços duplos
            item.descricao = " ".join(raw_desc.split()).strip()

        # 4. Extrair Impostos (Varredura no bloco do item)
        m_ii = self.RE_TAX_II.search(text)
        if m_ii: item.vlr_ii = self._parse_money(m_ii.group(1))

        m_ipi = self.RE_TAX_IPI.search(text)
        if m_ipi: item.vlr_ipi = self._parse_money(m_ipi.group(1))

        m_pis = self.RE_TAX_PIS.search(text)
        if m_pis: item.vlr_pis = self._parse_money(m_pis.group(1))

        m_cofins = self.RE_TAX_COFINS.search(text)
        if m_cofins: item.vlr_cofins = self._parse_money(m_cofins.group(1))

        return item

    def process_pdf(self, file_bytes) -> pd.DataFrame:
        items_found = []
        current_item: Optional[DuimpItem] = None
        
        with pdfplumber.open(file_bytes) as pdf:
            total_pages = len(pdf.pages)
            prog_bar = st.progress(0)
            status_txt = st.empty()

            for i, page in enumerate(pdf.pages):
                # UI Update
                if i % 5 == 0:
                    prog_bar.progress(int((i / total_pages) * 100))
                    status_txt.text(f"Processando página {i+1} de {total_pages}...")

                # Extração de texto mantendo layout relativo
                page_text = page.extract_text()
                if not page_text: continue

                # Estratégia de "Split Stream":
                # Vamos varrer o texto procurando cabeçalhos de novos itens.
                # Cada vez que achamos um novo cabeçalho, fechamos o item anterior.
                
                # Iterador de matches de cabeçalho na página atual
                matches = list(self.RE_HEADER.finditer(page_text))
                
                if not matches:
                    # Se não tem cabeçalho novo, TUDO nessa página pertence ao item atual (continuação)
                    if current_item:
                        current_item.raw_buffer += "\n" + page_text
                else:
                    # Temos novos itens nesta página
                    last_pos = 0
                    for match in matches:
                        # 1. Se existe item aberto, fechamos ele com o texto ANTES deste novo cabeçalho
                        if current_item:
                            chunk = page_text[last_pos:match.start()]
                            current_item.raw_buffer += "\n" + chunk
                            items_found.append(self._finalize_item(current_item))
                        
                        # 2. Inicia NOVO item
                        adicao, item_num = match.groups()
                        current_item = DuimpItem(adicao=adicao, item=item_num)
                        last_pos = match.start() # Atualiza posição
                    
                    # 3. O resto da página (após o último cabeçalho) pertence ao último item criado
                    if current_item:
                        current_item.raw_buffer += "\n" + page_text[last_pos:]

            # Adiciona o último item que ficou aberto no final do arquivo
            if current_item:
                items_found.append(self._finalize_item(current_item))
                
            prog_bar.progress(100)
            status_txt.text("Finalizando estruturação dos dados...")

        return pd.DataFrame([item.as_dict() for item in items_found])

# ==============================================================================
# INTERFACE (FRONTEND)
# ==============================================================================
def main():
    st.title("Extrator de DUIMP - Versão Profissional")
    st.markdown("""
    **Capacidade:** Processamento ilimitado de páginas.
    **Tecnologia:** Máquina de Estados (State Machine) para captura de itens que quebram páginas.
    """)

    uploaded_file = st.file_uploader("Carregue o arquivo PDF (Completo)", type="pdf")

    if uploaded_file:
        extractor = RobustExtractor()
        
        try:
            with st.spinner("Inicializando motor de extração..."):
                df = extractor.process_pdf(uploaded_file)
            
            if df.empty:
                st.error("Nenhum item encontrado. Verifique se o arquivo é um Extrato de Conferência DUIMP válido.")
            else:
                # Layout de Resultados
                st.success(f"Processamento concluído: {len(df)} itens extraídos de {uploaded_file.name}")
                
                # Métricas Rápidas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Itens", len(df))
                col2.metric("Total II", f"R$ {df['II (R$)'].sum():,.2f}")
                col3.metric("Total IPI", f"R$ {df['IPI (R$)'].sum():,.2f}")
                col4.metric("Total PIS/COFINS", f"R$ {(df['PIS (R$)'].sum() + df['COFINS (R$)'].sum()):,.2f}")

                # Preview de Dados (Primeiras 50 linhas para não travar navegador se forem 1000 itens)
                st.subheader("Visualização dos Dados (Amostra)")
                st.dataframe(df.head(1000), use_container_width=True)

                # Exportação Excel (Crucial para o trabalho)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Itens DUIMP')
                    
                    # Auto-ajuste de colunas
                    workbook = writer.book
                    worksheet = writer.sheets['Itens DUIMP']
                    format_money = workbook.add_format({'num_format': '#,##0.00'})
                    
                    worksheet.set_column('A:B', 10) # Adição/Item
                    worksheet.set_column('C:C', 20) # Código
                    worksheet.set_column('D:D', 60) # Descrição (bem largo)
                    worksheet.set_column('F:I', 15, format_money) # Impostos

                st.download_button(
                    label="💾 BAIXAR EXCEL COMPLETO (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="Relatorio_DUIMP_Completo.xlsx",
                    mime="application/vnd.ms-excel",
                    type="primary"
                )

        except Exception as e:
            st.error(f"Erro fatal durante o processamento: {str(e)}")
            st.warning("Dica: Verifique se o PDF não está protegido por senha ou corrompido.")

if __name__ == "__main__":
    main()
