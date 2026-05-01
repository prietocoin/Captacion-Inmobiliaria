import asyncio
import os
import json
import requests
from playwright.async_api import async_playwright

C_USER = os.getenv("FB_C_USER")
XS = os.getenv("FB_XS")

# Reemplaza esto con la URL de tu Webhook de n8n
WEBHOOK_URL = "AQUI_PONES_TU_URL_DE_N8N"

async def run_scraper():
    if not C_USER or not XS:
        print(json.dumps({"error": "Faltan variables de entorno FB_C_USER o FB_XS"}))
        return

    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        await context.add_cookies([
            {"name": "c_user", "value": C_USER, "domain": ".facebook.com", "path": "/"},
            {"name": "xs", "value": XS, "domain": ".facebook.com", "path": "/"}
        ])
        
        page = await context.new_page()
        url = "https://www.facebook.com/groups/1561165307960664/"
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)
            
            try:
                await page.wait_for_function(
                    "() => document.querySelectorAll('div[role=\"article\"]').length > 2", 
                    timeout=30000
                )
            except:
                pass

            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)

            posts = await page.query_selector_all("div[role='article']")

            for post in posts[:5]:
                # SOLUCIÓN "Ver más": Buscamos cualquier elemento que contenga el texto y le hacemos clic
                try:
                    botones = await post.locator("text='Ver más'").element_handles()
                    for btn in botones:
                        await btn.click(timeout=2000)
                        await asyncio.sleep(1.5) # Damos tiempo a que la animación de Facebook despliegue el texto
                except:
                    pass

                texto = await post.text_content()
                
                if texto and texto.strip():
                    texto_limpio = ' '.join(texto.split())
                    # Filtramos los que siguen siendo esqueletos vacíos
                    if len(texto_limpio) > 20: 
                        resultados.append({
                            "origen": "Facebook Group",
                            "contenido": texto_limpio
                        })

            payload = {
                "status": "success", 
                "total_extraido": len(resultados),
                "data": resultados
            }
            
            # Mostramos el JSON en consola para verificar
            print(json.dumps(payload, ensure_ascii=False))

            # ENVIAMOS A N8N
            if WEBHOOK_URL != "AQUI_PONES_TU_URL_DE_N8N":
                print(f"\nEnviando datos a n8n...")
                response = requests.post(WEBHOOK_URL, json=payload)
                print(f"Respuesta de n8n: {response.status_code}")

        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
