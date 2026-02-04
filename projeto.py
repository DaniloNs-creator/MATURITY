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
# CONFIGURAÇÃO DO WEBDRIVER (CORRIGIDA PARA CLOUD)
# ============================================================================
print("\n" + "=" * 70)
print("🔧 CONFIGURANDO WEBDRIVER")
print("=" * 70)

def setup_webdriver():
    """Configura o WebDriver com suporte nativo ao Streamlit Cloud (Linux)"""
    
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    
    chrome_options = Options()
    
    # Configurações OBRIGATÓRIAS para rodar em container/cloud
    chrome_options.add_argument('--headless')  # Sem interface gráfica
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Configurar downloads
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # ------------------------------------------------------------------------
    # CENÁRIO 1: STREAMLIT CLOUD (LINUX DEBIAN)
    # ------------------------------------------------------------------------
    if IS_STREAMLIT_CLOUD:
        try:
            print("\n☁️ Detectado ambiente Cloud. Configurando Chromium do sistema...")
            
            # Caminhos padrão no ambiente Debian do Streamlit
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromedriver")
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ WebDriver Cloud configurado com sucesso!")
            return driver, "System Chromium (Cloud)"
            
        except Exception as e:
            print(f"❌ Falha ao iniciar Chromium do sistema: {e}")
            # Se falhar aqui no Cloud, é crítico, mas tentaremos os fallbacks abaixo

    # ------------------------------------------------------------------------
    # CENÁRIO 2: AMBIENTE LOCAL (WINDOWS/MAC) - TENTATIVAS ORIGINAIS
    # ------------------------------------------------------------------------
    
    # Tentativa com AutoInstaller (Melhor para Windows local)
    try:
        print("\n🔄 Tentativa Local: ChromeDriver AutoInstaller")
        import chromedriver_autoinstaller
        chromedriver_path = chromedriver_autoinstaller.install()
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriver Local configurado com sucesso")
        return driver, "ChromeDriver AutoInstaller"
    except Exception as e:
        print(f"❌ Tentativa Local falhou: {e}")

    # Tentativa com WebDriver Manager
    try:
        print("\n🔄 Tentativa Local: WebDriver Manager")
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriver Manager configurado com sucesso")
        return driver, "WebDriver Manager"
    except Exception as e:
        print(f"❌ Tentativa Manager falhou: {e}")

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
        
        if "login" not in current_url.lower():
            print("✅ Login verificado pela URL")
            return True
        
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
        
        # 1. LOGIN
        print("\n1️⃣  ETAPA 1: LOGIN")
        print("-" * 40)
        
        print("🌐 Navegando para página de login...")
        driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
        
        time.sleep(5)
        salvar_screenshot("login_page")
        
        try:
            user_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nomeusuario"]')))
            user_field.clear()
            user_field.send_keys("HBR0455")
            print("👤 Usuário preenchido: HBR0455")
        except Exception as e:
            print(f"❌ Erro ao preencher usuário: {e}")
            return
        
        try:
            pwd_field = driver.find_element(By.XPATH, '//*[@id="senha"]')
            pwd_field.clear()
            pwd_field.send_keys("XXXXXXXXXX")  # Substituir pela senha real
            print("🔒 Senha preenchida")
        except:
            print("🚨 Não foi possível encontrar campo de senha")
            return
        
        try:
            pwd_field.send_keys(Keys.ENTER)
            print("↵ Enter pressionado para login")
        except:
            print("⚠️  Não foi possível submeter formulário")
        
        time.sleep(8)
        salvar_screenshot("pos_login")
        
        if not verificar_login():
            print("❌ Falha no login. Verifique as credenciais.")
            return
        
        print("✅ Login realizado com sucesso!")
        
        # 2. NAVEGAÇÃO
        print("\n2️⃣  ETAPA 2: NAVEGAÇÃO PARA RECEPTOR CTEs")
        print("-" * 40)
        
        try:
            receptor_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a'))
            )
            receptor_link.click()
            print("📍 Navegando para Receptor CTEs (XPATH)")
        except:
            print("⚠️  XPATH não encontrado, tentando busca por texto...")
            try:
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    if 'receptor' in link.text.lower():
                        link.click()
                        break
            except:
                print("❌ Não foi possível navegar")
                return
        
        time.sleep(5)
        salvar_screenshot("receptor_ctes")
        
        # 3. FILTRO DE DATAS
        print("\n3️⃣  ETAPA 3: FILTRO DE DATAS")
        print("-" * 40)
        
        try:
            dt_ini = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDataInicial"]')))
            dt_ini.click()
            dt_ini.clear()
            dt_ini.send_keys("01/09/2025")
            print("📅 Data inicial: 01/09/2025")
        except:
            print("❌ Erro data inicial")
        
        try:
            dt_fim = driver.find_element(By.XPATH, '//*[@id="consultaDataFinal"]')
            dt_fim.click()
            dt_fim.clear()
            dt_fim.send_keys("31/01/2026")
            dt_fim.send_keys(Keys.ENTER)
            print("📅 Data final: 31/01/2026 e Enter pressionado")
        except:
            print("❌ Erro data final")
        
        time.sleep(5)
        salvar_screenshot("filtro_aplicado")
        
        # 4. PAGINAÇÃO
        print("\n4️⃣  ETAPA 4: CONFIGURAÇÃO DE PAGINAÇÃO")
        print("-" * 40)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        try:
            selects = driver.find_elements(By.TAG_NAME, 'select')
            for select_element in selects:
                try:
                    select = Select(select_element)
                    for option in select.options:
                        if '200' in option.text or option.get_attribute('value') == '200':
                            select.select_by_visible_text(option.text)
                            print(f"✅ Paginação configurada: {option.text}")
                            break
                except:
                    continue
        except Exception as e:
            print(f"⚠️  Erro paginação: {e}")
        
        time.sleep(3)
        
        # 5. DOWNLOAD
        print("\n5️⃣  ETAPA 5: DOWNLOAD DOS XMLs")
        print("=" * 70)
        
        ciclos_executados = 0
        max_ciclos = 5 
        
        for ciclo in range(max_ciclos):
            print(f"\n🔄 CICLO {ciclo + 1} de {max_ciclos}")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Selecionar itens
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                if checkboxes:
                    for cb in checkboxes:
                        if cb.is_displayed() and cb.is_enabled():
                            if not cb.is_selected():
                                cb.click()
                                print("✅ Todos os itens selecionados")
                            break
            except Exception as e:
                print(f"⚠️ Erro checkbox: {e}")
            
            time.sleep(2)
            
            # Clicar botão XML
            try:
                buttons = driver.find_elements(By.TAG_NAME, 'button')
                xml_button = None
                for button in buttons:
                    text = button.text.lower()
                    if 'xml' in text and ('múltiplo' in text or 'multiplo' in text):
                        xml_button = button
                        break
                
                if xml_button:
                    xml_button.click()
                    print("📄 Download iniciado")
                    aguardar_download(8)
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                    except:
                        pass
                else:
                    print("⚠️ Botão XML não encontrado")
            except Exception as e:
                print(f"⚠️ Erro botão XML: {e}")
            
            time.sleep(3)
            
            # Desmarcar
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if checkboxes and len(checkboxes) > 0:
                    checkboxes[0].click()
            except:
                pass
            
            # Próxima página
            if ciclo < max_ciclos - 1:
                if verificar_proxima_pagina():
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    try:
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, '#next_plistagem, .ui-paginator-next')
                        if next_buttons:
                            next_buttons[0].click()
                            print("➡️ Próxima página")
                            ciclos_executados += 1
                            time.sleep(5)
                        else:
                            break
                    except:
                        break
                else:
                    break
            else:
                ciclos_executados += 1
        
        # 6. RELATÓRIO
        print("\n" + "=" * 70)
        print(f"✅ FIM. Ciclos: {ciclos_executados}")
        arquivos = list(Path(os.getcwd()).glob('*.xml')) + list(Path(os.getcwd()).glob('*.zip'))
        print(f"📁 Arquivos baixados: {len(arquivos)}")

    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        salvar_screenshot("erro_critico")

# ============================================================================
# EXECUÇÃO
# ============================================================================
def main():
    try:
        executar_processo()
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    if IS_STREAMLIT_CLOUD:
        try:
            import streamlit as st
            st.set_page_config(page_title="MasterSAF XML", layout="wide")
            st.title("📊 MasterSAF XML Download")
            
            with st.sidebar:
                if st.button("🚀 Iniciar Download", type="primary"):
                    with st.spinner("Executando..."):
                        import io
                        from contextlib import redirect_stdout, redirect_stderr
                        f = io.StringIO()
                        with redirect_stdout(f), redirect_stderr(f):
                            main()
                        st.text_area("Logs", f.getvalue(), height=400)
            
            st.info("Sistema pronto. Clique no botão lateral para iniciar.")
        except ImportError:
            main()
    else:
        main()
