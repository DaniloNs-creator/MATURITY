import streamlit as st
import pandas as pd
import io
from datetime import datetime
import re

# Configura a página
st.set_page_config(page_title="Conversor 69 PG", page_icon="📄", layout="wide")

st.title("📄 Conversor de Arquivo 69 PG para Excel")
st.markdown("""
Este aplicativo converte arquivos 69 PG para Excel, extraindo:
- **Nome** do titular
- **Módulo** (informações de coparticipação)
- **Família** e **Dependentes**
""")

# Widget para upload de arquivo
uploaded_file = st.file_uploader(
    "Faça o upload do arquivo 69 PG", 
    type=['txt', 'pg', '69'],
    help="Selecione o arquivo 69 PG que deseja converter"
)

def processar_arquivo_69pg(conteudo):
    """
    Processa o conteúdo do arquivo 69 PG e extrai as informações estruturadas
    """
    linhas = conteudo.splitlines()
    
    familias = []
    current_family = {}
    current_dependentes = []
    in_familia_section = False
    in_dependentes_section = False
    
    for i, linha in enumerate(linhas):
        linha = linha.strip()
        
        if not linha:
            continue
            
        # Detecta seção "Nome:"
        if linha.startswith("Nome:") or linha.startswith("Nome :"):
            if current_family and current_family.get('Nome'):
                # Salva a família anterior antes de iniciar nova
                current_family["Dependentes"] = current_dependentes.copy()
                familias.append(current_family.copy())
                current_dependentes = []
            
            # Extrai o nome após "Nome:"
            nome = linha.split(":", 1)[1].strip() if ":" in linha else linha.replace("Nome", "").strip()
            current_family = {
                "Nome": nome,
                "Modulo": "",
                "Familia": "",
                "Dependentes": []
            }
            in_familia_section = False
            in_dependentes_section = False
        
        # Detecta seção "I módulo" ou informações de coparticipação
        elif "módulo" in linha.lower() or "modulo" in linha.lower() or "coparticipação" in linha.lower():
            if current_family:
                current_family["Modulo"] = linha
                # Tenta pegar linhas subsequentes do módulo
                mod_lines = [linha]
                for j in range(i+1, min(i+5, len(linhas))):
                    next_line = linhas[j].strip()
                    if next_line and not any(x in next_line.lower() for x in ['nome:', 'família', 'familia', 'dependente']):
                        mod_lines.append(next_line)
                    else:
                        break
                current_family["Modulo"] = " | ".join(mod_lines)
        
        # Detecta início da seção "Familia"
        elif "familia" in linha.lower() or "família" in linha.lower():
            if current_family:
                current_family["Familia"] = linha
                in_familia_section = True
                in_dependentes_section = True
        
        # Identifica dependentes (apenas quando estiver na seção da família)
        elif in_dependentes_section and linha:
            # Verifica se é um dependente (não é outro cabeçalho)
            is_dependente = (
                not linha.startswith("Nome:") and 
                not linha.startswith("I módulo") and 
                "módulo" not in linha.lower() and
                "familia" not in linha.lower() and
                "família" not in linha.lower() and
                len(linha) > 3  # Linhas muito curtas provavelmente não são dependentes
            )
            
            if is_dependente:
                current_dependentes.append(linha)
        
        # Se encontrar um novo nome sem fechar a família anterior
        elif linha.startswith("Nome:") and current_family and current_family.get('Nome'):
            current_family["Dependentes"] = current_dependentes.copy()
            familias.append(current_family.copy())
            current_dependentes = []
            
            nome = linha.split(":", 1)[1].strip() if ":" in linha else linha.replace("Nome", "").strip()
            current_family = {
                "Nome": nome,
                "Modulo": "",
                "Familia": "",
                "Dependentes": []
            }
            in_familia_section = False
            in_dependentes_section = False
    
    # Adiciona a última família processada
    if current_family and current_family.get('Nome'):
        current_family["Dependentes"] = current_dependentes
        familias.append(current_family)
    
    return familias

def criar_dataframe_exportacao(familias):
    """
    Cria DataFrame para exportação a partir da lista de famílias
    """
    export_data = []
    
    for familia in familias:
        nome = familia.get("Nome", "")
        modulo = familia.get("Modulo", "")
        familia_info = familia.get("Familia", "")
        dependentes = familia.get("Dependentes", [])
        
        # Se não houver dependentes, inclui pelo menos a família
        if not dependentes:
            export_data.append({
                "Nome_Titular": nome,
                "Modulo_Coparticipacao": modulo,
                "Info_Familia": familia_info,
                "Dependente": "",
                "Tipo": "Titular"
            })
        else:
            # Inclui o titular
            export_data.append({
                "Nome_Titular": nome,
                "Modulo_Coparticipacao": modulo,
                "Info_Familia": familia_info,
                "Dependente": nome,
                "Tipo": "Titular"
            })
            
            # Inclui os dependentes
            for dependente in dependentes:
                export_data.append({
                    "Nome_Titular": nome,
                    "Modulo_Coparticipacao": modulo,
                    "Info_Familia": familia_info,
                    "Dependente": dependente,
                    "Tipo": "Dependente"
                })
    
    return pd.DataFrame(export_data)

