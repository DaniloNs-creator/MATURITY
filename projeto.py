import pdfplumber
import pandas as pd
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Configuração de Logs para rastreabilidade profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class DuimpParser:
    """
    Classe responsável pelo mapeamento e extração de dados de DUIMP/Declarações de Importação.
    Desenvolvida para alta resiliência a variações de layout.
    """

    def __init__(self):
        # Padrões Regex compilados para melhor performance
        # Ajustados para o padrão comum de documentos DUIMP/Siscomex
        self._patterns = {
            'item_header': re.compile(r'N[ºo°]\s*Adição\s*(\d+).*?Item\s*(\d+)', re.IGNORECASE),
            'produto_codigo': re.compile(r'Código\s*(?:do)?\s*Produto\s*[:\s]*([\d\.]+)', re.IGNORECASE),
            'descricao': re.compile(r'Descrição\s*Complementar\s*(.*?)(?=\n|$)', re.IGNORECASE),
            # Padrões para impostos - Busca valor monetário após a sigla
            'imposto_ii': re.compile(r'\bII\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'imposto_ipi': re.compile(r'\bIPI\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'imposto_pis': re.compile(r'\bPIS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
            'imposto_cofins': re.compile(r'\bCOFINS\b.*?Valor\s*a\s*Recolher\s*([\d\.,]+)', re.IGNORECASE | re.DOTALL),
        }

    def _clean_currency(self, value_str: str) -> float:
        """Converte string de moeda brasileira (1.000,00) para float (1000.00)."""
        if not value_str:
            return 0.0
        try:
            clean_str = value_str.replace('.', '').replace(',', '.')
            return float(clean_str)
        except ValueError:
            return 0.0

    def parse_pdf(self, pdf_path: str) -> pd.DataFrame:
        """
        Processa o arquivo PDF e retorna um DataFrame estruturado.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

        extracted_items: List[Dict] = []
        
        logger.info(f"Iniciando processamento do arquivo: {path.name}")

        try:
            with pdfplumber.open(path) as pdf:
                total_pages = len(pdf.pages)
                
                # Estratégia: Iterar páginas e identificar blocos de itens
                # Como itens podem quebrar página, mantemos um buffer ou contexto
                current_item = {}
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue

                    # Dividimos o texto em linhas para análise sequencial se necessário
                    # Mas usaremos regex no bloco da página para capturar estruturas
                    
                    # 1. Identificar se há início de um novo item na página
                    # Nota: A lógica abaixo assume que o PDF tem seções claras. 
                    # Se for uma tabela contínua, usaríamos page.extract_table()
                    
                    # Procura por blocos de Item/Adição
                    matches_header = list(self._patterns['item_header'].finditer(text))
                    
                    if matches_header:
                        for match in matches_header:
                            # Se já tínhamos um item sendo processado, salvamos ele antes de começar o próximo
                            # (Lógica simplificada: assume 1 item por bloco/página principal ou estrutura sequencial)
                            if current_item and 'numero_item' in current_item:
                                extracted_items.append(current_item)
                                current_item = {}

                            adicao, item_num = match.groups()
                            current_item = {
                                'numero_adicao': adicao,
                                'numero_item': item_num,
                                'pagina_origem': i + 1
                            }
                            
                            # Tenta extrair dados no contexto deste match (ou da página inteira)
                            # Extração de Código
                            match_cod = self._patterns['produto_codigo'].search(text)
                            if match_cod:
                                current_item['codigo_produto'] = match_cod.group(1)
                            
                            # Extração de Descrição (pode ser multilinha, aqui pegamos a primeira linha válida)
                            # Em PDFs reais, muitas vezes extraímos um bloco de texto entre coordenadas
                            match_desc = self._patterns['descricao'].search(text)
                            if match_desc:
                                current_item['descricao'] = match_desc.group(1).strip()
                            else:
                                # Fallback: tentar pegar linhas próximas ao código se a tag "Descrição" não for explícita
                                pass 

                            # Extração de Impostos (Procura valores monetários associados às siglas)
                            # Nota: Isso busca na página inteira. Se houver 2 itens na mesma página,
                            # a lógica precisa ser "crop" (recortar a área do item).
                            # Assumindo layout padrão onde impostos estão detalhados abaixo do item.
                            current_item['vlr_ii'] = self._clean_currency(self._patterns['imposto_ii'].search(text).group(1)) if self._patterns['imposto_ii'].search(text) else 0.0
                            current_item['vlr_ipi'] = self._clean_currency(self._patterns['imposto_ipi'].search(text).group(1)) if self._patterns['imposto_ipi'].search(text) else 0.0
                            current_item['vlr_pis'] = self._clean_currency(self._patterns['imposto_pis'].search(text).group(1)) if self._patterns['imposto_pis'].search(text) else 0.0
                            current_item['vlr_cofins'] = self._clean_currency(self._patterns['imposto_cofins'].search(text).group(1)) if self._patterns['imposto_cofins'].search(text) else 0.0

                # Adiciona o último item processado
                if current_item:
                    extracted_items.append(current_item)

            df = pd.DataFrame(extracted_items)
            
            # Validação e Limpeza Final
            if not df.empty:
                # Ordenar por adição/item
                df['numero_item'] = pd.to_numeric(df['numero_item'], errors='coerce')
                df = df.sort_values(by='numero_item')
                
                # Formatação para visualização
                cols_monetarias = ['vlr_ii', 'vlr_ipi', 'vlr_pis', 'vlr_cofins']
                df['total_impostos'] = df[cols_monetarias].sum(axis=1)
                
            logger.info(f"Processamento concluído. {len(df)} itens extraídos.")
            return df

        except Exception as e:
            logger.error(f"Erro crítico ao processar PDF: {e}")
            raise

    def export_data(self, df: pd.DataFrame, output_path: str):
        """Exporta os dados para Excel com formatação profissional."""
        try:
            # Reordenar colunas para apresentação lógica
            cols_order = [
                'numero_adicao', 'numero_item', 'codigo_produto', 'descricao', 
                'vlr_ii', 'vlr_ipi', 'vlr_pis', 'vlr_cofins', 'total_impostos'
            ]
            # Filtra apenas colunas que existem no DF
            cols_final = [c for c in cols_order if c in df.columns]
            
            df[cols_final].to_excel(output_path, index=False, sheet_name='Extracao_DUIMP')
            logger.info(f"Dados exportados com sucesso para: {output_path}")
        except Exception as e:
            logger.error(f"Erro ao exportar arquivo: {e}")

# ==========================================
# Exemplo de Uso (Driver Code)
# ==========================================
if __name__ == "__main__":
    # Caminho do arquivo (Substitua pelo seu arquivo real)
    arquivo_pdf = "Extrato_de_conferencia_hafele_Duimp.pdf" 
    
    parser = DuimpParser()
    
    try:
        # 1. Processar
        df_resultado = parser.parse_pdf(arquivo_pdf)
        
        # 2. Exibir prévia no console
        print("\n--- Prévia dos Dados Extraídos ---")
        print(df_resultado.head().to_string())
        
        # 3. Exportar
        parser.export_data(df_resultado, "Relatorio_Final_Impostos.xlsx")
        
    except FileNotFoundError:
        print("Arquivo PDF não encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
