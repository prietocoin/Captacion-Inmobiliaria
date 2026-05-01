import asyncio
import os
from playwright.async_api import async_playwright

# Tus llaves de sesión
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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Inyectamos tus cookies
        await context.add_cookies([
            {"name": "c_user", "value": C_USER, "domain": ".facebook.com", "path": "/"},
            {"name": "xs", "value": XS, "domain": ".facebook.com", "path": "/"}
        ])
        
        page = await context.new_page()
        
        # TU ESTRATEGIA: URL directa del grupo de la captura
        url = "https://www.facebook.com/groups/1561165307960664/"
        print(f"Navegando directamente al grupo: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            print("Esperando a que cargue el grupo...")
            await asyncio.sleep(8) 
            
            # Hacemos un poco de scroll hacia abajo para forzar que carguen los posts
            await page.evaluate("window.scrollBy(0, 1500)")
            await asyncio.sleep(5)
            
            titulo = await page.title()
            print(f"Título detectado: {titulo}")

            posts = await page.query_selector_all("div[role='article']")
            print(f"Total de publicaciones detectadas: {len(posts)}")

            if len(posts) > 0:
                print("\n--- EXTRAYENDO TEXTOS ---")
                for i, post in enumerate(posts[:3]): 
                    texto = await post.inner_text()
                    print(f"\n[PUBLICACIÓN {i+1}]")
                    print(texto[:300].replace('\n', ' // ')) 

        except Exception as e:
            print(f"Fallo en la ejecución: {e}")
        finally:
            await browser.close()
            print("\nNavegador cerrado. Ciclo finalizado.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
