import asyncio
import requests
import re
from playwright.async_api import async_playwright

WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def limpiar_telefono(texto):
    numeros = re.sub(r'\D', '', texto)
    if numeros.startswith('09'): return '595' + numeros[1:]
    if numeros.startswith('9'): return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    print(f"🚀 INICIANDO CAPTURA DE EMERGENCIA - MODO TANQUE")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # User agent de Chrome real para evitar bloqueos
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        page = await context.new_page()

        for i in range(1, 21):
            try:
                print(f"🕵️ Intentando Página {i}...")
                # Cargamos la página esperando a que el tráfico de red se detenga
                await page.goto(f"https://clasipar.paraguay.com/inmuebles?page={i}", wait_until="networkidle", timeout=90000)
                
                # Obtenemos TODO el contenido de la página para buscar teléfonos
                contenido_pagina = await page.content()
                
                # Buscamos el patrón de teléfono de Paraguay: 09xx xxx xxx
                telefonos_encontrados = re.findall(r'09\d{2}\s?\d{3}\s?\d{3}', contenido_pagina)
                
                if telefonos_encontrados:
                    for tel in set(telefonos_encontrados): # set() para no duplicar en la misma página
                        tel_f = limpiar_telefono(tel)
                        resultados.append({
                            "telefono_meta": tel_f,
                            "contenido": "Captura Masiva Reciente",
                            "origen": "Clasipar Directo"
                        })
                
                print(f"✅ Página {i} OK. Acumulado real: {len(resultados)}")
                await asyncio.sleep(3) # Pausa estratégica

            except Exception as e:
                print(f"⚠️ Error en pág {i}: {str(e)[:50]}")
                continue

        if resultados:
            print(f"📦 ENVIANDO {len(resultados)} NÚMEROS A N8N...")
            requests.post(WEBHOOK_URL, json=resultados, timeout=120)
            print("🔥 ¡LOGRADO! Revisa n8n.")
        else:
            print("❌ No se detectó nada. Clasipar está bloqueando la IP o cambió drásticamente.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
