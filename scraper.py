import asyncio
import requests
import re
from playwright.async_api import async_playwright

# Configuración única
WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def limpiar_telefono(texto):
    numeros = re.sub(r'\D', '', texto)
    if numeros.startswith('09'):
        return '595' + numeros[1:]
    if numeros.startswith('9'):
        return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    paginas = 20
    
    print(f"🚀 VOLVIENDO A MODO CAPTACIÓN TOTAL...")

    async with async_playwright() as p:
        # Usamos parámetros de navegación estándar que ya te funcionaron
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas + 1):
            url = f"https://clasipar.paraguay.com/inmuebles?page={i}"
            try:
                # Volvemos al tiempo de espera domcontentloaded que es más rápido y estable
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2) 

                # Seleccionamos TODOS los artículos sin filtros de zona aquí
                anuncios = await page.query_selector_all("article") 
                
                conteo_pagina = 0
                for anuncio in anuncios:
                    texto_crudo = await anuncio.text_content()
                    if texto_crudo:
                        # Extraemos teléfono con el patrón que no falla
                        match_tel = re.search(r'09\d{2}\s?\d{3}\s?\d{3}', texto_crudo)
                        
                        if match_tel:
                            tel = limpiar_telefono(match_tel.group())
                            texto_limpio = ' '.join(texto_crudo.split())
                            
                            resultados.append({
                                "telefono_meta": tel,
                                "contenido": texto_limpio,
                                "origen": "Clasipar Directo"
                            })
                            conteo_pagina += 1
                
                print(f"✅ Página {i} OK. Diamantes encontrados: {conteo_pagina}")

            except Exception as e:
                print(f"⚠️ Error en página {i}: {e}")
                continue 

        # Envío Masivo a n8n
        if resultados:
            print(f"📦 ENVIANDO {len(resultados)} PROSPECTOS A TU N8N...")
            try:
                requests.post(WEBHOOK_URL, json=resultados, timeout=120)
                print("🔥 ¡LOGRADO! Revisá n8n ahora mismo.")
            except:
                print("❌ Error de red con el webhook.")
        else:
            print("⚠️ No se detectaron números. Revisá la URL de Clasipar.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
