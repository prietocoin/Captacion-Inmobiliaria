import asyncio
import requests
import re
from playwright.async_api import async_playwright

WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def extraer_telefonos(texto):
    # Patrón robusto para 09xx xxx xxx
    patron = r'09\d{2}[-.\s]?\d{3}[-.\s]?\d{3}'
    encontrados = re.findall(patron, texto)
    limpios = []
    for tel in encontrados:
        num = re.sub(r'\D', '', tel)
        if len(num) == 10 and num.startswith('09'):
            limpios.append('595' + num[1:])
    return list(set(limpios))

async def run_scraper():
    resultados = []
    print(f"🚀 MODO SIGILO ACTIVADO - CAPTURA DE ALTA PRECISIÓN")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Cabeceras de un navegador real actualizado
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        for i in range(1, 21):
            try:
                print(f"🕵️ Escaneando Página {i}...")
                await page.goto(f"https://clasipar.paraguay.com/inmuebles?page={i}", wait_until="networkidle", timeout=60000)
                
                # Forzamos un scroll para que Clasipar cargue todo el contenido dinámico
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

                # Obtenemos el texto completo de la página
                cuerpo_texto = await page.content()
                telefonos = extraer_telefonos(cuerpo_texto)
                
                conteo_página = 0
                for tel in telefonos:
                    # Evitamos inmobiliarias conocidas del Summit
                    if not any(ex in cuerpo_texto.lower() for ex in ["remax", "century", "c21"]):
                        resultados.append({
                            "telefono_meta": tel,
                            "contenido": "Captura Reciente Asunción/Central",
                            "origen": "Clasipar Directo"
                        })
                        conteo_página += 1
                
                print(f"✅ Página {i} OK. Encontrados: {conteo_página}")
                await asyncio.sleep(3) # Pausa humana para no ser baneado

            except Exception as e:
                print(f"⚠️ Error en pág {i}: {str(e)[:50]}")
                continue

        if resultados:
            print(f"📦 ENVIANDO {len(resultados)} NÚMEROS A N8N...")
            requests.post(WEBHOOK_URL, json=resultados, timeout=120)
        else:
            print("❌ No se capturó nada. Intentando cambio de estrategia...")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
