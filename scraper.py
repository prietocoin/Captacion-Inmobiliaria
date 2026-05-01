import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def run_scraper():
    async with async_playwright() as p:
        # Lanzamos el navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Aplicamos el modo stealth
        await stealth_async(page) 

        # Intentamos entrar a la búsqueda de Barrio Jara
        url = "https://www.facebook.com/groups/inmobiliariaparaguay/search/?q=Barrio%20Jara"
        
        print(f"Abriendo: {url}")
        await page.goto(url)
        await asyncio.sleep(10) # Damos tiempo extra para cargar

        # Buscamos los posts
        posts = await page.query_selector_all("div[role='article']")
        
        if len(posts) == 0:
            print("No se encontraron publicaciones. Es probable que Facebook pida login.")
        else:
            print(f"¡Éxito! Se encontraron {len(posts)} publicaciones.")
            for i, post in enumerate(posts[:3]):
                texto = await post.inner_text()
                print(f"--- POST {i+1} ---")
                print(texto[:150])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
