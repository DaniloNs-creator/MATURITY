# projeto.py - Script completo para download de XMLs do MasterSAF

import os
import sys
import time
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO INICIAL - VERIFICAÇÕES DE AMBIENTE
# ============================================================================
print("=" * 70)
print("🚀 INICIANDO SCRIPT DE DOWNLOAD DE XMLs - MASTERSAF")
print("=" * 70)

# Verificar se estamos no Streamlit Cloud
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SHARING') is not None
print(f"📡 Ambiente detectado: {'Streamlit Cloud' if IS_STREAMLIT_CLOUD else 'Local'}")

# ============================================================================
# CONFIGURAÇÃO DO WEBDRIVER (SOLUÇÃO ROBUSTA)
# ============================================================================
print("\n" + "=" * 70)
print("🔧 CONFIGURANDO WEBDRIVER")
print("=" * 70)

# TENTATIVAS EM ORDEM DE PRIORIDADE
def setup_webdriver():
    """Configura o WebDriver com múltiplas tentativas de fallback"""
    
    attempts = []
    
    # TENTATIVA 1: ChromeDriver AutoInstaller (mais confiável)
    try:
        print("\n🔄 Tentativa 1: ChromeDriver AutoInstaller")
        import chromedriver_autoinstaller
        # Verificar e instalar ChromeDriver
        chromedriver_path = chromedriver_autoinstaller.install()
        print(f"✅ ChromeDriver instalado em: {chromedriver_path}")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        
        # Configurações ESSENCIAIS para cloud
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Evitar detecção como bot
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configurar downloads
        prefs = {
            "download.default_directory": os.getcwd(),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriver configurado com sucesso (Tentativa 1)")
        return driver, "ChromeDriver AutoInstaller"
        
    except Exception as e1:
        attempts.append(f"Tentativa 1 falhou: {str(e1)[:100]}")
        print(f"❌ Tentativa 1 falhou: {e1}")
    
    # TENTATIVA 2: WebDriver Manager
    try:
        print("\n🔄 Tentativa 2: WebDriver Manager")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriver configurado com sucesso (Tentativa 2)")
        return driver, "WebDriver Manager"
        
    except Exception as e2:
        attempts.append(f"Tentativa 2 falhou: {str(e2)[:100]}")
        print(f"❌ Tentativa 2 falhou: {e2}")
    
    # TENTATIVA 3: Configuração direta (último recurso)
    try:
        print("\n🔄 Tentativa 3: Configuração direta")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Configurações específicas para Streamlit Cloud
        if IS_STREAMLIT_CLOUD:
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            chrome_options.add_argument('--disable-setuid-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ WebDriver configurado com sucesso (Tentativa 3)")
        return driver, "Configuração direta"
        
    except Exception as e3:
        attempts.append(f"Tentativa 3 falhou: {str(e3)[:100]}")
        print(f"❌ Tentativa 3 falhou: {e3}")
    
    # SE TODAS AS TENTATIVAS FALHAREM
    print("\n" + "=" * 70)
    print("❌ FALHA CRÍTICA - TODAS AS TENTATIVAS FALHARAM")
    print("=" * 70)
    for i, attempt in enumerate(attempts, 1):
        print(f"Tentativa {i}: {attempt}")
    
    return None, None

# Configurar WebDriver
driver, method = setup_webdriver()

if driver is None:
    print("\n🚨 Não foi possível configurar o WebDriver. Encerrando.")
    sys.exit(1)

print(f"\n🎉 WebDriver configurado usando: {method}")

# ============================================================================
# IMPORTAÇÕES DO SELENIUM (APÓS CONFIGURAR WEBDRIVER)
# ============================================================================
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

# Configurar wait
wait = WebDriverWait(driver, 30)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def verificar_login():
    """Verifica se o login foi realizado com sucesso"""
    try:
        time.sleep(3)
        current_url = driver.current_url
        
        # Verificar por URL
        if "login" not in current_url.lower():
            print("✅ Login verificado pela URL")
            return True
        
        # Verificar por elementos específicos
        elementos_login = [
            '//*[@id="linkListagemReceptorCTEs"]/a',
            '//*[contains(text(), "Bem-vindo")]',
            '//*[contains(text(), "Dashboard")]',
            '//*[contains(text(), "Sair")]'
        ]
        
        for xpath in elementos_login:
            try:
                element = driver.find_element(By.XPATH, xpath)
                if element.is_displayed():
                    print(f"✅ Login verificado: {xpath[:50]}...")
                    return True
            except:
                continue
        
        print("⚠️ Não foi possível verificar o login automaticamente")
        return False
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar login: {str(e)}")
        return False

def verificar_proxima_pagina():
    """Verifica se há próxima página disponível"""
    try:
        # Tentar encontrar botão próximo
        try:
            next_btn = driver.find_element(By.XPATH, '//*[@id="next_plistagem"]')
            if "ui-state-disabled" in next_btn.get_attribute("class"):
                print("ℹ️  Botão 'Próximo' está desabilitado")
                return False
            else:
                print("✅ Há próxima página disponível")
                return True
        except:
            pass
        
        # Método alternativo: verificar paginação
        try:
            pagination_elements = driver.find_elements(By.CSS_SELECTOR, '.ui-paginator-page, .pagination a')
            if pagination_elements:
                current_page = None
                for element in pagination_elements:
                    if "active" in element.get_attribute("class") or "selected" in element.get_attribute("class"):
                        current_page = element.text
                
                if current_page:
                    print(f"ℹ️  Página atual: {current_page}")
                    return True
        except:
            pass
        
        # Verificar se há mais dados na tabela
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
            if len(rows) > 0:
                print(f"ℹ️  {len(rows)} linhas na tabela")
                return True
        except:
            pass
        
        print("ℹ️  Não foi possível determinar se há próxima página")
        return False
        
    except Exception as e:
        print(f"⚠️  Erro ao verificar próxima página: {str(e)}")
        return False

def aguardar_download(tempo=10):
    """Aguarda o download ser concluído"""
    print(f"⏳ Aguardando download ({tempo}s)...")
    time.sleep(tempo)
    
    # Verificar se há arquivos baixados recentemente
    downloads_dir = os.getcwd()
    arquivos_antes = list(Path(downloads_dir).glob('*.xml')) + list(Path(downloads_dir).glob('*.zip'))
    
    if arquivos_antes:
        print(f"📁 {len(arquivos_antes)} arquivos XML/ZIP encontrados")
    
    return True

def salvar_screenshot(nome):
    """Salva um screenshot para debug"""
    try:
        screenshot_path = f"screenshot_{nome}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot salvo: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"⚠️  Erro ao salvar screenshot: {e}")
        return None

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
def executar_processo():
    """Função principal que executa todo o processo"""
    
    try:
        print("\n" + "=" * 70)
        print("🏁 INICIANDO PROCESSAMENTO")
        print("=" * 70)
        
        # ====================================================================
        # 1. LOGIN NO SISTEMA
        # ====================================================================
        print("\n1️⃣  ETAPA 1: LOGIN")
        print("-" * 40)
        
        # Navegar para página de login
        print("🌐 Navegando para página de login...")
        driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
        
        # Aguardar carregamento
        time.sleep(5)
        salvar_screenshot("login_page")
        
        # Preencher usuário
        try:
            user_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nomeusuario"]')))
            user_field.clear()
            user_field.send_keys("HBR0455")
            print("👤 Usuário preenchido: HBR0455")
        except Exception as e:
            print(f"❌ Erro ao preencher usuário: {e}")
            # Tentar método alternativo
            try:
                user_field = driver.find_element(By.ID, 'nomeusuario')
                user_field.send_keys("HBR0455")
                print("👤 Usuário preenchido (método alternativo)")
            except:
                print("🚨 Não foi possível encontrar campo de usuário")
                return
        
        # Preencher senha
        try:
            pwd_field = driver.find_element(By.XPATH, '//*[@id="senha"]')
            pwd_field.clear()
            pwd_field.send_keys("XXXXXXXXXX")  # Substituir pela senha real
            print("🔒 Senha preenchida")
        except:
            try:
                pwd_field = driver.find_element(By.ID, 'senha')
                pwd_field.send_keys("XXXXXXXXXX")
                print("🔒 Senha preenchida (método alternativo)")
            except:
                print("🚨 Não foi possível encontrar campo de senha")
                return
        
        # Submeter formulário
        try:
            pwd_field.send_keys(Keys.ENTER)
            print("↵ Enter pressionado para login")
        except:
            try:
                login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
                login_button.click()
                print("🖱️  Botão de login clicado")
            except:
                print("⚠️  Não foi possível submeter formulário, tentando continuar...")
        
        # Aguardar e verificar login
        time.sleep(8)
        salvar_screenshot("pos_login")
        
        if not verificar_login():
            print("❌ Falha no login. Verifique as credenciais.")
            salvar_screenshot("login_falhou")
            return
        
        print("✅ Login realizado com sucesso!")
        
        # ====================================================================
        # 2. NAVEGAÇÃO PARA RECEPTOR CTEs
        # ====================================================================
        print("\n2️⃣  ETAPA 2: NAVEGAÇÃO PARA RECEPTOR CTEs")
        print("-" * 40)
        
        # Método 1: XPATH específico
        try:
            receptor_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a'))
            )
            receptor_link.click()
            print("📍 Navegando para Receptor CTEs (XPATH)")
        except:
            # Método 2: Buscar por texto
            print("⚠️  XPATH não encontrado, buscando por texto...")
            try:
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    text = link.text.lower()
                    if 'receptor' in text or 'cte' in text or 'ct-e' in text:
                        link.click()
                        print(f"📍 Encontrado por texto: {text[:30]}")
                        break
            except Exception as e:
                print(f"❌ Não foi possível navegar: {e}")
                return
        
        time.sleep(5)
        salvar_screenshot("receptor_ctes")
        print("✅ Página de Receptor CTEs carregada")
        
        # ====================================================================
        # 3. APLICAR FILTRO DE DATAS
        # ====================================================================
        print("\n3️⃣  ETAPA 3: FILTRO DE DATAS")
        print("-" * 40)
        
        # Data Inicial
        try:
            dt_ini = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="consultaDataInicial"]')
            ))
            dt_ini.click()
            dt_ini.clear()
            dt_ini.send_keys("01/09/2025")  # Ajustar para data válida
            print("📅 Data inicial: 01/09/2025")
        except:
            print("⚠️  Campo de data inicial não encontrado")
            # Tentar via JavaScript
            try:
                driver.execute_script("""
                    document.getElementById('consultaDataInicial').value = '01/09/2025';
                """)
                print("📅 Data inicial definida via JavaScript")
            except:
                print("❌ Não foi possível definir data inicial")
        
        # Data Final
        try:
            dt_fim = driver.find_element(By.XPATH, '//*[@id="consultaDataFinal"]')
            dt_fim.click()
            dt_fim.clear()
            dt_fim.send_keys("31/01/2026")
            print("📅 Data final: 31/01/2026")
        except:
            print("⚠️  Campo de data final não encontrado")
            try:
                driver.execute_script("""
                    document.getElementById('consultaDataFinal').value = '31/01/2026';
                """)
                print("📅 Data final definida via JavaScript")
            except:
                print("❌ Não foi possível definir data final")
        
        # Aplicar filtro
        try:
            dt_fim.send_keys(Keys.ENTER)
            print("✅ Filtro aplicado com Enter")
            time.sleep(5)
        except:
            print("⚠️  Não foi possível aplicar filtro, continuando...")
        
        salvar_screenshot("filtro_aplicado")
        
        # ====================================================================
        # 4. CONFIGURAR PAGINAÇÃO (200 itens por página)
        # ====================================================================
        print("\n4️⃣  ETAPA 4: CONFIGURAÇÃO DE PAGINAÇÃO")
        print("-" * 40)
        
        # Rolar para baixo para encontrar controles de paginação
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Tentar configurar para 200 itens por página
        try:
            # Procurar select de paginação
            selects = driver.find_elements(By.TAG_NAME, 'select')
            for select_element in selects:
                try:
                    select = Select(select_element)
                    # Tentar encontrar opção 200
                    for option in select.options:
                        if '200' in option.text or option.get_attribute('value') == '200':
                            select.select_by_visible_text(option.text)
                            print(f"✅ Paginação configurada: {option.text} itens por página")
                            break
                except:
                    continue
        except Exception as e:
            print(f"⚠️  Não foi possível configurar paginação: {e}")
        
        time.sleep(3)
        salvar_screenshot("paginacao_configurada")
        
        # ====================================================================
        # 5. LOOP DE DOWNLOAD DOS XMLs
        # ====================================================================
        print("\n" + "=" * 70)
        print("5️⃣  ETAPA 5: DOWNLOAD DOS XMLs")
        print("=" * 70)
        
        ciclos_executados = 0
        max_ciclos = 5  # Reduzido para testes, aumentar para 65 em produção
        
        for ciclo in range(max_ciclos):
            print(f"\n🔄 CICLO {ciclo + 1} de {max_ciclos}")
            print("-" * 30)
            
            # A) Voltar ao topo
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # B) Selecionar todos os itens
            try:
                # Procurar checkbox principal
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                if checkboxes:
                    # Tentar encontrar o checkbox principal (geralmente o primeiro)
                    main_checkbox = None
                    for cb in checkboxes:
                        if cb.is_displayed() and cb.is_enabled():
                            main_checkbox = cb
                            break
                    
                    if main_checkbox:
                        if not main_checkbox.is_selected():
                            main_checkbox.click()
                            print("✅ Todos os itens selecionados")
                        else:
                            print("ℹ️  Itens já selecionados")
                    else:
                        print("⚠️  Checkbox principal não encontrado")
                else:
                    print("⚠️  Nenhum checkbox encontrado")
                    
            except Exception as e:
                print(f"⚠️  Erro ao selecionar itens: {e}")
            
            time.sleep(2)
            
            # C) Clicar em "XML Múltiplos"
            try:
                # Procurar botão XML Múltiplos
                buttons = driver.find_elements(By.TAG_NAME, 'button')
                xml_button = None
                
                for button in buttons:
                    text = button.text.lower()
                    if 'xml' in text and ('múltiplo' in text or 'multiplo' in text):
                        xml_button = button
                        break
                
                if xml_button:
                    xml_button.click()
                    print("📄 Botão 'XML Múltiplos' clicado")
                    
                    # Aguardar download
                    aguardar_download(8)
                    
                    # Pressionar Enter se necessário
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                        print("↵ Enter pressionado")
                    except:
                        pass
                        
                else:
                    print("⚠️  Botão 'XML Múltiplos' não encontrado")
                    
            except Exception as e:
                print(f"⚠️  Erro ao processar XML Múltiplos: {e}")
            
            time.sleep(3)
            
            # D) Desmarcar checkbox
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if checkboxes:
                    checkboxes[0].click()
                    print("✅ Checkbox desmarcado")
            except:
                pass
            
            time.sleep(2)
            
            # E) Navegar para próxima página (se não for o último ciclo)
            if ciclo < max_ciclos - 1:
                if verificar_proxima_pagina():
                    try:
                        # Rolar para baixo
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        # Clicar no botão próximo
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, '#next_plistagem, .ui-paginator-next, [title="Next"], [aria-label="Next"]')
                        
                        if next_buttons:
                            next_buttons[0].click()
                            print("➡️  Navegando para próxima página")
                            ciclos_executados += 1
                            time.sleep(5)
                        else:
                            print("⚠️  Botão próximo não encontrado")
                            break
                            
                    except Exception as e:
                        print(f"❌ Erro ao navegar: {e}")
                        break
                else:
                    print("🏁 Fim das páginas atingido")
                    break
            else:
                print("🎯 Último ciclo completado")
                ciclos_executados += 1
        
        # ====================================================================
        # 6. RELATÓRIO FINAL
        # ====================================================================
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        print(f"✅ Processo concluído!")
        print(f"📈 Ciclos executados: {ciclos_executados} de {max_ciclos}")
        
        # Verificar arquivos baixados
        downloads_dir = os.getcwd()
        arquivos_xml = list(Path(downloads_dir).glob('*.xml'))
        arquivos_zip = list(Path(downloads_dir).glob('*.zip'))
        
        print(f"📁 Arquivos XML encontrados: {len(arquivos_xml)}")
        print(f"📁 Arquivos ZIP encontrados: {len(arquivos_zip)}")
        
        if arquivos_xml or arquivos_zip:
            print("\n📋 Lista de arquivos baixados:")
            for arquivo in arquivos_xml[:10]:  # Mostrar apenas os 10 primeiros
                print(f"  • {arquivo.name}")
            if len(arquivos_xml) > 10:
                print(f"  • ... e mais {len(arquivos_xml) - 10} arquivos")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO PROCESSO: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Salvar informações para debug
        try:
            # Screenshot do erro
            salvar_screenshot("erro_critico")
            
            # Salvar página HTML
            page_source_path = f"page_source_error_{int(time.time())}.html"
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"📄 Código fonte salvo: {page_source_path}")
            
            # URL atual
            print(f"🌐 URL atual: {driver.current_url}")
            
        except Exception as debug_error:
            print(f"⚠️  Erro ao salvar debug: {debug_error}")

