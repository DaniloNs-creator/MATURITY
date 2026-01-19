import re
from typing import Dict, List

class DocumentExtractor:
    def __init__(self):
        self._current_item = {}
    
    def _parse_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            valor_str = valor_str.replace('.', '').replace(',', '.')
            return float(valor_str)
        except (ValueError, AttributeError):
            return 0.0
    
    def _find_tax_near_text(self, text: str, tax_name: str) -> float:
        """Busca valores de impostos próximos ao nome do imposto"""
        pattern = rf'{tax_name}.*?([\d\.,]+)\s*R\$\s*([\d\.,]+)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return self._parse_valor(match.group(2))
        return 0.0
    
    def _extract_basic_item_info(self, text: str) -> Dict:
        """Extrai informações básicas da tabela inicial"""
        item = {}
        
        # Padrão para capturar a linha da tabela
        table_pattern = r'\|(\d+)\s*\|\s*[✅✔✓]\s*\|([\d\.]+)\s*\|(\d+)\s*\|(\d+)\s*\|(\w+)\s*\|(\d+)'
        table_match = re.search(table_pattern, text)
        
        if table_match:
            item['item'] = table_match.group(1)
            item['ncm'] = table_match.group(2)
            item['codigo_produto'] = table_match.group(3)
            item['versao'] = table_match.group(4)
            item['cond_venda'] = table_match.group(5)
            item['fatura_invoice'] = table_match.group(6)
        
        return item
    
    def _extract_dados_mercadoria(self, text: str, item: Dict) -> Dict:
        """Extrai dados da seção DADOS DA MERCADORIA"""
        
        # Aplicação
        aplicacao_pattern = r'Aplicação\s*\n?\s*(\w+)'
        aplicacao_match = re.search(aplicacao_pattern, text, re.IGNORECASE)
        if aplicacao_match:
            item['aplicacao'] = aplicacao_match.group(1)
        
        # Condição Mercadoria
        cond_merc_pattern = r'Condição Mercadoria\s*\n?\s*(\w+)'
        cond_merc_match = re.search(cond_merc_pattern, text, re.IGNORECASE)
        if cond_merc_match:
            item['condicao_mercadoria'] = cond_merc_match.group(1)
        
        # Qtde Unid. Estatística
        qtd_estat_pattern = r'Qtde Unid\. Estatistica\s*([\d\.,]+)'
        qtd_estat_match = re.search(qtd_estat_pattern, text, re.IGNORECASE)
        if qtd_estat_match:
            item['qtde_unid_estatistica'] = self._parse_valor(qtd_estat_match.group(1))
        
        # Unidade Estatística
        unid_estat_pattern = r'Unidad Estatistica\s*\n?\s*([A-ZÀ-Ü\s]+)'
        unid_estat_match = re.search(unid_estat_pattern, text, re.IGNORECASE)
        if unid_estat_match:
            item['unidade_estatistica'] = unid_estat_match.group(1).strip()
        
        # Qtde Unid. Comercial
        qtd_comerc_pattern = r'Qtde Unid\. Comercial\s*([\d\.,]+)'
        qtd_comerc_match = re.search(qtd_comerc_pattern, text, re.IGNORECASE)
        if qtd_comerc_match:
            item['qtde_unid_comercial'] = self._parse_valor(qtd_comerc_match.group(1))
        
        # Unidade Comercial
        unid_comerc_pattern = r'Unidade Comercial\s*\n?\s*(\w+)'
        unid_comerc_match = re.search(unid_comerc_pattern, text, re.IGNORECASE)
        if unid_comerc_match:
            item['unidade_comercial'] = unid_comerc_match.group(1)
        
        # Peso Líquido
        peso_pattern = r'Peso Líquido \(KG\)\s*([\d\.,]+)'
        peso_match = re.search(peso_pattern, text, re.IGNORECASE)
        if peso_match:
            item['peso_liquido_kg'] = self._parse_valor(peso_match.group(1))
        
        # Moeda Negociada
        moeda_pattern = r'Moeda Negociada\s*\n?\s*(\d+)\s*-\s*([\w\s]+)'
        moeda_match = re.search(moeda_pattern, text, re.IGNORECASE)
        if moeda_match:
            item['moeda_codigo'] = moeda_match.group(1)
            item['moeda_nome'] = moeda_match.group(2).strip()
        
        # Valor Unitário
        valor_unit_pattern = r'Valor Unit Cond Venda\s*([\d\.,]+)'
        valor_unit_match = re.search(valor_unit_pattern, text, re.IGNORECASE)
        if valor_unit_match:
            item['valor_unitario'] = self._parse_valor(valor_unit_match.group(1))
        
        # Valor Total
        valor_total_pattern = r'Valor Tot\. Cond Venda\s*([\d\.,]+)'
        valor_total_match = re.search(valor_total_pattern, text, re.IGNORECASE)
        if valor_total_match:
            item['valor_total'] = self._parse_valor(valor_total_match.group(1))
        
        return item
    
    def _extract_taxes_directly(self, text: str, item: Dict) -> Dict:
        """Extrai impostos diretamente do texto"""
        # MÉTODO 1: Buscar "Valor Devido" em sequência
        valor_devido_pattern = r'Valor Devido \(R\$\)\s*([\d\.,]+)'
        valor_devido_matches = list(re.finditer(valor_devido_pattern, text))
        
        # Se encontrou 4 valores (II, IPI, PIS, COFINS)
        if len(valor_devido_matches) >= 4:
            item['ii_valor_devido'] = self._parse_valor(valor_devido_matches[0].group(1))
            item['ipi_valor_devido'] = self._parse_valor(valor_devido_matches[1].group(1))
            item['pis_valor_devido'] = self._parse_valor(valor_devido_matches[2].group(1))
            item['cofins_valor_devido'] = self._parse_valor(valor_devido_matches[3].group(1))
        
        # MÉTODO 2: Buscar cada imposto individualmente
        else:
            patterns = {
                'pis_valor_devido': r'PIS.*?Valor Devido \(R\$\)\s*([\d\.,]+)',
                'cofins_valor_devido': r'COFINS.*?Valor Devido \(R\$\)\s*([\d\.,]+)'
            }
            
            for tax_key, pattern in patterns.items():
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    item[tax_key] = self._parse_valor(match.group(1))
        
        # MÉTODO 3: Buscar valores próximos aos nomes
        if 'pis_valor_devido' not in item or item.get('pis_valor_devido', 0) == 0:
            item['pis_valor_devido'] = self._find_tax_near_text(text, 'PIS')
        
        if 'cofins_valor_devido' not in item or item.get('cofins_valor_devido', 0) == 0:
            item['cofins_valor_devido'] = self._find_tax_near_text(text, 'COFINS')
        
        return item
    
    def _extract_codigo_interno(self, text: str, item: Dict) -> Dict:
        """Extrai o código interno (PARTNUMBER) seguindo a mesma lógica dos impostos"""
        # Padrão robusto para encontrar o código interno
        codigo_patterns = [
            # Padrão 1: Formato mais comum
            r'CÓDIGO INTERNO \(PARTNUMBER\)\s*[\*\-\s]*\n?\s*Código interno\s*\n?\s*([\d\s\.\-]+)',
            # Padrão 2: Formato alternativo
            r'CÓDIGO INTERNO[\s\S]*?Código interno[\s\S]*?(\d[\d\s\.\-]+)',
            # Padrão 3: Busca direta pelo formato conhecido
            r'(\d{8}\s*[\-\s]+\s*\d{2}\s*[\-\s]+\s*[\d\.]{9})'
        ]
        
        for pattern in codigo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                codigo = match.group(1).strip()
                # Limpar espaços extras e formatação
                codigo = ' '.join(codigo.split())
                item['codigo_interno'] = codigo
                break
        
        return item
    
    def _extract_fabricante_info(self, text: str, item: Dict) -> Dict:
        """Extrai informações do fabricante/produtor"""
        
        # Fabricante Conhecido
        fabricante_pattern = r'FABRICANTE/PRODUTOR[\s\S]*?Conhecido\s*\n?\s*(SIM|NÃO)'
        fabricante_match = re.search(fabricante_pattern, text, re.IGNORECASE)
        if fabricante_match:
            item['fabricante_conhecido'] = fabricante_match.group(1)
        
        # País de Origem
        pais_pattern = r'Pais Origem\s*\n?\s*DE?\s*([A-ZÀ-Ü\s]+)'
        pais_match = re.search(pais_pattern, text, re.IGNORECASE)
        if pais_match:
            item['pais_origem'] = pais_match.group(1).strip()
        
        return item
    
    def _extract_descricao_produto(self, text: str, item: Dict) -> Dict:
        """Extrai denominação e descrição do produto"""
        
        # Denominação do Produto
        denominacao_pattern = r'DENOMINAÇÃO DO PRODUTO\s*\n(.+?)\n'
        denominacao_match = re.search(denominacao_pattern, text, re.DOTALL | re.IGNORECASE)
        if denominacao_match:
            item['denominacao_produto'] = denominacao_match.group(1).strip()
        
        # Descrição do Produto
        descricao_pattern = r'DESCRIÇÃO DO PRODUTO\s*\n(.+?)\n'
        descricao_match = re.search(descricao_pattern, text, re.DOTALL | re.IGNORECASE)
        if descricao_match:
            item['descricao_produto'] = descricao_match.group(1).strip()
        
        return item
    
    def _extract_condicao_venda_valores(self, text: str, item: Dict) -> Dict:
        """Extrai valores da condição de venda"""
        
        # Método de Valoração
        metodo_pattern = r'Método de Valoração\s*\n?\s*(.+?)\n'
        metodo_match = re.search(metodo_pattern, text, re.IGNORECASE)
        if metodo_match:
            item['metodo_valoracao'] = metodo_match.group(1).strip()
        
        # Condição de Venda
        cond_pattern = r'Condição de Venda\s*\n?\s*([A-Z]+)\s*-\s*'
        cond_match = re.search(cond_pattern, text, re.IGNORECASE)
        if cond_match:
            item['condicao_venda'] = cond_match.group(1)
        
        # Valor Condição Venda em Moeda
        vlr_moeda_pattern = r'Vlr Cond Venda \(Moeda\)\s*([\d\.,]+)'
        vlr_moeda_match = re.search(vlr_moeda_pattern, text, re.IGNORECASE)
        if vlr_moeda_match:
            item['vlr_cond_venda_moeda'] = self._parse_valor(vlr_moeda_match.group(1))
        
        # Valor Condição Venda em R$
        vlr_rs_pattern = r'Vlr Cond Venda \(R\\\$\)\*\s*([\d\.,]+)'
        vlr_rs_match = re.search(vlr_rs_pattern, text, re.IGNORECASE)
        if vlr_rs_match:
            item['vlr_cond_venda_rs'] = self._parse_valor(vlr_rs_match.group(1))
        
        # Frete Internacional
        frete_pattern = r'Frete Internac\. \(R\\\*\)\*\s*([\d\.,]+)'
        frete_match = re.search(frete_pattern, text, re.IGNORECASE)
        if frete_match:
            item['frete_internacional_rs'] = self._parse_valor(frete_match.group(1))
        
        # Seguro Internacional
        seguro_pattern = r'Seguro Internac\. \(R\\\*\)\s*([\d\.,]+)'
        seguro_match = re.search(seguro_pattern, text, re.IGNORECASE)
        if seguro_match:
            item['seguro_internacional_rs'] = self._parse_valor(seguro_match.group(1))
        
        # Local Embarque
        local_emb_pattern = r'Local Embarque \(R\\\*\)\s*([\d\.,]+)'
        local_emb_match = re.search(local_emb_pattern, text, re.IGNORECASE)
        if local_emb_match:
            item['local_embarque_rs'] = self._parse_valor(local_emb_match.group(1))
        
        # Local Aduaneiro
        local_adu_pattern = r'Local Aduaneiro \(R\\\*\)\s*([\d\.,]+)'
        local_adu_match = re.search(local_adu_pattern, text, re.IGNORECASE)
        if local_adu_match:
            item['local_aduaneiro_rs'] = self._parse_valor(local_adu_match.group(1))
        
        return item
    
    def _extract_exportador_info(self, text: str, item: Dict) -> Dict:
        """Extrai informações do exportador"""
        
        # Relação Exportador/Fabricante
        relacao_pattern = r'RELAÇÃO EXPORTADOR E FABRIC\./PRODUTOR\s*\n?\s*(.+?)\n'
        relacao_match = re.search(relacao_pattern, text, re.IGNORECASE)
        if relacao_match:
            item['relacao_exportador_fabricante'] = relacao_match.group(1).strip()
        
        # Exportador Estrangeiro
        exportador_pattern = r'EXPORTADOR ESTRANGEIRO\s*\n?\s*(.+?)\s*-\s*PAIS:'
        exportador_match = re.search(exportador_pattern, text, re.IGNORECASE)
        if exportador_match:
            item['exportador_estrangeiro'] = exportador_match.group(1).strip()
        
        # Vinculação
        vinculacao_pattern = r'VINCULAÇÃO ENTRE COMPRADOR/VENDEDOR\s*\n?\s*(.+?)\n'
        vinculacao_match = re.search(vinculacao_pattern, text, re.IGNORECASE)
        if vinculacao_match:
            item['vinculacao_comprador_vendedor'] = vinculacao_match.group(1).strip()
        
        return item
    
    def extract_all_from_page(self, page_text: str) -> Dict:
        """Extrai TODAS as informações de uma página completa"""
        item = {}
        
        # 1. Informações básicas da tabela
        item.update(self._extract_basic_item_info(page_text))
        
        # 2. Descrição do produto
        item.update(self._extract_descricao_produto(page_text, item))
        
        # 3. Código interno (PARTNUMBER) - usando a mesma lógica dos impostos
        item.update(self._extract_codigo_interno(page_text, item))
        
        # 4. Fabricante/Produtor
        item.update(self._extract_fabricante_info(page_text, item))
        
        # 5. Dados da mercadoria
        item.update(self._extract_dados_mercadoria(page_text, item))
        
        # 6. Exportador
        item.update(self._extract_exportador_info(page_text, item))
        
        # 7. Condição de venda e valores
        item.update(self._extract_condicao_venda_valores(page_text, item))
        
        # 8. Impostos (seu código original)
        item.update(self._extract_taxes_directly(page_text, item))
        
        return item
    
    def extract_from_all_pages(self, pages_text: List[str]) -> List[Dict]:
        """Processa todos os itens de todas as páginas"""
        all_items = []
        
        for i, page_text in enumerate(pages_text, 1):
            print(f"Processando página {i}...")
            
            item = self.extract_all_from_page(page_text)
            
            # Adiciona índice da página
            item['pagina'] = i
            
            all_items.append(item)
        
        print(f"Total de {len(all_items)} itens processados.")
        return all_items


