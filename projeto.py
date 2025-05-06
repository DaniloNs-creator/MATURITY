import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import os
import base64
from io import BytesIO
import zipfile
import tempfile
from collections import defaultdict
import cssutils
import re

# Configuração inicial da página
st.set_page_config(
    page_title="Sistema de Apuração Fiscal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Criar arquivo CSS se não existir
if not os.path.exists("style.css"):
    with open("style.css", "w") as f:
        f.write("""
        /* Estilos gerais */
        body {
            font-family: 'Arial', sans-serif;
            color: #333;
        }
        
        /* Cabeçalho */
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        /* Botões de navegação */
        .nav-button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            margin: 0.2rem;
            border-radius: 0.3rem;
            cursor: pointer;
            width: 100%;
            text-align: left;
        }
        
        .nav-button:hover {
            background-color: #2980b9;
        }
        
        .nav-button.active {
            background-color: #2c3e50;
            font-weight: bold;
        }
        
        /* Cards de informações */
        .info-card {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Tabelas */
        .dataframe {
            width: 100%;
        }
        
        /* Inputs */
        .stTextInput>div>div>input {
            border-radius: 0.3rem;
            padding: 0.5rem;
        }
        
        /* Mensagens de sucesso */
        .success-message {
            color: #27ae60;
            font-weight: bold;
        }
        
        /* Mensagens de erro */
        .error-message {
            color: #e74c3c;
            font-weight: bold;
        }
        """)

local_css("style.css")

# Namespaces XML
ns = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'ds': 'http://www.w3.org/2000/09/xmldsig#'
}

