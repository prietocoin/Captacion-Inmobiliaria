import asyncio
import requests
import re
from playwright.async_api import async_playwright

WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

# Whitelist basada en el Kirkoff y tus pedidos
ZONAS_CALIENTES = [
    "barrio jara", "las lomas", "molas lopez", "ytay", "ycua sati", 
    "manora", "recoleta", "villa morra", "herrera", "mburucuya", 
    "trinidad", "laureles", "mburicao", "san cristobal", "villa aurelia", 
    "luque", "san bernardino", "fernando de la mora", "san lorenzo", "mariano roque alonso"
]

def limpiar_telefono(texto):
    numeros = re.sub(r'\D', '', texto)
    if numeros.startswith('09'):
        return '595' + numeros[1:]
    if numeros.startswith('9'):
        return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    # Mantenemos 20 páginas para asegurar calidad
    for i in range(1, 21):
        print(f"🕵️ Escaneando página {i}...")
        # ... (lógica de navegación Playwright igual que antes)
        
        # --- EL CAMBIO ESTÁ AQUÍ ---
        # Solo guardamos si hay una coincidencia CLARA con la zona
        if any(f" {zona} " in f" {texto_limpio} " for zona in ZONAS_CALIENTES):
            # Verificación extra: Que NO sea inmobiliaria
            if not any(excluir in texto_limpio for excluir in ["remax", "century", "c21", "agente"]):
                # Extraer teléfono y agregar a resultados
                # ...
