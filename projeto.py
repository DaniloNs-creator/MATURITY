from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Configuração para ambientes cloud (Streamlit Cloud, Heroku, etc.)
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Execução sem interface gráfica
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Configurações adicionais para estabilidade
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Para Streamlit Cloud ou ambientes cloud
    try:
        # Verificar se estamos em ambiente cloud
        if os.environ.get('STREAMLIT_SHARING') or os.environ.get('DYNO') or 'google.colab' in sys.modules:
            # Em ambiente cloud, tente usar caminhos padrão
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Ambiente local - usar webdriver-manager ou chromedriver autoinstaller
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                # Fallback para chromedriver padrão
                driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Erro ao configurar WebDriver: {e}")
        print("Tentando configuração alternativa...")
        # Última tentativa com configuração básica
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver

# Inicializar driver
print("Iniciando configuração do WebDriver...")
driver = setup_driver()
driver.maximize_window()
wait = WebDriverWait(driver, 30)  # Aumentei o timeout para 30 segundos
print("WebDriver iniciado com sucesso!")

try:
    # 1. Login
    print("Realizando login...")
    driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
    
    user = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nomeusuario"]')))
    user.send_keys("HBR0455")
    
    pwd = driver.find_element(By.XPATH, '//*[@id="senha"]')
    pwd.send_keys("XXXXXXXXXX")
    pwd.send_keys(Keys.ENTER)
    
    time.sleep(5)
    print("Login realizado!")

    # 2. Navegação para Receptor CTEs
    print("Navegando para Receptor CTEs...")
    receptor = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a')))
    receptor.click()
    
    time.sleep(5)
    print("Página de Receptor CTEs carregada!")

    # 3. Filtro de Datas
    print("Aplicando filtro de datas...")
    dt_ini = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDataInicial"]')))
    dt_ini.click()
    dt_ini.send_keys(Keys.CONTROL + "a")
    dt_ini.send_keys("01092026")

    dt_fim = driver.find_element(By.XPATH, '//*[@id="consultaDataFinal"]')
    dt_fim.click()
    dt_fim.send_keys("31012026")
    dt_fim.send_keys(Keys.ENTER)
    
    time.sleep(2)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
    time.sleep(2)
    print("Filtro de datas aplicado!")

    # 4. Configurar 200 itens por página
    print("Configurando 200 itens por página...")
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.END)
    time.sleep(2)
    
    select_pag = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="plistagem_center"]/table/tbody/tr/td[8]/select')))
    select_pag.click()
    select_pag.send_keys("200")
    select_pag.send_keys(Keys.ENTER)
    
    time.sleep(3)
    print("Configuração de paginação concluída!")

    # --- INÍCIO DO LOOP (65 VEZES) ---
    print("\n" + "="*50)
    print("INICIANDO PROCESSO DE DOWNLOAD DOS XMLs")
    print("="*50 + "\n")
    
    for i in range(65):
        print(f"\n🚀 Executando ciclo {i+1} de 65...")
        print(f"Página atual: {i+1}")

        # Voltar ao topo e selecionar tudo
        print("Selecionando todos os itens...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input'))).click()
        
        time.sleep(6)
        print("Itens selecionados!")
        
        # Clicar em XML Múltiplos
        print("Clicando em 'XML Múltiplos'...")
        driver.find_element(By.XPATH, '//*[@id="xml_multiplos"]/h3').click()
        time.sleep(5)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
        print("Download iniciado...")
        
        # Desmarcar para evitar conflito na próxima página
        print("Desmarcando itens...")
        driver.find_element(By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input').click()
        time.sleep(2)
        
        # Ir para o fim da página e clicar em "Próximo"
        print("Navegando para próxima página...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.END)
        time.sleep(2)
        
        try:
            next_btn = driver.find_element(By.XPATH, '//*[@id="next_plistagem"]/span')
            next_btn.click()
            print(f"✅ Ciclo {i+1} concluído com sucesso!")
            time.sleep(3)  # Aguardar carregamento da próxima página
        except Exception as e:
            print(f"❌ Botão 'Próximo' não encontrado ou fim da listagem atingido.")
            print(f"Motivo: {str(e)}")
            
            # Tentar verificar se há mais páginas
            try:
                current_page = driver.find_element(By.CLASS_NAME, 'ui-state-disabled')
                if 'next' in current_page.get_attribute('class'):
                    print("🏁 Fim da paginação alcançado!")
                    break
            except:
                pass
            
            # Tentar método alternativo para navegação
            try:
                print("Tentando método alternativo de navegação...")
                driver.execute_script("$('#next_plistagem').click();")
                time.sleep(3)
                print("Navegação alternativa bem-sucedida!")
            except:
                print("Não foi possível navegar para próxima página. Encerrando loop.")
                break

    # --- FIM DO LOOP ---
    
    print("\n" + "="*50)
    print("PROCESSO CONCLUÍDO COM SUCESSO!")
    print(f"Total de ciclos executados: {i+1}")
    print("="*50)

except Exception as e:
    print(f"\n⚠️ ERRO CRÍTICO: {str(e)}")
    
    # Capturar informações para debug
    try:
        # Screenshot
        driver.save_screenshot(f'error_screenshot_{time.strftime("%Y%m%d_%H%M%S")}.png')
        print("Screenshot salvo para análise.")
        
        # Código da página
        with open(f'page_source_{time.strftime("%Y%m%d_%H%M%S")}.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Código fonte da página salvo.")
    except:
        pass

finally:
    print("\nEncerrando navegador...")
    try:
        driver.quit()
        print("Navegador encerrado com sucesso!")
    except:
        print("Navegador já encerrado.")
    
    print("🎯 Script finalizado!")