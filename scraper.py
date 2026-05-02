import asyncio
import requests
import re
from playwright.async_api import async_playwright

# Configuración del Webhook
WEBHOOK_URL = "http://automatizaciones_n8n:5678/webhook-test/189b1141-6f1f-4ba8-b460-d7e31998bbdb"

# Whitelist Táctica de 20 Zonas (Summit 2024 + Pedidos Jairo)
ZONAS_CALIENTES = [
    "barrio jara", "las lomas", "molas lopez", "ytay", "ycua sati", 
    "manora", "recoleta", "villa morra", "herrera", "mburucuya", 
    "trinidad", "laureles", "mburicao", "san cristobal", "villa aurelia", 
    "luque", "san bernardino", "fernando de la mora", "san lorenzo", "mariano roque alonso"
]

def limpiar_telefono(texto):
    # Extrae solo los dígitos
    numeros = re.sub(r'\D', '', texto)
    # Formato Internacional Paraguay para Meta Ads
    if numeros.startswith('09'):
        return '595' + numeros[1:]
    if numeros.startswith('9'):
        return '595' + numeros
    return numeros

async def run_scraper():
    resultados = []
    paginas = 20 
    
    print(f"🚀 Iniciando barrido de {paginas} páginas en zonas de alta captación...")

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
                await asyncio.sleep(2) # Pausa de seguridad para evitar bloqueos de IP
                
                anuncios = await page.query_selector_all("article, .list-item") 
                
                for anuncio in anuncios:
                    texto_crudo = await anuncio.text_content()
                    if texto_crudo:
                        texto = ' '.join(texto_crudo.split()).lower()
                        
                        # Filtro 1: Que pertenezca a tus 20 zonas calientes
                        if any(zona in texto for zona in ZONAS_CALIENTES):
                            # Filtro 2: Excluir competencia directa
                            if not any(exp in texto for i, exp in enumerate(["remax", "century", "c21", "agente", "inmobiliaria"])):
                                
                                # Extracción de Teléfono
                                match_tel = re.search(r'09\d{2}\s?\d{3}\s?\d{3}', texto_crudo)
                                if match_tel:
                                    tel_limpio = limpiar_telefono(match_tel.group())
                                    
                                    resultados.append({
                                        "telefono_meta": tel_limpio,
                                        "zona_detectada": next((z for z in ZONAS_CALIENTES if z in texto), "otra"),
                                        "origen": "Clasipar Directo",
                                        "es_caliente": True
                                    })
                
                print(f"✅ Página {i} procesada. Prospectos acumulados: {len(resultados)}")
            except Exception as e:
                print(f"⚠️ Error en pág {i}: {e}")
                continue

        # Envío de datos a n8n para el Retargeting de Autoridad
        if resultados:
            print(f"📦 Enviando {len(resultados)} números a n8n...")
            try:
                response = requests.post(WEBHOOK_URL, json=resultados, timeout=60)
                print(f"📡 Respuesta n8n: {response.status_code}")
            except Exception as e_send:
                print(f"❌ Error de conexión: {e_send}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
