import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# URL de TEST (Asegúrate de darle a "Listen for test event" en n8n)
WEBHOOK_URL = "https://n8n.jairokov.com/webhook-test/clasipar-directo"
BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    paginas_a_extraer = 10 # Bajamos a 10 para depuración rápida
    
    palabras_prohibidas = [
        "inmobiliaria", "inmobiliario", "remax", "re/max", "century", "c21", 
        "keller williams", "kw", "agente", "comisión", "comision", 
        "bienes raíces", "bienes raices", "broker", "franquicia", "asesor"
    ]
    
    print(f"🕵️ Iniciando prueba de 10 páginas...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(1) 
                anuncios = await page.query_selector_all("article, .list-item, .ad-listing") 
                
                for anuncio in anuncios:
                    texto_crudo = await anuncio.text_content()
                    if texto_crudo:
                        texto_limpio = ' '.join(texto_crudo.split())
                        if not any(p in texto_limpio.lower() for p in palabras_prohibidas):
                            if len(texto_limpio) > 30:
                                resultados.append({"contenido": texto_limpio})
            except Exception as e:
                print(f"Error pág {i}: {e}")
                break

        # DEPUREMOS EL ENVÍO
        if not resultados:
            print("⚠️ No se encontraron diamantes en estas 10 páginas. El filtro es muy estricto.")
            return

        print(f"📦 Enviando {len(resultados)} propiedades a n8n...")
        
        try:
            # Enviamos como una lista simple para que n8n la entienda mejor
            response = requests.post(WEBHOOK_URL, json=resultados, timeout=30)
            print(f"Respuesta de n8n: {response.status_code}")
            print(f"Cuerpo de respuesta: {response.text}")
        except Exception as e_send:
            print(f"❌ Error de red: {e_send}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
