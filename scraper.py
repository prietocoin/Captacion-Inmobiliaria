import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def run_scraper():
    async with async_playwright() as p:
        # Iniciamos el navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page) 

        # URL de búsqueda en un grupo (ejemplo Barrio Jara)
        url = "https://www.facebook.com/groups/inmobiliariaparaguay/search/?q=Barrio%20Jara"
        
        print(f"Abriendo: {url}")
        await page.goto(url)
        await asyncio.sleep(5) # Esperamos a que cargue

        # Extraemos los textos de los posts
        posts = await page.query_selector_all("div[role='article']")
        
        for i, post in enumerate(posts[:5]): # Solo los primeros 5 para probar
            texto = await post.inner_text()
            print(f"--- POST {i+1} ---")
            print(texto[:200]) # Mostramos un resumen

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
