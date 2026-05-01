import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# --- CONFIGURACIÓN DIRECTA POR IP ---
# Usamos la IP interna/pública y el puerto para evitar fallos de DNS/Proxy
IP_SERVIDOR = "192.64.115.249"
PUERTO_N8N = "5678" 
WEBHOOK_URL = f"http://{IP_SERVIDOR}:{PUERTO_N8N}/webhook-test/clasipar-directo"

BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    # Probemos con 10 páginas para asegurar que lleguen los datos
    paginas_a_extraer = 10 
    
    palabras_prohibidas = [
        "inmobiliaria", "remax", "century", "c21", "kw", "agente", 
        "comisión", "broker", "asesor", "bienes raíces"
    ]
    
    print(f"🚀 Iniciando captura táctica (Prueba de {paginas_a_extraer} páginas)")
    print(f"📡 Apuntando a: {WEBHOOK_URL}")

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
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(1.5) 

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
                            
                            # Filtro de dueños directos
                            if not any(p in texto_minusculas for p in palabras_prohibidas):
                                if len(texto_limpio) > 35:
                                    resultados.append({
                                        "contenido": texto_limpio,
                                        "url": enlace
                                    })
                    except:
                        continue
                
                print(f"✅ Página {i} lista. Total acumulado: {len(resultados)}")

            except Exception as e:
                print(f"❌ Error en pág {i}: {e}")
                break

        # --- ENVÍO DE DATOS ---
        if resultados:
            print(f"📦 Enviando {len(resultados)} diamantes a n8n...")
            try:
                # Aumentamos el timeout del envío a 60 segundos
                response = requests.post(WEBHOOK_URL, json=resultados, timeout=60)
                print(f"📡 Respuesta de n8n: {response.status_code}")
            except Exception as e_send:
                print(f"❌ Error crítico de conexión: {e_send}")
        else:
            print("⚠️ No se encontraron propiedades que pasaran el filtro.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
