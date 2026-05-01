import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# --- CONFIGURACIÓN DE TU FÁBRICA DE CONTENIDO ---
# Cambia a la URL de producción cuando verifiques que los datos llegan bien
WEBHOOK_URL = "https://n8n.jairokov.com/webhook-test/clasipar-directo"

# URL base de Inmuebles en Clasipar
BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    # 60 páginas x ~17 diamantes por página ≈ 1000 propiedades
    paginas_a_extraer = 60 
    
    # LISTA NEGRA: Filtro para eliminar competencia e inmobiliarias
    palabras_prohibidas = [
        "inmobiliaria", "inmobiliario", "remax", "re/max", "century", "c21", 
        "keller williams", "kw", "agente", "comisión", "comision", 
        "bienes raíces", "bienes raices", "broker", "franquicia", "asesor"
    ]
    
    print(f"🚀 Iniciando Cazador de Dueños Directos...")
    print(f"Objetivo: {paginas_a_extraer} páginas | Webhook: {WEBHOOK_URL}")

    async with async_playwright() as p:
        # Lanzamos el navegador de forma eficiente
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            
            try:
                # Navegación rápida con tiempo de espera prudencial
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(1.5) # Pausa técnica para no saturar el servidor

                # Detectamos todos los contenedores de anuncios
                anuncios = await page.query_selector_all("article, .list-item, .ad-listing") 
                
                if not anuncios:
                    print(f"⚠️ No se encontraron más anuncios en la página {i}. Finalizando.")
                    break

                for anuncio in anuncios:
                    try:
                        # Extraemos el texto para aplicar el filtro
                        texto_crudo = await anuncio.text_content()
                        
                        # Extraemos el enlace directo a la propiedad
                        enlace_elemento = await anuncio.query_selector("a")
                        enlace = await enlace_elemento.get_attribute("href") if enlace_elemento else ""
                        if enlace and not enlace.startswith("http"):
                            enlace = f"https://clasipar.paraguay.com{enlace}"

                        if texto_crudo and texto_crudo.strip():
                            texto_limpio = ' '.join(texto_crudo.split())
                            texto_minusculas = texto_limpio.lower()
                            
                            # FILTRO TÁCTICO: ¿Es dueño directo?
                            if any(palabra in texto_minusculas for palabra in palabras_prohibidas):
                                continue # Es competencia, lo ignoramos
                                
                            # Si pasa el filtro, lo agregamos al lote
                            if len(texto_limpio) > 30:
                                resultados.append({
                                    "origen": "Clasipar Directo",
                                    "contenido": texto_limpio,
                                    "url": enlace,
                                    "pagina_fuente": i
                                })
                    except:
                        continue 
                
                print(f"✅ Página {i} procesada. Acumulado: {len(resultados)} diamantes.")

            except Exception as e:
                print(f"❌ Error en página {i}: {str(e)}")
                break 

        # --- ENVÍO DE DATOS A N8N ---
        payload = {
            "status": "success",
            "total_extraido": len(resultados),
            "data": resultados
        }
        
        print(f"\n--- EXTRACCIÓN FINALIZADA ---")
        print(f"Propiedades listas para n8n: {len(resultados)}")
        
        try:
            print(f"Enviando lote de datos a {WEBHOOK_URL}...")
            response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            print(f"Respuesta de n8n: {response.status_code}")
        except Exception as e_send:
            print(f"❌ Falló el envío al Webhook: {str(e_send)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
