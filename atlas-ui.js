/* 悬浮 UI 状态：触碰地图 → 75%；拖动 / 滚轮缩放地图 → 15%；松手恢复 */
(function () {
  function boot() {
    var body = document.body;
    var viewport = document.getElementById('viewport-frame');
    var dock = document.getElementById('scrubber-dock');
    if (!viewport || !dock) { setTimeout(boot, 120); return; }
    /* 图例仅通过手柄移动，不再响应左右滑动切换年份。 */
    var key = document.getElementById('map-key');
    if (key) {
      var dragState = null, customPosition = false;
      function boundLegend(x, y) {
        var r = key.getBoundingClientRect();
        var dr = dock.getBoundingClientRect();
        var bottomLimit = Math.max(70, dr.top - 8);
        key.style.setProperty('left', Math.max(8, Math.min(window.innerWidth-r.width-8, x)) + 'px', 'important');
        key.style.setProperty('top', Math.max(64, Math.min(bottomLimit-r.height, y)) + 'px', 'important');
        key.style.setProperty('bottom', 'auto', 'important');
      }
      function addHandle() {
        if (key.querySelector('.legend-drag-handle')) return;
        var handle = document.createElement('button');
        handle.className = 'legend-drag-handle'; handle.type = 'button';
        handle.textContent = '⠿  图例';
        handle.title = '拖动移动图例；方向键微调位置';
        handle.setAttribute('aria-label', '移动图例，支持拖动和方向键');
        key.prepend(handle);
        handle.addEventListener('pointerdown', function(e) {
          if (e.button) return;
          e.preventDefault(); e.stopPropagation();
          if (window.atlasApp) window.atlasApp.stopAutoplay();
          var r = key.getBoundingClientRect();
          dragState = {id:e.pointerId,x:e.clientX,y:e.clientY,left:r.left,top:r.top};
          handle.setPointerCapture(e.pointerId); key.classList.add('is-legend-dragging');
        });
        handle.addEventListener('pointermove', function(e) {
          if (!dragState || e.pointerId !== dragState.id) return;
          e.stopPropagation(); customPosition = true;
          boundLegend(dragState.left+e.clientX-dragState.x, dragState.top+e.clientY-dragState.y);
        });
        function finish(e) { if (!dragState) return; e.stopPropagation(); dragState=null; key.classList.remove('is-legend-dragging'); }
        handle.addEventListener('pointerup', finish);
        handle.addEventListener('pointercancel', finish);
        handle.addEventListener('lostpointercapture', finish);
        handle.addEventListener('click', function(e) { e.stopPropagation(); });
        handle.addEventListener('keydown', function(e) {
          var step = e.shiftKey ? 30 : 10, dx = {ArrowLeft:-step,ArrowRight:step}[e.key]||0, dy = {ArrowUp:-step,ArrowDown:step}[e.key]||0;
          if (!dx && !dy) return;
          e.preventDefault(); e.stopPropagation(); customPosition=true;
          var r=key.getBoundingClientRect(); boundLegend(r.x+dx,r.y+dy);
        });
      }
      addHandle();
      new MutationObserver(addHandle).observe(key,{childList:true});
      new ResizeObserver(function(){if(customPosition){var r=key.getBoundingClientRect();boundLegend(r.x,r.y);}}).observe(key);
      window.addEventListener('resize',function(){if(customPosition){var r=key.getBoundingClientRect();boundLegend(r.x,r.y);}});
    }

    /* ===== v13：档案夹双标签 + 浮卡对时间轴的实测避让 ===== */
    var pane = document.getElementById('chronicle-pane');
    var balloon = document.getElementById('milestone-balloon');
    var root = document.documentElement;
    var archivePlaceholder = false;
    var layoutRaf = 0;

    function archiveMode() { return window.innerWidth >= 768; }
    function setVar(name, value) {
      if (root.style.getPropertyValue(name) !== value) root.style.setProperty(name, value);
    }
    function scheduleLayout() {
      if (layoutRaf) return;
      layoutRaf = requestAnimationFrame(function () {
        layoutRaf = 0;
        var dr = dock.getBoundingClientRect();
        var dockClear = 0;
        if (dr.height > 0) {
          dockClear = Math.max(72, Math.round(window.innerHeight - dr.top + 6));
          setVar('--dock-clearance', dockClear + 'px');
        }
        if (pane && window.innerWidth < 768) {
          var pr = pane.getBoundingClientRect();
          if (pr.height > 0 && dockClear) {
            /* 面板底边贴时间轴上方；图例再贴面板上缘，全部按实测高度推算 */
            setVar('--phone-pane-clearance', Math.round(dockClear + pr.height + 6) + 'px');
          }
        }
      });
    }

    if (pane && balloon) {
      var tabs = document.createElement('div');
      tabs.className = 'archive-folder-tabs';
      tabs.setAttribute('role', 'tablist');
      tabs.setAttribute('aria-label', '历史档案分类');
      tabs.innerHTML =
        '<button type="button" class="archive-folder-tab is-active" data-tab="chronicle" role="tab" aria-selected="true">史志<small>CHRONICLE</small></button>' +
        '<button type="button" class="archive-folder-tab" data-tab="event" role="tab" aria-selected="false">事件<small>EVENT</small></button>' +
        '<button type="button" class="archive-folder-tab" data-tab="genealogy" role="tab" aria-selected="false">沿革 / 人物<small>PLACE</small></button>' +
        '<button type="button" class="archive-folder-tab" data-tab="journey" role="tab" aria-selected="false">路线<small>ROUTE</small></button>';
      var collapseButton = document.createElement('button');
      collapseButton.type = 'button';
      collapseButton.className = 'archive-collapse';
      collapseButton.textContent = '收起';
      collapseButton.setAttribute('aria-expanded', 'true');
      function expandArchive() {
        body.classList.remove('archive-collapsed');
        collapseButton.textContent = '收起';
        collapseButton.setAttribute('aria-expanded', 'true');
      }
      collapseButton.addEventListener('click', function (e) {
        e.stopPropagation();
        var collapsed = body.classList.toggle('archive-collapsed');
        collapseButton.textContent = collapsed ? '展开' : '收起';
        collapseButton.setAttribute('aria-expanded', String(!collapsed));
      });
      tabs.appendChild(collapseButton);
      body.appendChild(tabs);
      body.setAttribute('data-archive-tab', 'chronicle');

      function paintTabs(name) {
        tabs.querySelectorAll('.archive-folder-tab').forEach(function (btn) {
          var on = btn.getAttribute('data-tab') === name;
          btn.classList.toggle('is-active', on);
          btn.setAttribute('aria-selected', on ? 'true' : 'false');
        });
      }
      function showEventPlaceholder() {
        archivePlaceholder = true;
        balloon.innerHTML = '<div class="archive-empty"><strong>事件档案</strong>点击地图上的事件圆点，或切换到「史志」签点击重大事件，这里就会展开对应的年份、地点与史事。</div>';
        balloon.classList.remove('is-hidden', 'is-offscreen');
      }
      function selectArchive(name) {
        if (!archiveMode()) return;
        expandArchive();
        if (name === 'chronicle') {
          var workspace = document.getElementById('workspace-body');
          if (workspace && workspace.classList.contains('is-pane-collapsed')) {
            var toggle = document.getElementById('act-toggle-pane');
            if (toggle) toggle.click();
          }
          if (archivePlaceholder) {
            archivePlaceholder = false;
            balloon.classList.add('is-hidden');
          }
        } else if (name === 'event' && !balloon.querySelector('.ep-text')) {
          showEventPlaceholder();
        } else if (name === 'genealogy') {
          // 切到「沿革」签：若当前没有激活的地名沿革，显示引导占位
          var genCard = document.getElementById('genealogy-card');
          if (genCard && genCard.classList.contains('is-hidden')) {
            var timeline = genCard.querySelector('#genealogy-timeline');
            if (timeline && !timeline.children.length) {
              document.getElementById('genealogy-heading').textContent = '沿革档案';
              document.getElementById('genealogy-sub').textContent = '点击地图城名或双击任意位置，查看该地历代政区沿革。';
            }
            genCard.classList.remove('is-hidden');
          }
        } else if (name === 'journey') {
          var journeyCard = document.getElementById('journey-card');
          if (journeyCard && journeyCard.classList.contains('is-hidden')) {
            journeyCard.innerHTML = '<div class="archive-empty"><strong>路线档案</strong>在地图上选择人物或事件后，这里会展示对应的行迹路线与多站轨迹。</div>';
            journeyCard.classList.remove('is-hidden');
          }
        }
        body.setAttribute('data-archive-tab', name);
        paintTabs(name);
        scheduleLayout();
      }
      tabs.addEventListener('pointerdown', function (e) {
        e.stopPropagation();
      }, { passive: true });
      tabs.querySelectorAll('.archive-folder-tab').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault(); e.stopPropagation();
          selectArchive(btn.getAttribute('data-tab'));
        });
      });

      var gen = document.getElementById('genealogy-card');
      if (gen) new MutationObserver(function () {
        if (!gen.classList.contains('is-hidden')) {
          expandArchive();
          body.setAttribute('data-archive-tab', 'genealogy');
          paintTabs('genealogy');
          scheduleLayout();
        }
      }).observe(gen, {childList:true, subtree:true, attributes:true, attributeFilter:['class']});
      /* 点击地图事件后自动翻到「事件」签；关闭事件后回到「史志」签 */
      var balloonObserver = new MutationObserver(function () {
        if (!archiveMode()) return;
        var hidden = balloon.classList.contains('is-hidden');
        if (!hidden && balloon.querySelector('.ep-text')) {
          archivePlaceholder = false;
          var atlas = window.atlasApp;
          var automatic = atlas && atlas.activeMilestone && atlas.activeMilestone.isAuto;
          if (!automatic) {
            body.setAttribute('data-archive-tab', 'event');
            paintTabs('event');
          }
        } else if (hidden && !archivePlaceholder && body.getAttribute('data-archive-tab') === 'event') {
          body.setAttribute('data-archive-tab', 'chronicle');
          paintTabs('chronicle');
        }
        scheduleLayout();
      });
      balloonObserver.observe(balloon, { attributes: true, attributeFilter: ['class'], childList: true });

      function onResize() {
        if (!archiveMode()) {
          if (archivePlaceholder) {
            archivePlaceholder = false;
            balloon.classList.add('is-hidden');
          }
          body.setAttribute('data-archive-tab', 'chronicle');
          paintTabs('chronicle');
        }
        scheduleLayout();
      }
      window.addEventListener('resize', onResize, { passive: true });
      window.addEventListener('orientationchange', function () { setTimeout(scheduleLayout, 260); }, { passive: true });
      if (window.ResizeObserver) {
        var layoutObserver = new ResizeObserver(scheduleLayout);
        layoutObserver.observe(dock);
        layoutObserver.observe(pane);
        if (key) layoutObserver.observe(key);
      }
      scheduleLayout();
      setTimeout(scheduleLayout, 350);
      setTimeout(scheduleLayout, 1100);
    }
  }
  boot();
})();
