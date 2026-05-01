import asyncio
from playwright.async_api import async_playwright

async def run_scraper():
    print("Iniciando motor de Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Añadimos un user-agent básico para simular un navegador real sin usar la librería stealth
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.facebook.com/groups/inmobiliariaparaguay/search/?q=Barrio%20Jara"
        print(f"Navegando a: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5) 
            
            titulo = await page.title()
            print(f"Título de la página cargada: {titulo}")

            posts = await page.query_selector_all("div[role='article']")
            print(f"Total de nodos de artículos detectados: {len(posts)}")

        except Exception as e:
            print(f"Fallo en la ejecución: {e}")
        finally:
            await browser.close()
            print("Navegador cerrado.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
