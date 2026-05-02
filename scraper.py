import asyncio
import requests
import re
from playwright.async_api import async_playwright

# Configuración del Webhook
WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

# Whitelist de zonas (Summit 2024 + Tus pedidos)[cite: 1]
ZONAS_CALIENTES = [
    "barrio jara", "las lomas", "molas lopez", "ytay", "ycua sati", 
    "manora", "recoleta", "villa morra", "herrera", "mburucuya", 
    "trinidad", "laureles", "mburicao", "san cristobal", "villa aurelia", 
    "luque", "san bernardino", "fernando de la mora", "san lorenzo", "mariano roque alonso"
]

def limpiar_telefono(texto):
    numeros = re.sub(r'\D', '', texto)
    if numeros.startswith('09'):
        return '595' + numeros[1:]
    if numeros.startswith('9'):
        return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    paginas_a_revisar = 20 
    
    print(f"🚀 Iniciando captura táctica (20 páginas)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_revisar + 1):
            try:
                await page.goto(f"https://clasipar.paraguay.com/inmuebles?page={i}", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2) # Seguridad
                
                anuncios = await page.query_selector_all("article, .list-item") 
                
                for anuncio in anuncios:
                    texto_crudo = await anuncio.text_content()
                    if texto_crudo:
                        # Limpiamos el texto para el filtro
                        t = ' '.join(texto_crudo.split()).lower()
                        
                        # FILTRO ESTRICTO: Solo tus zonas y NO inmobiliarias
                        es_zona_target = any(f" {zona} " in f" {t} " for zona in ZONAS_CALIENTES)
                        es_inmobiliaria = any(ex in t for ex in ["remax", "century", "c21", "agente", "inmobiliaria", "propiedades"])
                        
                        if es_zona_target and not es_inmobiliaria:
                            match_tel = re.search(r'09\d{2}\s?\d{3}\s?\d{3}', texto_crudo)
                            if match_tel:
                                tel = limpiar_telefono(match_tel.group())
                                resultados.append({
                                    "telefono_meta": tel,
                                    "zona": next((z for z in ZONAS_CALIENTES if z in t), "Asunción"),
                                    "contenido": t[:150], # Para que veas qué captó
                                    "origen": "Clasipar Directo"
                                })
                print(f"✅ Página {i} lista. Prospectos: {len(resultados)}")
            except Exception as e:
                print(f"⚠️ Error en pág {i}: {e}")
                continue

        # Envío final a n8n
        if resultados:
            print(f"📦 Enviando {len(resultados)} diamantes a la base de retargeting...")
            requests.post(WEBHOOK_URL, json=resultados, timeout=120)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
