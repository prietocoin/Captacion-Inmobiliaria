import asyncio
import requests
import re
from playwright.async_api import async_playwright

WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def extraer_telefonos(texto):
    # Busca patrones 09xx xxx xxx con o sin espacios/guiones
    patron = r'09\d{2}[-.\s]?\d{3}[-.\s]?\d{3}'
    encontrados = re.findall(patron, texto)
    
    limpios = []
    for tel in encontrados:
        num = re.sub(r'\D', '', tel)
        if len(num) == 10 and num.startswith('09'):
            limpios.append('595' + num[1:])
        elif len(num) == 9:
            limpios.append('595' + num)
    return list(set(limpios)) # Elimina duplicados en el mismo anuncio

async def run_scraper():
    resultados = []
    paginas = 20
    
    print(f"🚀 INICIANDO CAPTURA DE EMERGENCIA - MODO FUERZA BRUTA")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page = await context.new_page()

        for i in range(1, paginas + 1):
            url = f"https://clasipar.paraguay.com/inmuebles?page={i}"
            try:
                print(f"🕵️ Navegando a página {i}...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Capturamos todos los contenedores posibles de anuncios
                elementos = await page.query_selector_all("article, .list-item, .ad-item, .item")
                
                conteo_pagina = 0
                for el in elementos:
                    texto_anuncio = await el.text_content()
                    if texto_anuncio:
                        telefonos = extraer_telefonos(texto_anuncio)
                        
                        # Si encontramos al menos un teléfono, guardamos el anuncio
                        for tel in telefonos:
                            # Filtro mínimo para no traer inmobiliarias grandes
                            t_lower = texto_anuncio.lower()
                            if not any(ex in t_lower for ex in ["remax", "century", "c21"]):
                                resultados.append({
                                    "telefono_meta": tel,
                                    "contenido": ' '.join(texto_anuncio.split())[:300],
                                    "origen": "Clasipar Directo"
                                })
                                conteo_pagina += 1
                
                print(f"✅ Página {i} terminada. Encontrados en esta pág: {conteo_pagina}")
                await asyncio.sleep(2) # Pausa humana

            except Exception as e:
                print(f"❌ Error en pág {i}: {e}")
                continue

        if resultados:
            print(f"📦 ENVIANDO {len(resultados)} REGISTROS A N8N...")
            try:
                requests.post(WEBHOOK_URL, json=resultados, timeout=120)
                print("🔥 ¡ÉXITO! Revisa tu flujo en n8n.")
            except:
                print("📡 Error de conexión con n8n.")
        else:
            print("⚠️ No se capturó nada. Posible bloqueo de IP o cambio de estructura.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
