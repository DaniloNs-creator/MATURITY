from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configuração inicial
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 20)

try:
    # 1. Login
    driver.get("https://p.dfe.mastersaf.com.br/mvc/login")
    
    user = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nomeusuario"]')))
    user.send_keys("HBR0455")
    
    pwd = driver.find_element(By.XPATH, '//*[@id="senha"]')
    pwd.send_keys("XXXXXXXXXX")
    pwd.send_keys(Keys.ENTER)
    
    time.sleep(5)

    # 2. Navegação para Receptor CTEs
    receptor = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="linkListagemReceptorCTEs"]/a')))
    receptor.click()
    
    time.sleep(5)

    # 3. Filtro de Datas
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

    # 4. Configurar 200 itens por página
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.END)
    time.sleep(2)
    
    select_pag = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="plistagem_center"]/table/tbody/tr/td[8]/select')))
    select_pag.click()
    select_pag.send_keys("200")
    select_pag.send_keys(Keys.ENTER)
    
    time.sleep(3)

    # --- INÍCIO DO LOOP (65 VEZES) ---
    for i in range(65):
        print(f"Executando ciclo {i+1} de 65...")

        # Voltar ao topo e selecionar tudo
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input'))).click()
        
        time.sleep(6)
        
        # Clicar em XML Múltiplos
        driver.find_element(By.XPATH, '//*[@id="xml_multiplos"]/h3').click()
        time.sleep(5)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
        
        # Desmarcar para evitar conflito na próxima página
        driver.find_element(By.XPATH, '//*[@id="jqgh_listagem_checkBox"]/div/input').click()
        time.sleep(2)
        
        # Ir para o fim da página e clicar em "Próximo"
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.END)
        time.sleep(2)
        
        try:
            next_btn = driver.find_element(By.XPATH, '//*[@id="next_plistagem"]/span')
            next_btn.click()
        except Exception:
            print("Botão 'Próximo' não encontrado ou fim da listagem atingido.")
            break

    # --- FIM DO LOOP ---

finally:
    print("Processo concluído.")
    # driver.quit()