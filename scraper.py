import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# Tu URL del nodo de n8n
WEBHOOK_URL = "AQUI_PONES_TU_URL_DE_N8N"

# URL base de la categoría de inmuebles con el parámetro de página listo
BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    
    # Empecemos con 3 páginas para probar que n8n reciba bien los datos. 
    # Luego puedes subir este número a 50 para sacar tus 1000 propiedades de golpe.
    paginas_a_extraer = 3 
    
    print(f"Iniciando motor para Clasipar... Objetivo: {paginas_a_extraer} páginas")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            print(f"\nNavegando a: {url}")
            
            try:
                # domcontentloaded es rapidísimo en sitios como Clasipar
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(2) # Pausa de respeto para el servidor

                # Clasipar suele envolver sus anuncios en la etiqueta <article> o contenedores con clase específica
                anuncios = await page.query_selector_all("article, .list-item, .ad-listing") 
                
                print(f"Anuncios detectados en página {i}: {len(anuncios)}")

                for anuncio in anuncios:
                    try:
                        # Sacamos el texto completo de la tarjeta (precio, título, ubicación)
                        texto_crudo = await anuncio.text_content()
                        
                        # Extraemos el enlace para que puedas ir directo a la oferta desde n8n
                        enlace_elemento = await anuncio.query_selector("a")
                        enlace = await enlace_elemento.get_attribute("href") if enlace_elemento else ""
                        
                        if enlace and not enlace.startswith("http"):
                            enlace = f"https://clasipar.paraguay.com{enlace}"

                        if texto_crudo and texto_crudo.strip():
                            texto_limpio = ' '.join(texto_crudo.split())
                            # Descartamos basuras pequeñas
                            if len(texto_limpio) > 20:
                                resultados.append({
                                    "origen": "Clasipar Inmuebles",
                                    "contenido": texto_limpio,
                                    "url": enlace
                                })
                    except:
                        continue # Si una tarjeta individual falla, no detenemos todo el bot

            except Exception as e_pagina:
                print(f"Aviso: La página {i} falló o no existe. ({str(e_pagina)})")
                break # Rompemos el ciclo si llegamos al final de la paginación real

        payload = {
            "status": "success",
            "total_extraido": len(resultados),
            "data": resultados
        }
        
        print(f"\n--- CICLO FINALIZADO ---")
        print(f"Total de propiedades capturadas listas para tu fábrica: {len(resultados)}")
        
        # Enviamos el paquete a tu automatización
        if WEBHOOK_URL != "AQUI_PONES_TU_URL_DE_N8N":
            print(f"Disparando webhook hacia n8n...")
            response = requests.post(WEBHOOK_URL, json=payload)
            print(f"Respuesta del servidor n8n: {response.status_code}")
        else:
            print("AVISO: No pusiste tu WEBHOOK_URL, los datos solo se quedaron en consola.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
