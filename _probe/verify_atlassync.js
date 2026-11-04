const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  const errors = [];
  const page = await browser.newPage({ viewport: { width: 820, height: 1180 }, hasTouch: true });
  page.on('pageerror', e => errors.push('JS: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  await page.goto('http://localhost:8097/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(3000);

  const r = await page.evaluate(() => {
    const res = { view: document.body.getAttribute('data-view') };
    // 事件数量
    if (typeof HISTORICAL_EVENTS !== 'undefined') res.events = HISTORICAL_EVENTS.length;
    if (typeof FIGURE_AXIS !== 'undefined') res.figures = FIGURE_AXIS.length;
    if (typeof LITERATI_AXIS !== 'undefined') res.literati = LITERATI_AXIS.length;
    if (typeof ERA_AXIS !== 'undefined') res.eras = ERA_AXIS.length;
    // 检查最早事件和最早人物
    if (typeof HISTORICAL_EVENTS !== 'undefined' && HISTORICAL_EVENTS.length) {
      res.firstEvent = HISTORICAL_EVENTS[0].year + ' ' + HISTORICAL_EVENTS[0].shortTitle;
    }
    if (typeof FIGURE_AXIS !== 'undefined' && FIGURE_AXIS.length) {
      res.firstFigure = FIGURE_AXIS[0].year + ' ' + FIGURE_AXIS[0].n;
    }
    return res;
  });
  console.log('[数据]', JSON.stringify(r));

  // 切换到事件图层，看是否渲染
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll('[data-layer], .fchip, [data-cat]')].find(b => b.textContent.includes('事件'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // 截图
  await page.screenshot({ path: 'C:/Users/Lenovo/Desktop/MyProject/Chinese-history/_probe/atlassync_events.png' });

  // 点击第一个事件竹简验证详情
  const evDetail = await page.evaluate(() => {
    const slips = document.querySelectorAll('.vertical-bamboo-slip, [class*="bamboo"], [data-event-id]');
    return { slipCount: slips.length };
  });
  console.log('[竹简]', JSON.stringify(evDetail));

  console.log('[错误]', errors.length ? JSON.stringify(errors.slice(0, 8)) : '无');
  await browser.close();
  console.log('DONE');
})();
