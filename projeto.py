# projeto.py - Script completo para download de XMLs do MasterSAF

import os
import sys
import time
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO INICIAL
# ============================================================================
print("=" * 70)
print("🚀 INICIANDO SCRIPT DE DOWNLOAD DE XMLs - MASTERSAF")
print("=" * 70)

# Detectar ambiente
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SHARING') is not None or os.environ.get('STREAMLIT_SERVER') is not None
print(f"📡 Ambiente detectado: {'Streamlit Cloud' if IS_STREAMLIT_CLOUD else 'Local'}")

# ============================================================================
# CONFIGURAÇÃO DO WEBDRIVER (VERSÃO OTIMIZADA)
# ============================================================================
print("\n" + "=" * 70)
print("🔧 CONFIGURANDO WEBDRIVER")
print("=" * 70)

def setup_webdriver():
    """Configura o WebDriver com suporte para Streamlit Cloud"""
    
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    
    chrome_options = Options()
    
    # Configurações ESSENCIAIS para ambiente headless
    chrome_options.add_argument('--headless=new')  # Novo modo headless
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--remote-debugging-port=9222')
    
    # Configurações de download
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Configurações específicas para Streamlit Cloud
    if IS_STREAMLIT_CLOUD:
        # Caminhos comuns no Streamlit Cloud
        possible_chrome_paths = [
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable'
        ]
        
        chrome_binary = None
        for path in possible_chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome/Chromium encontrado em: {path}")
                chrome_options.binary_location = path
                break
        
        if not chrome_binary:
            print("⚠️ Chrome/Chromium não encontrado nos caminhos padrão")
    
    # TENTATIVA 1: Usar webdriver-manager
    try:
        print("\n🔄 Tentando webdriver-manager...")
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver configurado via webdriver-manager")
        return driver
        
    except Exception as e:
        print(f"❌ webdriver-manager falhou: {str(e)[:100]}")
    
    # TENTATIVA 2: Usar chromedriver-autoinstaller
    try:
        print("\n🔄 Tentando chromedriver-autoinstaller...")
        import chromedriver_autoinstaller
        
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver configurado via chromedriver-autoinstaller")
        return driver
        
    except Exception as e:
        print(f"❌ chromedriver-autoinstaller falhou: {str(e)[:100]}")
    
    # TENTATIVA 3: Procurar chromedriver instalado via apt
    try:
        print("\n🔄 Procurando chromedriver do sistema...")
        possible_driver_paths = [
            '/usr/bin/chromedriver',
            '/usr/lib/chromium/chromedriver',
            '/usr/lib/chromium-browser/chromedriver',
            '/snap/bin/chromium.chromedriver'
        ]
        
        for driver_path in possible_driver_paths:
            if os.path.exists(driver_path):
                print(f"✅ Chromedriver encontrado em: {driver_path}")
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
        
        print("❌ Chromedriver não encontrado no sistema")
        
    except Exception as e:
        print(f"❌ Busca por chromedriver falhou: {str(e)[:100]}")
    
    # Se todas as tentativas falharem
    raise Exception("Não foi possível configurar o WebDriver")

# Configurar WebDriver
try:
    driver = setup_webdriver()
    print("\n🎉 WebDriver configurado com sucesso!")
    
except Exception as e:
    print(f"\n❌ ERRO CRÍTICO: {str(e)}")
    print("\n" + "=" * 70)
    print("SOLUÇÕES POSSÍVEIS:")
    print("1. Verifique se o arquivo packages.txt existe com:")
    print("   chromium")
    print("   chromium-driver")
    print("   chromium-sandbox")
    print("2. Tente reiniciar o app")
    print("3. Verifique os logs completos")
    print("=" * 70)
    sys.exit(1)

# ============================================================================
# IMPORTAÇÕES DO SELENIUM
# ============================================================================
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

