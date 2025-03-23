import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(layout='wide')

def exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias, valores, valores_normalizados):
    linhas = []
    for item, conteudo in perguntas_hierarquicas.items():
        for subitem, subpergunta in conteudo["subitens"].items():
            linhas.append({"Pergunta": subpergunta, "Resposta": respostas[subitem]})

    df_respostas = pd.DataFrame(linhas)
    df_grafico = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
    df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_respostas.to_excel(writer, index=False, sheet_name='Respostas')
        df_grafico.to_excel(writer, index=False, sheet_name='Gráfico')
        df_grafico_normalizado.to_excel(writer, index=False, sheet_name='Gráfico Normalizado')
    return output.getvalue()

if "formulario_preenchido" not in st.session_state:
    st.session_state.formulario_preenchido = False
if "grupo_atual" not in st.session_state:
    st.session_state.grupo_atual = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}

if not st.session_state.formulario_preenchido:
    st.title("MATRIZ DE MATURIDADE DE COMPLIANCE E PROCESSOS")
    st.subheader("Por favor, preencha suas informações antes de prosseguir")

    nome = st.text_input("Nome")
    email = st.text_input("E-mail")
    empresa = st.text_input("Empresa")
    telefone = st.text_input("Telefone")
    if st.button("Prosseguir"):
        if nome and email and empresa and telefone:
            st.session_state.nome = nome
            st.session_state.email = email
            st.session_state.empresa = empresa
            st.session_state.telefone = telefone
            st.session_state.formulario_preenchido = True
            st.success("Informações preenchidas com sucesso! Você pode prosseguir para o questionário.")
        else:
            st.error("Por favor, preencha todos os campos antes de prosseguir.")
