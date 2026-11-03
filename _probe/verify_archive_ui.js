const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  const sizes = [
    ['phone', 390, 844],
    ['ipad-p', 820, 1180],
    ['ipad-l', 1180, 820],
    ['desktop', 1440, 900],
  ];
  for (const [name, width, height] of sizes) {
    const page = await browser.newPage({ viewport: { width, height }, hasTouch: true });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://localhost:8094/chinese-dynasty.html', { waitUntil: 'load' });
    await page.waitForTimeout(1600);
    await page.locator('.view-tab[data-view="map"]').click();
    await page.waitForTimeout(6000);
    const frame = page.frames().find(f => f !== page.mainFrame());
    if (!frame) throw new Error(name + ': no atlas frame');

    const initial = await frame.evaluate(() => {
      const r = id => {
        const el = document.getElementById(id);
        if (!el) return null;
        const x = el.getBoundingClientRect();
        return { l: Math.round(x.left), t: Math.round(x.top), r: Math.round(x.right), b: Math.round(x.bottom), w: Math.round(x.width), h: Math.round(x.height) };
      };
      return {
        vw: innerWidth, vh: innerHeight,
        dock: r('scrubber-dock'), key: r('map-key'), pane: r('chronicle-pane'), controls: r('canvas-br-dock'),
        tab: document.body.getAttribute('data-archive-tab'),
        tabsVisible: !!document.querySelector('.archive-folder-tabs') && getComputedStyle(document.querySelector('.archive-folder-tabs')).display !== 'none',
      };
    });
    console.log(`[${name}] initial`, JSON.stringify(initial));
    await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/archive_${name}_chronicle.png` });

    if (width < 768) {
      await frame.locator('#act-mobile-chronicle').click();
      await page.waitForTimeout(700);
      const expanded = await frame.evaluate(() => {
        const pane = document.getElementById('chronicle-pane').getBoundingClientRect();
        const dock = document.getElementById('scrubber-dock').getBoundingClientRect();
        return {
          paneBottom: Math.round(pane.bottom), dockTop: Math.round(dock.top),
          gap: Math.round(dock.top - pane.bottom),
          keyDisplay: getComputedStyle(document.getElementById('map-key')).display,
        };
      });
      console.log(`[${name}] expanded`, JSON.stringify(expanded));
      await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/archive_${name}_expanded.png` });
      await frame.locator('#act-mobile-chronicle').click();
      await page.waitForTimeout(400);
    }

    if (width >= 768) {
      await frame.locator('.archive-folder-tab[data-tab="event"]').click();
      await page.waitForTimeout(500);
      const eventState = await frame.evaluate(() => ({
        tab: document.body.getAttribute('data-archive-tab'),
        balloonVisibility: getComputedStyle(document.getElementById('milestone-balloon')).visibility,
        paneVisibility: getComputedStyle(document.getElementById('chronicle-pane')).visibility,
        placeholder: !!document.querySelector('#milestone-balloon .archive-empty'),
      }));
      console.log(`[${name}] event-tab`, JSON.stringify(eventState));
      await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/archive_${name}_event.png` });

      const pins = frame.locator('.milestone-pin');
      const pinCount = await pins.count();
      if (pinCount) {
        await pins.first().click({ force: true });
        await page.waitForTimeout(700);
        const actual = await frame.evaluate(() => ({
          tab: document.body.getAttribute('data-archive-tab'),
          text: (document.querySelector('#milestone-balloon .ep-text') || {}).textContent || '',
          hidden: document.getElementById('milestone-balloon').classList.contains('is-hidden'),
        }));
        console.log(`[${name}] real-event`, JSON.stringify(actual));
      }
      await frame.locator('.archive-folder-tab[data-tab="chronicle"]').click();
      await page.waitForTimeout(350);
    }
    console.log(`[${name}] errors`, JSON.stringify(errors));
    await page.close();
  }
  await browser.close();
  console.log('DONE');
})();