# Configurar wait
wait = WebDriverWait(driver, 30)
print(f"⏱️ Timeout configurado: 30 segundos")

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def salvar_screenshot(nome):
    """Salva screenshot para debug"""
    try:
        timestamp = int(time.time())
        filename = f"screenshot_{nome}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"📸 Screenshot salvo: {filename}")
        return filename
    except Exception as e:
        print(f"⚠️ Erro ao salvar screenshot: {e}")
        return None

def verificar_login():
    """Verifica se o login foi bem-sucedido"""
    try:
        time.sleep(3)
        
        # Verificar URL
        current_url = driver.current_url
        if "login" not in current_url.lower():
            print("✅ Login verificado pela URL")
            return True
        
        # Verificar elementos específicos
        elementos = [
            (By.XPATH, '//*[contains(text(), "Bem-vindo")]'),
            (By.XPATH, '//*[contains(text(), "Sair")]'),
            (By.XPATH, '//*[contains(text(), "Logout")]'),
            (By.ID, 'linkListagemReceptorCTEs')
        ]
        
        for by, selector in elementos:
            try:
                if driver.find_element(by, selector).is_displayed():
                    print(f"✅ Login verificado via elemento: {selector[:50]}")
                    return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar login: {e}")
        return False

def verificar_proxima_pagina():
    """Verifica se há próxima página"""
    try:
        # Verificar botão próximo
        selectores = [
            (By.XPATH, '//*[@id="next_plistagem"]'),
            (By.CSS_SELECTOR, '.ui-paginator-next'),
            (By.CSS_SELECTOR, '[title="Próxima"]'),
            (By.CSS_SELECTOR, '[aria-label="Next"]'),
            (By.LINK_TEXT, 'Próxima'),
            (By.LINK_TEXT, 'Próximo')
        ]
        
        for by, selector in selectores:
            try:
                elements = driver.find_elements(by, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        if "disabled" not in element.get_attribute("class").lower():
                            print("✅ Próxima página disponível")
                            return True
            except:
                continue
        
        print("ℹ️ Próxima página não encontrada ou desabilitada")
        return False
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar próxima página: {e}")
        return False

def aguardar_download(tempo=8):
    """Aguarda download"""
    print(f"⏳ Aguardando download ({tempo}s)...")
    time.sleep(tempo)
    
    # Listar arquivos baixados
    downloads = list(Path(os.getcwd()).glob('*.xml')) + list(Path(os.getcwd()).glob('*.zip'))
    if downloads:
        print(f"📁 Arquivos encontrados: {len(downloads)}")
        return True
    return False

def executar_clique_seguro(by, selector, descricao, tempo_espera=10):
    """Executa clique com segurança"""
    try:
        elemento = WebDriverWait(driver, tempo_espera).until(
            EC.element_to_be_clickable((by, selector))
        )
        elemento.click()
        print(f"✅ {descricao}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao clicar em {descricao}: {e}")
        return False

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
def main():
    """Função principal"""
    
    try:
        print("\n" + "=" * 70)
        print("🏁 INICIANDO PROCESSAMENTO")
        print("=" * 70)
        
        # ====================================================================
        # 1. LOGIN
        # ====================================================================
        print("\n1️⃣ ETAPA 1: LOGIN")
        print("-" * 40)
        
        # Acessar página
        print("🌐 Acessando página de login...")
        driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
        time.sleep(3)
        salvar_screenshot("pagina_login")
        
        # Preencher usuário
        try:
            campo_usuario = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="nomeusuario"]')))
            campo_usuario.clear()
            campo_usuario.send_keys("HBR0455")
            print("👤 Usuário preenchido")
        except:
            try:
                campo_usuario = driver.find_element(By.ID, 'nomeusuario')
                campo_usuario.send_keys("HBR0455")
                print("👤 Usuário preenchido (método alternativo)")
            except Exception as e:
                print(f"❌ Erro ao preencher usuário: {e}")
                salvar_screenshot("erro_usuario")
                return
        
        # Preencher senha
        try:
            campo_senha = driver.find_element(By.XPATH, '//*[@id="senha"]')
            campo_senha.clear()
            campo_senha.send_keys("XXXXXXXXXX")  # SUBSTITUIR PELA SENHA REAL
            print("🔒 Senha preenchida")
        except:
            try:
                campo_senha = driver.find_element(By.ID, 'senha')
                campo_senha.send_keys("XXXXXXXXXX")
                print("🔒 Senha preenchida (método alternativo)")
            except Exception as e:
                print(f"❌ Erro ao preencher senha: {e}")
                return
        
        # Submeter login
        try:
            campo_senha.send_keys(Keys.ENTER)
            print("↵ Enter pressionado")
        except:
            try:
                botao_login = driver.find_element(By.XPATH, '//button[@type="submit"]')
                botao_login.click()
                print("🖱️ Botão de login clicado")
            except:
                print("⚠️ Não foi possível submeter login")
        
        # Aguardar e verificar
        time.sleep(5)
        salvar_screenshot("pos_login")
        
        if not verificar_login():
            print("❌ Falha no login")
            salvar_screenshot("login_falhou")
            return
        
        print("✅ Login realizado com sucesso!")
        
        # ====================================================================
        # 2. NAVEGAR PARA RECEPTOR CTEs
        # ====================================================================
        print("\n2️⃣ ETAPA 2: NAVEGAÇÃO")
        print("-" * 40)
        
        # Tentar diferentes métodos para encontrar o link
        encontrado = False
        
        # Método 1: XPATH específico
        if not encontrado:
            try:
                receptor_link = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a')
                ))
                receptor_link.click()
                print("📍 Navegando via XPATH específico")
                encontrado = True
                time.sleep(3)
            except:
                pass
        
        # Método 2: Links com texto relacionado
        if not encontrado:
            try:
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    texto = link.text.lower()
                    if 'receptor' in texto or 'cte' in texto or 'ct-e' in texto:
                        link.click()
                        print(f"📍 Navegando via texto: {link.text[:30]}")
                        encontrado = True
                        time.sleep(3)
                        break
            except:
                pass
        
        if not encontrado:
            print("❌ Não foi possível navegar para Receptor CTEs")
            salvar_screenshot("erro_navegacao")
            return
        
        salvar_screenshot("receptor_ctes")
        
        # ====================================================================
        # 3. FILTRO DE DATAS
        # ====================================================================
        print("\n3️⃣ ETAPA 3: FILTRO DE DATAS")
        print("-" * 40)
        
        # Data inicial
        try:
            dt_inicial = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDataInicial"]')))
            dt_inicial.click()
            dt_inicial.clear()
            dt_inicial.send_keys("01/09/2026")
            print("📅 Data inicial: 01/09/2026")
        except:
            try:
                driver.execute_script("document.getElementById('consultaDataInicial').value = '01/09/2026';")
                print("📅 Data inicial via JavaScript")
            except Exception as e:
                print(f"⚠️ Erro data inicial: {e}")
        
        # Data final
        try:
            dt_final = driver.find_element(By.XPATH, '//*[@id="consultaDataFinal"]')
            dt_final.click()
            dt_final.clear()
            dt_final.send_keys("31/01/2026")
            print("📅 Data final: 31/01/2026")
        except:
            try:
                driver.execute_script("document.getElementById('consultaDataFinal').value = '31/01/2026';")
                print("📅 Data final via JavaScript")
            except Exception as e:
                print(f"⚠️ Erro data final: {e}")
        
        # Aplicar filtro
        try:
            dt_final.send_keys(Keys.ENTER)
            print("✅ Filtro aplicado")
        except:
            pass
        
        time.sleep(5)
        salvar_screenshot("filtro_aplicado")
        
        # ====================================================================
        # 4. LOOP DE DOWNLOAD
        # ====================================================================
        print("\n" + "=" * 70)
        print("4️⃣ ETAPA 4: DOWNLOAD DOS XMLs")
        print("=" * 70)
        
        ciclos = 0
        max_ciclos = 3  # REDUZIDO PARA TESTE
        
        for ciclo in range(max_ciclos):
            print(f"\n🔄 CICLO {ciclo + 1} de {max_ciclos}")
            print("-" * 30)
            
            # Rolar para topo
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Selecionar todos
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                for checkbox in checkboxes:
                    if checkbox.is_displayed() and not checkbox.is_selected():
                        checkbox.click()
                        break
                print("✅ Checkbox selecionado")
            except:
                print("⚠️ Não foi possível selecionar checkbox")
            
            time.sleep(2)
            
            # Clicar em XML Múltiplos
            try:
                elementos_xml = driver.find_elements(By.XPATH, '//*[contains(text(), "XML")]')
                for elemento in elementos_xml:
                    texto = elemento.text.lower()
                    if 'múltiplo' in texto or 'multiplo' in texto:
                        elemento.click()
                        print("📄 XML Múltiplos clicado")
                        aguardar_download(5)
                        break
            except Exception as e:
                print(f"⚠️ Erro XML Múltiplos: {e}")
            
            time.sleep(2)
            
            # Desmarcar checkbox
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if checkboxes:
                    checkboxes[0].click()
                    print("✅ Checkbox desmarcado")
            except:
                pass
            
            # Próxima página (se não for último ciclo)
            if ciclo < max_ciclos - 1:
                if verificar_proxima_pagina():
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        botoes_proximo = driver.find_elements(By.XPATH, '//*[contains(@id, "next") or contains(text(), "Próximo") or contains(text(), "Próxima")]')
                        if botoes_proximo:
                            for botao in botoes_proximo:
                                if botao.is_displayed():
                                    botao.click()
                                    print("➡️ Próxima página")
                                    time.sleep(5)
                                    break
                    except Exception as e:
                        print(f"⚠️ Erro ao navegar: {e}")
                        break
                else:
                    print("🏁 Fim das páginas")
                    break
            else:
                print("🎯 Último ciclo")
                ciclos += 1
        
        # ====================================================================
        # 5. RELATÓRIO FINAL
        # ====================================================================
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        
        # Contar arquivos baixados
        xml_files = list(Path(os.getcwd()).glob('*.xml'))
        zip_files = list(Path(os.getcwd()).glob('*.zip'))
        
        print(f"✅ Processo concluído!")
        print(f"📈 Ciclos executados: {ciclos}")
        print(f"📁 Arquivos XML: {len(xml_files)}")
        print(f"📁 Arquivos ZIP: {len(zip_files)}")
        
        if xml_files or zip_files:
            print("\n📋 Primeiros 10 arquivos:")
            for f in (xml_files + zip_files)[:10]:
                print(f"  • {f.name}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        salvar_screenshot("erro_critico")
    
    finally:
        print("\n" + "=" * 70)
        print("🧹 FINALIZANDO...")
        try:
            driver.quit()
            print("✅ Navegador fechado")
        except:
            print("⚠️ Erro ao fechar navegador")
        print("=" * 70)

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================
if __name__ == "__main__":
    
    # Interface Streamlit (opcional)
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
            
            with st.sidebar:
                st.header("⚙️ Configurações")
                ciclos = st.slider("Número de ciclos", 1, 10, 3)
                if st.button("🚀 Iniciar Download", type="primary"):
                    with st.spinner("Executando..."):
                        # Redirecionar output
                        import io
                        from contextlib import redirect_stdout
                        
                        f = io.StringIO()
                        with redirect_stdout(f):
                            main()
                        
                        st.text_area("Logs", f.getvalue(), height=400)
            
            st.info("""
            ### 📋 Instruções:
            1. Verifique se o arquivo `packages.txt` existe
            2. Configure o número de ciclos
            3. Clique em "Iniciar Download"
            4. Aguarde a execução
            """)
            
        except ImportError:
            main()
    else:
        main()
