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
    await page.goto('http://localhost:8095/chinese-dynasty.html', { waitUntil: 'load' });
    await page.waitForTimeout(1600);
    await page.locator('.view-tab[data-view="map"]').click();
    await page.waitForTimeout(6000);
    const frame = page.frames().find(f => f !== page.mainFrame());
    if (!frame) throw new Error(name + ': no atlas frame');

    const appTabs = await page.evaluate(() => {
      const el = document.querySelector('.bottom-tabs');
      return el ? getComputedStyle(el).display : 'missing';
    });

    const state = await frame.evaluate(() => {
      const rect = id => {
        const el = document.getElementById(id);
        if (!el) return null;
        const x = el.getBoundingClientRect();
        return { l: Math.round(x.left), t: Math.round(x.top), r: Math.round(x.right), b: Math.round(x.bottom), w: Math.round(x.width), h: Math.round(x.height) };
      };
      const style = id => {
        const el = document.getElementById(id);
        if (!el) return null;
        const s = getComputedStyle(el);
        return { opacity: s.opacity, bg: s.backgroundColor, bgImage: s.backgroundImage, blur: s.backdropFilter || s.webkitBackdropFilter || 'none' };
      };
      const dock = rect('scrubber-dock');
      const pane = rect('chronicle-pane');
      const key = rect('map-key');
      return {
        vw: innerWidth, vh: innerHeight,
        dock, pane, key,
        scale: rect('scale-bar-box'), reset: rect('canvas-br-dock'),
        gaps: dock ? {
          screenBottom: innerHeight - dock.b,
          paneToDock: pane ? dock.t - pane.b : null,
          keyToPane: key && pane ? pane.t - key.b : null,
        } : null,
        styles: {
          nav: style('nav-bar'), dock: style('scrubber-dock'), pane: style('chronicle-pane'),
          key: style('map-key'), scale: style('scale-bar-box'), toggle: style('act-toggle-pane'),
        },
      };
    });
    console.log(`[${name}] appTabs=${appTabs}`, JSON.stringify(state));

    await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/bottom_${name}.png` });

    // 拖动地图，确认不会出现 15% / 75% 的透明淡出
    const box = await page.locator('#map-embed').boundingBox();
    await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
    await page.mouse.down();
    for (let i = 1; i <= 8; i += 1) {
      await page.mouse.move(box.x + box.width * 0.5 + i * 16, box.y + box.height * 0.5 + i * 3);
    }
    const during = await frame.evaluate(() => ({
      bodyClass: document.body.className,
      nav: getComputedStyle(document.getElementById('nav-bar')).opacity,
      dock: getComputedStyle(document.getElementById('scrubber-dock')).opacity,
      pane: getComputedStyle(document.getElementById('chronicle-pane')).opacity,
      key: getComputedStyle(document.getElementById('map-key')).opacity,
    }));
    await page.mouse.up();
    await page.waitForTimeout(350);
    const after = await frame.evaluate(() => ({
      bodyClass: document.body.className,
      nav: getComputedStyle(document.getElementById('nav-bar')).opacity,
      dock: getComputedStyle(document.getElementById('scrubber-dock')).opacity,
      pane: getComputedStyle(document.getElementById('chronicle-pane')).opacity,
      key: getComputedStyle(document.getElementById('map-key')).opacity,
    }));
    console.log(`[${name}] drag`, JSON.stringify({ during, after }));

    if (width < 768) {
      await frame.locator('#act-mobile-chronicle').click();
      await page.waitForTimeout(700);
      const expanded = await frame.evaluate(() => {
        const r = id => {
          const x = document.getElementById(id).getBoundingClientRect();
          return { t: Math.round(x.top), b: Math.round(x.bottom), h: Math.round(x.height) };
        };
        const dock = r('scrubber-dock'), pane = r('chronicle-pane'), key = r('map-key');
        return { dock, pane, key, paneGap: dock.t - pane.b, keyGap: pane.t - key.b, keyDisplay: getComputedStyle(document.getElementById('map-key')).display };
      });
      console.log(`[${name}] expanded`, JSON.stringify(expanded));
      await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/bottom_${name}_expanded.png` });
    }

    if (width >= 768) {
      await frame.locator('.archive-folder-tab[data-tab="event"]').click();
      await page.waitForTimeout(500);
      const eventState = await frame.evaluate(() => {
        const b = document.getElementById('milestone-balloon');
        const s = getComputedStyle(b);
        return { tab: document.body.getAttribute('data-archive-tab'), visibility: s.visibility, opacity: s.opacity, bg: s.backgroundColor, bgImage: s.backgroundImage };
      });
      console.log(`[${name}] event`, JSON.stringify(eventState));
      await page.screenshot({ path: `C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/bottom_${name}_event.png` });
    }

    console.log(`[${name}] errors`, JSON.stringify(errors));
    await page.close();
  }
  await browser.close();
  console.log('DONE');
})();