# EXEMPLO DE USO:
if __name__ == "__main__":
    # Carregue seus textos das páginas
    pages_text = [
        # Texto da página 1
        """| 74 | ✅ | 8302.42.00 | 193 | 1 | FCA | 110338935 |
        DENOMINACAO DO PRODUTO
        CABIDEIRO BÁSICO 12KG EM AÇO PRETO PARA MÓVEIS
        
        DESCRICAO DO PRODUTO
        MARCA CONERO.
        
        CÓDIGO INTERNO (PARTNUMBER)
        Código interno
        25053315 - 30 - 811.62.363
        
        FABRICANTE/PRODUTOR
        Conhecido
        NAO
        Pais Origem
        DE ALEMANHA
        
        DADOS DA MERCADORIA
        Aplicação
        REVENDA
        
        Condição Mercadoria
        NOVA
        
        Qtde Unid. Estatistica
        14,27000
        
        Unidad Estatistica
        QUILOGRAMA LIQUIDO
        
        Qtde Unid. Comercial
        2,00000
        
        Unidade Comercial
        UNIDADE
        
        Peso Líquido (KG)
        14,27000
        
        Moeda Negociada
        978 - EURO (EUR)
        
        Valor Unit Cond Venda
        67,5900000
        
        Valor Tot. Cond Venda
        135,18
        
        CONDIÇÃO DE VENDA DA MERCADORIA
        Método de Valoração
        METODO 1 - ART. 1 DO ACORDO (DECRETO 92930/86)
        
        Condição de Venda
        FCA - FREE CARRIER
        
        Vlr Cond Venda (Moeda)
        135,18
        
        Vlr Cond Venda (R$)*
        837,18
        
        Frete Internac. (R*)*
        90,65
        
        Seguro Internac. (R*)
        3,25
        
        TRIBUTOS DA MERCADORIA - VALORES
        Local Embarque (R*)
        837,18
        
        Local Aduaneiro (R*)
        931,08
        
        II - Valor Devido (R$)
        112,45
        
        IPI - Valor Devido (R$)
        15,78
        
        PIS - Valor Devido (R$)
        8,92
        
        COFINS - Valor Devido (R$)
        41,15""",
        
        # Adicione mais páginas conforme necessário
    ]
    
    # Cria o extrator e processa
    extractor = DocumentExtractor()
    results = extractor.extract_from_all_pages(pages_text)
    
    # Exibe os resultados
    for i, result in enumerate(results, 1):
        print(f"\n=== ITEM {i} ===")
        for key, value in result.items():
            print(f"{key}: {value}")
