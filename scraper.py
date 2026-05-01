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
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            print("Cerrando posibles pop-ups invisibles...")
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)
            
            print("Esperando activamente a que Facebook inyecte las publicaciones reales (máximo 30s)...")
            
            # EL TRUCO: Facebook siempre pone 2 esqueletos. Esperamos a que haya más de 2.
            try:
                await page.wait_for_function(
                    "() => document.querySelectorAll('div[role=\"article\"]').length > 2", 
                    timeout=30000
                )
            except:
                print("Aviso: El feed tardó demasiado. Intentando extraer lo que haya...")

            # Hacemos múltiples scrolls suaves para despertar el contenido de los alquileres/ventas
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
            
            titulo = await page.title()
            print(f"Título detectado: {titulo}")

            posts = await page.query_selector_all("div[role='article']")
            print(f"Total de contenedores detectados: {len(posts)}")

            if len(posts) > 0:
                print("\n--- EXTRAYENDO TEXTOS ---")
                for i, post in enumerate(posts[:5]): 
                    texto = await post.text_content()
                    
                    if texto and texto.strip():
                        print(f"\n[PUBLICACIÓN {i+1}]")
                        # Limpiamos los saltos de línea para que se lea mejor en el log
                        texto_limpio = ' '.join(texto.split())
                        print(texto_limpio[:400] + "...") 
                    else:
                        print(f"\n[PUBLICACIÓN {i+1}] -> (Descartada: Sigue siendo esqueleto vacío)")

        except Exception as e:
            print(f"Fallo en la ejecución: {e}")
        finally:
            await browser.close()
            print("\nNavegador cerrado. Ciclo finalizado.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
