import asyncio
import requests
from playwright.async_api import async_playwright

# --- CONFIGURACIÓN DE RED INTERNA EASYPANEL ---
# Usamos el nombre del servicio interno y el ID exacto de tu webhook
WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    paginas_a_extraer = 10 
    
    # Filtro para asegurar que sean Dueños Directos
    palabras_prohibidas = [
        "inmobiliaria", "remax", "century", "c21", "kw", "agente", 
        "comisión", "broker", "asesor", "bienes raíces", "inmobiliario"
    ]
    
    print(f"🚀 Iniciando captura masiva en Clasipar...")
    print(f"📡 Enviando a n8n por red interna...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Usamos un User Agent real para evitar que Clasipar bloquee la conexión
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            try:
                # Aumentamos el tiempo de espera a 60s por si la web está lenta
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2) 

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
                            
                            # Filtro táctico de "Dueño Directo"
                            if not any(p in texto_limpio.lower() for p in palabras_prohibidas):
                                if len(texto_limpio) > 40:
                                    resultados.append({
                                        "contenido": texto_limpio,
                                        "url": enlace,
                                        "origen": "Clasipar Directo"
                                    })
                    except:
                        continue
                
                print(f"✅ Página {i} completada. Diamantes acumulados: {len(resultados)}")

            except Exception as e:
                print(f"⚠️ Salto en página {i} por demora: {e}")
                continue 

        # --- ENVÍO FINAL A N8N ---
        if resultados:
            print(f"📦 Enviando {len(resultados)} propiedades a n8n...")
            try:
                response = requests.post(WEBHOOK_URL, json=resultados, timeout=60)
                print(f"📡 Respuesta de n8n: {response.status_code}")
                if response.status_code == 200:
                    print("🎉 ¡Éxito! Los datos ya están en tu flujo de n8n.")
            except Exception as e_send:
                print(f"❌ Error de conexión interna: {e_send}")
        else:
            print("⚠️ No se encontraron propiedades que pasaran el filtro.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