# Interface principal
if uploaded_file is not None:
    try:
        # Lê o conteúdo do arquivo
        bytes_data = uploaded_file.getvalue()
        
        # Tenta decodificar como texto
        try:
            string_data = bytes_data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                string_data = bytes_data.decode("latin-1")
            except UnicodeDecodeError:
                string_data = bytes_data.decode("iso-8859-1")
        
        # Mostra preview do arquivo original
        with st.expander("📄 Visualizar arquivo original"):
            st.text_area("Conteúdo do arquivo", string_data, height=300, key="original_file")
        
        # Processa o arquivo
        with st.spinner("Processando arquivo..."):
            familias = processar_arquivo_69pg(string_data)
        
        if familias:
            st.success(f"✅ Processamento concluído! {len(familias)} famílias identificadas.")
            
            # Cria DataFrame para exportação
            df_export = criar_dataframe_exportacao(familias)
            
            # Exibe estatísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_familias = len(familias)
                st.metric("Famílias Identificadas", total_familias)
            with col2:
                total_dependentes = sum(len(fam.get("Dependentes", [])) for fam in familias)
                st.metric("Total de Dependentes", total_dependentes)
            with col3:
                st.metric("Total de Registros", len(df_export))
            with col4:
                st.metric("Arquivo", uploaded_file.name)
            
            # Exibe preview dos dados processados
            st.subheader("📊 Dados Processados")
            st.dataframe(df_export, use_container_width=True)
            
            # Mostra detalhes das famílias
            with st.expander("🔍 Detalhamento por Família"):
                for i, familia in enumerate(familias, 1):
                    st.write(f"**Família {i}: {familia['Nome']}**")
                    if familia.get('Modulo'):
                        st.write(f"**Módulo:** {familia['Modulo']}")
                    if familia.get('Familia'):
                        st.write(f"**Família:** {familia['Familia']}")
                    if familia.get('Dependentes'):
                        st.write("**Dependentes:**")
                        for dep in familia['Dependentes']:
                            st.write(f"  - {dep}")
                    st.write("---")
            
            # Prepara o arquivo Excel para download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, sheet_name='Dados_69PG', index=False)
                
                # Formatação da planilha
                workbook = writer.book
                worksheet = writer.sheets['Dados_69PG']
                
                # Formata cabeçalho
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                for col_num, value in enumerate(df_export.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 25)
            
            processed_data = output.getvalue()
            
            # Botão de download
            st.download_button(
                label="📥 Baixar Arquivo Excel",
                data=processed_data,
                file_name=f"69PG_convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
            
        else:
            st.warning("⚠️ Não foi possível identificar famílias no arquivo.")
            st.info("""
            **Sugestões:**
            - Verifique se o arquivo está no formato correto 69 PG
            - Confirme se existem seções 'Nome:', 'I módulo' e 'Familia'
            - O arquivo pode ter um formato diferente do esperado
            """)
            
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("Tente verificar o formato do arquivo ou entre em contato com o suporte.")

else:
    st.info("👆 Faça o upload do arquivo 69 PG para iniciar a conversão.")

# Adiciona seção de instruções e informações
with st.expander("ℹ️ Instruções de Uso e Informações"):
    st.markdown("""
    ### 📋 Como Usar:
    1. **Upload**: Clique em "Browse files" ou arraste seu arquivo 69 PG
    2. **Processamento Automático**: O app analisará e estruturará os dados
    3. **Verificação**: Confira os dados processados na visualização
    4. **Download**: Baixe o arquivo Excel estruturado

    ### 🏷️ Estrutura Esperada no Arquivo 69 PG:
    ```
    Nome: JOÃO DA SILVA
    I módulo: Coparticipação - Informações do plano...
    Familia: Dados da família...
    Dependente 1: MARIA SILVA
    Dependente 2: PEDRO SILVA
    ```

    ### 📊 Estrutura do Excel Gerado:
    - **Nome_Titular**: Nome do titular do plano
    - **Modulo_Coparticipacao**: Informações do módulo e coparticipação
    - **Info_Familia**: Dados da família
    - **Dependente**: Nome do dependente (ou titular se for ele mesmo)
    - **Tipo**: "Titular" ou "Dependente"

    ### 🔧 Suporte:
    Se o processamento não funcionar corretamente:
    - Verifique o formato exato do seu arquivo
    - Entre em contato para ajustes específicos
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido para conversão de arquivos 69 PG*")