else:
    perguntas_hierarquicas = {
        "1.0": {
            "titulo": "Eficiência de Gestão",
            "subitens": {
                "1.1": "Numa escala de 01 a 5 informe se você possui todos os indicadores gerenciais para a perspectiva que sua empresa precisa ter e se a gestão são orientadas e medidas por estes indicadores, com metas definidas e claras e com cobrança de resultados?",
                "1.2": "Considerando um ambiente controlavel de gestão, quantas vezes os executivos da empresa se reunem para discutir a avaliar os números considere 01 menos de 1 vez ao semestre, 2 pelo menos 1 vez ao trimestre, 3 pelo menos 1 vez ao bimestre, 4 pelo menos 1 vez ao mês, 5 Semanalmente.",
                "1.3": "Numa escala de 01 a 5 indique o quanto de confiabilidade vc possui quanto a apuração da LUCRATIVIDADE/ EBITDA/ MG EBITDA/MARK-UP/ INDICES DE LIQUIDEZ/NÍVEL DE ENDIVIDAMENTO/MARGEM BRUTA/LÍQUIDA/E RETORNO SOBRE O PATRIMÔNIO?",
                "1.4": "Numa escala de 01 a 5 indique o quanto você sabe sobre o aumento ou diminuição da geração de Caixa e Ebitda to Cash",
                "1.5": "Numa escala de 01 a 05 informe o quanto você estima conhecer sobre o valor do aumento ou diminuição do CAPEX sobre o Ebitda",
                "1.6": "Numa escala de 01 a 5 informe o quanto você confia na informação sobre a geração de caixa períódica da sua empresa",
                "1.7": "Numa escala de 01 a 5 informe o grau de confiança quanto aos indicadores de acuracidade de estoques e assertividade dos produtos.",
                "1.8": "Numa escala de 01 a 5 informe o grau de confiança quanto aos indicadores de Giro dos Estoques de matéria-prima e produtos acabados.",
                "1.9": "Num grau de 01 a 5 indique o quanto de confiança no 'Saving' (Mostra quanto a empresa conseguiu economizar. Isso é feito por meio da comparação do que foi orçado e o que foi comprado. Dessa forma, é possível saber quanto de lucro direto foi gerado e qual é a eficácia do setor).",
                "1.10": "Num grau de confiança de 01 a 5 informe o quanto a empresa dispõem de conhecimento sobre a 'Evolução dos Preços' dos principais insumos, a fim de prever sazonalidades e picos de elevação de preços.",
                "1.11": "Com relação aos Custos de Suprimento, informe num grau de 01 a 5 o quanto a empresa consegue demonstrar qual foi Percentual de Custos em Relação as Vendas e a Percentagem de Vendas que foi aplicado em Suprimentos",
                "1.12": "Numa escala de 01 a 5 indique o quanto a empresa consegue estimar a capacidade instalada x a capacidade real (aplicada) da força de trabalho.",
                "1.13": "Com base em seu conhecimento informe o grau de confiança com que você consegue estimar a sua participação de mercado utilize de 01 a 5 para informar.",
                "1.14": "Com base nos relatórios comerciais da administração de vendas, informe entre 01 a 5 o grau de confiança que você possui quanto a apuração do preço médio de vendas.",
                "1.15": "Com base na carteira de pedidos e no histórico de vendas, informe o grau de confiança que você possui quanto a apuração do cliclo vendas.",
                "1.16": "Com base nos controles hitóricos de vendas, informe qual é confiabilidade da taxa de 'Churn' (taxa de perda de clientes) utilize 01 a 5 para informar.",
                "1.17": "Com base no relatório de vendas, informe de 01 a 5 o grau de precisão que você acredita ter quanto ao valor demonstrado no período do Tickt Médio de Vendas?",
                "1.18": "Com base no relatório de cobranças, informe de 01 a 5 o grau de precisão que você acredita ter quanto ao valor médio e o percentual demonstrado no período da inadimplência da sua empresa.",
                "1.19": "Numa escala de 01 a 05 informe o grau de precisão quanto a mensuração dos prazos de recebimento e pagamentos para uma boa gestão do fluxo de caixa.",
                "1.20": "Numa escala de 01 a 5 informe o quanto você confia na informação sobre a geração de caixa períódica da sua empresa.",
                "1.21": "Numa escala de 01 a 5 qual o grau de precisão que a empresa possui para projetar a NECESSIDADE DE CAPITAL DE GIRO (NCG)",
                "1.22": "Numa escala de 01 a 10 qual o grau de precisão que a empresa possui para analisar a sua Liquidez Corrente",
                "1.23": "Num grau de certeza e precisão dos dados considerando de 01 a 5 indique sua confiança no Ponto de Equilíbrio Financeiro que a sua empresa dispõem?",
                "1.24": "Num grau de certeza e precisão dos dados considerando de 01 a 5 indique sua confiança na apuração da Margem de Lucro Líquido"
            }
        },
        "2.0": {
            "titulo": "Estruturas",
            "subitens": {
                "2.1": "A Organização possui código de ética, política de alçadas e canal de denúncias;",
                "2.2": "A Organização possui planejamento estratégico definido e atualizado, contendo missão, visão e valores;",
                "2.3": "A Organização possui Organograma de Governança definido e atualizado;",
                "2.4": "A Organização possui planejamento estratégico definido e atualizado, contendo as principais metas e objetivos de acordo com a missão, visão e valores;",
                "2.5": "As áreas-chave da Organização (Comercial, Compras, Estoque, Logística, Financeiro, Administrativo, RH e Contabilidade) estão devidamente estruturadas, contendo normas e políticas;",
                "2.6": "As áreas-chave da Organização (Comercial, Compras, Estoque, Logística, Financeiro, Administrativo, RH e Contabilidade) possuem procedimentos definidos;",
                "2.7": "Atualmente a Organização avalia periodicamente a eficiência e automação de seus principais controles sistêmicos;",
                "2.8": "Atualmente a Organização avalia, além da eficiência de seus principais controles sistêmicos, também os controles compensatórios;",
                "2.9": "Atualmente a organização utiliza indicadores com base da avaliação de eficiência de seus produtos/serviços;",
                "2.10": "A Organização possui uma estrutura de Compliance definida;",
                "2.11": "A Organização possui uma estrutura de Gestão de Riscos definida;",
                "2.12": "A Organização possui uma estrutura responsável pela padronização e armazenamento de documentos;",
                "2.13": "A Organização possui uma estrutura responsável pela gestão de melhorias;",
                "2.14": "A Organização possui uma estrutura responsável pela gestão de treinamentos;",
                "2.15": "A Organização possui uma estrutura responsável pela realização de avaliação de desempenho periódico;",
                "2.16": "A Organização possui uma estrutura responsável pela realização de auditorias internas periódicas;"
            }
        },
        "3.0": {
            "titulo": "Compliance",
            "subitens": {
                "3.1": "A organização possui um código de ética e conduta formalizado e disseminado para os colaboradores?",
                "3.2": "Há um programa de Compliance estruturado e alinhado às regulamentações aplicáveis ao setor?",
                "3.3": "Existe um canal de denúncias ativo e acessível para todos os stakeholders?",
                "3.4": "A empresa realiza treinamentos regulares de Compliance para seus colaboradores?",
                "3.5": "Existe um processo definido para investigar e tratar violações às normas de Compliance?",
                "3.6": "Há um responsável (Compliance Officer) ou um comitê de Compliance na organização?",
                "3.7": "A alta direção apoia e incentiva a cultura de Compliance?",
                "3.8": "São realizados testes ou auditorias periódicas para avaliar a eficácia do programa de Compliance?",
                "3.9": "A empresa possui políticas para evitar conflitos de interesse?",
                "3.10": "Há um processo de Due Diligence para terceiros e fornecedores críticos?",
                "3.11": "Possui políticas e procedimentos para a os processos de relações institucionais?",
                "3.12": "Possui políticas e procedimento de contratação e monitoramento de Colaboradores Próprios e Autônomos?",
                "3.13": "Possui políticas e procedimentos de permissões de acesso e alçadas de aprovação?",
                "3.14": "Possui políticas de controles e gestão de estoques e almoxarifados?",
                "3.15": "Possui políticas de controles de gestão financeira",
                "3.16": "Existe política de conciliações contábeis e de fechamento das demonstrações financeiras?",
                "3.17": "Existe política e procedimentos de faturamentos?",
                "3.18": "Existe política e procedimentos para cobranças?",
                "3.19": "Existe política e procedimentos para pagamentos de fornecedores e Prestadores de Serviços e Outros?",
                "3.20": "Existe política e procedimentos para controles de descontos e abatimentos?",
                "3.21": "Existe política e procedimentos para acordos e parcerias estratégicas?",
                "3.22": "Possui políticas de controles dos processos logísticos?",
                "3.23": "Possui políticas de controles dos processos de estoques?",
                "3.24": "Possui políticas e procedimentos para Contratação e Homologação de Fornecedores e Rede de Atendimento?",
                "3.25": "Possui políticas e procedimentos para admissão recrutamento e seleção?",
                "3.26": "Possui políticas e procedimentos para detecção de falhas de processos?",
                "3.27": "Possui políticas e procedimentos para unidades de produção?",
                "3.28": "Possui políticas e procedimentos para segurança patrimonial?",
                "3.29": "Possui políticas e procedimentos para fechamentos contábeis?",
                "3.30": "Possui políticas e procedimentos de TI e Estrutura de Tecnologia?",
                "3.31": "Possui políticas e procedimentos de investimentos?",
                "3.32": "Existem políticas de Privacidade e Proteção de dados pessoais?",
                "3.33": "Existem políticas e procedimentos que garantem gestão de crises?",
                "3.34": "Existem políticas de Governança Corporativa, Responsabilidade Social e Ambiental?",
                "3.35": "Existe Políticas de Combate a Corrupção, Fraude Lavagem de Dinheiro?",
                "3.36": "Existe políticas de controle dos ativos?"
            }
        },
        "4.0": {
            "titulo": "Gestão de Riscos",
            "subitens": {
                "4.1": "A organização possui um processo estruturado para identificar, avaliar e tratar riscos?",
                "4.2": "Os riscos operacionais são documentados e monitorados regularmente?",
                "4.3": "Existe um comitê de riscos ou uma área dedicada para a gestão de riscos?",
                "4.4": "São realizados testes e simulações para validar os planos de mitigação de riscos",
                "4.5": "A empresa possui um plano de continuidade de negócios?",
                "4.6": "Os riscos financeiros, regulatórios e de mercado são formalmente avaliados?",
                "4.7": "Há um sistema ou ferramenta de tecnologia para monitoramento e mitigação de riscos?",
                "4.8": "Existe um processo de revisão e atualização periódica do mapa de riscos?",
                "4.9": "Os riscos são considerados no planejamento estratégico da organização?",
                "4.10": "A empresa realiza auditorias internas para validar a efetividade das ações de mitigação de riscos?"
            }
        },
        "5.0": {
            "titulo": "Gestão de Processos",
            "subitens": {
                "5.1": "Os principais processos da organização estão formalmente documentados?",
                "5.2": "Existe um sistema para monitoramento e otimização dos processos internos?",
                "5.3": "Os processos são revisados periodicamente para melhoria contínua?",
                "5.4": "A organização adota metodologias como BPM, Lean ou Six Sigma para melhoria de processos?",
                "5.5": "Há um comitê ou área responsável pela gestão de processos?",
                "5.6": "Os indicadores de desempenho dos processos são definidos e acompanhados regularmente?",
                "5.7": "Há uma padronização entre processos operacionais e de suporte?",
                "5.8": "A empresa adota ferramentas para automatização e digitalização de processos?",
                "5.9": "Existe um sistema de feedback para identificar problemas e oportunidades de melhoria nos processos?",
                "5.10": "Os processos internos estão alinhados à estratégia organizacional?",
                "5.11": "Os Controles dos processos são automatizados?",
                "5.12": "Existem controles em planilhas ou em outras formas compensatórias?",
                "5.13": "Os indicadores são monitorados através de relatórios ou indicadores?",
                "5.14": "Este resultado é apresentado aos clientes internos?",
                "5.15": "Estes resultados atendem a necessidade do cliente ou do negócio?",
                "5.16": "Estes resultados são revisados periodicamente?",
                "5.17": "Existe algum programa de sugestões de melhorias para as atividades que desenvolve?",
                "5.18": "As melhorias que são sugeridas são tratadas para implementação?",
                "5.19": "As melhorias implantadas são monitoradas para garantir a eficiência?",
                "5.20": "Existe sistema para medir a eficiência das melhorias implantadas?",
                "5.21": "Existem documentos comuns para realização do seu processo (formulário, relatório, etc..)?",
                "5.22": "Os formulários e relatórios utilizados para seu dia-a-dia são padronizados?",
                "5.23": "Todos conhecem os formulários necessários para este processo?",
                "5.24": "Todos sabem utilizar / preencher os formulários?",
                "5.25": "Os relatórios atendem a necessidade do processo (informação e formato)?",
                "5.26": "Quando há mudanças no processo esta documentação é atualizada?",
                "5.27": "Há treinamento sobre estas mudanças?",
                "5.28": "Os clientes internos são ouvidos para sugerir melhorias e ou ajustes no processo?",
                "5.29": "Existem indicadores de desempenho do processo? Com metas definidas?",
                "5.30": "Os resultados operacionais são apresentados aos clientes (indicadores)?",
                "5.31": "Os desvios de processos são apresentados aos clientes (com a responsabilidade de ambos)?",
                "5.32": "Existe uma meta clara para os indicadores?",
                "5.33": "Existe uma meta clara para os indicadores?",
                "5.34": "Existe uma rotina (periódica) de apresentação dos resultados?",
                "5.35": "São montados planos para melhorar os resultados com indicadores?",
                "5.36": "Os indicadores são revisados periodicamente para avaliar sua aderência aos processos?",
                "5.37": "As metas são reavaliadas conforme resultados e períodos?"
            }
        },
        "6.0": {
            "titulo": "Governança Corporativa",
            "subitens": {
                "6.1": "A empresa possui um conselho de administração ativo e estruturado?",
                "6.2": "Existem políticas definidas para tomada de decisões estratégicas?",
                "6.3": "A estrutura organizacional é clara, com papéis e responsabilidades bem definidos?",
                "6.4": "Os acionistas e partes interessadas recebem informações transparentes sobre a gestão da empresa?",
                "6.5": "Há um plano de sucessão para cargos críticos na organização?",
                "6.6": "O plano estratégico é revisado e atualizado periodicamente?",
                "6.7": "A governança da empresa segue as melhores práticas do mercado?",
                "6.8": "Existe auditoria independente para verificar as demonstrações financeiras e operacionais?",
                "6.9": "A empresa possui políticas de sustentabilidade e responsabilidade social corporativa?",
                "6.10": "A governança incentiva a inovação e o desenvolvimento organizacional?"
            }
        },
        "7.0": {
            "titulo": "Recursos Humanos",
            "subitens": {
                "7.1": "Existe um programa estruturado de desenvolvimento e capacitação dos colaboradores?",
                "7.2": "A empresa possui políticas claras de recrutamento e retenção de talentos?",
                "7.3": "Os funcionários recebem treinamentos regulares sobre normas e políticas internas?",
                "7.4": "A cultura organizacional promove a diversidade e inclusão?",
                "7.5": "O clima organizacional é avaliado regularmente?",
                "7.6": "Há um plano de benefícios estruturado para colaboradores?",
                "7.7": "O desempenho dos colaboradores é avaliado periodicamente?",
                "7.8": "Existe um canal de comunicação eficaz entre gestão e colaboradores?",
                "7.9": "Os processos de desligamento de funcionários são conduzidos de maneira estruturada e ética?",
                "7.10": "Há ações internas voltadas ao bem-estar dos funcionários?",
                "7.11": "Há treinamentos sobre as melhorias e sistemas que utiliza?",
                "7.12": "Existe comunicação sobre a necessidade de treinamento para melhorar as atividades da equipe?",
                "7.13": "Existe um plano de treinamento contínuo?",
                "7.14": "Os envolvidos no processo possuem as competências técnicas necessárias?",
                "7.15": "Você foi treinado tecnicamente para desenvolver as atividades necessárias?",
                "7.16": "Há revisão dos conhecimentos necessários para desenvolvimento da atividade?",
                "7.17": "Esta competência e disseminada entre todos os envolvidos no processo?"
            }
        },
        "8.0": {
            "titulo": "Tecnologia da Informação",
            "subitens": {
                "8.1": "A empresa possui uma estratégia de transformação digital?",
                "8.2": "Existe um plano de segurança cibernética para proteção de dados?",
                "8.3": "Os sistemas utilizados pela empresa são atualizados e monitorados regularmente?",
                "8.4": "Há um plano de contingência para recuperação de dados em caso de incidentes?",
                "8.5": "A empresa utiliza tecnologia para otimizar seus processos internos?",
                "8.6": "Os colaboradores são treinados para identificar riscos cibernéticos?",
                "8.7": "Existe integração entre os sistemas de TI e as demais áreas da empresa?",
                "8.8": "Os fornecedores de tecnologia passam por um processo de Due Diligence?",
                "8.9": "A empresa utiliza inteligência artificial ou automação para ganho de eficiência?",
                "8.10": "Os investimentos em TI estão alinhados com os objetivos estratégicos da empresa?"
            }
        },
        "9.0": {
            "titulo": "Gestão Financeira",
            "subitens": {
                "9.1": "A empresa possui um orçamento estruturado e revisado periodicamente?",
                "9.2": "Há um sistema de controle de custos eficaz?",
                "9.3": "A empresa realiza análises financeiras e relatórios periódicos?",
                "9.4": "Existem processos estruturados para controle de fraudes financeiras?",
                "9.5": "A empresa possui um planejamento financeiro de longo prazo?",
                "9.6": "Os pagamentos a fornecedores são controlados para evitar inadimplências?",
                "9.7": "Há um plano de gestão de dívidas e passivos financeiros?",
                "9.8": "A organização realiza auditorias financeiras regularmente?",
                "9.9": "Os investimentos da empresa são avaliados em termos de risco e retorno?",
                "9.10": "Existe um processo de revisão e ajuste do fluxo de caixa?"
            }
        },
        "10.0": {
            "titulo": "Gestão de Fornecedores",
            "subitens": {
                "10.1": "A empresa possui um processo estruturado e formalizado para aquisição de bens e serviços?",
                "10.2": "Há critérios bem definidos para a seleção e homologação de fornecedores?",
                "10.3": "Existe um sistema de avaliação periódica do desempenho dos fornecedores?",
                "10.4": "A empresa possui um processo de Due Diligence para fornecedores críticos?",
                "10.5": "Os contratos de compras incluem cláusulas de compliance, qualidade e prazos de entrega?",
                "10.6": "Há um controle eficaz sobre os prazos de pagamento e condições contratuais com fornecedores?",
                "10.7": "A empresa realiza benchmarking para garantir melhores práticas e preços competitivos?",
                "10.8": "O setor de compras participa do planejamento estratégico da organização?",
                "10.9": "Existe um controle eficaz de orçamento e aprovação de compras?",
                "10.10": "A empresa adota tecnologia para automatizar e otimizar os processos de compras?"
            }
        },
        "11.0": {
            "titulo": "Gestão de Estoque",
            "subitens": {
                "11.1": "A empresa possui um sistema de controle de estoque atualizado e confiável?",
                "11.2": "Existem políticas bem definidas para reposição e níveis mínimos/máximos de estoque?",
                "11.3": "Os estoques são periodicamente avaliados para evitar obsolescência e perdas?",
                "11.4": "Há um controle efetivo de inventário e auditorias regulares nos estoques?",
                "11.5": "Os produtos armazenados seguem normas de acondicionamento e segurança?",
                "11.6": "A empresa utiliza tecnologia para otimizar o controle de estoques (ex.: RFID, ERP, WMS)?",
                "11.7": "Existe um fluxo de integração entre os setores de compras, produção e vendas para melhor gestão do estoque?",
                "11.8": "Os prazos de validade dos produtos são monitorados para evitar desperdícios?",
                "11.9": "Há um sistema para previsão de demanda e planejamento de estoque?",
                "11.10": "O giro de estoque é analisado periodicamente para otimizar capital de giro?"
            }
        },
        "12.0": {
            "titulo": "Logística e Distribuição",
            "subitens": {
                "12.1": "A empresa possui um planejamento estratégico para otimizar suas operações logísticas?",
                "12.2": "Existe um sistema para rastreamento e monitoramento de entregas em tempo real?",
                "12.3": "O custo logístico é acompanhado e analisado regularmente para otimização?",
                "12.4": "A empresa utiliza roteirização inteligente para reduzir custos e melhorar prazos de entrega?",
                "12.5": "Os fornecedores logísticos são avaliados e possuem contratos bem definidos?",
                "12.6": "Há controle de indicadores logísticos como OTIF (On-Time In-Full) e Lead Time de entrega?",
                "12.7": "Existe um plano de contingência para situações emergenciais (ex.: greves, falhas operacionais)?",
                "12.8": "A empresa adota práticas sustentáveis na sua logística (ex.: transporte verde, otimização de cargas)?",
                "12.9": "O transporte interno e externo é monitorado para garantir eficiência e segurança?",
                "12.10": "A empresa utiliza sistemas integrados (ERP, TMS, WMS) para otimizar processos logísticos?"
            }
        },
        "13.0": {
            "titulo": "Contabilidade e Controle Financeiro",
            "subitens": {
                "13.1": "A empresa possui um plano de contas estruturado e atualizado conforme normas contábeis?",
                "13.2": "Os relatórios contábeis são gerados regularmente e revisados por profissionais qualificados?",
                "13.3": "A empresa segue as normas internacionais de contabilidade (IFRS) ou normas locais aplicáveis?",
                "13.4": "Existem processos automatizados para lançamento e conciliação contábil?",
                "13.5": "A empresa realiza auditorias contábeis internas ou externas periodicamente?",
                "13.6": "O balanço patrimonial e os demonstrativos financeiros são revisados por especialistas antes da publicação?",
                "13.7": "Há um processo estruturado para pagamento de tributos e obrigações fiscais?",
                "13.8": "A empresa possui um plano de compliance fiscal para evitar riscos tributários?",
                "13.9": "Os ativos e passivos da empresa são monitorados regularmente?",
                "13.10": "Existe uma política de provisionamento financeiro para despesas futuras e contingências?"
            }
        }
    }

    grupos = list(perguntas_hierarquicas.keys())
    grupo_atual = st.session_state.grupo_atual

    if grupo_atual < len(grupos):
        grupo = grupos[grupo_atual]
        st.write(f"### Grupo {grupo} - {perguntas_hierarquicas[grupo]['titulo']}")
        for subitem, subpergunta in perguntas_hierarquicas[grupo]["subitens"].items():
            if subitem not in st.session_state.respostas:
                st.session_state.respostas[subitem] = 0
            st.session_state.respostas[subitem] = st.number_input(
                f"{subitem} - {subpergunta}",
                min_value=0,
                max_value=5,
                step=1,
                value=st.session_state.respostas[subitem]
            )
        if st.button("Prosseguir"):
            st.session_state.grupo_atual += 1
    else:
        st.write("### Todas as perguntas foram respondidas!")
        if st.button("Gerar Gráfico"):
            respostas = st.session_state.respostas
            categorias = []
            valores = []
            valores_normalizados = []
            soma_total_respostas = sum(respostas.values())
            for item, conteudo in perguntas_hierarquicas.items():
                soma_respostas = sum(respostas[subitem] for subitem in conteudo["subitens"].keys())
                num_perguntas = len(conteudo["subitens"])
                if num_perguntas > 0:
                    valor_percentual = (soma_respostas / (num_perguntas * 5)) * 100
                    valor_normalizado = (soma_respostas / valor_percentual) * 100 if valor_percentual > 0 else 0
                    categorias.append(conteudo["titulo"])
                    valores.append(valor_percentual)
                    valores_normalizados.append(valor_normalizado)
            if len(categorias) != len(valores) or len(categorias) != len(valores_normalizados):
                st.error("Erro: As listas de categorias e valores têm tamanhos diferentes.")
            else:
                if categorias:
                    valores_original = valores + valores[:1]
                    categorias_original = categorias + categorias[:1]
                    import plotly.graph_objects as go
                    fig_original = go.Figure()
                    fig_original.add_trace(go.Scatterpolar(
                        r=valores_original,
                        theta=categorias_original,
                        fill='toself',
                        name='Gráfico Original'
                    ))
                    fig_original.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )),
                        showlegend=False
                    )
                    valores_normalizados_fechado = valores_normalizados + valores_normalizados[:1]
                    fig_normalizado = go.Figure()
                    fig_normalizado.add_trace(go.Scatterpolar(
                        r=valores_normalizados_fechado,
                        theta=categorias_original,
                        fill='toself',
                        name='Gráfico Normalizado'
                    ))
                    fig_normalizado.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )),
                        showlegend=False
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_original, use_container_width=True)
                        st.write("### Gráfico 1")
                        df_grafico_original = pd.DataFrame({'Categoria': categorias, 'Porcentagem': valores})
                        st.dataframe(df_grafico_original)
                    with col2:
                        st.plotly_chart(fig_normalizado, use_container_width=True)
                        st.write("### Gráfico 2")
                        df_grafico_normalizado = pd.DataFrame({'Categoria': categorias, 'Porcentagem Normalizada': valores_normalizados})
                        st.dataframe(df_grafico_normalizado)
                    excel_data = exportar_para_excel_completo(respostas, perguntas_hierarquicas, categorias[:-1], valores[:-1], valores_normalizados[:-1])
                    st.download_button(
                        label="Exportar para Excel",
                        data=excel_data,
                        file_name="respostas_e_grafico.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
