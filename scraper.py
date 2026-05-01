import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# --- CONFIGURACIÓN DE CONEXIÓN INTERNA (EASYPANEL) ---
# Usamos el nombre del servicio interno para que la red de Docker lo resuelva directamente
NOMBRE_SERVICIO_N8N = "automatizaciones_n8n"
PUERTO_INTERNO = "5678"
WEBHOOK_URL = f"http://{NOMBRE_SERVICIO_N8N}:{PUERTO_INTERNO}/webhook-test/clasipar-directo"

BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    # Prueba controlada de 10 páginas
    paginas_a_extraer = 10 
    
    # Filtro de competencia (Lista Negra)
    palabras_prohibidas = [
        "inmobiliaria", "remax", "century", "c21", "kw", "agente", 
        "comisión", "broker", "asesor", "bienes raíces", "inmobiliario"
    ]
    
    print(f"🚀 Iniciando captura táctica en Clasipar...")
    print(f"📡 Destino interno: {WEBHOOK_URL}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            try:
                # Tiempo de espera optimizado para el servidor
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(1) 

                anuncios = await page.query_selector_all("article, .list-item, .ad-listing") 
                
                for anuncio in anuncios:
                    try:
                        texto_crudo = await anuncio.text_content()
                        enlace_elemento = await anuncio.query_selector("a")
                        enlace = await enlace_elemento.get_attribute("href") if enlace_elemento else ""
                        
                        if enlace and not enlace.startswith("http"):
                            enlace = f"https://clasipar.paraguay.com{enlace}"

                        if texto_crudo and texto_crudo.strip():
                            texto_limpio = ' '.join(texto_crudo.split())
                            texto_minusculas = texto_limpio.lower()
                            
                            # Si no contiene palabras prohibidas, es un diamante (dueño directo)
                            if not any(p in texto_minusculas for p in palabras_prohibidas):
                                if len(texto_limpio) > 35:
                                    resultados.append({
                                        "contenido": texto_limpio,
                                        "url": enlace,
                                        "origen": "Clasipar Directo"
                                    })
                    except:
                        continue
                
                print(f"✅ Página {i} revisada. Diamantes acumulados: {len(resultados)}")

            except Exception as e:
                print(f"❌ Error en página {i}: {e}")
                break

        # --- ENVÍO AL WEBHOOK DE N8N ---
        if resultados:
            print(f"📦 Enviando {len(resultados)} propiedades a la fábrica de contenido...")
            try:
                # Enviamos el JSON con un timeout de 60 segundos
                response = requests.post(WEBHOOK_URL, json=resultados, timeout=60)
                print(f"📡 Respuesta de n8n: {response.status_code}")
                if response.status_code == 200:
                    print("🎉 ¡Datos entregados con éxito!")
                else:
                    print(f"⚠️ n8n recibió los datos pero respondió: {response.text}")
            except Exception as e_send:
                print(f"❌ Falló el envío por la red interna: {e_send}")
        else:
            print("⚠️ El filtro fue muy estricto y no quedaron propiedades para enviar.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
