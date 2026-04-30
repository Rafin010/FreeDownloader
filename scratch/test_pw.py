import asyncio
from playwright.async_api import async_playwright

async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print("Navigating to fastdl.app...")
            # We must resolve it first or use DNS over HTTPS in playwright
            # Let's see if playwright resolves it normally (it uses OS DNS)
            try:
                await page.goto('https://fastdl.app/', timeout=15000)
                print("Page loaded!")
                
                # Wait for input
                await page.wait_for_selector('input[name="url"]', timeout=5000)
                await page.fill('input[name="url"]', 'https://www.instagram.com/p/C_1Q3Y7B-Y_/')
                
                # Click download
                await page.click('button[type="submit"]')
                print("Clicked download, waiting for results...")
                
                # Wait for download links
                await page.wait_for_selector('a.button.button--filled.button__download', timeout=15000)
                
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a.button__download')).map(a => a.href);
                }''')
                
                print("Found Links:", links)
            except Exception as e:
                print("Navigation/Scraping error:", e)
                
            await browser.close()
    except Exception as e:
        print("Playwright error:", e)

if __name__ == '__main__':
    asyncio.run(main())
