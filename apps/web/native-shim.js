/* ============================================================
   native-shim.js — 原生壳适配层（仅原生包使用，web 版不受影响）

   1. 视图状态上报：body[data-view] 变化时通知 native，
      让原生侧知道「现在能不能直接退出」（长卷=可退出，史图=先返回长卷）
   2. 返回键 / 侧滑返回：暴露 window.__nativeBack()，返回 true 表示已就地处理
   3. 地图 iframe 兜底：20 秒未就绪时用绝对地址重试一次（resource://、app:// 下常见）
   4. iOS 细节：抑制双击缩放与橡皮筋，修正 100vh
   ============================================================ */
(function () {
  'use strict';

  var isNative = /^(resource|app|file):/.test(location.protocol) ||
    navigator.userAgent.indexOf('HistoryScrollApp') > -1;
  if (!isNative) return;

  document.documentElement.classList.add('in-native-shell');

  /* ---------- 1. 通知 native ---------- */
  function toNative(channel, payload) {
    try {
      if (window.harmonyBridge && typeof window.harmonyBridge[channel] === 'function') {
        window.harmonyBridge[channel](payload);
        return;
      }
      var wk = window.webkit && window.webkit.messageHandlers;
      if (wk && wk[channel]) wk[channel].postMessage(payload);
    } catch (e) { /* 壳未注册时静默 */ }
  }

  function currentView() {
    return document.body.getAttribute('data-view') || 'scroll';
  }

  var lastView = currentView();
  var observer = new MutationObserver(function () {
    var v = currentView();
    if (v === lastView) return;
    lastView = v;
    toNative('onViewChange', v);
  });
  observer.observe(document.body, { attributes: true, attributeFilter: ['data-view'] });

  /* ---------- 2. 返回键：先退视图，再退应用 ---------- */
  window.__nativeBack = function () {
    if (currentView() === 'scroll') return false;   // 已在首页，交回系统退出
    var btn = document.querySelector('.vsc-item[data-switch-view="scroll"]');
    if (btn) { btn.click(); return true; }
    if (typeof window.switchView === 'function') { window.switchView('scroll'); return true; }
    return false;
  };

  /* ---------- 3. 地图 iframe 绝对地址兜底 ---------- */
  var retried = false;
  function retryMapWithAbsoluteUrl() {
    if (retried) return;
    var frame = document.getElementById('map-embed');
    if (!frame || !frame.getAttribute('src')) return;
    retried = true;
    var abs = new URL(frame.getAttribute('src'), location.href).href;
    if (abs === frame.src) return;
    frame.src = abs;
  }
  setTimeout(retryMapWithAbsoluteUrl, 12000);

  /* ---------- 4. iOS 细节 ---------- */
  var meta = document.querySelector('meta[name="viewport"]');
  if (meta && meta.content.indexOf('viewport-fit') === -1) {
    meta.content += ', viewport-fit=cover';
  }

  // 双击缩放（WebView 里偶发）——只拦快速双击，不影响单击交互
  var lastTap = 0;
  document.addEventListener('touchend', function (e) {
    var now = Date.now();
    if (now - lastTap < 300) e.preventDefault();
    lastTap = now;
  }, { passive: false });

  // 100vh 在 iOS 上会随地址栏跳动，用真实高度兜住
  function syncVh() {
    document.documentElement.style.setProperty('--vh', (window.innerHeight * 0.01) + 'px');
  }
  syncVh();
  window.addEventListener('resize', syncVh);
  window.addEventListener('orientationchange', function () { setTimeout(syncVh, 250); });

  // 告诉 native「首屏已就绪」，可收起启动图
  if (document.readyState === 'complete') toNative('onReady', currentView());
  else window.addEventListener('load', function () { toNative('onReady', currentView()); });
})();
