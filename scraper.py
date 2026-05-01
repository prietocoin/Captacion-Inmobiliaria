import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

# Tu URL del nodo de n8n (¡No olvides cambiarla!)
WEBHOOK_URL = "AQUI_PONES_TU_URL_DE_N8N"

BASE_URL = "https://clasipar.paraguay.com/inmuebles?page="

async def run_scraper():
    resultados = []
    paginas_a_extraer = 3 # Súbelo a 25 o 50 cuando confirmes que llega a n8n
    
    # LA LISTA NEGRA: Palabras típicas de la competencia
    palabras_prohibidas = [
        "inmobiliaria", "inmobiliario", "remax", "re/max", "century", "c21", 
        "keller williams", "kw", "agente", "comisión", "comision", 
        "bienes raíces", "bienes raices", "broker", "franquicia"
    ]
    
    print(f"Iniciando cazador de dueños directos... Objetivo: {paginas_a_extraer} páginas")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i in range(1, paginas_a_extraer + 1):
            url = f"{BASE_URL}{i}"
            print(f"\nRevisando página {i}...")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await asyncio.sleep(2) 

                anuncios = await page.query_selector_all("article, .list-item, .ad-listing") 
                
                anuncios_filtrados_pagina = 0

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
                            
                            # FILTRO NEGATIVO: Si alguna palabra prohibida está en el texto, saltamos al siguiente
                            if any(palabra in texto_minusculas for palabra in palabras_prohibidas):
                                continue # Ignora a la competencia
                                
                            # Si pasó el filtro y tiene contenido real, lo guardamos
                            if len(texto_limpio) > 20:
                                resultados.append({
                                    "origen": "Clasipar Directo",
                                    "contenido": texto_limpio,
                                    "url": enlace
                                })
                                anuncios_filtrados_pagina += 1
                    except:
                        continue 
                
                print(f"-> Diamantes (Dueño Directo) encontrados aquí: {anuncios_filtrados_pagina}")

            except Exception as e_pagina:
                print(f"Aviso: Fallo en página {i} ({str(e_pagina)})")
                break 

        payload = {
            "status": "success",
            "total_extraido": len(resultados),
            "data": resultados
        }
        
        print(f"\n--- EXTRACCIÓN LIMPIA FINALIZADA ---")
        print(f"Total de dueños directos capturados: {len(resultados)}")
        
        if WEBHOOK_URL != "AQUI_PONES_TU_URL_DE_N8N":
            print(f"Enviando oro puro a n8n...")
            response = requests.post(WEBHOOK_URL, json=payload)
            print(f"Respuesta de n8n: {response.status_code}")
        else:
            print("AVISO: Falta tu WEBHOOK_URL.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
