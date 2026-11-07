/* ============ 内嵌联动桥 v2（与「华夏千年历史长卷」双向同步）============
   上行：__atlasReady / __atlasAck / __atlasState / __atlasExit
   下行：{ __atlas:1, year, person, token } / { __atlas:1, __atlasQuery:1 }
   原则：只发消息，绝不重载文档，保证地图内部状态连续 */
/* iOS：锁整页上下滑动（overflow:hidden 在 iOS Safari 上仍会出现橡皮筋滚动）。
   触摸落在真实可滚动的容器（面板内容、史志窗格等）内时放行，其余一律拦截。 */
(function () {
  var isScrollable = function (el, axis) {
    var s = getComputedStyle(el);
    var ov = axis === 'x' ? s.overflowX : s.overflowY;
    return (ov === 'auto' || ov === 'scroll') &&
      (axis === 'x' ? el.scrollWidth : el.scrollHeight) >
      (axis === 'x' ? el.clientWidth : el.clientHeight) + 1;
  };
  document.addEventListener('touchmove', function (e) {
    var t = e.target;
    while (t && t.nodeType === 1 && t !== document.documentElement) {
      if (isScrollable(t, 'y') || isScrollable(t, 'x')) return;
      t = t.parentElement;
    }
    e.preventDefault();
  }, { passive: false });
})();
(function () {
  var EMBED = false;
  try { EMBED = !!(window.parent && window.parent !== window); } catch (e) { EMBED = false; }

  function post(msg) {
    if (!EMBED) return;
    try { window.parent.postMessage(msg, '*'); } catch (e) {}
  }
  function app() { return window.atlasApp || null; }

  function snap() {
    var a = app();
    if (!a) return null;
    var p = (a.activePerson && a.activePerson.profiles && a.activePerson.profiles[0]) || null;
    var d = (a.dynasties && a.dynasties[a.dynastyIdx]) || null;
    return {
      __atlasState: 1,
      year: typeof a.year === 'number' ? a.year : null,
      person: p ? p.key : null,
      personName: p ? (p.zh || p.nameZh || '') : null,
      dyn: d ? (d.nameZh || d.name || '') : '',
      playing: !!a.playing
    };
  }

  var lastSig = '';
  var syncTimer = 0;
  function sync(force) {
    var s = snap();
    if (!s) return;
    var sig = s.year + '|' + s.person;
    if (!force && sig === lastSig) return;
    lastSig = sig;
    post(s);
  }
  window.__atlasSync = function () {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(function () { sync(false); }, 120);
  };

  function apply(d) {
    var a = app();
    if (!a) return false;
    try {
      if (a.stopAutoplay) a.stopAutoplay();
      if (d.person) {
        if (!a.openPersonChronicle(d.person, -1)) return false;
        document.body.setAttribute('data-archive-tab', 'genealogy');
      } else {
        if (a.activePerson && a.closeGenealogyCard) a.closeGenealogyCard();
        if (typeof d.year === 'number' && isFinite(d.year) && a.jumpToYear) a.jumpToYear(d.year);
      }
      return true;
    } catch (e) { return false; }
  }

  var pending = null;

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (typeof d === 'string') { try { d = JSON.parse(d); } catch (err) { return; } }
    if (!d || d.__atlas !== 1) return;
    if (d.__atlasQuery) {
      var s0 = snap() || {};
      post({ __atlasAck: 1, token: d.token || null, year: s0.year, person: s0.person, personName: s0.personName });
      return;
    }
    if (apply(d)) {
      post({ __atlasAck: 1, token: d.token || null, year: d.year, person: d.person || null });
      sync(true);
    } else {
      pending = d;
    }
  });

  function bindBack() {
    var b = document.getElementById('act-home');
    if (!b || b.__atlasBound) return;
    b.__atlasBound = 1;
    b.addEventListener('click', function (ev) {
      ev.preventDefault();
      var s = snap() || {};
      post({
        __atlasExit: 1,
        year: s.year, person: s.person, personName: s.personName, dyn: s.dyn
      });
    });
  }

  var tries = 0;
  var timer = setInterval(function () {
    tries += 1;
    if (app()) {
      clearInterval(timer);
      bindBack();
      post({ __atlasReady: 1 });
      if (pending) {
        var p = pending; pending = null;
        if (apply(p)) post({ __atlasAck: 1, token: p.token || null, year: p.year, person: p.person || null });
        sync(true);
      } else {
        sync(true);
      }
    } else if (tries > 500) {
      clearInterval(timer);
    }
  }, 60);
})();
