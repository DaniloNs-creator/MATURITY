import re
from typing import Dict, Any, Optional
import logging

# Configuração de log para auditoria (essencial em produção)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuimpParser:
    """
    Parser profissional para documentos DUIMP.
    Focado em resiliência contra variações de OCR e formatação.
    """

    def extract_item_data(self, raw_text: str) -> Dict[str, Any]:
        """
        Processa o texto bruto de um item da DUIMP e retorna um dicionário estruturado.
        """
        # 1. Normalização: Remove excesso de espaços e quebras de linha para facilitar o regex
        # Transforma: "Código \n interno" em "Código interno"
        clean_text = " ".join(raw_text.split())
        
        item = {
            'meta_dados': {},
            'valores': {},
            'tributos': {}
        }

        # --- Extração de Identificadores ---
        
        # Código Interno: Captura robusta permitindo espaços e hífens variados
        # Baseado na imagem: "25053315 - 30 - 811.62.363"
        item['codigo_interno'] = self._extract_field(
            clean_text, 
            r'Código\s+interno\s+([\d\.\-\s]+?)(?=\s+FABRICANTE|CÓDIGO|$)',
            clean=True
        )

        # País de Origem
        # Regex captura "DE ALEMANHA" ou apenas "ALEMANHA"
        item['pais_origem'] = self._extract_field(
            clean_text,
            r'Pais\s+Origem\s+(?:DE\s+)?([A-ZÀ-Ü\s]+?)(?=\s+CARACTERIZAÇÃO|$)'
        )

        # Denominação e Descrição
        item['denominacao'] = self._extract_field(
            clean_text,
            r'DENOMINA[ÇC][ÃA]O DO PRODUTO\s+(.*?)\s+DESCRI[ÇC][ÃA]O'
        )
        
        item['descricao'] = self._extract_field(
            clean_text,
            r'DESCRI[ÇC][ÃA]O DO PRODUTO\s+(.*?)\s+CÓDIGO INTERNO'
        )

        # --- Extração de Valores Numéricos e Monetários ---
        
        # Mapeamento de campos numéricos (Regex -> Chave de Saída)
        # Nota: Usamos r'\(R[\$S]\)' para lidar com erro comum de OCR onde $ vira S
        numeric_fields = [
            (r'Qtde\s+Unid\.?\s+Comercial\s+([\d\.,]+)', 'quantidade_comercial'),
            (r'Peso\s+L[íi]quido\s*\(KG\)\s+([\d\.,]+)', 'peso_liquido_kg'),
            (r'Valor\s+Unit\s+Cond\s+Venda\s+([\d\.,]+)', 'valor_unitario'),
            (r'Valor\s+Tot\.?\s+Cond\s+Venda\s+([\d\.,]+)', 'valor_total_moeda'),
            # Captura específica do valor em Reais (R$)
            (r'Vlr\s+Cond\s+Venda\s*\(R[\$S]\)\s*([\d\.,]+)', 'valor_total_brl'),
            (r'Frete\s+Internac\.?\s*\(R[\$S]\)\s*([\d\.,]+)', 'frete_brl'),
            (r'Seguro\s+Internac\.?\s*\(R[\$S]\)\s*([\d\.,]+)', 'seguro_brl'),
            (r'Local\s+Aduaneiro\s*\(R[\$S]\)\s*([\d\.,]+)', 'valor_aduaneiro_brl'),
        ]

        for pattern, key in numeric_fields:
            item['valores'][key] = self._extract_money(clean_text, pattern)

        # --- Extração de Tributos (Lógica Otimizada) ---
        
        # Busca dinâmica para evitar if/else repetitivo
        tax_names = ['II', 'IPI', 'PIS', 'COFINS']
        for tax in tax_names:
            # Padrão: Nome do Imposto ... Valor Devido (R$) X.XXX,XX
            # O pattern permite caracteres entre o nome e o valor para robustez
            pattern = rf'{tax}.*?Valor Devido\s*\(R[\$S]\)\s*([\d\.,]+)'
            val = self._extract_money(clean_text, pattern)
            if val > 0:
                item['tributos'][f'{tax.lower()}_valor'] = val

        return item

    def _extract_field(self, text: str, pattern: str, clean: bool = False) -> Optional[str]:
        """Extrai texto genérico com tratamento de erros."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            return ' '.join(val.split()) if clean else val
        return None

    def _extract_money(self, text: str, pattern: str) -> float:
        """
        Converte string monetária brasileira (1.000,00) para float (1000.00).
        Retorna 0.0 se não encontrar ou falhar.
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            try:
                # Remove pontos de milhar e troca vírgula decimal por ponto
                clean_val = val_str.replace('.', '').replace(',', '.')
                return float(clean_val)
            except ValueError:
                logger.warning(f"Falha ao converter valor: {val_str}")
                return 0.0
        return 0.0

# --- Exemplo de Uso (Simulação) ---
# Se você tiver o texto extraído do OCR da imagem enviada:
if __name__ == "__main__":
    # Texto simulado baseado na sua imagem para teste
    ocr_text_simulated = """
    ITENS DA DUIMP - 00074
    CÓDIGO INTERNO (PARTNUMBER)
    Código interno 25053315 - 30 - 811.62.363
    FABRICANTE/PRODUTOR
    Conhecido NAO Pais Origem DE ALEMANHA
    Qtde Unid. Estatística 14,27000
    Peso Líquido (KG) 14,27000
    Valor Unit Cond Venda 67,5900000
    Valor Tot. Cond Venda 135,18
    Vlr Cond Venda (R$) 837,18
    Frete Internac. (R$) 90,65
    Seguro Internac. (R$) 3,25
    Local Aduaneiro (R$) 931,08
    """
    
    parser = DuimpParser()
    dados = parser.extract_item_data(ocr_text_simulated)
    
    import json
    print(json.dumps(dados, indent=4, ensure_ascii=False))
