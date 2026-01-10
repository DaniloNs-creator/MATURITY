import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import io

# --- FUNÇÕES UTILITÁRIAS DE FORMATAÇÃO ---

def format_number_xml(value_str, length=15, decimal_places=0):
    """
    Formata string de número (ex: '1.234,56') para formato XML (ex: '0000000123456').
    Remove pontos de milhar e vírgula decimal. Preenche com zeros à esquerda.
    """
    if not value_str:
        return "0" * length
    
    # Limpeza básica
    clean_val = value_str.strip()
    
    # Se for moeda europeia no PDF (1.000,00), remove ponto e depois remove virgula
    # Ajuste conforme o padrão do PDF. Pelo texto, parece padrão BR (ponto separa milhar, virgula decimal)
    clean_val = clean_val.replace('.', '').replace(',', '')
    
    # Preenchimento (Pad)
    if len(clean_val) > length:
        return clean_val[-length:] # Corta se for maior (erro de segurança)
    
    return clean_val.zfill(length)

def extract_field(text, pattern, group=1, default=""):
    """Função auxiliar para extrair regex com segurança"""
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(group).strip()
    return default

# --- LÓGICA DE EXTRAÇÃO DE DADOS (PARSER) ---

def parse_pdf_to_data(pdf_file):
    """
    Lê o PDF e extrai dados estruturados em um dicionário.
    """
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    data = {
        "header": {},
        "itens": []
    }

    # 1. Extração do Cabeçalho
    data["header"]["processo"] = extract_field(full_text, r"PROCESSO\s*#?(\d+)")
    data["header"]["importador"] = extract_field(full_text, r"IMPORTADOR\s*[\"']?([\w\s]+)[\"']?")
    data["header"]["numero_duimp"] = extract_field(full_text, r"Numero\s*[\"']?([0-9BR]+)[\"']?")
    
    # Extração de Frete/Seguro Totais (Aparecem no resumo)
    # Busca por padrões específicos de valor monetário
    data["header"]["frete_total_brl"] = extract_field(full_text, r"FRETE BASICO.*?([\d\.,]+)", group=1)
    
    # 2. Extração dos Itens (Adições)
    # Divide o texto pelos blocos "ITENS DA DUIMP-"
    # O regex captura o bloco até o próximo item ou fim de seção
    item_blocks = re.split(r"ITENS DA DUIMP[- ]+(\d+)", full_text)
    
    # O split retorna [texto_antes, num_item1, texto_item1, num_item2, texto_item2...]
    # Vamos iterar de 2 em 2
    for i in range(1, len(item_blocks), 2):
        item_num = item_blocks[i]
        item_text = item_blocks[i+1]
        
        item_data = {
            "numero_adicao": item_num.zfill(3),
            "ncm": extract_field(item_text, r"NCM\s*[\"']?([\d\.]+)[\"']?").replace(".", ""),
            "valor_unitario": extract_field(item_text, r"Valor Unit Cond Venda\s*([\d,.]+)"),
            "valor_total_moeda": extract_field(item_text, r"Valor Tot\. Cond Venda\s*([\d\.,]+)"),
            "peso_liquido": extract_field(item_text, r"Peso Líquido \(KG\)\s*([\d\.,]+)"),
            "quantidade_comercial": extract_field(item_text, r"Qtde Unid\. Comercial\s*([\d\.,]+)"),
            "descricao": extract_field(item_text, r"DENOMINACAO DO PRODUTO\s+(.*?)\s+CÓDIGO INTERNO", group=1).replace("\n", " "),
            # Impostos (Exemplos de captura, ajustar regex conforme necessidade exata)
            "ii_devido": extract_field(item_text, r"II.*?Valor Devido \(R\$\)\s*([\d\.,]+)"),
            "ipi_devido": extract_field(item_text, r"IPI.*?Valor Devido \(R\$\)\s*([\d\.,]+)"),
            "pis_devido": extract_field(item_text, r"PIS.*?Valor Devido \(R\$\)\s*([\d\.,]+)"),
            "cofins_devido": extract_field(item_text, r"COFINS.*?Valor Devido \(R\$\)\s*([\d\.,]+)"),
        }
        
        # Limpeza extra na descrição
        item_data["descricao"] = re.sub(r'\s+', ' ', item_data["descricao"]).strip()
        
        data["itens"].append(item_data)

    return data

# --- LÓGICA DE GERAÇÃO DO XML ---

