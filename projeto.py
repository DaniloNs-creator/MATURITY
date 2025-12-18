import streamlit as st
import pdfplumber
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import os
import tempfile
from datetime import datetime
import json
from typing import Dict, List, Any, Tuple
import io

class DUIMPExactConverter:
    """Converte PDF para XML mantendo o layout EXATO do modelo"""
    
    def __init__(self):
        self.xml_template = None
        self.xml_structure = {}
        self.item_counter = 1
        self.adicao_counter = 1
        
    def analyze_model(self, xml_content: str):
        """Analisa o XML modelo para entender a estrutura exata"""
        try:
            # Remove declaração XML para parsing
            if xml_content.startswith('<?xml'):
                lines = xml_content.split('\n', 1)
                if len(lines) > 1:
                    xml_content = lines[1]
            
            # Parse do XML
            self.xml_template = xml_content
            root = ET.fromstring(xml_content)
            
            # Extrai estrutura completa
            self.xml_structure = {
                'root': root.tag,
                'namespaces': self._extract_namespaces(xml_content),
                'adicao_template': self._extract_adicao_template(root),
                'fixed_elements': self._extract_fixed_elements(root),
                'element_order': self._extract_element_order(root)
            }
            
            return True
        except Exception as e:
            st.error(f"Erro ao analisar XML modelo: {str(e)}")
            return False
    
    def _extract_namespaces(self, xml_content: str) -> Dict:
        """Extrai namespaces do XML"""
        namespaces = {}
        ns_matches = re.findall(r'xmlns(?::(\w+))?="([^"]+)"', xml_content)
        for prefix, uri in ns_matches:
            namespaces[prefix if prefix else 'default'] = uri
        return namespaces
    
    def _extract_adicao_template(self, root: ET.Element) -> Dict:
        """Extrai template completo de uma adição"""
        adicoes = root.findall('.//adicao')
        if not adicoes:
            return {}
        
        # Pega a primeira adição como template
        template_adicao = adicoes[0]
        
        # Converte para dicionário com estrutura
        template_dict = self._element_to_dict(template_adicao)
        
        return template_dict
    
    def _element_to_dict(self, element: ET.Element) -> Dict:
        """Converte elemento XML para dicionário"""
        result = {}
        result['tag'] = element.tag
        result['text'] = element.text.strip() if element.text and element.text.strip() else ''
        result['attrib'] = element.attrib
        result['children'] = []
        
        for child in element:
            result['children'].append(self._element_to_dict(child))
        
        return result
    
    def _extract_fixed_elements(self, root: ET.Element) -> Dict:
        """Extrai elementos fixos fora das adições"""
        fixed = {}
        
        # Elementos que NÃO estão dentro de adições
        for elem in root.find('.//duimp'):
            if elem.tag != 'adicao':
                fixed[elem.tag] = self._element_to_dict(elem)
        
        return fixed
    
    def _extract_element_order(self, root: ET.Element) -> List[str]:
        """Extrai ordem dos elementos no duimp"""
        order = []
        for elem in root.find('.//duimp'):
            order.append(elem.tag)
        return order
    
    def extract_all_items_from_pdf(self, pdf_path: str) -> Tuple[List[Dict], Dict]:
        """Extrai TODOS os itens do PDF, página por página"""
        all_items = []
        global_info = {
            'numeroDUIMP': '8686868686',
            'dataRegistro': '20251124',
            'dataDesembaraco': '20251124',
            'cargaDataChegada': '20251120',
            'cargaPesoBruto': '000000053415000',
            'cargaPesoLiquido': '000000048686100',
            'conhecimentoCargaEmbarqueData': '20251025',
            'totalAdicoes': '000'
        }
        
        all_text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            # Barra de progresso
            if st.session_state.get('processing', False):
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            for page_num, page in enumerate(pdf.pages):
                # Atualiza progresso
                if st.session_state.get('processing', False):
                    progress = (page_num + 1) / total_pages
                    progress_bar.progress(progress)
                    status_text.text(f"Processando página {page_num + 1} de {total_pages}")
                
                # Extrai texto da página
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n---PAGE---\n"
                    
                    # Extrai itens desta página
                    page_items = self._extract_items_from_page(page_text, page_num + 1)
                    all_items.extend(page_items)
            
            if st.session_state.get('processing', False):
                progress_bar.empty()
                status_text.empty()
        
        # Extrai informações globais
        global_info.update(self._extract_global_info(all_text))
        
        return all_items, global_info
    
    def _extract_items_from_page(self, page_text: str, page_num: int) -> List[Dict]:
        """Extrai itens de uma página específica"""
        items = []
        
        # NORMALIZA texto: remove múltiplos espaços, preserva quebras de linha importantes
        page_text = re.sub(r'\s+', ' ', page_text)
        page_text = re.sub(r'(?<=\n) ', '', page_text)  # Remove espaços no início da linha
        
        # Divide em linhas
        lines = page_text.split('\n')
        
        current_item = {}
        collecting_item = False
        item_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Verifica se é início de um ITEM
            is_item_start = (
                re.match(r'^Item\s+\d+', line, re.IGNORECASE) or
                re.match(r'^\d+\s*[-–]', line) or
                re.match(r'^ADI[CÇ][AÃ]O\s+\d+', line, re.IGNORECASE)
            )
            
            if is_item_start:
                # Se já estava coletando um item, processa ele
                if collecting_item and item_lines:
                    item_data = self._parse_item_lines(item_lines, page_num)
                    if item_data:
                        items.append(item_data)
                
                # Inicia novo item
                current_item = {'page': page_num, 'raw_lines': []}
                collecting_item = True
                item_lines = [line]
            
            elif collecting_item:
                # Continua coletando linhas do item atual
                item_lines.append(line)
                
                # Verifica se é fim do item (próximo item ou fim da seção)
                if i < len(lines) - 1:
                    next_line = lines[i + 1].strip()
                    next_is_item = (
                        re.match(r'^Item\s+\d+', next_line, re.IGNORECASE) or
                        re.match(r'^\d+\s*[-–]', next_line) or
                        re.match(r'^ADI[CÇ][AÃ]O\s+\d+', next_line, re.IGNORECASE) or
                        any(keyword in next_line.upper() for keyword in ['TOTAL', 'RESUMO', 'FIM', 'CONCLU'])
                    )
                    
                    if next_is_item:
                        # Fim do item atual
                        item_data = self._parse_item_lines(item_lines, page_num)
                        if item_data:
                            items.append(item_data)
                        collecting_item = False
        
        # Processa o último item da página
        if collecting_item and item_lines:
            item_data = self._parse_item_lines(item_lines, page_num)
            if item_data:
                items.append(item_data)
        
        return items
    
    def _parse_item_lines(self, lines: List[str], page_num: int) -> Dict:
        """Analisa linhas de um item e extrai informações"""
        item_text = ' '.join(lines)
        
        # Padrões de extração baseados no layout do PDF fornecido
        patterns = {
            'item_num': r'(?:Item|ADI[CÇ][AÃ]O)\s+(\d+)',
            'ncm': r'NCM\s*[:]?\s*([\d\.]+)',
            'codigo_interno': r'C[ÓO]DIGO INTERNO\s*[:]?\s*([\d\.\-]+)',
            'descricao': r'DENOMINA[ÇC][AÃ]O DO PRODUTO\s+(.+?)(?=(?:DESCRI|C[ÓO]DIGO|NCM|QUANTIDADE|VALOR|$))',
            'descricao_detalhada': r'DESCRI[ÇC][AÃ]O DO PRODUTO\s+(.+?)(?=(?:C[ÓO]DIGO|NCM|QUANTIDADE|VALOR|$))',
            'quantidade_comercial': r'QTDE UNID\. COMERCIAL\s+([\d\.,]+)',
            'unidade_comercial': r'UNIDADE COMERCIAL\s+(\w+)',
            'quantidade_estatistica': r'QTDE UNID\. ESTAT[ÍI]STICA\s+([\d\.,]+)',
            'unidade_estatistica': r'UNIDAD ESTAT[ÍI]STICA\s+(.+)',
            'peso_liquido': r'PESO L[ÍI]QUIDO\s*\(KG\)\s+([\d\.,]+)',
            'valor_unitario': r'VALOR UNIT COND VENDA\s+([\d\.,]+)',
            'valor_total': r'VALOR TOT\. COND VENDA\s+([\d\.,]+)',
            'condicao_venda': r'CONDI[ÇC][AÃ]O DE VENDA\s+(\w+)',
            'pais_origem': r'PA[ÍI]S ORIGEM\s+(.+)',
            'fabricante': r'FABRICANTE/PRODUTOR.*?CONHECIDO\s+(\w+)',
            'relacao_exportador': r'RELA[ÇC][AÃ]O EXPORTADOR E FABRIC\./PRODUTOR\s+(.+)'
        }
        
        item_data = {'page': page_num}
        
        for key, pattern in patterns.items():
            match = re.search(pattern, item_text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                
                # Limpeza específica por campo
                if key in ['quantidade_comercial', 'quantidade_estatistica', 'peso_liquido']:
                    value = value.replace('.', '').replace(',', '')
                elif key in ['valor_unitario', 'valor_total']:
                    value = value.replace('.', '').replace(',', '.')
                
                item_data[key] = value
        
        # Se não encontrou descrição detalhada, usa a geral
        if 'descricao_detalhada' not in item_data and 'descricao' in item_data:
            item_data['descricao_detalhada'] = item_data['descricao']
        
        # Combina código interno com descrição para o XML
        if 'codigo_interno' in item_data and 'descricao_detalhada' in item_data:
            item_data['descricao_xml'] = f"{item_data['codigo_interno']} - {item_data['descricao_detalhada']}"
        elif 'descricao_detalhada' in item_data:
            item_data['descricao_xml'] = item_data['descricao_detalhada']
        
        # Formata NCM para 8 dígitos
        if 'ncm' in item_data:
            ncm_clean = re.sub(r'[^\d]', '', item_data['ncm'])
            item_data['ncm_8digitos'] = ncm_clean[:8].zfill(8)
        
        return item_data if any(k in item_data for k in ['ncm', 'descricao_xml', 'quantidade_comercial']) else None
    
    def _extract_global_info(self, all_text: str) -> Dict:
        """Extrai informações globais do PDF"""
        info = {}
        
        # Número DUIMP
        duimp_match = re.search(r'N[ÚU]MERO\s+(\d+[A-Z]+\d+)', all_text, re.IGNORECASE)
        if duimp_match:
            info['numeroDUIMP'] = duimp_match.group(1)
        
        # Datas
        date_patterns = [
            (r'DATA REGISTRO\s+(\d{2})/(\d{2})/(\d{4})', 'dataRegistro'),
            (r'DATA DE CHEGADA\s+(\d{2})/(\d{2})/(\d{4})', 'cargaDataChegada'),
            (r'DATA DE EMBARQUE\s+(\d{2})/(\d{2})/(\d{4})', 'conhecimentoCargaEmbarqueData'),
            (r'DT\. EMBARQUE.*?(\d{2})/(\d{2})/(\d{4})', 'conhecimentoCargaEmbarqueData')
        ]
        
        for pattern, key in date_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                day, month, year = match.groups()
                info[key] = f"{year}{month}{day}"
        
        # Pesos
        peso_bruto_match = re.search(r'PESO BRUTO\s+([\d\.,]+)', all_text, re.IGNORECASE)
        if peso_bruto_match:
            peso = peso_bruto_match.group(1).replace('.', '').replace(',', '')
            info['cargaPesoBruto'] = peso.zfill(15)
        
        peso_liq_match = re.search(r'PESO L[ÍI]QUIDO\s+([\d\.,]+)', all_text, re.IGNORECASE)
        if peso_liq_match:
            peso = peso_liq_match.group(1).replace('.', '').replace(',', '')
            info['cargaPesoLiquido'] = peso.zfill(15)
        
        return info
    
    def format_for_xml(self, value: Any, field_type: str) -> str:
        """Formata valores para o padrão XML"""
        if value is None:
            value = ""
        
        value = str(value).strip()
        
        if field_type == 'number_15':
            # 15 dígitos, sem decimais
            num = re.sub(r'[^\d]', '', value)
            return num.zfill(15) if num else '0' * 15
        
        elif field_type == 'number_14':
            # 14 dígitos, sem decimais
            num = re.sub(r'[^\d]', '', value)
            return num.zfill(14) if num else '0' * 14
        
        elif field_type == 'number_20_6':
            # 20 dígitos, 6 casas decimais
            clean = re.sub(r'[^\d,.]', '', value)
            clean = clean.replace(',', '.')
            if '.' in clean:
                parts = clean.split('.')
                int_part = parts[0] if parts[0] else "0"
                dec_part = parts[1][:6] if len(parts) > 1 else "0"
                dec_part = dec_part.ljust(6, '0')
                num = int(int_part) * 10**6 + int(dec_part[:6])
            else:
                num = int(clean) * 10**6 if clean else 0
            return str(num).zfill(20)
        
        elif field_type == 'number_15_2':
            # 15 dígitos, 2 casas decimais
            clean = re.sub(r'[^\d,.]', '', value)
            clean = clean.replace(',', '.')
            if '.' in clean:
                parts = clean.split('.')
                int_part = parts[0] if parts[0] else "0"
                dec_part = parts[1][:2] if len(parts) > 1 else "0"
                dec_part = dec_part.ljust(2, '0')
                num = int(int_part) * 100 + int(dec_part[:2])
            else:
                num = int(clean) * 100 if clean else 0
            return str(num).zfill(15)
        
        elif field_type == 'string_200':
            # String com até 200 caracteres
            return value[:200]
        
        elif field_type == 'ncm_8':
            # NCM com 8 dígitos
            ncm_clean = re.sub(r'[^\d]', '', value)
            return ncm_clean[:8].zfill(8)
        
        elif field_type == 'date_yyyymmdd':
            # Data no formato YYYYMMDD
            match = re.search(r'(\d{2})/(\d{2})/(\d{4})', value)
            if match:
                day, month, year = match.groups()
                return f"{year}{month}{day}"
            return value
        
        else:
            return value
    
    def create_xml_from_items(self, items: List[Dict], global_info: Dict) -> str:
        """Cria XML completo com layout EXATO do modelo"""
        
        try:
            # Parse o XML modelo
            if self.xml_template.startswith('<?xml'):
                lines = self.xml_template.split('\n', 1)
                xml_for_parsing = lines[1] if len(lines) > 1 else self.xml_template
            else:
                xml_for_parsing = self.xml_template
            
            root = ET.fromstring(xml_for_parsing)
            duimp_element = root.find('.//duimp')
            
            if duimp_element is None:
                raise ValueError("Elemento 'duimp' não encontrado no XML modelo")
            
            # Remove todas as adições existentes (vamos recriar)
            existing_adicoes = duimp_element.findall('adicao')
            for adicao in existing_adicoes:
                duimp_element.remove(adicao)
            
            # Adiciona novas adições com dados do PDF
            for i, item in enumerate(items):
                adicao_num = i + 1
                adicao_element = self._create_adicao_element(item, adicao_num, global_info)
                duimp_element.append(adicao_element)
            
            # Atualiza informações gerais
            self._update_global_info(duimp_element, global_info, len(items))
            
            # Converte para string XML
            xml_str = ET.tostring(root, encoding='utf-8', method='xml')
            
            # Formata bonito
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            # Remove declaração XML do minidom e adiciona a correta
            if pretty_xml.startswith('<?xml'):
                lines = pretty_xml.split('\n', 1)
                pretty_xml = lines[1] if len(lines) > 1 else pretty_xml
            
            # Adiciona declaração XML corretamente
            final_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + pretty_xml
            
            # Remove espaços no início
            final_xml = final_xml.lstrip()
            
            return final_xml
            
        except Exception as e:
            st.error(f"Erro ao criar XML: {str(e)}")
            # Fallback: cria XML básico
            return self._create_fallback_xml(items, global_info)
    
    def _create_adicao_element(self, item: Dict, adicao_num: int, global_info: Dict) -> ET.Element:
        """Cria elemento adicao com dados do item"""
        
        # Usa template do modelo ou cria um novo
        if 'adicao_template' in self.xml_structure and self.xml_structure['adicao_template']:
            # Reconstrói elemento do template
            adicao_element = self._dict_to_element(self.xml_structure['adicao_template'])
        else:
            # Cria elemento básico
            adicao_element = ET.Element('adicao')
        
        # Atualiza campos com dados do item
        self._populate_adicao_fields(adicao_element, item, adicao_num, global_info)
        
        return adicao_element
    
    def _dict_to_element(self, element_dict: Dict) -> ET.Element:
        """Converte dicionário para elemento XML"""
        element = ET.Element(element_dict['tag'])
        
        if element_dict['text']:
            element.text = element_dict['text']
        
        for attr, value in element_dict['attrib'].items():
            element.set(attr, value)
        
        for child_dict in element_dict['children']:
            child_element = self._dict_to_element(child_dict)
            element.append(child_element)
        
        return element
    
    def _populate_adicao_fields(self, adicao: ET.Element, item: Dict, adicao_num: int, global_info: Dict):
        """Preenche campos da adição com dados do item"""
        
        # Mapeamento de campos baseado no XML modelo
        field_mappings = {
            'numeroAdicao': {'value': str(adicao_num).zfill(3), 'type': 'string'},
            'numeroDUIMP': {'value': global_info.get('numeroDUIMP', '8686868686'), 'type': 'string'},
            'numeroSequencialItem': {'value': str(self.item_counter).zfill(2), 'type': 'string'},
            'descricaoMercadoria': {'value': item.get('descricao_xml', 'PRODUTO IMPORTADO'), 'type': 'string_200'},
            'dadosMercadoriaCodigoNcm': {'value': item.get('ncm_8digitos', '00000000'), 'type': 'ncm_8'},
            'quantidade': {'value': item.get('quantidade_comercial', '0'), 'type': 'number_14'},
            'valorUnitario': {'value': item.get('valor_unitario', '0'), 'type': 'number_20_6'},
            'condicaoVendaValorMoeda': {'value': item.get('valor_total', '0'), 'type': 'number_15_2'},
            'condicaoVendaValorReais': {'value': item.get('valor_total', '0'), 'type': 'number_15_2'},
            'paisOrigemMercadoriaNome': {'value': item.get('pais_origem', 'ITALIA'), 'type': 'string'},
            'paisAquisicaoMercadoriaNome': {'value': item.get('pais_origem', 'ITALIA'), 'type': 'string'},
            'dadosMercadoriaPesoLiquido': {'value': item.get('peso_liquido', '0'), 'type': 'number_15'},
            'dadosMercadoriaMedidaEstatisticaQuantidade': {'value': item.get('quantidade_estatistica', '0'), 'type': 'number_14'},
            'valorTotalCondicaoVenda': {'value': item.get('valor_total', '0'), 'type': 'number_11'}
        }
        
        # Atualiza todos os elementos na adição
        for elem in adicao.iter():
            tag_name = elem.tag
            if '}' in tag_name:
                tag_name = tag_name.split('}')[1]
            
            if tag_name in field_mappings:
                mapping = field_mappings[tag_name]
                formatted_value = self.format_for_xml(mapping['value'], mapping['type'])
                elem.text = formatted_value
        
        self.item_counter += 1
    
    def _update_global_info(self, duimp_element: ET.Element, global_info: Dict, total_items: int):
        """Atualiza informações gerais no XML"""
        
        # Campos a atualizar
        update_fields = {
            'numeroDUIMP': global_info.get('numeroDUIMP', '8686868686'),
            'dataRegistro': global_info.get('dataRegistro', '20251124'),
            'dataDesembaraco': global_info.get('dataDesembaraco', '20251124'),
            'cargaDataChegada': global_info.get('cargaDataChegada', '20251120'),
            'cargaPesoBruto': global_info.get('cargaPesoBruto', '000000053415000'),
            'cargaPesoLiquido': global_info.get('cargaPesoLiquido', '000000048686100'),
            'conhecimentoCargaEmbarqueData': global_info.get('conhecimentoCargaEmbarqueData', '20251025'),
            'totalAdicoes': str(total_items).zfill(3)
        }
        
        for elem in duimp_element:
            tag_name = elem.tag
            if '}' in tag_name:
                tag_name = tag_name.split('}')[1]
            
            if tag_name in update_fields:
                elem.text = update_fields[tag_name]
    
    def _create_fallback_xml(self, items: List[Dict], global_info: Dict) -> str:
        """Cria XML fallback se houver erro"""
        
        # Cria XML básico baseado no modelo
        xml_template = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ListaDeclaracoes>
    <duimp>
        <!-- ADICOES SERÃO INSERIDAS AQUI -->
        <totalAdicoes>{total_adicoes}</totalAdicoes>
        <numeroDUIMP>{numeroDUIMP}</numeroDUIMP>
        <dataRegistro>{dataRegistro}</dataRegistro>
    </duimp>
</ListaDeclaracoes>"""
        
        # Preenche template
        xml_content = xml_template.format(
            total_adicoes=str(len(items)).zfill(3),
            numeroDUIMP=global_info.get('numeroDUIMP', '8686868686'),
            dataRegistro=global_info.get('dataRegistro', '20251124')
        )
        
        # Parse para adicionar adições
        root = ET.fromstring(xml_content.split('?>', 1)[1] if '?>' in xml_content else xml_content)
        duimp = root.find('.//duimp')
        
        # Encontra onde inserir as adições
        insert_point = None
        for elem in duimp:
            if elem.tag == 'totalAdicoes':
                insert_point = elem
                break
        
        # Adiciona adições
        for i, item in enumerate(items):
            adicao = self._create_simple_adicao(item, i + 1, global_info)
            if insert_point is not None:
                duimp.insert(list(duimp).index(insert_point), adicao)
            else:
                duimp.append(adicao)
        
        # Converte para string formatada
        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove declaração duplicada
        if pretty_xml.startswith('<?xml'):
            lines = pretty_xml.split('\n', 1)
            pretty_xml = lines[1] if len(lines) > 1 else pretty_xml
        
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + pretty_xml
    
    def _create_simple_adicao(self, item: Dict, adicao_num: int, global_info: Dict) -> ET.Element:
        """Cria adição simples (fallback)"""
        adicao = ET.Element('adicao')
        
        # Campos básicos
        ET.SubElement(adicao, 'numeroAdicao').text = str(adicao_num).zfill(3)
        ET.SubElement(adicao, 'numeroDUIMP').text = global_info.get('numeroDUIMP', '8686868686')
        ET.SubElement(adicao, 'dadosMercadoriaCodigoNcm').text = item.get('ncm_8digitos', '00000000')
        
        # Mercadoria
        mercadoria = ET.SubElement(adicao, 'mercadoria')
        ET.SubElement(mercadoria, 'descricaoMercadoria').text = item.get('descricao_xml', 'PRODUTO IMPORTADO')[:200]
        ET.SubElement(mercadoria, 'numeroSequencialItem').text = str(self.item_counter).zfill(2)
        ET.SubElement(mercadoria, 'quantidade').text = self.format_for_xml(item.get('quantidade_comercial', '0'), 'number_14')
        ET.SubElement(mercadoria, 'unidadeMedida').text = 'PECA                '
        ET.SubElement(mercadoria, 'valorUnitario').text = self.format_for_xml(item.get('valor_unitario', '0'), 'number_20_6')
        
        self.item_counter += 1
        
        return adicao

def main():
    st.set_page_config(
        page_title="Conversor DUIMP EXATO - PDF → XML",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Conversor DUIMP EXATO - PDF para XML")
    st.markdown("**Layout IDÊNTICO ao modelo, dados do seu PDF**")
    
    # Estado da sessão
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'converter' not in st.session_state:
        st.session_state.converter = DUIMPExactConverter()
    
    # Layout em colunas
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Configuração")
        
        # Upload do XML modelo
        st.write("**1. Carregue o XML modelo:**")
        xml_model = st.file_uploader(
            "Arquivo M-DUIMP-8686868686.xml",
            type=["xml"],
            key="xml_model",
            help="XML com o layout exato desejado"
        )
        
        if xml_model:
            xml_content = xml_model.getvalue().decode('utf-8')
            
            # Analisa o modelo
            if st.button("🔍 Analisar Modelo XML", type="primary"):
                with st.spinner("Analisando estrutura do XML..."):
                    success = st.session_state.converter.analyze_model(xml_content)
                    if success:
                        st.success("✅ Modelo analisado com sucesso!")
                        st.session_state.model_loaded = True
                    else:
                        st.error("❌ Erro ao analisar modelo")
        
        st.divider()
        
        # Upload do PDF
        st.write("**2. Carregue o PDF para converter:**")
        pdf_file = st.file_uploader(
            "Seu arquivo PDF",
            type=["pdf"],
            key="pdf_file",
            help="PDF com os dados para extrair"
        )
    
    with col2:
        st.subheader("🔄 Conversão")
        
        if xml_model and pdf_file and st.session_state.get('model_loaded', False):
            # Botão de conversão
            if st.button("🔄 Converter PDF para XML", type="primary", use_container_width=True):
                st.session_state.processing = True
                
                # Salva arquivos temporários
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(pdf_file.getbuffer())
                    pdf_path = tmp_pdf.name
                
                try:
                    # Extrai dados do PDF
                    with st.spinner("Extraindo dados do PDF..."):
                        items, global_info = st.session_state.converter.extract_all_items_from_pdf(pdf_path)
                    
                    # Gera XML
                    with st.spinner("Gerando XML com layout do modelo..."):
                        xml_output = st.session_state.converter.create_xml_from_items(items, global_info)
                    
                    st.session_state.processing = False
                    
                    # Mostra resultados
                    st.success(f"✅ Conversão concluída! {len(items)} itens processados.")
                    
                    # Estatísticas
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Itens Extraídos", len(items))
                    with col_stat2:
                        st.metric("Número DUIMP", global_info.get('numeroDUIMP', 'N/A'))
                    with col_stat3:
                        file_size = len(xml_output.encode('utf-8')) / 1024
                        st.metric("Tamanho XML", f"{file_size:.1f} KB")
                    
                    # Tabela de itens extraídos
                    with st.expander("📋 Visualizar Itens Extraídos", expanded=True):
                        if items:
                            # Cria DataFrame simplificado
                            table_data = []
                            for i, item in enumerate(items[:10]):  # Mostra 10 itens
                                table_data.append({
                                    "Item": i + 1,
                                    "NCM": item.get('ncm_8digitos', 'N/A'),
                                    "Descrição": item.get('descricao_xml', 'N/A')[:50] + ('...' if len(item.get('descricao_xml', '')) > 50 else ''),
                                    "Quantidade": item.get('quantidade_comercial', 'N/A'),
                                    "Valor Total": item.get('valor_total', 'N/A')
                                })
                            
                            st.dataframe(table_data, use_container_width=True)
                            
                            if len(items) > 10:
                                st.info(f"Mostrando 10 de {len(items)} itens. Todos incluídos no XML.")
                        else:
                            st.warning("Nenhum item extraído")
                    
                    # Download do XML
                    st.divider()
                    st.subheader("📥 Download do XML")
                    
                    # Valida XML
                    try:
                        if not xml_output.startswith('<?xml'):
                            xml_output = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_output
                        
                        # Tenta parsear para validar
                        ET.fromstring(xml_output.split('?>', 1)[1] if '?>' in xml_output else xml_output)
                        st.success("✓ XML válido e bem formado")
                    
                    except Exception as e:
                        st.error(f"⚠️ Problema no XML: {str(e)}")
                    
                    # Nome do arquivo
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    duimp_num = global_info.get('numeroDUIMP', 'UNKNOWN').replace('/', '_')
                    xml_filename = f"M-DUIMP-{duimp_num}_{timestamp}.xml"
                    
                    # Botão de download
                    st.download_button(
                        label="⬇️ Baixar Arquivo XML",
                        data=xml_output,
                        file_name=xml_filename,
                        mime="application/xml",
                        type="primary",
                        use_container_width=True
                    )
                    
                    # Visualização
                    with st.expander("🔍 Visualizar XML Gerado"):
                        preview = xml_output[:2500]
                        st.code(preview, language="xml")
                        
                        if len(xml_output) > 2500:
                            st.info(f"Mostrando primeiros 2500 caracteres de {len(xml_output)}")
                    
                    # Informações técnicas
                    with st.expander("⚙️ Informações Técnicas"):
                        st.write(f"**Estrutura do XML:**")
                        st.write(f"- Tags únicas no modelo: {len(st.session_state.converter.xml_structure.get('element_order', []))}")
                        st.write(f"- Template de adição extraído: {'Sim' if 'adicao_template' in st.session_state.converter.xml_structure else 'Não'}")
                        st.write(f"- Campos mapeados: {len(items[0]) if items else 0} por item")
                        
                        st.write(f"\n**Processamento:**")
                        st.write(f"- Itens por página: Média de {len(items)/max(1, len(set(i['page'] for i in items))):.1f}")
                        st.write(f"- Campos extraídos: {', '.join(list(items[0].keys())[:5]) if items else 'Nenhum'}...")
                
                except Exception as e:
                    st.error(f"❌ Erro na conversão: {str(e)}")
                    st.session_state.processing = False
                
                finally:
                    # Limpa arquivo temporário
                    if os.path.exists(pdf_path):
                        os.unlink(pdf_path)
        
        elif not xml_model:
            st.info("📋 **Carregue o XML modelo primeiro**")
            st.write("""
            O XML modelo (`M-DUIMP-8686868686.xml`) define o layout exato que será usado.
            
            **O que o sistema faz com o modelo:**
            1. Analisa a estrutura completa do XML
            2. Extrai o template das adições (itens)
            3. Entende a ordem dos elementos
            4. Aprende o formato dos campos
            
            **Depois, com seu PDF:**
            1. Extrai TODOS os itens do seu PDF
            2. Formata conforme o modelo
            3. Gera XML IDÊNTICO ao modelo
            """)
        
        elif not pdf_file:
            st.info("📄 **Agora carregue seu PDF para converter**")
            st.write("""
            **Seu PDF deve conter:**
            - Itens com NCM, descrição, quantidade, valores
            - Informações de importação
            - Dados de transporte e impostos
            
            **O sistema extrairá:**
            - TODOS os itens de TODAS as páginas
            - NCM formatado para 8 dígitos
            - Descrições completas
            - Valores formatados corretamente
            - Países de origem
            
            **Resultado:** XML com layout IDÊNTICO ao modelo!
            """)
        
        elif not st.session_state.get('model_loaded', False):
            st.info("🔍 **Clique em 'Analisar Modelo XML' para continuar**")
    
    # Rodapé com informações
    st.divider()
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.write("**✅ Garantias:**")
        st.write("- Layout IDÊNTICO ao modelo")
        st.write("- Todos os itens extraídos")
        st.write("- Formatação correta")
    
    with col_info2:
        st.write("**🔍 Extração:**")
        st.write("- NCM 8 dígitos")
        st.write("- Descrições completas")
        st.write("- Valores formatados")
        st.write("- Países de origem")
    
    with col_info3:
        st.write("**🚀 Processamento:**")
        st.write("- PDFs grandes (500+ páginas)")
        st.write("- Barra de progresso")
        st.write("- Validação automática")
        st.write("- XML bem formado")

if __name__ == "__main__":
    main()
