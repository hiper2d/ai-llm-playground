import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const url = process.argv[2];
const timeout = 8000;

(async () => {
    const browser = await puppeteer.launch( {
        headless: false, // About other options: https://developer.chrome.com/docs/chromium/new-headless
    } );

    const page = await browser.newPage();

    await page.setViewport( {
        width: 1200,
        height: 1200,
        deviceScaleFactor: 1,
    } );

    setTimeout(async () => {
        await page.screenshot( {
            path: "screenshot.jpg",
            fullPage: true,
        } );
    }, timeout-2000);

    await page.goto( url, {
        waitUntil: "networkidle0", // Other values: https://pptr.dev/api/puppeteer.page.goforward/#remarks
        timeout: timeout,
    } );

    // Wait for a minute before taking the screenshot
    await page.waitForTimeout(300_000);

    await page.screenshot( {
        path: "screenshot.jpg",
        fullPage: true,
    } );

    await browser.close();
})();