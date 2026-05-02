import asyncio
import requests
import re
from playwright.async_api import async_playwright

# URL de tu webhook en n8n
WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

def limpiar_telefono(texto):
    # Extrae solo números
    numeros = re.sub(r'\D', '', texto)
    # Formatear para Meta Ads (Paraguay 595)
    if numeros.startswith('09'):
        return '595' + numeros[1:]
    if numeros.startswith('9'):
        return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    paginas = 20 # Extraemos lo más fresco
    
    print(f"🚀 Iniciando captura masiva de anuncios recientes...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas + 1):
            url = f"https://clasipar.paraguay.com/inmuebles?page={i}"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(1) # Pausa mínima técnica
                
                anuncios = await page.query_selector_all("article, .list-item") 
                
                for anuncio in anuncios:
                    texto_crudo = await anuncio.text_content()
                    if texto_crudo:
                        t_bajo = texto_crudo.lower()
                        
                        # FILTRO ÚNICO: Solo excluir inmobiliarias obvias para no saturar n8n
                        inmobiliarias = ["remax", "century", "c21", "kw", "agente", "inmobiliaria"]
                        if not any(exp in t_bajo for exp in inmobiliarias):
                            
                            # Extraer enlace si existe
                            enlace_el = await anuncio.query_selector("a")
                            url_anuncio = await enlace_el.get_attribute("href") if enlace_el else ""
                            
                            # Buscar teléfono
                            match_tel = re.search(r'09\d{2}\s?\d{3}\s?\d{3}', texto_crudo)
                            
                            if match_tel:
                                tel = limpiar_telefono(match_tel.group())
                                resultados.append({
                                    "telefono_meta": tel,
                                    "contenido": ' '.join(texto_crudo.split()),
                                    "url": f"https://clasipar.paraguay.com{url_anuncio}" if url_anuncio.startswith('/') else url_anuncio,
                                    "origen": "Clasipar Directo"
                                })
                
                print(f"✅ Página {i} capturada. Acumulado: {len(resultados)}")
            except Exception as e:
                print(f"⚠️ Error en pág {i}: {e}")
                continue

        # Envío del lote completo a n8n
        if resultados:
            print(f"📦 Enviando {len(resultados)} prospectos a n8n para filtrado posterior...")
            try:
                requests.post(WEBHOOK_URL, json=resultados, timeout=120)
            except Exception as e_send:
                print(f"❌ Error al enviar a n8n: {e_send}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
