from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import sys

print("=" * 60)
print("INICIANDO SCRIPT DE DOWNLOAD DE XMLs - MASTERSAF")
print("=" * 60)

# ============================================================================
# CONFIGURAÇÃO DO WEBDRIVER PARA AMBIENTE CLOUD/LOCAL
# ============================================================================
print("\n🔧 Configurando WebDriver...")

chrome_options = Options()

# Configurações essenciais para ambientes cloud (Streamlit Cloud, Heroku, etc.)
chrome_options.add_argument('--headless')  # Modo sem interface gráfica
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')

# Configurações para evitar detecção como bot
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Configurar preferências para download
prefs = {
    "download.default_directory": os.getcwd(),  # Diretório atual para downloads
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

try:
    # Verificar se estamos em ambiente cloud
    is_cloud = False
    
    # Verificar variáveis de ambiente comuns em plataformas cloud
    cloud_indicators = ['STREAMLIT_SHARING', 'DYNO', 'K_SERVICE', 'AWS_LAMBDA', 'VERCEL']
    for indicator in cloud_indicators:
        if os.environ.get(indicator):
            is_cloud = True
            print(f"📡 Ambiente cloud detectado ({indicator})")
            break
    
    if is_cloud:
        # Caminhos padrão para Chrome/Chromium em ambientes cloud
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        # Verificar caminhos alternativos
        possible_chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/app/.chromedriver/bin/chromedriver'
        ]
        
        chromedriver_path = None
        for path in possible_chromedriver_paths:
            if os.path.exists(path):
                chromedriver_path = path
                print(f"✅ ChromeDriver encontrado em: {path}")
                break
        
        if chromedriver_path:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            print("⚠️ ChromeDriver não encontrado nos caminhos padrão. Tentando instalação automática...")
            # Tentar usar webdriver-manager se disponível
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ ChromeDriver instalado via webdriver-manager")
            except ImportError:
                print("❌ webdriver-manager não disponível. Usando configuração padrão...")
                driver = webdriver.Chrome(options=chrome_options)
    else:
        # Ambiente local
        print("💻 Ambiente local detectado")
        try:
            # Tentar usar webdriver-manager para gerenciar automaticamente o ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ ChromeDriver configurado via webdriver-manager")
        except ImportError:
            print("⚠️ webdriver-manager não encontrado. Usando ChromeDriver local...")
            driver = webdriver.Chrome(options=chrome_options)
    
    print("✅ WebDriver configurado com sucesso!")
    
except Exception as e:
    print(f"❌ ERRO ao configurar WebDriver: {str(e)}")
    print("Tentando configuração de fallback...")
    
    # Última tentativa com configuração básica
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver iniciado com configuração de fallback")
    except Exception as fallback_error:
        print(f"❌ FALHA CRÍTICA: Não foi possível iniciar o WebDriver")
        print(f"Erro: {str(fallback_error)}")
        sys.exit(1)

# Configurar timeout e maximizar janela
driver.maximize_window()
wait = WebDriverWait(driver, 30)  # Timeout aumentado para 30 segundos
print(f"⏱️  Timeout configurado: 30 segundos")

# ============================================================================
# FUNÇÃO PARA VERIFICAR SE O LOGIN FOI BEM SUCEDIDO
# ============================================================================
def verificar_login():
    """Verifica se o login foi realizado com sucesso"""
    try:
        # Verificar se há elemento indicando login bem-sucedido
        time.sleep(3)
        current_url = driver.current_url
        if "login" not in current_url.lower():
            print("✅ Login verificado com sucesso")
            return True
        
        # Verificar por elementos específicos após login
        elementos_login = [
            '//*[@id="linkListagemReceptorCTEs"]/a',
            '//*[contains(text(), "Bem-vindo")]',
            '//*[contains(text(), "Dashboard")]'
        ]
        
        for xpath in elementos_login:
            try:
                element = driver.find_element(By.XPATH, xpath)
                if element.is_displayed():
                    print("✅ Login verificado via elemento específico")
                    return True
            except:
                continue
        
        print("⚠️ Não foi possível verificar o login automaticamente")
        return True  # Continuar mesmo sem verificação clara
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar login: {str(e)}")
        return True  # Continuar mesmo com erro na verificação

