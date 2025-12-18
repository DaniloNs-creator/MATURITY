import streamlit as st
import pdfplumber
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import io

def format_xml(elem):
    """Retorna uma string XML bonitinha e indentada."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def extract_data_from_pdf(pdf_file):
    """Extrai informações do PDF da DUIMP."""
    data = {
        "numeroDUIMP": "",
        "importador_cnpj": "",
        "adicoes": []
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
            
        # Extração de Campos Cabeçalho (Exemplos baseados no layout fornecido)
        num_match = re.search(r'Numero\s*,\s*"([\d]+)"', full_text)
        if num_match:
            data["numeroDUIMP"] = num_match.group(1)
            
        cnpj_match = re.search(r'CNPJ\s*,\s*"([\d./-]+)"', full_text)
        if cnpj_match:
            data["importador_cnpj"] = cnpj_match.group(1)

        # Lógica para capturar Adições/Itens
        # Nota: Em um cenário real, você usaria as tabelas do pdfplumber para precisão
        # Aqui simulamos a estrutura para o XML de exemplo
        item_matches = re.findall(r'Item\s*,\s*"(\d+)"', full_text)
        for idx, item_id in enumerate(item_matches):
            adicao = {
                "numeroAdicao": str(idx + 1).zfill(3),
                "descricaoMercadoria": f"Item extraído {item_id}",
                "pesoLiquido": "000000000000", # Valor placeholder
                "valorTotalCondicaoVenda": "000000000"
            }
            data["adicoes"].append(adicao)
            
    return data

def create_duimp_xml(data):
    """Gera o XML no layout padrão M-DUIMP."""
    root = ET.Element("ListaDeclaracoes")
    duimp = ET.SubElement(root, "duimp")
    
    for ad in data["adicoes"]:
        adicao = ET.SubElement(duimp, "adicao")
        
        # Mapeamento conforme arquivo M-DUIMP-8686868686.xml
        ET.SubElement(adicao, "numeroAdicao").text = ad["numeroAdicao"]
        ET.SubElement(adicao, "numeroDUIMP").text = data["numeroDUIMP"]
        
        mercadoria = ET.SubElement(adicao, "mercadoria")
        ET.SubElement(mercadoria, "descricaoMercadoria").text = ad["descricaoMercadoria"]
        ET.SubElement(mercadoria, "numeroSequencialItem").text = "01"
        
        # Campos de impostos (Exemplos fixos baseados no layout de saída esperado)
        ET.SubElement(adicao, "iiRegimeTributacaoNome").text = "RECOLHIMENTO INTEGRAL"
        ET.SubElement(adicao, "pisCofinsRegimeTributacaoNome").text = "RECOLHIMENTO INTEGRAL"
        
    return root

# Interface Streamlit
st.set_page_config(page_title="Conversor PDF para XML DUIMP", layout="centered")

st.title("📄 Conversor DUIMP: PDF ➔ XML")
st.markdown("Extraia dados de extratos DUIMP para o layout de importação do sistema.")

uploaded_file = st.file_uploader("Escolha o arquivo PDF do Extrato", type="pdf")

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    
    if st.button("Converter para XML"):
        with st.spinner("Processando todas as páginas do PDF..."):
            try:
                # 1. Extrair dados
                extracted_data = extract_data_from_pdf(uploaded_file)
                
                # 2. Gerar XML
                xml_root = create_duimp_xml(extracted_data)
                xml_string = format_xml(xml_root)
                
                # 3. Exibir e Download
                st.subheader("Pré-visualização do XML Gerado")
                st.code(xml_string, language='xml')
                
                st.download_button(
                    label="Baixar Arquivo XML",
                    data=xml_string,
                    file_name=f"M-DUIMP-{extracted_data['numeroDUIMP']}.xml",
                    mime="application/xml"
                )
            except Exception as e:
                st.error(f"Erro na conversão: {e}")

st.info("O layout segue o padrão do arquivo M-DUIMP-8686868686.xml fornecido.")
