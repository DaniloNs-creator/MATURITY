#!/bin/bash

# Configurar ambiente no Streamlit Cloud
apt-get update
apt-get install -y chromium-browser chromium-chromedriver

# Verificar instalações
which chromium-browser
which chromedriver

# Configurar variáveis de ambiente
export CHROMEDRIVER_PATH=/usr/bin/chromedriver
export CHROME_BIN=/usr/bin/chromium-browser