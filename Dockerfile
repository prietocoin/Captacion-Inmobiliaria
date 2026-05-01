# Usamos la imagen oficial de Playwright que ya tiene Chrome instalado
FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

# Directorio de trabajo
WORKDIR /app

# Instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos tu código al servidor
COPY . .

# Comando para ejecutar el scraper
CMD ["python", "scraper.py"]
