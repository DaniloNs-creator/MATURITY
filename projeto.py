import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from typing import Optional, List, Dict

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Extrator DUIMP Pro",
    page_icon="📦",
    layout="wide"
)

# ==============================================================================
# LÓGICA DE NEGÓCIO (BACKEND)
# ==============================================================================

class DuimpParser:
    """
    Classe especialista em extrair dados de PDFs de Conferência DUIMP.
    Usa padrões de Regex para identificar campos chave independente da página.
    """
    
    def __init__(self):
        # Regex compilado para performance e robustez
        # Captura: "Item 1", "Código Produto: 123", "Descrição..."
        self.patterns = {
            'novo_item': re.compile(r'N[ºo°]\s*Adição\s*(\d+).*?Item\s*(\d+)', re.IGNORECASE),
            'codigo': re.compile(r'Código\s*(?:do)?\s*Produto\s*[:\s]*([\w\.-]+)', re.IGNORECASE),
            # Captura a descrição até encontrar uma palavra chave de parada (ex: NCM, Quantidade) ou quebra de linha dupla
            'descricao': re.compile(r'Descrição\s*Complementar\s*(.*?)(?=\n\s*(?:NCM|Unidade|Qtd)|$)', re.IGNORECASE | re.DOTALL),
            
            # Impostos: Busca a sigla seguida de "Valor a Recolher" e o número
            'ii': re.compile(r'\bII\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'ipi': re.compile(r'\bIPI\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'pis': re.compile(r'\bPIS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'cofins': re.compile(r'\bCOFINS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
        }

    def _clean_currency(self, value_str: Optional[str]) -> float:
        """Converte string '1.234,56' para float 1234.56 de forma segura."""
        if not value_str:
            return 0.0
        try:
            # Remove pontos de milhar e troca vírgula decimal por ponto
            clean = value_str.replace('.', '').replace(',', '.')
            return float(clean)
        except ValueError:
            return 0.0

    def process_file(self, file_buffer) -> pd.DataFrame:
        """Lê o buffer do arquivo e retorna DataFrame estruturado."""
        extracted_data = []
        
        with pdfplumber.open(file_buffer) as pdf:
            total_pages = len(pdf.pages)
            
            # Variáveis de estado para rastrear o item atual enquanto percorre as páginas
            current_item: Dict = {}
            
            # Barra de progresso na UI
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, page in enumerate(pdf.pages):
                # Atualiza UI
                progress = int((i + 1) / total_pages * 100)
                progress_bar.progress(progress)
                status_text.text(f"Processando página {i + 1} de {total_pages}...")

                text = page.extract_text()
                if not text:
                    continue

                # Divide o texto da página em blocos baseados no cabeçalho do item
                # Isso evita que o imposto do Item 2 seja atribuído ao Item 1 se estiverem na mesma página
                
                # Encontra todas as ocorrências de início de item
                matches = list(self.patterns['novo_item'].finditer(text))
                
                # Se não tem início de item, pode ser continuação da página anterior (ex: impostos na pág seguinte)
                if not matches and current_item:
                    self._extract_fields(text, current_item)
                
                # Se tem itens novos
                else:
                    prev_idx = 0
                    for idx, match in enumerate(matches):
                        # Se já existe um item sendo montado, salva ele antes de começar o novo
                        if current_item:
                            extracted_data.append(current_item)
                        
                        # Inicia novo item
                        adicao, item_num = match.groups()
                        current_item = {
                            'Adição': int(adicao),
                            'Item': int(item_num),
                            'Código': None,
                            'Descrição': None,
                            'II': 0.0, 'IPI': 0.0, 'PIS': 0.0, 'COFINS': 0.0,
                            'Origem': f'Pág {i+1}'
                        }

                        # Define o escopo do texto para este item (do match atual até o próximo match ou fim da pag)
                        start_pos = match.start()
                        end_pos = matches[idx+1].start() if idx + 1 < len(matches) else len(text)
                        item_text_block = text[start_pos:end_pos]
                        
                        self._extract_fields(item_text_block, current_item)

            # Adiciona o último item encontrado
            if current_item:
                extracted_data.append(current_item)
                
            progress_bar.empty()
            status_text.empty()

        df = pd.DataFrame(extracted_data)
        if not df.empty:
            # Reorganiza colunas e cria totais
            cols = ['Adição', 'Item', 'Código', 'Descrição', 'II', 'IPI', 'PIS', 'COFINS']
            df = df[cols]
            df['Total Impostos'] = df['II'] + df['IPI'] + df['PIS'] + df['COFINS']
            
        return df

    def _extract_fields(self, text_block: str, item_dict: Dict):
        """Método auxiliar para preencher o dicionário do item com regex."""
        # Código
        if not item_dict.get('Código'):
            m_cod = self.patterns['codigo'].search(text_block)
            if m_cod: item_dict['Código'] = m_cod.group(1)
        
        # Descrição (se ainda não pegou, ou para concatenar se quebrou página - aqui simplificado)
        if not item_dict.get('Descrição'):
            m_desc = self.patterns['descricao'].search(text_block)
            if m_desc: item_dict['Descrição'] = m_desc.group(1).replace('\n', ' ').strip()

        # Impostos (Soma cumulativa caso apareça duplicado ou fragmentado, embora raro)
        # Usamos 'max' aqui assumindo que se aparecer de novo é o mesmo valor, ou soma se for lógica diferente.
        # Para DUIMP, geralmente aparece uma vez. Vamos substituir se encontrar valor > 0.
        
        for tax in ['ii', 'ipi', 'pis', 'cofins']:
            m_tax = self.patterns[tax].search(text_block)
            if m_tax:
                val = self._clean_currency(m_tax.group(1))
                key = tax.upper()
                if val > 0: item_dict[key] = val

# ==============================================================================
# FRONTEND (STREAMLIT)
# ==============================================================================

def to_excel(df):
    """Converte DataFrame para Excel em memória para download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens DUIMP')
        workbook = writer.book
        worksheet = writer.sheets['Itens DUIMP']
        
        # Formatação de moeda
        money_fmt = workbook.add_format({'num_format': 'R$ #,##0.00'})
        worksheet.set_column('E:I', 15, money_fmt) # Colunas de impostos
        
        # Ajuste de largura
        worksheet.set_column('C:C', 15) # Código
        worksheet.set_column('D:D', 40) # Descrição
        
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("📄 Extrator Profissional de DUIMP")
    st.markdown("""
    Faça upload do PDF da DUIMP/Siscomex para extrair automaticamente:
    **Itens, Códigos (Part Number), Descrições e Impostos (II, IPI, PIS, COFINS).**
    """)

    # Sidebar para controles
    with st.sidebar:
        st.header("Upload")
        uploaded_file = st.file_uploader("Arraste seu PDF aqui", type=["pdf"])
        st.info("O processamento é feito localmente na memória. Seus dados estão seguros.")

    if uploaded_file is not None:
        parser = DuimpParser()
        
        try:
            with st.spinner('Lendo e estruturando dados do PDF... Isso pode levar alguns segundos.'):
                # Processamento
                df = parser.process_file(uploaded_file)
            
            if df.empty:
                st.warning("O arquivo foi lido, mas nenhum item foi identificado. Verifique se é um PDF de Extrato de Conferência DUIMP padrão.")
            else:
                # Métricas de Resumo (KPIs)
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total de Itens", len(df))
                c2.metric("Total II", f"R$ {df['II'].sum():,.2f}")
                c3.metric("Total IPI", f"R$ {df['IPI'].sum():,.2f}")
                c4.metric("Total Geral Impostos", f"R$ {df['Total Impostos'].sum():,.2f}")
                st.divider()

                # Tabela Interativa
                st.subheader("Detalhamento dos Itens")
                st.dataframe(
                    df, 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Total Impostos": st.column_config.NumberColumn(format="R$ %.2f"),
                        "II": st.column_config.NumberColumn(format="R$ %.2f"),
                        "IPI": st.column_config.NumberColumn(format="R$ %.2f"),
                        "PIS": st.column_config.NumberColumn(format="R$ %.2f"),
                        "COFINS": st.column_config.NumberColumn(format="R$ %.2f"),
                    }
                )

                # Botão de Exportação
                excel_data = to_excel(df)
                st.download_button(
                    label="📥 Baixar Planilha Excel (.xlsx)",
                    data=excel_data,
                    file_name="extrato_duimp_processado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.expander("Ver detalhes do erro").write(e)

if __name__ == "__main__":
    main()