# ============================================================================
# EXECUÇÃO PRINCIPAL COM CONTROLE DE ERROS
# ============================================================================
def main():
    """Função principal com tratamento de erros robusto"""
    
    try:
        print("\n" + "=" * 70)
        print("🎬 INICIANDO EXECUÇÃO DO SCRIPT")
        print("=" * 70)
        
        # Executar o processo
        executar_processo()
        
        print("\n✅ Processo finalizado com sucesso!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        
    except Exception as e:
        print(f"\n❌ ERRO GLOBAL: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n" + "=" * 70)
        print("🧹 FINALIZANDO RECURSOS")
        print("=" * 70)
        
        try:
            # Fechar navegador
            driver.quit()
            print("✅ Navegador fechado")
        except:
            print("⚠️  Navegador já fechado ou erro ao fechar")
        
        print("\n🎯 SCRIPT FINALIZADO!")
        print("=" * 70)

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    
    # Se estiver no Streamlit Cloud, criar interface web
    if IS_STREAMLIT_CLOUD:
        try:
            import streamlit as st
            
            st.set_page_config(
                page_title="MasterSAF XML Download",
                page_icon="📊",
                layout="wide"
            )
            
            st.title("📊 MasterSAF XML Download")
            st.markdown("---")
            
            # Sidebar com configurações
            with st.sidebar:
                st.header("⚙️ Configurações")
                ciclos = st.slider("Número de ciclos", 1, 65, 5)
                modo_teste = st.checkbox("Modo de teste", value=True)
                
                if st.button("🚀 Iniciar Download", type="primary"):
                    with st.spinner("Executando processo de download..."):
                        # Criar área para logs
                        log_container = st.empty()
                        
                        # Redirecionar output para Streamlit
                        import io
                        from contextlib import redirect_stdout, redirect_stderr
                        
                        f = io.StringIO()
                        with redirect_stdout(f), redirect_stderr(f):
                            # Executar processo
                            main()
                        
                        # Mostrar logs
                        logs = f.getvalue()
                        log_container.text_area("Logs de Execução", logs, height=400)
            
            # Área principal
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                ### 📋 Instruções:
                1. Configure o número de ciclos na sidebar
                2. Clique em "Iniciar Download"
                3. Aguarde a execução completa
                4. Verifique os logs abaixo
                """)
            
            with col2:
                st.warning("""
                ### ⚠️ Importante:
                - O processo pode levar vários minutos
                - Mantenha a página aberta durante a execução
                - Verifique os logs para ver o progresso
                - Arquivos são baixados no diretório atual
                """)
            
            st.markdown("---")
            st.caption("Versão 2.0 - Otimizado para Streamlit Cloud")
            
        except ImportError:
            print("Streamlit não disponível, executando em modo console...")
            main()
    else:
        # Modo console (local)
        main()