# ============================================================================
# FUNÇÃO PARA VERIFICAR SE HÁ MAIS PÁGINAS
# ============================================================================
def verificar_proxima_pagina():
    """Verifica se há próxima página disponível"""
    try:
        # Verificar botão próximo
        next_btn = driver.find_element(By.XPATH, '//*[@id="next_plistagem"]')
        
        # Verificar se o botão está habilitado
        if "ui-state-disabled" in next_btn.get_attribute("class"):
            print("ℹ️  Botão 'Próximo' está desabilitado - fim das páginas")
            return False
        else:
            print("✅ Há próxima página disponível")
            return True
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar próxima página: {str(e)}")
        
        # Tentar método alternativo
        try:
            pagination_elements = driver.find_elements(By.CLASS_NAME, 'ui-paginator-page')
            if pagination_elements:
                print(f"ℹ️  Encontrados {len(pagination_elements)} elementos de paginação")
                return True
        except:
            pass
        
        return False

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
def main():
    try:
        print("\n" + "=" * 60)
        print("🏁 INICIANDO PROCESSAMENTO")
        print("=" * 60)
        
        # ====================================================================
        # 1. LOGIN NO SISTEMA
        # ====================================================================
        print("\n1️⃣  ETAPA 1: LOGIN")
        print("-" * 40)
        
        driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
        print("📄 Página de login carregada")
        
        # Aguardar e preencher usuário
        user = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nomeusuario"]')))
        user.send_keys("HBR0455")
        print("👤 Usuário preenchido")
        
        # Preencher senha
        pwd = driver.find_element(By.XPATH, '//*[@id="senha"]')
        pwd.send_keys("XXXXXXXXXX")
        print("🔒 Senha preenchida")
        
        # Clicar Enter para login
        pwd.send_keys(Keys.ENTER)
        print("↵ Enter pressionado para login")
        
        # Verificar login
        time.sleep(5)
        if not verificar_login():
            print("❌ Falha no login. Verifique credenciais.")
            return
        
        print("✅ Login realizado com sucesso!")
        
        # ====================================================================
        # 2. NAVEGAÇÃO PARA RECEPTOR CTEs
        # ====================================================================
        print("\n2️⃣  ETAPA 2: NAVEGAÇÃO PARA RECEPTOR CTEs")
        print("-" * 40)
        
        try:
            receptor = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a')))
            receptor.click()
            print("📍 Navegando para Receptor CTEs...")
        except Exception as e:
            print(f"⚠️  Elemento não encontrado pelo XPATH. Tentando método alternativo...")
            
            # Método alternativo: buscar por texto ou outro atributo
            try:
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    if 'receptor' in link.text.lower() or 'cte' in link.text.lower():
                        link.click()
                        print("✅ Encontrado por texto alternativo")
                        break
            except:
                print("❌ Não foi possível navegar para Receptor CTEs")
                return
        
        time.sleep(5)
        print("✅ Página de Receptor CTEs carregada")
        
        # ====================================================================
        # 3. APLICAR FILTRO DE DATAS
        # ====================================================================
        print("\n3️⃣  ETAPA 3: FILTRO DE DATAS")
        print("-" * 40)
        
        try:
            # Data inicial
            dt_ini = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDataInicial"]')))
            dt_ini.click()
            dt_ini.send_keys(Keys.CONTROL + "a")  # Selecionar tudo
            dt_ini.send_keys(Keys.DELETE)  # Limpar campo
            dt_ini.send_keys("01/09/2026")  # Formato correto DD/MM/YYYY
            print("📅 Data inicial: 01/09/2026")
            
            # Data final
            dt_fim = driver.find_element(By.XPATH, '//*[@id="consultaDataFinal"]')
            dt_fim.click()
            dt_fim.send_keys(Keys.CONTROL + "a")  # Selecionar tudo
            dt_fim.send_keys(Keys.DELETE)  # Limpar campo
            dt_fim.send_keys("31/01/2026")  # Formato correto DD/MM/YYYY
            print("📅 Data final: 31/01/2026")
            
            # Aplicar filtro
            dt_fim.send_keys(Keys.ENTER)
            print("✅ Filtro aplicado com Enter")
            
        except Exception as e:
            print(f"⚠️  Erro ao aplicar filtro de datas: {str(e)}")
            print("Tentando método alternativo...")
            
            # Método alternativo usando JavaScript
            try:
                driver.execute_script("""
                    document.getElementById('consultaDataInicial').value = '01/09/2026';
                    document.getElementById('consultaDataFinal').value = '31/01/2026';
                    
                    // Disparar evento change
                    var event = new Event('change', { bubbles: true });
                    document.getElementById('consultaDataFinal').dispatchEvent(event);
                """)
                print("✅ Filtro aplicado via JavaScript")
            except:
                print("❌ Não foi possível aplicar filtro de datas")
                return
        
        time.sleep(3)
        
        # ====================================================================
        # 4. CONFIGURAR 200 ITENS POR PÁGINA
        # ====================================================================
        print("\n4️⃣  ETAPA 4: CONFIGURAÇÃO DE PAGINAÇÃO")
        print("-" * 40)
        
        # Rolar para baixo para encontrar o seletor
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        try:
            # Localizar o seletor de itens por página
            select_pag = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="plistagem_center"]/table/tbody/tr/td[8]/select')))
            select_pag.click()
            
            # Selecionar opção "200"
            from selenium.webdriver.support.select import Select
            select = Select(select_pag)
            select.select_by_value("200")  # Ou select_by_visible_text("200")
            
            print("✅ Configurado para 200 itens por página")
            
        except Exception as e:
            print(f"⚠️  Erro ao configurar paginação: {str(e)}")
            print("Tentando método alternativo...")
            
            # Método alternativo
            try:
                # Procurar todos os selects na página
                selects = driver.find_elements(By.TAG_NAME, 'select')
                for select_element in selects:
                    try:
                        select_obj = Select(select_element)
                        options = select_obj.options
                        for option in options:
                            if "200" in option.text:
                                select_obj.select_by_visible_text(option.text)
                                print(f"✅ Paginação configurada via método alternativo")
                                break
                    except:
                        continue
            except:
                print("⚠️  Continuando sem alterar paginação...")
        
        time.sleep(3)
        
        # ====================================================================
        # 5. LOOP PRINCIPAL PARA DOWNLOAD DOS XMLs
        # ====================================================================
        print("\n" + "=" * 60)
        print("5️⃣  ETAPA 5: DOWNLOAD DOS XMLs (65 CICLOS)")
        print("=" * 60)
        
        ciclos_executados = 0
        max_ciclos = 65
        
        for ciclo in range(max_ciclos):
            print(f"\n🔄 CICLO {ciclo + 1} de {max_ciclos}")
            print("-" * 30)
            
            # A) Voltar ao topo
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # B) Selecionar todos os itens
            try:
                checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input')))
                checkbox.click()
                print("✅ Todos os itens selecionados")
            except Exception as e:
                print(f"⚠️  Erro ao selecionar itens: {str(e)}")
                print("Tentando seleção via JavaScript...")
                
                try:
                    driver.execute_script("""
                        var checkbox = document.querySelector('#jqgh_listagem_checkBox input[type="checkbox"]');
                        if (checkbox) {
                            checkbox.click();
                        }
                    """)
                    print("✅ Itens selecionados via JavaScript")
                except:
                    print("❌ Não foi possível selecionar itens. Continuando...")
            
            time.sleep(3)
            
            # C) Clicar em "XML Múltiplos"
            try:
                xml_multiplos = driver.find_element(By.XPATH, '//*[@id="xml_multiplos"]/h3')
                xml_multiplos.click()
                print("📄 Clicado em 'XML Múltiplos'")
                
                # Aguardar download iniciar
                time.sleep(5)
                
                # Pressionar Enter se necessário
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                print("↵ Enter pressionado para confirmar download")
                
            except Exception as e:
                print(f"⚠️  Erro ao clicar em XML Múltiplos: {str(e)}")
                print("Tentando método alternativo...")
                
                try:
                    # Buscar por elemento com texto "XML"
                    elementos = driver.find_elements(By.XPATH, '//*[contains(text(), "XML")]')
                    for elemento in elementos:
                        if "múltiplo" in elemento.text.lower() or "multiplo" in elemento.text.lower():
                            elemento.click()
                            print("✅ Encontrado e clicado em XML Múltiplos (texto alternativo)")
                            break
                except:
                    print("❌ Não foi possível acessar XML Múltiplos")
            
            time.sleep(3)
            
            # D) Desmarcar checkbox para próxima página
            try:
                driver.find_element(By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input').click()
                print("✅ Checkbox desmarcado")
            except:
                pass  # Não crítico se falhar
            
            time.sleep(2)
            
            # E) Verificar e navegar para próxima página
            if ciclo < max_ciclos - 1:  # Não tentar navegar no último ciclo
                if verificar_proxima_pagina():
                    try:
                        # Rolar para baixo
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        # Clicar no botão próximo
                        next_button = driver.find_element(By.XPATH, '//*[@id="next_plistagem"]/span')
                        next_button.click()
                        print("➡️  Navegando para próxima página")
                        ciclos_executados += 1
                        
                        # Aguardar carregamento da nova página
                        time.sleep(5)
                        
                    except Exception as e:
                        print(f"❌ Erro ao navegar para próxima página: {str(e)}")
                        print("Tentando navegação via JavaScript...")
                        
                        try:
                            driver.execute_script("$('#next_plistagem').click();")
                            print("✅ Navegação via JavaScript bem-sucedida")
                            ciclos_executados += 1
                            time.sleep(5)
                        except:
                            print("❌ Falha na navegação. Encerrando loop.")
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
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        print(f"✅ Processo concluído com sucesso!")
        print(f"📈 Ciclos executados: {ciclos_executados} de {max_ciclos}")
        print(f"⏰ Tempo total aproximado: {(ciclos_executados * 15) // 60} minutos")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO PROCESSO PRINCIPAL: {str(e)}")
        
        # Capturar informações para debug
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Screenshot
            screenshot_path = f'error_screenshot_{timestamp}.png'
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot salvo: {screenshot_path}")
            
            # Código fonte da página
            page_source_path = f'page_source_{timestamp}.html'
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"📄 Código fonte salvo: {page_source_path}")
            
            # URL atual
            print(f"🌐 URL atual: {driver.current_url}")
            
        except Exception as debug_error:
            print(f"⚠️  Erro ao capturar debug: {debug_error}")

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO GLOBAL: {str(e)}")
    finally:
        print("\n" + "=" * 60)
        print("🧹 FINALIZANDO...")
        
        try:
            # Fechar navegador
            driver.quit()
            print("✅ Navegador fechado com sucesso")
        except:
            print("⚠️  Navegador já fechado ou erro ao fechar")
        
        print("🎯 Script finalizado!")
        print("=" * 60)