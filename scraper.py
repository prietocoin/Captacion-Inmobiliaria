import asyncio
import os
from playwright.async_api import async_playwright

C_USER = os.getenv("FB_C_USER")
XS = os.getenv("FB_XS")

async def run_scraper():
    print("Iniciando motor de Playwright con sesión de usuario...")
    
    if not C_USER or not XS:
        print("ERROR CRÍTICO: Faltan las variables de entorno FB_C_USER o FB_XS.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # SOLUCIÓN 1: Simulamos un monitor Full HD para que Facebook no colapse el diseño
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
        print(f"Navegando al grupo: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            print("Esperando 10 segundos a que los esqueletos de carga desaparezcan...")
            await asyncio.sleep(10) 
            
            # Scroll agresivo para despertar el contenido de React
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(5)
            
            titulo = await page.title()
            print(f"Título detectado: {titulo}")

            posts = await page.query_selector_all("div[role='article']")
            print(f"Total de contenedores detectados: {len(posts)}")

            if len(posts) > 0:
                print("\n--- EXTRAYENDO TEXTOS ---")
                for i, post in enumerate(posts[:5]): # Ampliamos a 5 para más seguridad
                    # SOLUCIÓN 2: text_content() extrae todo sin importar si está visible u oculto
                    texto = await post.text_content()
                    
                    # Limpiamos el texto para ver si realmente hay contenido
                    if texto and texto.strip():
                        print(f"\n[PUBLICACIÓN {i+1}]")
                        print(texto.strip()[:400].replace('\n', ' // ')) 
                    else:
                        print(f"\n[PUBLICACIÓN {i+1}] -> (Descartada: Era un bloque de carga vacío)")

        except Exception as e:
            print(f"Fallo en la ejecución: {e}")
        finally:
            await browser.close()
            print("\nNavegador cerrado. Ciclo finalizado.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
