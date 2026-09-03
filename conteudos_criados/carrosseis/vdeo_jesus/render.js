const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 1 });
        const htmlPath = 'file://' + path.resolve(__dirname, 'carrossel.html');
        await page.goto(htmlPath, { waitUntil: 'networkidle0' });
        
        const slides = await page.$$('.slide');
        for (let i = 0; i < slides.length; i++) {
            await slides[i].screenshot({ path: path.join(__dirname, `slide_${i + 1}.png`) });
        }
        await browser.close();
        console.log("Renderização concluída.");
    } catch(e) {
        console.error("Erro na renderização:", e);
        process.exit(1);
    }
})();