# Classes para armazenamento de dados
class NotaFiscal:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.chave = self._extrair_chave()
        self.emitente = self._extrair_emitente()
        self.destinatario = self._extrair_destinatario()
        self.data_emissao = self._extrair_data_emissao()
        self.valor_total = self._extrair_valor_total()
        self.itens = self._extrair_itens()
        self.tipo_operacao = self._extrair_tipo_operacao()
        self.icms = self._extrair_icms()
        self.ipi = self._extrair_ipi()
        self.pis = self._extrair_pis()
        self.cofins = self._extrair_cofins()

    def _extrair_chave(self):
        inf_nfe = self.root.find('.//nfe:infNFe', ns)
        if inf_nfe is not None:
            return inf_nfe.attrib.get('Id')[3:]  # Remove 'NFe' do início
        return None

    def _extrair_emitente(self):
        emit = self.root.find('.//nfe:emit', ns)
        if emit is not None:
            return {
                'cnpj': emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else None,
                'nome': emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else None
            }
        return None

    def _extrair_destinatario(self):
        dest = self.root.find('.//nfe:dest', ns)
        if dest is not None:
            return {
                'cnpj': dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else None,
                'nome': dest.find('nfe:xNome', ns).text if dest.find('nfe:xNome', ns) is not None else None
            }
        return None

    def _extrair_data_emissao(self):
        ide = self.root.find('.//nfe:ide', ns)
        if ide is not None:
            dh_emissao = ide.find('nfe:dhEmi', ns)
            if dh_emissao is not None:
                return datetime.strptime(dh_emissao.text, '%Y-%m-%dT%H:%M:%S%z')
            
            d_emissao = ide.find('nfe:dEmi', ns)
            if d_emissao is not None:
                return datetime.strptime(d_emissao.text, '%Y-%m-%d')
        return None

    def _extrair_valor_total(self):
        total = self.root.find('.//nfe:total/nfe:ICMSTot', ns)
        if total is not None:
            return {
                'vProd': float(total.find('nfe:vProd', ns).text) if total.find('nfe:vProd', ns) is not None else 0.0,
                'vNF': float(total.find('nfe:vNF', ns).text) if total.find('nfe:vNF', ns) is not None else 0.0,
                'vICMS': float(total.find('nfe:vICMS', ns).text) if total.find('nfe:vICMS', ns) is not None else 0.0,
                'vST': float(total.find('nfe:vST', ns).text) if total.find('nfe:vST', ns) is not None else 0.0,
                'vIPI': float(total.find('nfe:vIPI', ns).text) if total.find('nfe:vIPI', ns) is not None else 0.0,
                'vPIS': float(total.find('nfe:vPIS', ns).text) if total.find('nfe:vPIS', ns) is not None else 0.0,
                'vCOFINS': float(total.find('nfe:vCOFINS', ns).text) if total.find('nfe:vCOFINS', ns) is not None else 0.0
            }
        return None

    def _extrair_itens(self):
        itens = []
        dets = self.root.findall('.//nfe:det', ns)
        for det in dets:
            prod = det.find('nfe:prod', ns)
            imposto = det.find('nfe:imposto', ns)
            
            item = {
                'nItem': det.attrib.get('nItem'),
                'cProd': prod.find('nfe:cProd', ns).text if prod.find('nfe:cProd', ns) is not None else None,
                'xProd': prod.find('nfe:xProd', ns).text if prod.find('nfe:xProd', ns) is not None else None,
                'NCM': prod.find('nfe:NCM', ns).text if prod.find('nfe:NCM', ns) is not None else None,
                'CFOP': prod.find('nfe:CFOP', ns).text if prod.find('nfe:CFOP', ns) is not None else None,
                'uCom': prod.find('nfe:uCom', ns).text if prod.find('nfe:uCom', ns) is not None else None,
                'qCom': float(prod.find('nfe:qCom', ns).text) if prod.find('nfe:qCom', ns) is not None else 0.0,
                'vUnCom': float(prod.find('nfe:vUnCom', ns).text) if prod.find('nfe:vUnCom', ns) is not None else 0.0,
                'vProd': float(prod.find('nfe:vProd', ns).text) if prod.find('nfe:vProd', ns) is not None else 0.0,
                'ICMS': self._extrair_icms_item(imposto),
                'IPI': self._extrair_ipi_item(imposto),
                'PIS': self._extrair_pis_item(imposto),
                'COFINS': self._extrair_cofins_item(imposto)
            }
            itens.append(item)
        return itens

    def _extrair_tipo_operacao(self):
        ide = self.root.find('.//nfe:ide', ns)
        if ide is not None:
            return ide.find('nfe:indOper', ns).text if ide.find('nfe:indOper', ns) is not None else None
        return None

    def _extrair_icms_item(self, imposto):
        icms = imposto.find('nfe:ICMS', ns)
        if icms is not None:
            # Verifica todos os possíveis tipos de ICMS
            for trib in icms:
                if trib.tag.endswith('ICMS00'):
                    return {
                        'tipo': '00',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS10'):
                    return {
                        'tipo': '10',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS20'):
                    return {
                        'tipo': '20',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0,
                        'pRedBC': float(trib.find('nfe:pRedBC', ns).text) if trib.find('nfe:pRedBC', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS30'):
                    return {
                        'tipo': '30',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS60'):
                    return {
                        'tipo': '60',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBCSTRet': float(trib.find('nfe:vBCSTRet', ns).text) if trib.find('nfe:vBCSTRet', ns) is not None else 0.0,
                        'vICMSSTRet': float(trib.find('nfe:vICMSSTRet', ns).text) if trib.find('nfe:vICMSSTRet', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS70'):
                    return {
                        'tipo': '70',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0,
                        'pRedBC': float(trib.find('nfe:pRedBC', ns).text) if trib.find('nfe:pRedBC', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMS90'):
                    return {
                        'tipo': '90',
                        'CST': trib.find('nfe:CST', ns).text if trib.find('nfe:CST', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0,
                        'pRedBC': float(trib.find('nfe:pRedBC', ns).text) if trib.find('nfe:pRedBC', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMSSN101'):
                    return {
                        'tipo': 'SN101',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None,
                        'pCredSN': float(trib.find('nfe:pCredSN', ns).text) if trib.find('nfe:pCredSN', ns) is not None else 0.0,
                        'vCredICMSSN': float(trib.find('nfe:vCredICMSSN', ns).text) if trib.find('nfe:vCredICMSSN', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMSSN102'):
                    return {
                        'tipo': 'SN102',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None
                    }
                elif trib.tag.endswith('ICMSSN201'):
                    return {
                        'tipo': 'SN201',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0,
                        'pCredSN': float(trib.find('nfe:pCredSN', ns).text) if trib.find('nfe:pCredSN', ns) is not None else 0.0,
                        'vCredICMSSN': float(trib.find('nfe:vCredICMSSN', ns).text) if trib.find('nfe:vCredICMSSN', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMSSN202'):
                    return {
                        'tipo': 'SN202',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMSSN500'):
                    return {
                        'tipo': 'SN500',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None,
                        'vBCSTRet': float(trib.find('nfe:vBCSTRet', ns).text) if trib.find('nfe:vBCSTRet', ns) is not None else 0.0,
                        'vICMSSTRet': float(trib.find('nfe:vICMSSTRet', ns).text) if trib.find('nfe:vICMSSTRet', ns) is not None else 0.0
                    }
                elif trib.tag.endswith('ICMSSN900'):
                    return {
                        'tipo': 'SN900',
                        'CSOSN': trib.find('nfe:CSOSN', ns).text if trib.find('nfe:CSOSN', ns) is not None else None,
                        'vBC': float(trib.find('nfe:vBC', ns).text) if trib.find('nfe:vBC', ns) is not None else 0.0,
                        'pICMS': float(trib.find('nfe:pICMS', ns).text) if trib.find('nfe:pICMS', ns) is not None else 0.0,
                        'vICMS': float(trib.find('nfe:vICMS', ns).text) if trib.find('nfe:vICMS', ns) is not None else 0.0,
                        'vBCST': float(trib.find('nfe:vBCST', ns).text) if trib.find('nfe:vBCST', ns) is not None else 0.0,
                        'pICMSST': float(trib.find('nfe:pICMSST', ns).text) if trib.find('nfe:pICMSST', ns) is not None else 0.0,
                        'vICMSST': float(trib.find('nfe:vICMSST', ns).text) if trib.find('nfe:vICMSST', ns) is not None else 0.0,
                        'pCredSN': float(trib.find('nfe:pCredSN', ns).text) if trib.find('nfe:pCredSN', ns) is not None else 0.0,
                        'vCredICMSSN': float(trib.find('nfe:vCredICMSSN', ns).text) if trib.find('nfe:vCredICMSSN', ns) is not None else 0.0
                    }
        return None

    def _extrair_ipi_item(self, imposto):
        ipi = imposto.find('nfe:IPI', ns)
        if ipi is not None:
            ipi_trib = ipi.find('nfe:IPITrib', ns)
            if ipi_trib is not None:
                return {
                    'CST': ipi_trib.find('nfe:CST', ns).text if ipi_trib.find('nfe:CST', ns) is not None else None,
                    'vBC': float(ipi_trib.find('nfe:vBC', ns).text) if ipi_trib.find('nfe:vBC', ns) is not None else 0.0,
                    'pIPI': float(ipi_trib.find('nfe:pIPI', ns).text) if ipi_trib.find('nfe:pIPI', ns) is not None else 0.0,
                    'vIPI': float(ipi_trib.find('nfe:vIPI', ns).text) if ipi_trib.find('nfe:vIPI', ns) is not None else 0.0
                }
            
            ipi_nt = ipi.find('nfe:IPINT', ns)
            if ipi_nt is not None:
                return {
                    'CST': ipi_nt.find('nfe:CST', ns).text if ipi_nt.find('nfe:CST', ns) is not None else None,
                    'vBC': 0.0,
                    'pIPI': 0.0,
                    'vIPI': 0.0
                }
        return None

    def _extrair_pis_item(self, imposto):
        pis = imposto.find('nfe:PIS', ns)
        if pis is not None:
            pis_aliq = pis.find('nfe:PISAliq', ns)
            if pis_aliq is not None:
                return {
                    'CST': pis_aliq.find('nfe:CST', ns).text if pis_aliq.find('nfe:CST', ns) is not None else None,
                    'vBC': float(pis_aliq.find('nfe:vBC', ns).text) if pis_aliq.find('nfe:vBC', ns) is not None else 0.0,
                    'pPIS': float(pis_aliq.find('nfe:pPIS', ns).text) if pis_aliq.find('nfe:pPIS', ns) is not None else 0.0,
                    'vPIS': float(pis_aliq.find('nfe:vPIS', ns).text) if pis_aliq.find('nfe:vPIS', ns) is not None else 0.0
                }
            
            pis_nt = pis.find('nfe:PISNT', ns)
            if pis_nt is not None:
                return {
                    'CST': pis_nt.find('nfe:CST', ns).text if pis_nt.find('nfe:CST', ns) is not None else None,
                    'vBC': 0.0,
                    'pPIS': 0.0,
                    'vPIS': 0.0
                }
            
            pis_outr = pis.find('nfe:PISOutr', ns)
            if pis_outr is not None:
                return {
                    'CST': pis_outr.find('nfe:CST', ns).text if pis_outr.find('nfe:CST', ns) is not None else None,
                    'vBC': float(pis_outr.find('nfe:vBC', ns).text) if pis_outr.find('nfe:vBC', ns) is not None else 0.0,
                    'pPIS': float(pis_outr.find('nfe:pPIS', ns).text) if pis_outr.find('nfe:pPIS', ns) is not None else 0.0,
                    'vPIS': float(pis_outr.find('nfe:vPIS', ns).text) if pis_outr.find('nfe:vPIS', ns) is not None else 0.0,
                    'qBCProd': float(pis_outr.find('nfe:qBCProd', ns).text) if pis_outr.find('nfe:qBCProd', ns) is not None else 0.0,
                    'vAliqProd': float(pis_outr.find('nfe:vAliqProd', ns).text) if pis_outr.find('nfe:vAliqProd', ns) is not None else 0.0
                }
        return None

    def _extrair_cofins_item(self, imposto):
        cofins = imposto.find('nfe:COFINS', ns)
        if cofins is not None:
            cofins_aliq = cofins.find('nfe:COFINSAliq', ns)
            if cofins_aliq is not None:
                return {
                    'CST': cofins_aliq.find('nfe:CST', ns).text if cofins_aliq.find('nfe:CST', ns) is not None else None,
                    'vBC': float(cofins_aliq.find('nfe:vBC', ns).text) if cofins_aliq.find('nfe:vBC', ns) is not None else 0.0,
                    'pCOFINS': float(cofins_aliq.find('nfe:pCOFINS', ns).text) if cofins_aliq.find('nfe:pCOFINS', ns) is not None else 0.0,
                    'vCOFINS': float(cofins_aliq.find('nfe:vCOFINS', ns).text) if cofins_aliq.find('nfe:vCOFINS', ns) is not None else 0.0
                }
            
            cofins_nt = cofins.find('nfe:COFINSNT', ns)
            if cofins_nt is not None:
                return {
                    'CST': cofins_nt.find('nfe:CST', ns).text if cofins_nt.find('nfe:CST', ns) is not None else None,
                    'vBC': 0.0,
                    'pCOFINS': 0.0,
                    'vCOFINS': 0.0
                }
            
            cofins_outr = cofins.find('nfe:COFINSOutr', ns)
            if cofins_outr is not None:
                return {
                    'CST': cofins_outr.find('nfe:CST', ns).text if cofins_outr.find('nfe:CST', ns) is not None else None,
                    'vBC': float(cofins_outr.find('nfe:vBC', ns).text) if cofins_outr.find('nfe:vBC', ns) is not None else 0.0,
                    'pCOFINS': float(cofins_outr.find('nfe:pCOFINS', ns).text) if cofins_outr.find('nfe:pCOFINS', ns) is not None else 0.0,
                    'vCOFINS': float(cofins_outr.find('nfe:vCOFINS', ns).text) if cofins_outr.find('nfe:vCOFINS', ns) is not None else 0.0,
                    'qBCProd': float(cofins_outr.find('nfe:qBCProd', ns).text) if cofins_outr.find('nfe:qBCProd', ns) is not None else 0.0,
                    'vAliqProd': float(cofins_outr.find('nfe:vAliqProd', ns).text) if cofins_outr.find('nfe:vAliqProd', ns) is not None else 0.0
                }
        return None

    def _extrair_icms(self):
        icms = {
            'vICMS': 0.0,
            'vST': 0.0,
            'vFCP': 0.0,
            'vFCPST': 0.0,
            'vFCPSTRet': 0.0,
            'vICMSDeson': 0.0,
            'vICMSOp': 0.0,
            'vICMSDIF': 0.0,
            'vICMSST': 0.0
        }
        
        total = self.root.find('.//nfe:total/nfe:ICMSTot', ns)
        if total is not None:
            icms['vICMS'] = float(total.find('nfe:vICMS', ns).text) if total.find('nfe:vICMS', ns) is not None else 0.0
            icms['vST'] = float(total.find('nfe:vST', ns).text) if total.find('nfe:vST', ns) is not None else 0.0
            icms['vFCP'] = float(total.find('nfe:vFCP', ns).text) if total.find('nfe:vFCP', ns) is not None else 0.0
            icms['vFCPST'] = float(total.find('nfe:vFCPST', ns).text) if total.find('nfe:vFCPST', ns) is not None else 0.0
            icms['vFCPSTRet'] = float(total.find('nfe:vFCPSTRet', ns).text) if total.find('nfe:vFCPSTRet', ns) is not None else 0.0
            icms['vICMSDeson'] = float(total.find('nfe:vICMSDeson', ns).text) if total.find('nfe:vICMSDeson', ns) is not None else 0.0
            icms['vICMSOp'] = float(total.find('nfe:vICMSOp', ns).text) if total.find('nfe:vICMSOp', ns) is not None else 0.0
            icms['vICMSDIF'] = float(total.find('nfe:vICMSDIF', ns).text) if total.find('nfe:vICMSDIF', ns) is not None else 0.0
            icms['vICMSST'] = float(total.find('nfe:vICMSST', ns).text) if total.find('nfe:vICMSST', ns) is not None else 0.0
        
        return icms

    def _extrair_ipi(self):
        ipi = {
            'vIPI': 0.0
        }
        
        total = self.root.find('.//nfe:total/nfe:IPITot', ns)
        if total is not None:
            ipi['vIPI'] = float(total.find('nfe:vIPI', ns).text) if total.find('nfe:vIPI', ns) is not None else 0.0
        
        return ipi

    def _extrair_pis(self):
        pis = {
            'vPIS': 0.0
        }
        
        total = self.root.find('.//nfe:total/nfe:PISTot', ns)
        if total is not None:
            pis['vPIS'] = float(total.find('nfe:vPIS', ns).text) if total.find('nfe:vPIS', ns) is not None else 0.0
        
        return pis

    def _extrair_cofins(self):
        cofins = {
            'vCOFINS': 0.0
        }
        
        total = self.root.find('.//nfe:total/nfe:COFINSTot', ns)
        if total is not None:
            cofins['vCOFINS'] = float(total.find('nfe:vCOFINS', ns).text) if total.find('nfe:vCOFINS', ns) is not None else 0.0
        
        return cofins

class ApuracaoFiscal:
    def __init__(self):
        self.notas = []
        self.cnpj_empresa = None
        self.periodo_inicio = None
        self.periodo_fim = None
    
    def adicionar_nota(self, nota):
        self.notas.append(nota)
    
    def definir_cnpj_empresa(self, cnpj):
        self.cnpj_empresa = cnpj
    
    def definir_periodo(self, inicio, fim):
        self.periodo_inicio = inicio
        self.periodo_fim = fim
    
    def calcular_icms(self):
        debito = 0.0
        credito = 0.0
        st = 0.0
        difal = 0.0
        
        for nota in self.notas:
            # Verifica se a nota está dentro do período definido
            if self.periodo_inicio and self.periodo_fim:
                if not (self.periodo_inicio <= nota.data_emissao.date() <= self.periodo_fim):
                    continue
            
            # Verifica se a nota é de entrada ou saída para o CNPJ da empresa
            if nota.emitente['cnpj'] == self.cnpj_empresa:
                # Nota de saída (débito)
                debito += nota.valor_total['vICMS']
                st += nota.valor_total['vST']
            elif nota.destinatario['cnpj'] == self.cnpj_empresa:
                # Nota de entrada (crédito)
                credito += nota.valor_total['vICMS']
                
                # Cálculo do DIFAL (se aplicável)
                if nota.emitente['cnpj'] and nota.destinatario['cnpj']:
                    # Verifica se é operação interestadual
                    uf_emitente = nota.emitente['cnpj'][:2]  # Simplificação - na prática, deveria pegar a UF do emitente
                    uf_destino = nota.destinatario['cnpj'][:2]  # Simplificação
                    
                    if uf_emitente != uf_destino:
                        # Calcula o DIFAL (simplificado)
                        aliquota_interna = 0.18  # Exemplo - deveria ser obtido de uma tabela por UF e NCM
                        aliquota_interestadual = 0.12  # Exemplo
                        difal += (nota.valor_total['vProd'] * (aliquota_interna - aliquota_interestadual))
        
        return {
            'Débito': debito,
            'Crédito': credito,
            'Saldo': debito - credito,
            'ST': st,
            'DIFAL': difal
        }
    
    def calcular_ipi(self):
        debito = 0.0
        credito = 0.0
        
        for nota in self.notas:
            if self.periodo_inicio and self.periodo_fim:
                if not (self.periodo_inicio <= nota.data_emissao.date() <= self.periodo_fim):
                    continue
            
            if nota.emitente['cnpj'] == self.cnpj_empresa:
                debito += nota.valor_total['vIPI']
            elif nota.destinatario['cnpj'] == self.cnpj_empresa:
                credito += nota.valor_total['vIPI']
        
        return {
            'Débito': debito,
            'Crédito': credito,
            'Saldo': debito - credito
        }
    
    def calcular_pis(self):
        debito = 0.0
        credito = 0.0
        
        for nota in self.notas:
            if self.periodo_inicio and self.periodo_fim:
                if not (self.periodo_inicio <= nota.data_emissao.date() <= self.periodo_fim):
                    continue
            
            if nota.emitente['cnpj'] == self.cnpj_empresa:
                debito += nota.valor_total['vPIS']
            elif nota.destinatario['cnpj'] == self.cnpj_empresa:
                credito += nota.valor_total['vPIS']
        
        return {
            'Débito': debito,
            'Crédito': credito,
            'Saldo': debito - credito
        }
    
    def calcular_cofins(self):
        debito = 0.0
        credito = 0.0
        
        for nota in self.notas:
            if self.periodo_inicio and self.periodo_fim:
                if not (self.periodo_inicio <= nota.data_emissao.date() <= self.periodo_fim):
                    continue
            
            if nota.emitente['cnpj'] == self.cnpj_empresa:
                debito += nota.valor_total['vCOFINS']
            elif nota.destinatario['cnpj'] == self.cnpj_empresa:
                credito += nota.valor_total['vCOFINS']
        
        return {
            'Débito': debito,
            'Crédito': credito,
            'Saldo': debito - credito
        }

# Funções auxiliares
def processar_arquivos(uploaded_files, apuracao):
    notas_processadas = 0
    erros = 0
    
    for uploaded_file in uploaded_files:
        try:
            # Salvar o arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Verificar se é um arquivo ZIP
            if uploaded_file.name.lower().endswith('.zip'):
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    # Extrair todos os arquivos XML
                    for file_info in zip_ref.infolist():
                        if file_info.filename.lower().endswith('.xml'):
                            with zip_ref.open(file_info) as xml_file:
                                xml_content = xml_file.read()
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as xml_tmp:
                                    xml_tmp.write(xml_content)
                                    xml_tmp_path = xml_tmp.name
                                
                                try:
                                    nota = NotaFiscal(xml_tmp_path)
                                    apuracao.adicionar_nota(nota)
                                    notas_processadas += 1
                                except ET.ParseError:
                                    erros += 1
                                finally:
                                    os.unlink(xml_tmp_path)
            else:
                # Processar arquivo XML individual
                try:
                    nota = NotaFiscal(tmp_path)
                    apuracao.adicionar_nota(nota)
                    notas_processadas += 1
                except ET.ParseError:
                    erros += 1
        except Exception as e:
            erros += 1
            st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    return notas_processadas, erros

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mostrar_resumo_apuracao(apuracao):
    st.subheader("Resumo da Apuração")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Notas", len(apuracao.notas))
    
    with col2:
        if apuracao.periodo_inicio and apuracao.periodo_fim:
            st.metric("Período", f"{apuracao.periodo_inicio.strftime('%d/%m/%Y')} a {apuracao.periodo_fim.strftime('%d/%m/%Y')}")
        else:
            st.metric("Período", "Não definido")
    
    with col3:
        st.metric("CNPJ", apuracao.cnpj_empresa if apuracao.cnpj_empresa else "Não informado")

# Estado da aplicação
if 'apuracao' not in st.session_state:
    st.session_state.apuracao = ApuracaoFiscal()

# Navegação
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Selecione a página:", 
                         ["Início", "ICMS", "IPI", "PIS", "COFINS", "Importar XMLs"])

# Página Inicial
if pagina == "Início":
    st.title("Sistema de Apuração Fiscal")
    st.markdown("""
    <div class="header">
        <h2>Bem-vindo ao Sistema de Apuração de ICMS, IPI, PIS e COFINS</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <h3>Instruções:</h3>
        <ol>
            <li>Informe o CNPJ da empresa na página "Importar XMLs"</li>
            <li>Defina o período de apuração</li>
            <li>Importe os arquivos XML das notas fiscais</li>
            <li>Navegue pelas abas para visualizar as apurações de cada imposto</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <h3>Funcionalidades:</h3>
        <ul>
            <li>Apuração de ICMS (incluindo ST e DIFAL)</li>
            <li>Apuração de IPI</li>
            <li>Apuração de PIS</li>
            <li>Apuração de COFINS</li>
            <li>Importação de múltiplos arquivos XML ou ZIP</li>
            <li>Filtro por período</li>
            <li>Relatórios detalhados</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Página de Importação de XMLs
elif pagina == "Importar XMLs":
    st.title("Importação de Arquivos XML")
    
    # Input do CNPJ
    cnpj = st.text_input("Informe o CNPJ da empresa (somente números):", 
                        value=st.session_state.apuracao.cnpj_empresa or "")
    
    if cnpj:
        # Validar CNPJ
        if len(cnpj) == 14 and cnpj.isdigit():
            st.session_state.apuracao.definir_cnpj_empresa(cnpj)
            st.success("CNPJ válido e salvo com sucesso!")
        else:
            st.error("CNPJ inválido. Deve conter 14 dígitos numéricos.")
    
    # Período de apuração
    st.subheader("Período de Apuração")
    col1, col2 = st.columns(2)
    
    with col1:
        data_inicio = st.date_input("Data inicial:", 
                                  value=st.session_state.apuracao.periodo_inicio or datetime.today().replace(day=1))
    
    with col2:
        data_fim = st.date_input("Data final:", 
                               value=st.session_state.apuracao.periodo_fim or datetime.today())
    
    if st.button("Definir Período"):
        st.session_state.apuracao.definir_periodo(data_inicio, data_fim)
        st.success(f"Período definido: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    # Upload de arquivos
    st.subheader("Importar Arquivos")
    uploaded_files = st.file_uploader("Selecione os arquivos XML ou ZIP contendo XMLs:", 
                                    type=["xml", "zip"], 
                                    accept_multiple_files=True)
    
    if uploaded_files and st.button("Processar Arquivos"):
        with st.spinner("Processando arquivos..."):
            notas_processadas, erros = processar_arquivos(uploaded_files, st.session_state.apuracao)
            
            if notas_processadas > 0:
                st.success(f"{notas_processadas} nota(s) fiscal(is) processada(s) com sucesso!")
            if erros > 0:
                st.error(f"{erros} arquivo(s) com erro(s) no processamento.")
    
    # Resumo
    if st.session_state.apuracao.notas:
        mostrar_resumo_apuracao(st.session_state.apuracao)
        
        st.subheader("Últimas Notas Processadas")
        ultimas_notas = st.session_state.apuracao.notas[-5:] if len(st.session_state.apuracao.notas) > 5 else st.session_state.apuracao.notas
        for nota in reversed(ultimas_notas):
            with st.expander(f"Nota {nota.chave} - {nota.data_emissao.strftime('%d/%m/%Y')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Emitente:** {nota.emitente['nome']} ({nota.emitente['cnpj']})")
                    st.write(f"**Destinatário:** {nota.destinatario['nome']} ({nota.destinatario['cnpj']})")
                with col2:
                    st.write(f"**Valor Total:** {formatar_moeda(nota.valor_total['vNF'])}")
                    st.write(f"**Operação:** {'Saída' if nota.emitente['cnpj'] == st.session_state.apuracao.cnpj_empresa else 'Entrada'}")

# Página de ICMS
elif pagina == "ICMS":
    st.title("Apuração de ICMS")
    
    if not st.session_state.apuracao.cnpj_empresa:
        st.warning("Por favor, informe o CNPJ da empresa na página 'Importar XMLs' antes de prosseguir.")
        st.stop()
    
    if not st.session_state.apuracao.notas:
        st.warning("Nenhuma nota fiscal foi importada ainda. Por favor, importe os arquivos XML na página 'Importar XMLs'.")
        st.stop()
    
    mostrar_resumo_apuracao(st.session_state.apuracao)
    
    # Cálculo do ICMS
    resultado_icms = st.session_state.apuracao.calcular_icms()
    
    st.subheader("Resultado da Apuração")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Débito", formatar_moeda(resultado_icms['Débito']))
    
    with col2:
        st.metric("Crédito", formatar_moeda(resultado_icms['Crédito']))
    
    with col3:
        st.metric("Saldo", formatar_moeda(resultado_icms['Saldo']), 
                delta_color="inverse" if resultado_icms['Saldo'] < 0 else "normal")
    
    with col4:
        st.metric("ST", formatar_moeda(resultado_icms['ST']))
    
    with col5:
        st.metric("DIFAL", formatar_moeda(resultado_icms['DIFAL']))
    
    # Detalhamento
    st.subheader("Detalhamento por Nota Fiscal")
    
    # Filtrar por tipo de operação
    tipo_operacao = st.radio("Filtrar por:", ["Todas", "Débito", "Crédito"], horizontal=True)
    
    # Criar DataFrame com os dados
    dados = []
    for nota in st.session_state.apuracao.notas:
        if st.session_state.apuracao.periodo_inicio and st.session_state.apuracao.periodo_fim:
            if not (st.session_state.apuracao.periodo_inicio <= nota.data_emissao.date() <= st.session_state.apuracao.periodo_fim):
                continue
        
        if nota.emitente['cnpj'] == st.session_state.apuracao.cnpj_empresa:
            tipo = "Débito"
        else:
            tipo = "Crédito"
        
        if tipo_operacao != "Todas" and tipo != tipo_operacao:
            continue
        
        dados.append({
            'Chave': nota.chave,
            'Data': nota.data_emissao.strftime('%d/%m/%Y'),
            'Emitente': nota.emitente['nome'],
            'Destinatário': nota.destinatario['nome'],
            'Tipo': tipo,
            'Valor ICMS': nota.valor_total['vICMS'],
            'Valor ST': nota.valor_total['vST'],
            'Valor Total': nota.valor_total['vNF']
        })
    
    df = pd.DataFrame(dados)
    
    if not df.empty:
        # Formatar valores monetários
        df['Valor ICMS'] = df['Valor ICMS'].apply(lambda x: formatar_moeda(x))
        df['Valor ST'] = df['Valor ST'].apply(lambda x: formatar_moeda(x))
        df['Valor Total'] = df['Valor Total'].apply(lambda x: formatar_moeda(x))
        
        st.dataframe(df, use_container_width=True)
        
        # Botão para exportar
        csv = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
        st.download_button(
            label="Exportar para CSV",
            data=csv,
            file_name="apuracao_icms.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma nota fiscal encontrada com os filtros selecionados.")

# Página de IPI
elif pagina == "IPI":
    st.title("Apuração de IPI")
    
    if not st.session_state.apuracao.cnpj_empresa:
        st.warning("Por favor, informe o CNPJ da empresa na página 'Importar XMLs' antes de prosseguir.")
        st.stop()
    
    if not st.session_state.apuracao.notas:
        st.warning("Nenhuma nota fiscal foi importada ainda. Por favor, importe os arquivos XML na página 'Importar XMLs'.")
        st.stop()
    
    mostrar_resumo_apuracao(st.session_state.apuracao)
    
    # Cálculo do IPI
    resultado_ipi = st.session_state.apuracao.calcular_ipi()
    
    st.subheader("Resultado da Apuração")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Débito", formatar_moeda(resultado_ipi['Débito']))
    
    with col2:
        st.metric("Crédito", formatar_moeda(resultado_ipi['Crédito']))
    
    with col3:
        st.metric("Saldo", formatar_moeda(resultado_ipi['Saldo']), 
                delta_color="inverse" if resultado_ipi['Saldo'] < 0 else "normal")
    
    # Detalhamento
    st.subheader("Detalhamento por Nota Fiscal")
    
    # Filtrar por tipo de operação
    tipo_operacao = st.radio("Filtrar por:", ["Todas", "Débito", "Crédito"], horizontal=True)
    
    # Criar DataFrame com os dados
    dados = []
    for nota in st.session_state.apuracao.notas:
        if st.session_state.apuracao.periodo_inicio and st.session_state.apuracao.periodo_fim:
            if not (st.session_state.apuracao.periodo_inicio <= nota.data_emissao.date() <= st.session_state.apuracao.periodo_fim):
                continue
        
        if nota.emitente['cnpj'] == st.session_state.apuracao.cnpj_empresa:
            tipo = "Débito"
        else:
            tipo = "Crédito"
        
        if tipo_operacao != "Todas" and tipo != tipo_operacao:
            continue
        
        dados.append({
            'Chave': nota.chave,
            'Data': nota.data_emissao.strftime('%d/%m/%Y'),
            'Emitente': nota.emitente['nome'],
            'Destinatário': nota.destinatario['nome'],
            'Tipo': tipo,
            'Valor IPI': nota.valor_total['vIPI'],
            'Valor Total': nota.valor_total['vNF']
        })
    
    df = pd.DataFrame(dados)
    
    if not df.empty:
        # Formatar valores monetários
        df['Valor IPI'] = df['Valor IPI'].apply(lambda x: formatar_moeda(x))
        df['Valor Total'] = df['Valor Total'].apply(lambda x: formatar_moeda(x))
        
        st.dataframe(df, use_container_width=True)
        
        # Botão para exportar
        csv = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
        st.download_button(
            label="Exportar para CSV",
            data=csv,
            file_name="apuracao_ipi.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma nota fiscal encontrada com os filtros selecionados.")

# Página de PIS
elif pagina == "PIS":
    st.title("Apuração de PIS")
    
    if not st.session_state.apuracao.cnpj_empresa:
        st.warning("Por favor, informe o CNPJ da empresa na página 'Importar XMLs' antes de prosseguir.")
        st.stop()
    
    if not st.session_state.apuracao.notas:
        st.warning("Nenhuma nota fiscal foi importada ainda. Por favor, importe os arquivos XML na página 'Importar XMLs'.")
        st.stop()
    
    mostrar_resumo_apuracao(st.session_state.apuracao)
    
    # Cálculo do PIS
    resultado_pis = st.session_state.apuracao.calcular_pis()
    
    st.subheader("Resultado da Apuração")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Débito", formatar_moeda(resultado_pis['Débito']))
    
    with col2:
        st.metric("Crédito", formatar_moeda(resultado_pis['Crédito']))
    
    with col3:
        st.metric("Saldo", formatar_moeda(resultado_pis['Saldo']), 
                delta_color="inverse" if resultado_pis['Saldo'] < 0 else "normal")
    
    # Detalhamento
    st.subheader("Detalhamento por Nota Fiscal")
    
    # Filtrar por tipo de operação
    tipo_operacao = st.radio("Filtrar por:", ["Todas", "Débito", "Crédito"], horizontal=True)
    
    # Criar DataFrame com os dados
    dados = []
    for nota in st.session_state.apuracao.notas:
        if st.session_state.apuracao.periodo_inicio and st.session_state.apuracao.periodo_fim:
            if not (st.session_state.apuracao.periodo_inicio <= nota.data_emissao.date() <= st.session_state.apuracao.periodo_fim):
                continue
        
        if nota.emitente['cnpj'] == st.session_state.apuracao.cnpj_empresa:
            tipo = "Débito"
        else:
            tipo = "Crédito"
        
        if tipo_operacao != "Todas" and tipo != tipo_operacao:
            continue
        
        dados.append({
            'Chave': nota.chave,
            'Data': nota.data_emissao.strftime('%d/%m/%Y'),
            'Emitente': nota.emitente['nome'],
            'Destinatário': nota.destinatario['nome'],
            'Tipo': tipo,
            'Valor PIS': nota.valor_total['vPIS'],
            'Valor Total': nota.valor_total['vNF']
        })
    
    df = pd.DataFrame(dados)
    
    if not df.empty:
        # Formatar valores monetários
        df['Valor PIS'] = df['Valor PIS'].apply(lambda x: formatar_moeda(x))
        df['Valor Total'] = df['Valor Total'].apply(lambda x: formatar_moeda(x))
        
        st.dataframe(df, use_container_width=True)
        
        # Botão para exportar
        csv = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
        st.download_button(
            label="Exportar para CSV",
            data=csv,
            file_name="apuracao_pis.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma nota fiscal encontrada com os filtros selecionados.")

# Página de COFINS
elif pagina == "COFINS":
    st.title("Apuração de COFINS")
    
    if not st.session_state.apuracao.cnpj_empresa:
        st.warning("Por favor, informe o CNPJ da empresa na página 'Importar XMLs' antes de prosseguir.")
        st.stop()
    
    if not st.session_state.apuracao.notas:
        st.warning("Nenhuma nota fiscal foi importada ainda. Por favor, importe os arquivos XML na página 'Importar XMLs'.")
        st.stop()
    
    mostrar_resumo_apuracao(st.session_state.apuracao)
    
    # Cálculo do COFINS
    resultado_cofins = st.session_state.apuracao.calcular_cofins()
    
    st.subheader("Resultado da Apuração")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Débito", formatar_moeda(resultado_cofins['Débito']))
    
    with col2:
        st.metric("Crédito", formatar_moeda(resultado_cofins['Crédito']))
    
    with col3:
        st.metric("Saldo", formatar_moeda(resultado_cofins['Saldo']), 
                delta_color="inverse" if resultado_cofins['Saldo'] < 0 else "normal")
    
    # Detalhamento
    st.subheader("Detalhamento por Nota Fiscal")
    
    # Filtrar por tipo de operação
    tipo_operacao = st.radio("Filtrar por:", ["Todas", "Débito", "Crédito"], horizontal=True)
    
    # Criar DataFrame com os dados
    dados = []
    for nota in st.session_state.apuracao.notas:
        if st.session_state.apuracao.periodo_inicio and st.session_state.apuracao.periodo_fim:
            if not (st.session_state.apuracao.periodo_inicio <= nota.data_emissao.date() <= st.session_state.apuracao.periodo_fim):
                continue
        
        if nota.emitente['cnpj'] == st.session_state.apuracao.cnpj_empresa:
            tipo = "Débito"
        else:
            tipo = "Crédito"
        
        if tipo_operacao != "Todas" and tipo != tipo_operacao:
            continue
        
        dados.append({
            'Chave': nota.chave,
            'Data': nota.data_emissao.strftime('%d/%m/%Y'),
            'Emitente': nota.emitente['nome'],
            'Destinatário': nota.destinatario['nome'],
            'Tipo': tipo,
            'Valor COFINS': nota.valor_total['vCOFINS'],
            'Valor Total': nota.valor_total['vNF']
        })
    
    df = pd.DataFrame(dados)
    
    if not df.empty:
        # Formatar valores monetários
        df['Valor COFINS'] = df['Valor COFINS'].apply(lambda x: formatar_moeda(x))
        df['Valor Total'] = df['Valor Total'].apply(lambda x: formatar_moeda(x))
        
        st.dataframe(df, use_container_width=True)
        
        # Botão para exportar
        csv = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
        st.download_button(
            label="Exportar para CSV",
            data=csv,
            file_name="apuracao_cofins.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma nota fiscal encontrada com os filtros selecionados.")
