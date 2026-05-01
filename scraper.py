import asyncio
from playwright.async_api import async_playwright
import playwright_stealth

async def run_scraper():
    async with async_playwright() as p:
        # Lanzamos el navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Aplicamos el modo stealth de la forma correcta
        await playwright_stealth.stealth_async(page) 

        # URL de búsqueda
        url = "https://www.facebook.com/groups/inmobiliariaparaguay/search/?q=Barrio%20Jara"
        
        print(f"Iniciando navegación en: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5) # Espera manual para carga de contenido dinámico

            # Buscamos los contenedores de los posts
            posts = await page.query_selector_all("div[role='article']")
            
            if not posts:
                print("Aviso: No se detectaron publicaciones. Facebook podría estar bloqueando el acceso anónimo.")
            else:
                print(f"Éxito: Se encontraron {len(posts)} publicaciones potenciales.")
                for i, post in enumerate(posts[:3]):
                    texto = await post.inner_text()
                    print(f"--- CONTENIDO POST {i+1} ---")
                    print(texto[:150]) # Solo los primeros 150 caracteres

        except Exception as e:
            print(f"Error durante la navegación: {e}")

        await browser.close()
        print("Proceso finalizado.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
