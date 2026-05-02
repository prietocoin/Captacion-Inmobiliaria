import asyncio
import requests
import re
import random
from playwright.async_api import async_playwright

WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def limpiar_telefono(texto):
    numeros = re.sub(r'\D', '', texto)
    if len(numeros) >= 9:
        if numeros.startswith('09'): return '595' + numeros[1:]
        if numeros.startswith('9'): return '595' + numeros
    return None

async def run_scraper():
    resultados = []
    print(f"🕵️ INICIANDO OPERACIÓN SIGILO - OBJETIVO: 1000 CONTACTOS")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Usamos un perfil de navegador más realista
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()

        for i in range(1, 21):
            try:
                print(f"📄 Procesando página {i}...")
                # Navegación con espera de carga completa
                await page.goto(f"https://clasipar.paraguay.com/inmuebles?page={i}", wait_until="networkidle", timeout=90000)
                
                # Tiempo de espera aleatorio para imitar a un humano
                await asyncio.sleep(random.uniform(2, 5))

                # Extraemos todo el contenido de texto visible
                contenido = await page.evaluate("() => document.body.innerText")
                
                # Buscamos patrones de teléfonos de Paraguay
                telefonos = re.findall(r'09\d{2}\s?\d{3}\s?\d{3}', contenido)
                
                conteo_página = 0
                for tel_crudo in set(telefonos):
                    tel_f = limpiar_telefono(tel_crudo)
                    if tel_f:
                        # Evitamos los nombres de la competencia del Summit
                        if not any(ex in contenido.lower() for ex in ["remax", "century", "c21"]):
                            resultados.append({
                                "telefono_meta": tel_f,
                                "contenido": "Captura Masiva Reciente",
                                "origen": "Clasipar Sigilo"
                            })
                            conteo_página += 1
                
                print(f"✅ Página {i} completada. Encontrados: {conteo_página}")

            except Exception as e:
                print(f"⚠️ Salto de página {i} por error técnico.")
                continue

        if resultados:
            print(f"📦 ENVIANDO {len(resultados)} NÚMEROS A N8N PARA TU PÚBLICO")
            requests.post(WEBHOOK_URL, json=resultados, timeout=120)
        else:
            print("❌ El bloqueo persiste. Clasipar requiere una IP residencial o rotación de Proxy.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