def create_xml_structure(data):
    """
    Recebe o dicionário de dados e cria a árvore XML.
    """
    root = ET.Element("ListaDeclaracoes")
    duimp = ET.SubElement(root, "duimp")

    # Loop para criar as Adições
    for item in data["itens"]:
        adicao = ET.SubElement(duimp, "adicao")
        
        # Exemplo de mapeamento de campos (Isso deve ser expandido conforme todas as tags obrigatórias)
        
        # Tag <mercadoria>
        mercadoria = ET.SubElement(adicao, "mercadoria")
        ET.SubElement(mercadoria, "descricaoMercadoria").text = item["descricao"]
        ET.SubElement(mercadoria, "numeroSequencialItem").text = item["numero_adicao"][-2:] # Pega os 2 ultimos digitos
        
        # Formatação de valores numéricos para o padrão do XML (sem virgula, padded)
        qtd_fmt = format_number_xml(item["quantidade_comercial"], length=14)
        ET.SubElement(mercadoria, "quantidade").text = qtd_fmt
        
        # <numeroAdicao>
        ET.SubElement(adicao, "numeroAdicao").text = item["numero_adicao"]
        
        # <numeroDUIMP>
        ET.SubElement(adicao, "numeroDUIMP").text = data["header"].get("numero_duimp", "").replace("25BR", "") # Exemplo de limpeza
        
        # --- Impostos (Exemplo PIS/COFINS) ---
        # No seu XML de exemplo, os valores são inteiros longos sem virgula
        
        # Pis
        pis_val = format_number_xml(item["pis_devido"], length=15)
        ET.SubElement(adicao, "pisPasepAliquotaValorRecolher").text = pis_val
        
        # Cofins
        cofins_val = format_number_xml(item["cofins_devido"], length=15)
        ET.SubElement(adicao, "cofinsAliquotaValorRecolher").text = cofins_val
        
        # Dados Carga (Estático ou extraído)
        ET.SubElement(adicao, "dadosCargaViaTransporteNome").text = "MARÍTIMA"
        
        # Exemplo de dados da mercadoria NCM
        ET.SubElement(adicao, "dadosMercadoriaCodigoNcm").text = item["ncm"]
        
        # Peso Liquido
        peso_fmt = format_number_xml(item["peso_liquido"], length=15)
        ET.SubElement(adicao, "dadosMercadoriaPesoLiquido").text = peso_fmt

    # --- Tags Gerais da DUIMP (Irmãs das Adições no XML de exemplo, mas no ElementTree ficam dentro se não estruturar bem) ---
    # Nota: No seu XML de exemplo, <adicao> se repete. Tags como <importador> estão fora de <adicao>?
    # Verifiquei o XML anexado: <importador...> é irmão de <adicao> dentro de <duimp>.
    
    # Importador
    importador_nome = ET.SubElement(duimp, "importadorNome")
    importador_nome.text = data["header"].get("importador", "HAFELE BRASIL LTDA")
    
    # Informação Complementar (Pode ser fixa ou extraída)
    info_compl = ET.SubElement(duimp, "informacaoComplementar")
    info_compl.text = f"PROCESSO: {data['header'].get('processo', '')} - GERAÇÃO AUTOMÁTICA VIA STREAMLIT"

    return root

def prettify_xml(element):
    """Retorna uma string XML formatada e bonita."""
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

# --- INTERFACE STREAMLIT ---

def main():
    st.set_page_config(page_title="Conversor PDF DUIMP para XML", layout="wide")
    
    st.title("📄 Conversor de Extrato DUIMP (PDF) para XML")
    st.markdown("""
    Faça o upload do **Extrato de Conferência DUIMP (PDF)**. 
    O sistema extrairá os dados e gerará o XML no layout obrigatório.
    """)

    uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

    if uploaded_file is not None:
        st.success("Arquivo carregado com sucesso!")
        
        if st.button("Processar e Gerar XML"):
            with st.spinner("Processando dados..."):
                try:
                    # 1. Extrair Dados
                    extracted_data = parse_pdf_to_data(uploaded_file)
                    
                    # Mostrar prévia dos dados para conferência (Opcional)
                    with st.expander("Ver dados extraídos (Debug)"):
                        st.json(extracted_data)
                    
                    st.info(f"Foram encontrados {len(extracted_data['itens'])} itens na DUIMP.")

                    # 2. Gerar XML
                    xml_root = create_xml_structure(extracted_data)
                    xml_string = prettify_xml(xml_root)

                    # 3. Botão de Download
                    st.download_button(
                        label="📥 Baixar XML Gerado",
                        data=xml_string,
                        file_name=f"DUIMP_{extracted_data['header'].get('processo', 'S_N')}.xml",
                        mime="application/xml"
                    )
                    
                    # Prévia do XML na tela
                    st.subheader("Prévia do XML:")
                    st.code(xml_string, language="xml")

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
                    st.exception(e)

if __name__ == "__main__":
    main()
