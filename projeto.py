# -*- coding: utf-8 -*-
"""
Confiábil — Painel de Controle 2026
Réplica fiel em Python/Streamlit + SQLite do controle de entregas por área
(Contabilidade, Fiscal, Recursos Humanos, Societário) para 137 empresas ativas.

Estrutura replicada da planilha original (verificada campo a campo):
  - Contabilidade: por mês -> Status(Balancete) + Link + Extratos Recebidos + Link(Extrato)
                    anual  -> Status(ECD) + Link, Status(ECF) + Link
                    % Conclusão conta Status E Extratos igualmente (26 campos)
  - Fiscal / RH / Societário: por mês -> Status + Link (12 meses, sem Extratos)
                    % Conclusão conta apenas os 12 campos de Status
  - Agenda: Reuniões Agendadas + Saídas Particulares (tabelas próprias) + calendário mensal
  - Relatórios / Declarações / Reembolso: abas placeholder (estrutura a definir)

Persistência: banco SQLite local (confiabil.db), criado e populado automaticamente
na primeira execução. Os dados sobrevivem a reinícios do app (diferente de
st.session_state, que se perde ao fechar a aba do navegador).

Execução:
    pip install -r requirements.txt
    streamlit run app.py
"""

import contextlib
import io
import os
import sqlite3
from datetime import datetime, date
import calendar as pycalendar

import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ──────────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "confiabil.db")

st.set_page_config(
    page_title="Confiábil | Painel de Controle 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main { background-color: #f7f8fa; }
        [data-testid="stSidebar"] { background-color: #10233f; }
        [data-testid="stSidebar"] * { color: #e8edf5 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }
        h1, h2, h3 { color: #10233f; font-family: "Segoe UI", sans-serif; }
        .kpi-card {
            background: #ffffff; border-radius: 12px; padding: 18px 20px;
            border: 1px solid #e6e9ef; box-shadow: 0 1px 3px rgba(16,35,63,0.06);
        }
        .kpi-label { font-size: 0.80rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }
        .kpi-value { font-size: 1.9rem; color: #10233f; font-weight: 700; }
        .kpi-sub   { font-size: 0.78rem; color: #9aa4b2; }
        .placeholder-box {
            background:#fff8e6; border:1px solid #f0d78c; border-radius:10px;
            padding:16px 20px; color:#6b5300;
        }
        .day-cell {
            border:1px solid #e6e9ef; border-radius:8px; padding:6px 8px; min-height:70px;
            background:#fff; font-size:0.8rem;
        }
        .day-num { font-weight:700; color:#10233f; }
        .stTabs [data-baseweb="tab"] { font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


EMPRESAS_CSV = """codigo,cnpj,razao_social,municipio,regime,atividade,responsavel,contato,telefone,email
1,82.016.981/0001-20,ARRATA & ARRATA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,CARMEN REGINA ARRATA,CARMEN,(41) 99199-7744,carmen@vctpromo.com
1.2,82.016.981/0002-00,ARRATA & ARRATA LTDA (Filial Armazém do Jardim),CURITIBA-PR,SIMPLES,SERVIÇOS,CARMEN REGINA ARRATA,CARMEN,(41) 99199-7744,carmen@vctpromo.com
1.3,82.016.981/0003-91,ARRATA & ARRATA LTDA (Filial Empório Gran Reserva Muller),CURITIBA-PR,SIMPLES,SERVIÇOS,CARMEN REGINA ARRATA,CARMEN,(41) 99199-7744,carmen@vctpromo.com
1.4,82.016.981/0004-72,ARRATA & ARRATA LTDA (Filial Empório Gran Reserva Curitiba),CURITIBA-PR,SIMPLES,SERVIÇOS,CARMEN REGINA ARRATA,CARMEN,(41) 99199-7744,carmen@vctpromo.com
2,03.490.566/0001-37,VCT SERVICOS TEMPORARIOS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,CARMEN REGINA ARRATA,CARMEN,(41) 99199-7744,carmen@vctpromo.com
3,11.282.962/0001-05,FELIPE POHL DE SOUZA - IMPRESSAO DE FOTOS RAPIDAS,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE POHL DE SOUZA,FELIPE,(41) 99199-7744,felipe@example.com
3.2,11.282.962/0002-88,FELIPE POHL DE SOUZA - IMPRESSAO DE FOTOS RAPIDAS,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE POHL DE SOUZA,FELIPE,(41) 99199-7744,felipe@example.com
3.3,11.282.962/0003-69,FELIPE POHL DE SOUZA - IMPRESSAO DE FOTOS RAPIDAS,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE POHL DE SOUZA,FELIPE,(41) 99199-7744,felipe@example.com
3.4,11.282.962/0004-40,FELIPE POHL DE SOUZA - IMPRESSAO DE FOTOS RAPIDAS,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE POHL DE SOUZA,FELIPE,(41) 99199-7744,felipe@example.com
3.5,11.282.962/0005-20,FELIPE POHL DE SOUZA - IMPRESSAO DE FOTOS RAPIDAS,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE POHL DE SOUZA,FELIPE,(41) 99199-7744,felipe@example.com
4,00.407.461/0001-83,IMIX MASSAS ALIMENTICIAS LTDA,CURITIBA-PR,SIMPLES,INDÚSTRIA,ELENA MARGARITA DE LA CARIDAD ALFIERO GALLEGOS,ELENA,(41) 99199-7744,elena@example.com
5,10.655.437/0001-17,C.A.B. DE CAMARGO - RETIFICA DE MOTORES,CURITIBA-PR,SIMPLES,SERVIÇOS,CARLOS ALBERTO BARBOSA DE CAMARGO,CARLOS,(41) 99199-7744,carlos@example.com
6,08.960.794/0001-47,REDEMPTORIS COMERCIO IMPORTACAO E EXPORTACAO LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,EMERSON GOMES,EMERSON,(41) 99199-7744,emerson@example.com
7,65.313.411/0001-82,ALMEIDA ROCHA PRESTACAO DE SERVICOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ANDRESSA ALMEIDA,ANDRESSA,(41) 99199-7744,andressa@example.com
9,65.342.456/0001-85,ALTHEA MEDICAL LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,FABIO LAGE,FABIO,(41) 99199-7744,fabio@example.com
12,59.215.134/0001-72,GN CLIMATIZACAO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,GUILHERME NASCIMENTO DE CAMARGO,GUILHERME,(41) 99199-7744,guilherme@example.com
13,08.333.495/0001-82,PAYTON CORDEIRO ENTREGAS E COLETAS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,OSVALDO CORDEIRO PINTO,OSVALDO,(41) 99199-7744,osvaldo@example.com
14,16.743.923/0001-73,ANDERSON JOSIAS VITZKI,CURITIBA-PR,SIMPLES,SERVIÇOS,ANDERSON JOSIAS VITZKI,ANDERSON,(41) 99199-7744,anderson@example.com
15,26.018.072/0001-50,PEDRO DOMINGOS DOS SANTOS,CURITIBA-PR,SIMPLES,SERVIÇOS,PEDRO DOMINGOS DOS SANTOS,PEDRO,(41) 99199-7744,pedro@example.com
17,30.022.940/0001-42,GELOPIA FABRICA DE GELO LTDA,CURITIBA-PR,SIMPLES,INDÚSTRIA,CRISTIANE DE CARVALHO SILVA,CRISTIANE,(41) 99199-7744,cristiane@example.com
18,29.981.521/0001-59,JOAO ALVARO PEDROSO RIBAS,CURITIBA-PR,SIMPLES,SERVIÇOS,JOAO ALVARO PEDROSO RIBAS,JOAO,(41) 99199-7744,joao@example.com
19,40.322.168/0001-38,SABLIER COMERCIO DE VESTUARIOS E ACESSORIOS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,OSWALDO DIAS DOS SANTOS JUNIOR,OSWALDO,(41) 99199-7744,oswaldo@example.com
21,61.564.729/0001-85,PIZZARIA SCALLA GUAÍRA,GUAIRA-PR,SIMPLES,COMÉRCIO,KAYNARA KARLA NUNES PEREIRA,KAYNARA,(41) 99199-7744,kaynara@example.com
22,30.222.036/0001-80,MABECO COMERCIO E CONFECCAO LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,ALEKSANDRO DE OLIVEIRA,ALEKSANDRO,(41) 99199-7744,aleksandro@example.com
23,63.671.479/0001-08,DR PIERO PERICIAS MEDICAS S/S,CURITIBA-PR,SIMPLES,SERVIÇOS,PIERO VICTOR DEKI SERUR,PIERO,(41) 99199-7744,piero@example.com
24,12.028.231/0001-92,PREISS UNION – ADMINISTRAÇÃO E CORRETAGEM DE SEGUROS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,LUCILIA PREISS,LUCILIA,(41) 99199-7744,lucilia@example.com
27,64.075.545/0001-40,CAPIM LIMAO COMERCIO DE ARTIGOS DE CAMA MESA BANHO E AROMAS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,MARIANI NASCIMENTO,MARIANI,(41) 99199-7744,mariani@example.com
28,64.120.113/0001-03,CLINICA CONECTA- PSICOPEDAGOGIA E DESENVOLVIMENTO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,GILMENIA BUENO,GILMENIA,(41) 99199-7744,gilmenia@example.com
29,64.158.858/0001-61,CIMEX GESTAO EM NEGOCIOS INTERNACIONAIS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,CRISTIANO GOMES,CRISTIANO,(41) 99199-7744,cristiano@example.com
30,23.387.330/0001-87,FENIX SEGURANÇA PRIVADA LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,ADILSON RODRIGUES,ADILSON,(41) 99199-7744,adilson@example.com
31,02.386.325/0001-80,PARABELLUM COTURNOS E UNIFORMES LTDA,CURITIBA-PR,PRESUMIDO,INDÚSTRIA,ILTON MACHADO MARTINS,ILTON,(41) 99199-7744,ilton@example.com
31.2,02.386.325/0002-60,PARABELLUM COTURNOS E UNIFORMES LTDA (Filial Caçador),CACADOR-SC,PRESUMIDO,INDÚSTRIA,ILTON MACHADO MARTINS,ILTON,(41) 99199-7744,ilton@example.com
31.3,02.386.325/0003-41,PARABELLUM COTURNOS E UNIFORMES LTDA (Filial Maua),MAUA-SP,PRESUMIDO,INDÚSTRIA,ILTON MACHADO MARTINS,ILTON,(41) 99199-7744,ilton@example.com
31.4,02.386.325/0004-22,PARABELLUM COTURNOS E UNIFORMES LTDA (Filial Maceio),MACEIO-AL,SIMPLES,INDÚSTRIA,ILTON MACHADO MARTINS,ILTON,(41) 99199-7744,ilton@example.com
32,31.734.728/0001-70,O CHURRASQUEIRO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,ANA LICE,ANA,(41) 99199-7744,ana@example.com
33,34.180.162/0001-70,MIKAELA THAIS DEKI SERUR,CURITIBA-PR,SIMPLES,SERVIÇOS,MIKAELA THAIS DEKI SERUR,MIKAELA,(41) 99199-7744,mikaela@example.com
35,34.756.342/0001-58,MFXLAB LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,SILVANA APARECIDA DA SILVA,SILVANA,(41) 99199-7744,silvana@example.com
35.2,34.756.342/0002-39,MFXLAB LTDA (Filial Campo Largo),CAMPO LARGO-PR,SIMPLES,SERVIÇOS,SILVANA APARECIDA DA SILVA,SILVANA,(41) 99199-7744,silvana@example.com
35.4,34.756.342/0004-09,MFXLAB LTDA (Filial Araucaria),ARAUCARIA-PR,SIMPLES,SERVIÇOS,SILVANA APARECIDA DA SILVA,SILVANA,(41) 99199-7744,silvana@example.com
35.5,34.756.342/0005-81,MFXLAB LTDA (Filial Lapa),LAPA-PR,SIMPLES,SERVIÇOS,SILVANA APARECIDA DA SILVA,SILVANA,(41) 99199-7744,silvana@example.com
36,64.921.593/0001-01,ROTA CERTA MARKETING SOLUTIONS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JESSICA MENESES DE SOUZA,JESSICA,(41) 99199-7744,jessica@example.com
38,40.213.019/0001-30,TW ADMINISTRADORA DE IMOVEIS S/S LIMITADA,CURITIBA-PR,SIMPLES,SERVIÇOS,ADILSON LUIZ TERRES VENANCIO,ADILSON,(41) 99199-7744,adilsonl@example.com
39,26.082.898/0001-88,ROBERTO VALENTE FAVARO SERVICOS DE CARGA E DESCARGA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ROBERTO VALENTE FAVARO,ROBERTO,(41) 99199-7744,roberto@example.com
40,11.775.963/0001-83,ESTACA FORTE INCORPORADORA LTDA.,CURITIBA-PR,PRESUMIDO,SERVIÇOS,WASHINGTON WELGNER NUNES,WASHINGTON,(41) 99199-7744,washington@example.com
41,36.688.165/0001-45,CRISTIANO FREITAS DA SILVA,CURITIBA-PR,SIMPLES,SERVIÇOS,CRISTIANO FREITAS DA SILVA,CRISTIANO,(41) 99199-7744,cristianof@example.com
50,29.545.804/0001-58,MARIA VERONICA MIRANDA CAMPOS- FREESHOP,CURITIBA-PR,SIMPLES,COMÉRCIO,MARIA VERONICA MIRANDA CAMPOS,MARIA,(41) 99199-7744,maria@example.com
57,39.709.816/0001-24,WANDERLEI ROBERTO PIRES - RTGM TRANSPORTES,CURITIBA-PR,SIMPLES,SERVIÇOS,WANDERLEI ROBERTO PIRES,WANDERLEI,(41) 99199-7744,wanderlei@example.com
60,29.992.944/0001-74,RRT SERVICOS LOGISTICA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,STEFANIE HELOIZE STRICKER,STEFANIE,(41) 99199-7744,stefanie@example.com
60.2,29.992.944/0002-55,RRT SERVICOS LOGISTICA LTDA (Filial ITUPEVA),ITUPEVA-SP,SIMPLES,SERVIÇOS,STEFANIE HELOIZE STRICKER,STEFANIE,(41) 99199-7744,stefanie@example.com
61,35.532.408/0001-99,FLAVIO FERRAZ ODONTOLOGIA ESTETICA - EIRELI,CURITIBA-PR,SIMPLES,SERVIÇOS,FLAVIO BARRETO FERRAZ,FLAVIO,(41) 99199-7744,flavio@example.com
62,10.195.348/0001-35,SABECK PRESTACAO DE SERVICOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ELZA SALETE BECKER,ELZA,(41) 99199-7744,elza@example.com
64,12.298.752/0001-60,SABECK - COMERCIO DE PRODUTOS E EQUIPAMENTOS AGROPECUARIOS LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,LENICE MARIA ZANQUI BECKER,LENICE,(41) 99199-7744,lenice@example.com
68,26.310.575/0001-02,PRIORIZE GESTAO E CONTABILIDADE PARA CONDOMINIOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,LEONARDO FONINI SANKIO,LEONARDO,(41) 99199-7744,leonardo@example.com
71,46.339.717/0001-63,CAZUNI AUTO SERVICE LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,KLEBER LUAN CAZUNI FERREIRA,KLEBER,(41) 99199-7744,kleber@example.com
73,47.068.177/0001-93,VENTO INDUSTRIA E COMERCIO LTDA,CURITIBA-PR,SIMPLES,INDÚSTRIA,RAMON PHILIP MONROE,RAMON,(41) 99199-7744,ramon@example.com
90,39.753.808/0001-85,WORLDSIZE DO BRASIL LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,RODRIGO NICOLAU DOS SANTOS NOGUEIRA,RODRIGO,(41) 99199-7744,rodrigo@example.com
94,12.040.232/0001-52,CIMEX IMPORTACAO E EXPORTACAO LTDA.,CURITIBA-PR,SIMPLES,COMÉRCIO,CRISTIANO GOMES,CRISTIANO,(41) 99199-7744,cristianog@example.com
95,24.632.810/0001-29,H.B.KURAMOTO - COMERCIAL IMPORTADORA LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,HEBER DE BASTOS KURAMOTO,HEBER,(41) 99199-7744,heber@example.com
96,40.038.748/0001-06,HBK ILUMINACAO LED ATACADAO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,HEBER DE BASTOS KURAMOTO,HEBER,(41) 99199-7744,heber2@example.com
97,20.174.792/0001-28,PSIU COMUNICACAO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,KIM CHARLES DA MAIA KOPYCKI,KIM,(41) 99199-7744,kim@example.com
100,08.610.864/0001-37,SABRINA DE OLIVEIRA CARDOSO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,SABRINA DE OLIVEIRA CARDOSO,SABRINA,(41) 99199-7744,sabrina@example.com
101,05.790.243/0001-94,TREINIT COMERCIO DE ARTIGOS ESPORTIVOS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,DIRCEU CARDOSO NETO,DIRCEU,(41) 99199-7744,dirceu@example.com
102,38.057.521/0001-58,ROUPARIA COMERCIO ELETRONICO DE ARTIGOS DE VESTUARIO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,DIRCEU CARDOSO NETO,DIRCEU,(41) 99199-7744,dirceu2@example.com
103,24.985.967/0001-38,ANDRE LUIZ LEANDRO E SILVA INFORMATICA,CURITIBA-PR,SIMPLES,SERVIÇOS,ANDRE LUIZ LEANDRO E SILVA,ANDRE,(41) 99199-7744,andre@example.com
104,46.361.998/0001-50,ALL E AJR INFORMATICA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ANDRE LUIZ LEANDRO E SILVA,ANDRE,(41) 99199-7744,andre2@example.com
105,23.876.443/0001-46,INSTITUTO DE ANDROLOGIA DE CURITIBA LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,TIAGO CESAR MIERZWA,TIAGO,(41) 99199-7744,tiago@example.com
111,49.932.291/0001-45,P&P VENDA E LOCACAO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,SIDNEI MARCOS PECHIBILSKI,SIDNEI,(41) 99199-7744,sidnei@example.com
118,49.889.243/0001-11,FGR REPRESENTACOES LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,FERNANDA GARCIA RODRIGUES,FERNANDA,(41) 99199-7744,fernanda@example.com
120,01.264.508/0001-60,LUCPRADO OTICA E FOTO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,LUCIANO ONADIR DO PRADO,LUCIANO,(41) 99199-7744,luciano@example.com
121,27.590.192/0001-90,ENGEZAN ENGENHARIA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,RODRIGO FERES ZANIN,RODRIGOZ,(41) 99199-7744,rodrigoz@example.com
125,43.265.384/0001-87,ON EQUIPAMENTOS E LOCACOES LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,MURIEL FABRICIO DOS SANTOS,MURIEL,(41) 99199-7744,muriel@example.com
132,51.124.952/0001-58,JF CORRETORA DE IMOVEIS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,LUCIANE VALERIA DA SIQUEIRA,LUCIANE,(41) 99199-7744,luciane@example.com
133,51.474.148/0001-07,M M TECNICOS ASSOCIADOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,MARCELO LOURENCO DA SILVA,MARCELO,(41) 99199-7744,marcelo@example.com
135,05.398.594/0001-54,VAL TRES CONSULTORIA IMOBILIARIA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,VALDILENE TRES,VALDILENE,(41) 99199-7744,valdilene@example.com
136,09.522.156/0001-07,CONDOMINIO ILHA DE LANZAROTE,CURITIBA-PR,PRESUMIDO,SERVIÇOS,sem certificado digital,-,-,-
137,19.768.069/0001-98,PROJEART CONSTRUCOES E EMPREENDIMENTOS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,ELISABETH MARI DA ROSA CUNHA DE LIMA E SILVA,ELISABETH,(41) 99199-7744,elisabeth@example.com
139,511585812108,JORGETE MARIA BUSO BAZZO,CURITIBA-PR,SIMPLES,SERVIÇOS,-,-,-,-
140,35.900.477/0001-08,OPENCON TECNOLOGIA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ALBARI GRUNER DE CAMARGO FILHO,ALBARI,(41) 99199-7744,albari@example.com
142,09.502.227/0001-00,SOLLIEVO ASSESSORIA E CORRETAGEM DE SEGUROS LTDA.,CURITIBA-PR,SIMPLES,SERVIÇOS,PAULO GIOVANNI ECHEVERRIA,PAULO,(41) 99199-7744,paulo@example.com
143,52.609.588/0001-89,TRNT COMERCIO DE RELOGIOS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,SABRINA DE OLIVEIRA CARDOSO,SABRINA2,(41) 99199-7744,sabrina2@example.com
146,53.127.641/0001-78,LETICIA OLIARSKI ODONTOLOGIA AVANCADA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,LETICIA OLIARSKI NOBRE SOARES,LETICIA,(41) 99199-7744,leticia@example.com
149,42.130.218/0001-00,MACSUP COMERCIO E REPRESENTACOES LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,MARIO ANTONIO CORAIOLA,MARIO,(41) 99199-7744,mario@example.com
151,03.045.362/0001-97,V.S.B. PARTICIPACAO E ADMINISTRACAO DE IMOVEIS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,BRUNO BOTTON SCHMIDT,BRUNO,(41) 99199-7744,bruno@example.com
153,53.643.075/0001-57,LT SCORSIN ODONTOLOGIA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,THAIS SCORSIN CUBAS,THAIS,(41) 99199-7744,thais@example.com
154,19.744.306/0001-80,SINERGIA ENGENHARIA DE MEIO AMBIENTE LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JESSICA DE MIRANDA PAULO,JESSICAM,(41) 99199-7744,jessicam@example.com
155,04.423.382/0001-17,PRO FIANCA SEGUROS E GARANTIAS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,GUSTAVO CASTILHOS ARNOLD,GUSTAVO,(41) 99199-7744,gustavo@example.com
156,44.799.758/0001-07,MAGIE ADMINISTRADORA DE BENS LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,MARIANI NASCIMENTO,MARIANI2,(41) 99199-7744,mariani2@example.com
157,53.942.515/0001-77,SETSUL AR CONDICIONADO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,BRUNO DE MENEZES KLEIN DE MIRANDA,BRUNOK,(41) 99199-7744,brunok@example.com
158,54.217.051/0001-07,LOTUS ESTETICA AVANCADA & MEDICINA INTEGRATIVA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,LUCIMARA DA COSTA MARTINS,LUCIMARA,(41) 99199-7744,lucimara@example.com
159,28.717.584/0001-30,CLINICA CIKLOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,FERNANDA QUEIROZ DE MORAES PIRIH SOUZA,FERNANDAQ,(41) 99199-7744,fernandaq@example.com
160,06.198.189/0001-55,BARRETO & BARRETO STUDIO LTDA.,CURITIBA-PR,SIMPLES,SERVIÇOS,ROSALVO MANIQUE BARRETO,ROSALVO,(41) 99199-7744,rosalvo@example.com
161,36.380.466/0001-07,IRBEC - INSTITUTO ROSALVO BARRETO DE ENSINO A CONSULTORES LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ROSALVO MANIQUE BARRETO,ROSALVO2,(41) 99199-7744,rosalvo2@example.com
163,07.625.587/0001-73,DREAMSHOP COMERCIO DE EQUIPAMENTOS DE INFORMATICA LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,ABNER CONRADO VIEIRA DE OLIVEIRA,ABNER,(41) 99199-7744,abner@example.com
164,09.594.093/0001-02,NETWORKBOX COMERCIO DE EQUIPAMENTOS ELETRONICOS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,ABNER CONRADO VIEIRA DE OLIVEIRA,ABNER2,(41) 99199-7744,abner2@example.com
165,54.800.077/0001-75,HBK ILUMINACAO LED LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,SABRINA RIGON,SABRINAR,(41) 99199-7744,sabrinar@example.com
168,55.167.875/0001-74,INGEE INOVAÇÃO SUSTENTAVEL LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JÉSSICA DE MIRANDA PAULA,JESSICAP,(41) 99199-7744,jessicap@example.com
169,05.248.772/0001-60,MG SINDICOS PROFISSIONAIS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,MARCOS JOSE SORRILHA,MARCOS,(41) 99199-7744,marcos@example.com
171,32.930.395/0001-18,GIANCARLO BOREICO - COMERCIO DE MAQUINAS E FERRAGENS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,GIANCARLO BOREICO,GIANCARLO,(41) 99199-7744,giancarlo@example.com
172,09.520.521/0001-44,BOREICO & BOREICO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,GIANCARLO BOREICO,GIANCARLO2,(41) 99199-7744,giancarlo2@example.com
173,02.885.932/0001-94,MGB COMERCIO DE INSUMOS AGROPECUARIOS LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,GIANCARLO BOREICO,GIANCARLO3,(41) 99199-7744,giancarlo3@example.com
173.1,02.885.932/0003-56,MGB COMERCIO DE INSUMOS AGROPECUARIOS LTDA (Filial turvo),TURVO-PR,PRESUMIDO,COMÉRCIO,GIANCARLO BOREICO,GIANCARLO4,(41) 99199-7744,giancarlo4@example.com
175,55.254.208/0001-29,BJLM PARTICIPACOES LTDA,CURITIBA-PR,PRESUMIDO,SERVIÇOS,LUCIANO RONDI NETO,LUCIANOR,(41) 99199-7744,lucianor@example.com
178,55.623.127/0001-59,BRAND ADM LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ODIVAL CEZAR BRAND,ODIVAL,(41) 99199-7744,odival@example.com
184,37.883.785/0001-06,ARNOLD NUTRITION GROUP DO BRASIL LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,RODRIGO NICOLAU DOS SANTOS NOGUEIRA,RODRIGO2,(41) 99199-7744,rodrigo2@example.com
185,06.934.638/0001-86,NUTRIBRANDS LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,RODRIGO NICOLAU DOS SANTOS NOGUEIRA,RODRIGO3,(41) 99199-7744,rodrigo3@example.com
186,25.286.141/0001-43,NUTRIDIRECT SUPLEMENTOS LTDA,CURITIBA-PR,PRESUMIDO,COMÉRCIO,RODRIGO NICOLAU DOS SANTOS NOGUEIRA,RODRIGO4,(41) 99199-7744,rodrigo4@example.com
188,27.564.340/0001-00,ATACADO DA PRATA,CURITIBA-PR,SIMPLES,COMÉRCIO,LENON FABIANO MIRANDA,LENON,(41) 99199-7744,lenon@example.com
191,56.444.609/0001-04,SOMA GARANTIDORA CONDOMINIAL LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,LEONARDO FONINI SANKIO,LEONARDO2,(41) 99199-7744,leonardo2@example.com
192,56.779.138/0001-95,LAVANDERIAS TEKAKI,CURITIBA-PR,SIMPLES,SERVIÇOS,KAREN MICHETECHUQUE GOULART KITZIG,KAREN,(41) 99199-7744,karen@example.com
193,56.616.541/0001-01,LIZ MUNDIAL,CURITIBA-PR,SIMPLES,COMÉRCIO,NEBORA LIZ VENDRAMIN BRASIL,NEBORA,(41) 99199-7744,nebora@example.com
194,49.182.487/0001-60,CAMPO LARGO LOCAÇÕES,CAMPO LARGO-PR,SIMPLES,SERVIÇOS,VINICIUS MANTOVANI NICOLOTTI,VINICIUS,(41) 99199-7744,vinicius@example.com
195,43.177.661/0001-08,MARE ESTRATEGIAS PARA ECONOMIA DE IMPACTO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,SERGIO AUGUSTO CUNHA COELHO,SERGIO,(41) 99199-7744,sergio@example.com
197,57.451.514/0001-80,E-MAX COMÉRCIO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,EVANDRO LUIZ SCHLIT,EVANDRO,(41) 99199-7744,evandro@example.com
198,54.589.923/0001-50,GUILGAB SOLUTIONS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,MARIANNA CHRISTOVAO STRUTZ MOLLICA,MARIANNA,(41) 99199-7744,marianna@example.com
199,58.257.434/0001-51,DL ILUMINAÇÃO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,DANIELLE MONIQUE SARTORI,DANIELLE,(41) 99199-7744,danielle@example.com
202,58.761.413/0001-79,AVANTE SOLUÇÕES E SERVIÇOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JAQUELINE DE OLIVEIRA QUESADA,JAQUELINE,(41) 99199-7744,jaqueline@example.com
209,59.790.247/0001-00,ROSALVO BARRETO GESTÃO E TREINAMENTOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ROSALVO MANIQUE BARRETO,ROSALVO3,(41) 99199-7744,rosalvo3@example.com
210,59.839.673/0001-82,CHEIRO DE ENROSCADA LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,DANIELLA SAPELLI SILVA,DANIELLA,(41) 99199-7744,daniella@example.com
212,60.546.242/0001-07,PIZZARTE & MEATME BURGUER,CURITIBA-PR,SIMPLES,COMÉRCIO,FELIPE COSTA DA SILVA,FELIPEC,(41) 99199-7744,felipec@example.com
215,60.737.404/0001-94,VRK SEGURANÇA E TELECOMUNICAÇÕES LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JHONATA KEHL,JHONATA,(41) 99199-7744,jhonata@example.com
216,60.757.941/0001-04,CL LANCHES LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,BRYAN ADRIAN XAVIER,BRYAN,(41) 99199-7744,bryan@example.com
218,61.175.708/0001-78,BJLM SOLUÇOES E CORRETAGEM DE SEGUROS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,JOAO PAULO DA LUZ,JOAOP,(41) 99199-7744,joaop@example.com
219,03.500.318/0001-20,SEEK INDUSTRIA COMERCIO E SERVICOS DE EQUIPAMENTOS INDUSTRIAIS LTDA,CURITIBA-PR,SIMPLES,INDÚSTRIA,ALDEIR LARTES PAVOWSKI,ALDEIR,(41) 99199-7744,aldeir@example.com
220,55.124.574/0001-63,SOLLIEVO HOLDING LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,PAULO GIOVANII ECHEVERRIA,PAULO2,(41) 99199-7744,paulo2@example.com
221,52.157.362/0001-94,NM ASSESSORIA E CONSULTORIA FLORESTAL LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,NATALIE APARECIDA MENDES ARAUJO,NATALIE,(41) 99199-7744,natalie@example.com
222,59.988.901/0001-86,DOM GUSTA PIZZARIA LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,SAID SILVA DE SOUZA,SAID,(41) 99199-7744,said@example.com
223,62.663.135/0001-94,SOLID BUSINESS SOLUTIONS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,FERNANDO NAHORNI,FERNANDO,(41) 99199-7744,fernando@example.com
224,66.292.544/0001-82,FENIX AR PRESTADORA DE SERVIÇOS,CURITIBA-PR,SIMPLES,SERVIÇOS,ADILSON RODRIGUES,ADILSON2,(41) 99199-7744,adilson2@example.com
225,66.317.533/0001-00,CASSEMIRA PSICOLOGIA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,CASSEMIRA KOPYCKI,CASSEMIRA,(41) 99199-7744,cassemira@example.com
226,32.639.680/0001-84,CHAGAS ADVOCACIA E ASSOCIADOS,CURITIBA-PR,SIMPLES,SERVIÇOS,FABIO ALVES DAS CHAGAS,FABIOC,(41) 99199-7744,fabioc@example.com
227,23.865.964/0001-06,MELODIAS DE VIVER PROCUÇÕES ARTISTICAS E TREINAMENTO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,MYRIA TOUKMAJI,MYRIA,(41) 99199-7744,myria@example.com
228,66.470.682/0001-04,P3 SOLUÇÕES EM LOCAÇÃO LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,RAFAEL PIASSA DA SILVA NETO,RAFAEL,(41) 99199-7744,rafael@example.com
229,34.711.639/0001-05,RENTAL LOC SUL LOCACOES E SERVIÇOS LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,ANA PAULA NOGUEIRA,ANAP,(41) 99199-7744,anap@example.com
230,58.934.524/0001-30,404 LABS,CURITIBA-PR,SIMPLES,SERVIÇOS,GABRIEL SMANGORZEWSKI FLORIANO,GABRIEL,(41) 99199-7744,gabriel@example.com
231,60.073.916/0001-01,CRA COMERCIAL DE ARTEFATOS DE COURO LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,CARMEN REGINA ARRATA,CARMEN2,(41) 99199-7744,carmen2@example.com
232,67.647.477/0001-34,ZENI-ALMEIDA ARQUITETURA LTDA,CURITIBA-PR,SIMPLES,SERVIÇOS,KEILA RAFAELA ZENI,KEILA,(41) 99199-7744,keila@example.com
233,67.688.850/0001-03,FENIX IR CONVENIENCIAS LTDA,CURITIBA-PR,SIMPLES,COMÉRCIO,IVANIR DOS ANJOS RODRIGUES,IVANIR,(41) 99199-7744,ivanir@example.com
"""

# ──────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────────────────
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MES_NUM = {m: i + 1 for i, m in enumerate(MESES)}
STATUS_OPTIONS = ["", "▲ Entregue", "▼ Atrasado", "● Pendente", "○ N/A"]

AREAS = {
    "Contabilidade": {
        "icone": "📗", "tem_extratos": True, "periodos_extra": ["ECD", "ECF"],
        "descricao": "Status(Balancete) + Link + Extratos Recebidos + Link(Extrato) por mês, "
                     "e ECD / ECF anuais.",
    },
    "Fiscal": {
        "icone": "💰", "tem_extratos": False, "periodos_extra": [],
        "descricao": "Status + Link de obrigações fiscais mensais.",
    },
    "Recursos Humanos": {
        "icone": "👥", "tem_extratos": False, "periodos_extra": [],
        "descricao": "Status + Link de rotinas de RH mensais (folha, eSocial etc.).",
    },
    "Societário": {
        "icone": "🏛️", "tem_extratos": False, "periodos_extra": [],
        "descricao": "Status + Link de atos societários.",
    },
}

PLACEHOLDERS = {
    "Relatórios": "🚧 Aqui você poderá ver relatórios consolidados de todas as áreas. "
                  "Estrutura a definir.",
    "Declarações": "🚧 Controle de entregas de declarações (SPED, DIRF, RAIS etc.) — "
                   "estrutura a definir.",
    "Reembolso": "🚧 Controle de solicitações e pagamentos de reembolso — estrutura a definir.",
}

MENU = [
    ("🏠", "Painel"),
    ("📗", "Contabilidade"),
    ("💰", "Fiscal"),
    ("👥", "Recursos Humanos"),
    ("🏛️", "Societário"),
    ("📄", "Relatórios"),
    ("📄", "Declarações"),
    ("💵", "Reembolso"),
    ("📅", "Agenda"),
    ("🧑", "Lista de Empresas"),
    ("ℹ️", "Legenda"),
]


# ──────────────────────────────────────────────────────────────────────────
# CAMADA DE BANCO DE DADOS (SQLite)
# ──────────────────────────────────────────────────────────────────────────
@contextlib.contextmanager
def get_conn():
    """Conexão com commit automático e fechamento garantido."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Cria o schema (idempotente) e popula dados na primeira execução."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS empresas (
                codigo         TEXT PRIMARY KEY,
                cnpj           TEXT NOT NULL,
                razao_social   TEXT NOT NULL,
                municipio      TEXT,
                regime         TEXT,
                atividade      TEXT,
                responsavel    TEXT,
                contato        TEXT,
                telefone       TEXT,
                email          TEXT
            );

            CREATE TABLE IF NOT EXISTS entregas (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_codigo   TEXT NOT NULL REFERENCES empresas(codigo) ON DELETE CASCADE,
                area             TEXT NOT NULL,
                periodo          TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT '',
                link             TEXT NOT NULL DEFAULT '',
                extratos_status  TEXT NOT NULL DEFAULT '',
                extratos_link    TEXT NOT NULL DEFAULT '',
                atualizado_em    TEXT,
                UNIQUE(empresa_codigo, area, periodo)
            );
            CREATE INDEX IF NOT EXISTS idx_entregas_area ON entregas(area);
            CREATE INDEX IF NOT EXISTS idx_entregas_empresa ON entregas(empresa_codigo);

            CREATE TABLE IF NOT EXISTS reunioes (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                data           TEXT NOT NULL,
                horario        TEXT,
                titulo         TEXT NOT NULL,
                participantes  TEXT,
                local          TEXT,
                teams          TEXT,
                observacoes    TEXT
            );

            CREATE TABLE IF NOT EXISTS saidas (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                data              TEXT NOT NULL,
                saida             TEXT,
                retorno_previsto  TEXT,
                responsavel       TEXT,
                motivo            TEXT,
                observacoes       TEXT
            );
            """
        )
    _seed_empresas_if_empty()
    _seed_entregas_if_empty()


def _seed_empresas_if_empty():
    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
        if n == 0:
            df = pd.read_csv(io.StringIO(EMPRESAS_CSV))
            df.to_sql("empresas", conn, if_exists="append", index=False)


def _seed_entregas_if_empty():
    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM entregas").fetchone()[0]
        if n > 0:
            return
        codigos = [r[0] for r in conn.execute("SELECT codigo FROM empresas").fetchall()]
        registros = []
        for codigo in codigos:
            for area, cfg in AREAS.items():
                for periodo in MESES + cfg["periodos_extra"]:
                    registros.append((codigo, area, periodo))
        conn.executemany(
            "INSERT OR IGNORE INTO entregas (empresa_codigo, area, periodo) VALUES (?, ?, ?)",
            registros,
        )


def carregar_empresas() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM empresas ORDER BY CAST(codigo AS TEXT)", conn)


def carregar_grid(area: str) -> pd.DataFrame:
    """Monta a grade larga (empresa × período) de uma área a partir do banco."""
    cfg = AREAS[area]
    with get_conn() as conn:
        long_df = pd.read_sql_query(
            """
            SELECT e.codigo, e.cnpj, e.razao_social, e.regime, e.responsavel,
                   t.periodo, t.status, t.link, t.extratos_status, t.extratos_link
            FROM empresas e
            JOIN entregas t ON t.empresa_codigo = e.codigo
            WHERE t.area = ?
            """,
            conn,
            params=(area,),
        )
    fixed = (
        long_df[["codigo", "cnpj", "razao_social", "regime", "responsavel"]]
        .drop_duplicates()
        .set_index("codigo")
    )
    wide = fixed.copy()
    for periodo in MESES + cfg["periodos_extra"]:
        sub = long_df[long_df["periodo"] == periodo].set_index("codigo")
        wide[f"{periodo} · Status"] = sub["status"]
        wide[f"{periodo} · Link"] = sub["link"]
        if cfg["tem_extratos"] and periodo in MESES:
            wide[f"{periodo} · Extratos"] = sub["extratos_status"]
            wide[f"{periodo} · Link Extrato"] = sub["extratos_link"]
    return wide.reset_index()


def salvar_grid(area: str, df_editado: pd.DataFrame, periodos: list):
    """Grava de volta no SQLite as células editadas de uma aba/trimestre."""
    cfg = AREAS[area]
    agora = datetime.now().isoformat(timespec="seconds")
    registros = []
    for _, row in df_editado.iterrows():
        for periodo in periodos:
            status = row.get(f"{periodo} · Status", "") or ""
            link = row.get(f"{periodo} · Link", "") or ""
            if cfg["tem_extratos"] and periodo in MESES:
                extratos_status = row.get(f"{periodo} · Extratos", "") or ""
                extratos_link = row.get(f"{periodo} · Link Extrato", "") or ""
            else:
                extratos_status = extratos_link = ""
            registros.append(
                (status, link, extratos_status, extratos_link, agora,
                 row["codigo"], area, periodo)
            )
    with get_conn() as conn:
        conn.executemany(
            """
            UPDATE entregas
               SET status = ?, link = ?, extratos_status = ?, extratos_link = ?, atualizado_em = ?
             WHERE empresa_codigo = ? AND area = ? AND periodo = ?
            """,
            registros,
        )


def calcular_conclusao(area: str, wide_df: pd.DataFrame) -> pd.Series:
    """Replica exatamente a fórmula original: %Entregue / (preenchidos - N/A),
    contando Status E Extratos igualmente quando a área os possui (Contabilidade)."""
    cfg = AREAS[area]
    campos = []
    for periodo in MESES:
        campos.append(f"{periodo} · Status")
        if cfg["tem_extratos"]:
            campos.append(f"{periodo} · Extratos")
    for extra in cfg["periodos_extra"]:
        campos.append(f"{extra} · Status")
    sub = wide_df[campos]
    entregues = (sub == "▲ Entregue").sum(axis=1)
    preenchidos = (sub != "").sum(axis=1)
    nao_aplicaveis = (sub == "○ N/A").sum(axis=1)
    denom = (preenchidos - nao_aplicaveis).replace(0, pd.NA)
    return (entregues / denom).fillna(0.0).astype(float)


def contar_status(area: str, status_alvo: str) -> pd.DataFrame:
    """Conta quantas ocorrências de um status (ex: Atrasado) cada empresa tem na área."""
    df = carregar_grid(area)
    cols_status = [c for c in df.columns if c.endswith("· Status") or c.endswith("· Extratos")]
    contagem = (df[cols_status] == status_alvo).sum(axis=1)
    return pd.DataFrame({"razao_social": df["razao_social"], "responsavel": df["responsavel"],
                          "Área": area, "Qtd": contagem})[lambda d: d["Qtd"] > 0]


# ---- Agenda: Reuniões e Saídas -------------------------------------------
def carregar_reunioes() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM reunioes ORDER BY data, horario", conn)


def carregar_saidas() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM saidas ORDER BY data", conn)


def adicionar_reuniao(data_, horario, titulo, participantes, local, teams, obs):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO reunioes (data, horario, titulo, participantes, local, teams, observacoes) "
            "VALUES (?,?,?,?,?,?,?)",
            (data_, horario, titulo, participantes, local, teams, obs),
        )


def adicionar_saida(data_, saida, retorno, responsavel, motivo, obs):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO saidas (data, saida, retorno_previsto, responsavel, motivo, observacoes) "
            "VALUES (?,?,?,?,?,?)",
            (data_, saida, retorno, responsavel, motivo, obs),
        )


def excluir_registro(tabela: str, id_: int):
    assert tabela in ("reunioes", "saidas")
    with get_conn() as conn:
        conn.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_,))


def adicionar_empresa(dados: dict):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO empresas (codigo, cnpj, razao_social, municipio, regime,
                                      atividade, responsavel, contato, telefone, email)
               VALUES (:codigo, :cnpj, :razao_social, :municipio, :regime,
                       :atividade, :responsavel, :contato, :telefone, :email)""",
            dados,
        )
    with get_conn() as conn:
        for area, cfg in AREAS.items():
            for periodo in MESES + cfg["periodos_extra"]:
                conn.execute(
                    "INSERT OR IGNORE INTO entregas (empresa_codigo, area, periodo) VALUES (?,?,?)",
                    (dados["codigo"], area, periodo),
                )


# ──────────────────────────────────────────────────────────────────────────
# EXPORTAÇÃO PARA EXCEL (fiel à estrutura original)
# ──────────────────────────────────────────────────────────────────────────
def gerar_excel() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        carregar_empresas().to_excel(writer, sheet_name="Lista Empresas", index=False)
        for area, cfg in AREAS.items():
            df = carregar_grid(area)
            df["% Conclusão"] = (calcular_conclusao(area, df) * 100).round(1)
            df.to_excel(writer, sheet_name=area[:31], index=False)
        reun = carregar_reunioes()
        if not reun.empty:
            reun.to_excel(writer, sheet_name="Agenda - Reuniões", index=False)
        said = carregar_saidas()
        if not said.empty:
            said.to_excel(writer, sheet_name="Agenda - Saídas", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes(1, 5)
    buffer.seek(0)
    return buffer.getvalue()


# ──────────────────────────────────────────────────────────────────────────
# COMPONENTES
# ──────────────────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: PAINEL
# ──────────────────────────────────────────────────────────────────────────
def pagina_painel():
    st.title("📊 Painel de Controle 2026")
    st.caption(f"Confiábil · Banco: {os.path.basename(DB_PATH)} · "
               f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    empresas = carregar_empresas()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Empresas Ativas", f"{len(empresas)}", "cadastradas no banco")
    with col2:
        kpi_card("Responsáveis", f"{empresas['responsavel'].nunique()}", "distintos")
    with col3:
        regimes = empresas["regime"].value_counts()
        kpi_card("Simples Nacional", f"{regimes.get('SIMPLES', 0)}", "empresas no regime")
    with col4:
        kpi_card("Lucro Presumido", f"{regimes.get('PRESUMIDO', 0)}", "empresas no regime")

    st.markdown("### Conclusão por área")
    resumo = []
    for area in AREAS:
        df = carregar_grid(area)
        pct = calcular_conclusao(area, df).mean() * 100
        resumo.append({"Área": f"{AREAS[area]['icone']} {area}", "% Conclusão": round(pct, 1)})
    resumo_df = pd.DataFrame(resumo).set_index("Área")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.bar_chart(resumo_df, height=280)
    with c2:
        st.dataframe(
            resumo_df.style.format({"% Conclusão": "{:.1f}%"}).background_gradient(
                cmap="RdYlGn", vmin=0, vmax=100
            ),
            width='stretch',
        )

    st.markdown("### Empresas com pendências / atrasos")
    linhas = []
    for area in AREAS:
        df = carregar_grid(area)
        cols = [c for c in df.columns if c.endswith("· Status") or c.endswith("· Extratos")]
        atrasos = (df[cols] == "▼ Atrasado").sum(axis=1)
        pendentes = (df[cols] == "● Pendente").sum(axis=1)
        tmp = df[["razao_social", "responsavel"]].copy()
        tmp["Área"] = area
        tmp["Atrasados"] = atrasos
        tmp["Pendentes"] = pendentes
        linhas.append(tmp[(atrasos > 0) | (pendentes > 0)])
    alerta = pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()
    if len(alerta):
        st.dataframe(alerta.sort_values("Atrasados", ascending=False),
                     width='stretch', hide_index=True)
    else:
        st.success("Nenhuma pendência ou atraso registrado no momento. ✅")

    st.divider()
    st.download_button(
        "⬇️ Exportar tudo para Excel",
        data=gerar_excel(),
        file_name=f"Confiabil_Painel_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: ÁREAS OPERACIONAIS (Contabilidade / Fiscal / RH / Societário)
# ──────────────────────────────────────────────────────────────────────────
def pagina_area(area: str):
    cfg = AREAS[area]
    st.title(f"{cfg['icone']} {area} 2026")
    st.caption(cfg["descricao"] + " Base: 137 empresas ativas — dados no SQLite (`confiabil.db`).")

    df_full = carregar_grid(area)

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        busca = st.text_input("🔎 Buscar por razão social ou CNPJ", key=f"busca_{area}")
    with fcol2:
        responsaveis = ["Todos"] + sorted(df_full["responsavel"].dropna().unique().tolist())
        resp_sel = st.selectbox("Responsável", responsaveis, key=f"resp_{area}")
    with fcol3:
        regimes = ["Todos"] + sorted(df_full["regime"].dropna().unique().tolist())
        regime_sel = st.selectbox("Regime", regimes, key=f"regime_{area}")

    mask = pd.Series(True, index=df_full.index)
    if busca:
        mask &= (
            df_full["razao_social"].str.contains(busca, case=False, na=False)
            | df_full["cnpj"].str.contains(busca, case=False, na=False)
        )
    if resp_sel != "Todos":
        mask &= df_full["responsavel"] == resp_sel
    if regime_sel != "Todos":
        mask &= df_full["regime"] == regime_sel
    indices_visiveis = df_full[mask].index

    tri_labels = ["Jan–Mar", "Abr–Jun", "Jul–Set", "Out–Dez"]
    tri_meses = [MESES[0:3], MESES[3:6], MESES[6:9], MESES[9:12]]
    abas = tri_labels + (["ECD / ECF"] if cfg["periodos_extra"] else [])
    tabs = st.tabs(abas)

    colunas_fixas = ["codigo", "cnpj", "razao_social", "regime", "responsavel"]
    config_fixas = {
        "codigo": st.column_config.TextColumn("Código", width="small", disabled=True),
        "cnpj": st.column_config.TextColumn("CNPJ", width="medium", disabled=True),
        "razao_social": st.column_config.TextColumn("Razão Social", width="large", disabled=True),
        "regime": st.column_config.TextColumn("Regime", width="small", disabled=True),
        "responsavel": st.column_config.TextColumn("Responsável", width="medium", disabled=True),
    }

    for tab, meses_tri, label in zip(tabs[:4], tri_meses, tri_labels):
        with tab:
            colunas_mes = []
            col_config = dict(config_fixas)
            for mes in meses_tri:
                colunas_mes += [f"{mes} · Status", f"{mes} · Link"]
                col_config[f"{mes} · Status"] = st.column_config.SelectboxColumn(
                    f"{mes} · Status", options=STATUS_OPTIONS, width="small"
                )
                col_config[f"{mes} · Link"] = st.column_config.TextColumn(
                    f"{mes} · Link", width="medium"
                )
                if cfg["tem_extratos"]:
                    colunas_mes += [f"{mes} · Extratos", f"{mes} · Link Extrato"]
                    col_config[f"{mes} · Extratos"] = st.column_config.SelectboxColumn(
                        f"{mes} · Extratos", options=STATUS_OPTIONS, width="small"
                    )
                    col_config[f"{mes} · Link Extrato"] = st.column_config.TextColumn(
                        f"{mes} · Link Extrato", width="medium"
                    )
            colunas_exibir = colunas_fixas + colunas_mes
            editado = st.data_editor(
                df_full.loc[indices_visiveis, colunas_exibir],
                column_config=col_config,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{area}_{label}",
            )
            if not editado.equals(df_full.loc[indices_visiveis, colunas_exibir]):
                salvar_grid(area, editado, meses_tri)
                st.toast(f"Alterações salvas no banco ({label}).", icon="💾")

    if cfg["periodos_extra"]:
        with tabs[-1]:
            colunas_extra, col_config = [], dict(config_fixas)
            for extra in cfg["periodos_extra"]:
                colunas_extra += [f"{extra} · Status", f"{extra} · Link"]
                col_config[f"{extra} · Status"] = st.column_config.SelectboxColumn(
                    f"{extra} · Status", options=STATUS_OPTIONS, width="small"
                )
                col_config[f"{extra} · Link"] = st.column_config.TextColumn(
                    f"{extra} · Link", width="medium"
                )
            colunas_exibir = colunas_fixas + colunas_extra
            editado = st.data_editor(
                df_full.loc[indices_visiveis, colunas_exibir],
                column_config=col_config,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{area}_extra",
            )
            if not editado.equals(df_full.loc[indices_visiveis, colunas_exibir]):
                salvar_grid(area, editado, cfg["periodos_extra"])
                st.toast("Alterações salvas no banco (ECD/ECF).", icon="💾")

    st.markdown("### % Conclusão por empresa")
    df_atual = carregar_grid(area)
    resultado = df_atual.loc[indices_visiveis, ["razao_social", "responsavel"]].copy()
    resultado["% Conclusão"] = (calcular_conclusao(area, df_atual.loc[indices_visiveis]) * 100).round(1)
    resultado = resultado.sort_values("% Conclusão")
    st.dataframe(
        resultado,
        column_config={"% Conclusão": st.column_config.ProgressColumn(
            "% Conclusão", min_value=0, max_value=100, format="%.1f%%")},
        width='stretch', hide_index=True,
    )


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: PLACEHOLDERS (Relatórios / Declarações / Reembolso)
# ──────────────────────────────────────────────────────────────────────────
def pagina_placeholder(nome: str):
    st.title(f"{nome} 2026")
    st.markdown(f'<div class="placeholder-box">{PLACEHOLDERS[nome]}</div>', unsafe_allow_html=True)
    st.caption("Aba criada como estrutura inicial, replicando o estado do arquivo original. "
               "Me diga o formato desejado (colunas, regras) e eu monto a estrutura completa.")


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: AGENDA
# ──────────────────────────────────────────────────────────────────────────
def pagina_agenda():
    st.title("📅 Agenda 2026")
    st.caption("Reuniões agendadas, saídas particulares e calendário do mês — gravado no SQLite.")

    hoje = date.today()
    col_a, col_b = st.columns(2)
    with col_a:
        ano = st.selectbox("Ano", [2026], index=0)
    with col_b:
        mes_nome = st.selectbox("Mês", MESES, index=min(hoje.month - 1, 11))
    mes_num = MES_NUM[mes_nome]

    reun = carregar_reunioes()
    said = carregar_saidas()

    def _no_mes(df, col="data"):
        if df.empty:
            return df
        d = pd.to_datetime(df[col], errors="coerce")
        return df[(d.dt.year == ano) & (d.dt.month == mes_num)]

    reun_mes = _no_mes(reun)
    said_mes = _no_mes(said)

    st.markdown(f"### Cronograma — {mes_nome}/{ano}")
    cal = pycalendar.Calendar(firstweekday=6)  # domingo primeiro
    semanas = cal.monthdayscalendar(ano, mes_num)
    dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    header_cols = st.columns(7)
    for c, dia in zip(header_cols, dias_semana):
        c.markdown(f"**{dia}**")
    for semana in semanas:
        cols = st.columns(7)
        for c, dia in zip(cols, semana):
            if dia == 0:
                c.markdown("&nbsp;", unsafe_allow_html=True)
                continue
            data_str = f"{ano}-{mes_num:02d}-{dia:02d}"
            eventos = []
            if not reun_mes.empty:
                for _, r in reun_mes[pd.to_datetime(reun_mes["data"]).dt.day == dia].iterrows():
                    eventos.append(f"🗓️ {r['horario'] or ''} {r['titulo']}")
            if not said_mes.empty:
                for _, s in said_mes[pd.to_datetime(said_mes["data"]).dt.day == dia].iterrows():
                    eventos.append(f"🚗 {s['motivo'] or 'Saída'}")
            corpo = "<br>".join(eventos[:3]) if eventos else ""
            c.markdown(
                f'<div class="day-cell"><span class="day-num">{dia}</span><br>{corpo}</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    tab1, tab2 = st.tabs(["📅 Reuniões Agendadas", "🚗 Saídas Particulares"])

    with tab1:
        st.dataframe(reun, width='stretch', hide_index=True)
        with st.expander("➕ Nova reunião"):
            with st.form("form_reuniao", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data_r = c1.date_input("Data", value=hoje)
                horario_r = c2.time_input("Horário")
                titulo_r = st.text_input("Título")
                participantes_r = st.text_input("Participantes")
                c3, c4 = st.columns(2)
                local_r = c3.text_input("Local")
                teams_r = c4.selectbox("Teams?", ["Não", "Sim"])
                obs_r = st.text_area("Observações")
                if st.form_submit_button("Salvar reunião"):
                    adicionar_reuniao(str(data_r), str(horario_r), titulo_r,
                                       participantes_r, local_r, teams_r, obs_r)
                    st.success("Reunião adicionada.")
                    st.rerun()
        if not reun.empty:
            with st.expander("🗑️ Excluir reunião"):
                id_del = st.selectbox("Selecione o ID", reun["id"].tolist(), key="del_reuniao")
                if st.button("Excluir", key="btn_del_reuniao"):
                    excluir_registro("reunioes", int(id_del))
                    st.rerun()

    with tab2:
        st.dataframe(said, width='stretch', hide_index=True)
        with st.expander("➕ Nova saída"):
            with st.form("form_saida", clear_on_submit=True):
                c1, c2 = st.columns(2)
                data_s = c1.date_input("Data", value=hoje, key="data_saida")
                saida_s = c2.time_input("Horário de saída")
                c3, c4 = st.columns(2)
                retorno_s = c3.text_input("Retorno previsto")
                responsavel_s = c4.text_input("Responsável")
                motivo_s = st.text_input("Motivo")
                obs_s = st.text_area("Observações", key="obs_saida")
                if st.form_submit_button("Salvar saída"):
                    adicionar_saida(str(data_s), str(saida_s), retorno_s,
                                     responsavel_s, motivo_s, obs_s)
                    st.success("Saída adicionada.")
                    st.rerun()
        if not said.empty:
            with st.expander("🗑️ Excluir saída"):
                id_del = st.selectbox("Selecione o ID", said["id"].tolist(), key="del_saida")
                if st.button("Excluir", key="btn_del_saida"):
                    excluir_registro("saidas", int(id_del))
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: LISTA DE EMPRESAS
# ──────────────────────────────────────────────────────────────────────────
def pagina_lista_empresas():
    st.title("🧑 Lista de Empresas")
    st.caption("137 empresas ativas — tabela de cadastro (dimensão), relacionada às áreas pelo CNPJ. "
               "Fonte: SQLite (`confiabil.db`).")
    df = carregar_empresas()

    busca = st.text_input("🔎 Buscar por razão social, CNPJ ou responsável")
    if busca:
        m = (
            df["razao_social"].str.contains(busca, case=False, na=False)
            | df["cnpj"].str.contains(busca, case=False, na=False)
            | df["responsavel"].str.contains(busca, case=False, na=False)
        )
        df = df[m]

    st.dataframe(
        df.rename(columns={
            "codigo": "Código Domínio", "cnpj": "CNPJ", "razao_social": "Razão Social",
            "municipio": "Município", "regime": "Regime Tributário", "atividade": "Atividade",
            "responsavel": "Responsável", "contato": "Nome do Contato",
            "telefone": "Telefone", "email": "E-mail",
        }),
        width='stretch', hide_index=True, height=520,
    )

    with st.expander("➕ Cadastrar nova empresa"):
        with st.form("form_empresa", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            codigo = c1.text_input("Código Domínio")
            cnpj = c2.text_input("CNPJ")
            regime = c3.selectbox("Regime", ["SIMPLES", "PRESUMIDO", "REAL"])
            razao = st.text_input("Razão Social")
            c4, c5 = st.columns(2)
            municipio = c4.text_input("Município")
            atividade = c5.selectbox("Atividade", ["SERVIÇOS", "COMÉRCIO", "INDÚSTRIA"])
            c6, c7 = st.columns(2)
            responsavel = c6.text_input("Responsável")
            contato = c7.text_input("Nome do Contato")
            c8, c9 = st.columns(2)
            telefone = c8.text_input("Telefone")
            email = c9.text_input("E-mail")
            if st.form_submit_button("Cadastrar"):
                if codigo and cnpj and razao:
                    adicionar_empresa({
                        "codigo": codigo, "cnpj": cnpj, "razao_social": razao,
                        "municipio": municipio, "regime": regime, "atividade": atividade,
                        "responsavel": responsavel, "contato": contato,
                        "telefone": telefone, "email": email,
                    })
                    st.success(f"Empresa {razao} cadastrada com sucesso.")
                    st.rerun()
                else:
                    st.error("Preencha ao menos Código, CNPJ e Razão Social.")


# ──────────────────────────────────────────────────────────────────────────
# PÁGINA: LEGENDA
# ──────────────────────────────────────────────────────────────────────────
def pagina_legenda():
    st.title("ℹ️ Legenda e Instruções")
    st.markdown(
        """
        | Campo | Descrição |
        |---|---|
        | **Código Domínio** | Código da empresa no Sistema Domínio. |
        | **CNPJ** | CNPJ completo, importado da Lista de Empresas. |
        | **Razão Social** | Nome da empresa. |
        | **Status** | Situação da entrega/obrigação no mês: `▲ Entregue`, `▼ Atrasado`, `● Pendente`, `○ N/A`. |
        | **Link** | Caminho ou URL do arquivo (rede, OneDrive, SharePoint, Google Drive). |
        | **Extratos Recebidos** | Só na aba Contabilidade: se os extratos bancários do período já foram recebidos do cliente (mesmo dropdown de Status). |
        | **ECD / ECF** | Só na aba Contabilidade: Escrituração Contábil Digital e Fiscal, entregas anuais (Status + Link, sem Extratos). |
        | **% Conclusão** | `▲ Entregue` dividido pelo total preenchido (excluindo N/A). Na Contabilidade, soma Status **e** Extratos igualmente. |
        """
    )
    st.info(
        "Todos os dados são gravados em um banco **SQLite** local (`confiabil.db`), no mesmo "
        "diretório do app — sobrevivem a reinícios. Use **Exportar tudo para Excel** no Painel "
        "para gerar um arquivo `.xlsx` a qualquer momento."
    )



# ──────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────
def main():
    init_db()

    with st.sidebar:
        st.markdown("## Confiábil")
        st.caption("Painel de Controle 2026")
        st.divider()
        rotulos = [f"{icone}  {nome}" for icone, nome in MENU]
        escolha = st.radio("Navegação", rotulos, label_visibility="collapsed")
        nome_pagina = escolha.split("  ", 1)[1]
        st.divider()
        st.caption(f"Banco: `{os.path.basename(DB_PATH)}`")

    if nome_pagina == "Painel":
        pagina_painel()
    elif nome_pagina == "Lista de Empresas":
        pagina_lista_empresas()
    elif nome_pagina == "Legenda":
        pagina_legenda()
    elif nome_pagina == "Agenda":
        pagina_agenda()
    elif nome_pagina in PLACEHOLDERS:
        pagina_placeholder(nome_pagina)
    elif nome_pagina in AREAS:
        pagina_area(nome_pagina)


if __name__ == "__main__":
    main()
