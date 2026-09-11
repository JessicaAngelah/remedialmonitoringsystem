/* Adds Excel-like column/row resizing, double-click-to-fit, and a
 * per-sheet wrap-text toggle to any .xl-card table (used by the project
 * "spreadsheet" view and the imported-file viewer). Purely client-side —
 * sizes and the wrap setting reset on reload. */
(function () {
  function closestPositioned(el) {
    return getComputedStyle(el).position;
  }

  function ensurePositioned(el) {
    if (closestPositioned(el) === 'static') el.style.position = 'relative';
  }

  function measureNaturalWidth(cell) {
    var clone = cell.cloneNode(true);
    var handles = clone.querySelectorAll('.xl-col-resize, .xl-row-resize');
    handles.forEach(function (h) { h.remove(); });
    clone.style.position = 'absolute';
    clone.style.visibility = 'hidden';
    clone.style.left = '-9999px';
    clone.style.top = '0';
    clone.style.width = 'auto';
    clone.style.maxWidth = 'none';
    clone.style.whiteSpace = 'nowrap';
    document.body.appendChild(clone);
    var w = clone.getBoundingClientRect().width;
    document.body.removeChild(clone);
    return w;
  }

  function autoFitColumn(table, colIndex, cells, colEl) {
    var max = 50;
    cells.forEach(function (cell) {
      var w = measureNaturalWidth(cell);
      if (w > max) max = w;
    });
    setColWidth(table, cells, colEl, Math.min(Math.ceil(max) + 4, 640));
  }

  function buildColgroup(table, headerCells) {
    var existing = table.querySelector('colgroup');
    if (existing) existing.remove();
    var colgroup = document.createElement('colgroup');
    Array.prototype.forEach.call(headerCells, function () { colgroup.appendChild(document.createElement('col')); });
    table.insertBefore(colgroup, table.firstChild);
    return colgroup.children;
  }

  function setColWidth(table, cells, colEl, px) {
    var w = Math.max(40, px) + 'px';
    // Belt-and-suspenders, taken further: rather than trust table-layout
    // and <colgroup> semantics (which have turned out to be inconsistent
    // here — the drag updates values fine but the rendered column doesn't
    // move), set the width explicitly on every cell in the column,
    // header and body alike. With every cell agreeing on the same width,
    // there's no ambiguity left for the browser's table layout algorithm
    // to resolve differently, in auto or fixed mode.
    if (colEl) colEl.style.width = w;
    cells.forEach(function (c) { c.style.width = w; c.style.maxWidth = w; });
    syncTableWidth(table);
  }

  // table-layout:fixed only fixes how width is *distributed* across
  // columns — it does nothing to stop the table's own (auto) width from
  // shrinking to fit its container. With wrapping off that never shows up,
  // because unbroken text keeps every cell's min-content width at its full
  // length, which is normally wider than the container, so the table has
  // no room to shrink and just overflows into a horizontal scrollbar
  // instead. Turn wrapping on and a cell's min-content width collapses to
  // roughly its longest unbreakable word — tiny — so the table suddenly
  // has plenty of room to shrink, and every column gets squeezed down
  // proportionally, discarding whatever width was just dragged. Pinning
  // the table's own width to the sum of its columns (recomputed after
  // every resize) keeps it from ever "fitting" its container, so wrapping
  // can no longer trigger that shrink — same fix a real spreadsheet's
  // frozen column widths rely on.
  function syncTableWidth(table) {
    var cols = table.querySelectorAll(':scope > colgroup > col');
    var total = 0;
    cols.forEach(function (col) {
      var w = parseFloat(col.style.width);
      if (!isNaN(w)) total += w;
    });
    if (total > 0) {
      table.style.width = total + 'px';
      table.style.minWidth = total + 'px';
    }
  }

  function columnCells(table, colIndex) {
    var cells = [];
    var headerRow = table.querySelector('thead tr');
    if (headerRow && headerRow.children[colIndex]) cells.push(headerRow.children[colIndex]);
    table.querySelectorAll('tbody tr').forEach(function (tr) {
      if (tr.children[colIndex]) cells.push(tr.children[colIndex]);
    });
    return cells;
  }

  function ensureGhostLine(card) {
    var scrollEl = card.querySelector('.xl-scroll') || card;
    var line = scrollEl.querySelector(':scope > .xl-resize-ghost');
    if (!line) {
      line = document.createElement('div');
      line.className = 'xl-resize-ghost';
      scrollEl.appendChild(line);
    }
    var table = scrollEl.querySelector('table.xl-table');
    // Fixed at drag-start height — nothing during the drag itself changes
    // the table's rendered height (we're only moving a ghost line, not
    // touching real cell widths until release), so one measurement here
    // is enough.
    if (table) line.style.height = table.getBoundingClientRect().height + 'px';
    return { el: line, scrollEl: scrollEl };
  }

  function ghostLeftFor(ghostInfo, edgeClientX) {
    var scrollRect = ghostInfo.scrollEl.getBoundingClientRect();
    return (edgeClientX - scrollRect.left + ghostInfo.scrollEl.scrollLeft) + 'px';
  }

  function addColumnResize(table, cols, card) {
    var headerRow = table.querySelector('thead tr');
    if (!headerRow) return;
    var headerCells = Array.prototype.slice.call(headerRow.children);
    headerCells.forEach(function (th, i) {
      var cells = columnCells(table, i);
      var rect = th.getBoundingClientRect();
      if (rect.width) setColWidth(table, cells, cols[i], rect.width);

      var handle = document.createElement('div');
      handle.className = 'xl-col-resize';
      handle.setAttribute('contenteditable', 'false');
      ensurePositioned(th);
      th.appendChild(handle);

      // Live-reflowing every cell in the column on every pointermove used
      // to make the drag while wrapping is on (or on a sheet with lots of
      // rows) feel completely frozen — re-wrapping text on every frame for
      // hundreds of cells is expensive. Follow the cursor with a cheap
      // "ghost line" instead (the same trick Excel/Sheets use) and only
      // touch the real cells once, when the drag ends.
      var startX, startWidth, dragging = false, ghostInfo, activePointerId;
      handle.addEventListener('pointerdown', function (e) {
        if (e.button !== undefined && e.button !== 0) return;
        e.preventDefault();
        e.stopPropagation();
        dragging = true;
        activePointerId = e.pointerId;
        startX = e.clientX;
        startWidth = th.getBoundingClientRect().width;
        ghostInfo = ensureGhostLine(card);
        ghostInfo.el.style.left = ghostLeftFor(ghostInfo, th.getBoundingClientRect().right);
        ghostInfo.el.style.display = 'block';
        document.body.classList.add('xl-resizing-col');
        try { handle.setPointerCapture(e.pointerId); } catch (err) { /* not supported — document-level listeners below still track it */ }
      });
      // Bound to the document rather than the 8px handle itself. Pointer
      // capture (set above) is what's *supposed* to keep routing move/up
      // events to the handle once the cursor drifts off that thin strip,
      // but it isn't something to bet the whole drag on — a taller header
      // (wrapping pushes it to multiple lines) means the strip shifts and
      // is easier to drift off mid-drag, and if capture doesn't take hold
      // at that exact moment, handle-only listeners go silent: the cursor
      // still looks like it's mid-resize (that's just CSS) but nothing is
      // listening anymore, so the drag never commits. Listening on the
      // document — the same fallback the plain-mouse-event path below
      // already relies on — means the drag tracks correctly either way.
      function onDocPointerMove(e) {
        if (!dragging || (activePointerId !== undefined && e.pointerId !== activePointerId)) return;
        e.preventDefault();
        var newWidth = Math.max(40, startWidth + (e.clientX - startX));
        ghostInfo.el.style.left = ghostLeftFor(ghostInfo, th.getBoundingClientRect().left + newWidth);
      }
      function endColDrag(e) {
        if (!dragging || (activePointerId !== undefined && e.pointerId !== activePointerId)) return;
        dragging = false;
        if (ghostInfo) ghostInfo.el.style.display = 'none';
        document.body.classList.remove('xl-resizing-col');
        try { handle.releasePointerCapture(e.pointerId); } catch (err) { /* no-op */ }
        var newWidth = Math.max(40, startWidth + (e.clientX - startX));
        setColWidth(table, cells, cols[i], newWidth);
      }
      document.addEventListener('pointermove', onDocPointerMove);
      document.addEventListener('pointerup', endColDrag);
      document.addEventListener('pointercancel', endColDrag);
      handle.addEventListener('dblclick', function (e) {
        e.preventDefault();
        e.stopPropagation();
        autoFitColumn(table, i, cells, cols[i]);
      });
      handle.addEventListener('click', function (e) { e.stopPropagation(); });
      // Belt-and-suspenders: some older WebViews used for the desktop/mobile
      // shell don't fire pointer events reliably inside contenteditable
      // ancestors. Fall back to plain mouse events for those too — the two
      // sets of listeners never both apply to the same interaction because
      // "dragging" guards the pointermove/up handlers above.
      var mStartX, mStartWidth, mGhostInfo;
      handle.addEventListener('mousedown', function (e) {
        if (window.PointerEvent) return; // pointer events already handled it
        e.preventDefault();
        e.stopPropagation();
        mStartX = e.pageX;
        mStartWidth = th.getBoundingClientRect().width;
        mGhostInfo = ensureGhostLine(card);
        mGhostInfo.el.style.left = ghostLeftFor(mGhostInfo, th.getBoundingClientRect().right);
        mGhostInfo.el.style.display = 'block';
        document.body.classList.add('xl-resizing-col');
        function onMove(e2) {
          var w = Math.max(40, mStartWidth + (e2.pageX - mStartX));
          mGhostInfo.el.style.left = ghostLeftFor(mGhostInfo, th.getBoundingClientRect().left + w);
        }
        function onUp(e2) {
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onUp);
          document.body.classList.remove('xl-resizing-col');
          mGhostInfo.el.style.display = 'none';
          setColWidth(table, cells, cols[i], Math.max(40, mStartWidth + (e2.pageX - mStartX)));
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
      });
    });
  }

  function addRowResize(table) {
    var rows = table.querySelectorAll('tbody tr');
    rows.forEach(function (tr) {
      var firstCell = tr.children[0];
      if (!firstCell) return;
      var handle = document.createElement('div');
      handle.className = 'xl-row-resize';
      handle.setAttribute('contenteditable', 'false');
      ensurePositioned(firstCell);
      firstCell.appendChild(handle);

      var startY, startHeight, dragging = false, activePointerId;
      handle.addEventListener('pointerdown', function (e) {
        if (e.button !== undefined && e.button !== 0) return;
        e.preventDefault();
        e.stopPropagation();
        dragging = true;
        activePointerId = e.pointerId;
        startY = e.clientY;
        startHeight = tr.getBoundingClientRect().height;
        document.body.classList.add('xl-resizing-row');
        try { handle.setPointerCapture(e.pointerId); } catch (err) { /* not supported — document-level listeners below still track it */ }
      });
      // Bound to the document, not the 8px-tall handle — see the matching
      // comment in addColumnResize. Wrapping makes rows taller, which
      // shifts the handle further from the cursor mid-drag and makes it
      // easier to drift off; pointer capture alone isn't reliable enough
      // to bet the whole drag on.
      function onDocPointerMove(e) {
        if (!dragging || (activePointerId !== undefined && e.pointerId !== activePointerId)) return;
        e.preventDefault();
        var delta = e.clientY - startY;
        tr.style.height = Math.max(24, startHeight + delta) + 'px';
      }
      function endRowDrag(e) {
        if (!dragging || (activePointerId !== undefined && e.pointerId !== activePointerId)) return;
        dragging = false;
        document.body.classList.remove('xl-resizing-row');
        try { handle.releasePointerCapture(e.pointerId); } catch (err) { /* no-op */ }
      }
      document.addEventListener('pointermove', onDocPointerMove);
      document.addEventListener('pointerup', endRowDrag);
      document.addEventListener('pointercancel', endRowDrag);
      handle.addEventListener('dblclick', function (e) {
        e.preventDefault();
        e.stopPropagation();
        tr.style.height = '';
      });
      handle.addEventListener('click', function (e) { e.stopPropagation(); });
      var mStartY, mStartHeight;
      handle.addEventListener('mousedown', function (e) {
        if (window.PointerEvent) return;
        e.preventDefault();
        e.stopPropagation();
        mStartY = e.pageY;
        mStartHeight = tr.getBoundingClientRect().height;
        document.body.classList.add('xl-resizing-row');
        function onMove(e2) {
          var delta = e2.pageY - mStartY;
          tr.style.height = Math.max(24, mStartHeight + delta) + 'px';
        }
        function onUp() {
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onUp);
          document.body.classList.remove('xl-resizing-row');
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
      });
    });
  }

  function addWrapToggle(card, table) {
    if (card.querySelector('.xl-grid-toolbar')) return;
    var bar = document.createElement('div');
    bar.className = 'xl-grid-toolbar';

    var hint = document.createElement('span');
    hint.className = 'xl-grid-hint';
    hint.textContent = 'Drag a column or row edge to resize · double-click an edge to fit';
    bar.appendChild(hint);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'xl-wrap-toggle';
    btn.textContent = 'Wrap text';
    table.classList.add('xl-nowrap');
    btn.addEventListener('click', function () {
      var nowNowrap = !table.classList.contains('xl-nowrap');
      table.classList.toggle('xl-nowrap', nowNowrap);
      btn.classList.toggle('active', !nowNowrap);
    });
    bar.appendChild(btn);

    var scroll = card.querySelector('.xl-scroll');
    card.insertBefore(bar, scroll);
  }

  function reallyInit(panel, table, card) {
    panel.dataset.xlGridInit = '1';
    var headerRow = table.querySelector('thead tr');
    if (!headerRow) return;
    var cols = buildColgroup(table, headerRow.children);
    // addWrapToggle runs first so the nowrap class (single-line,
    // ellipsis-on-overflow) is already active when addColumnResize takes
    // its initial width measurement below. Measuring in the other order
    // used to lock in widths from the *wrapped* layout — text left free
    // to break onto several short lines needs far less horizontal room
    // than the same text held to one line — so as soon as nowrap kicked
    // in on top of those narrow widths, headers and cells that had
    // plenty of room a moment ago were suddenly clipped to "…".
    addWrapToggle(card, table);
    addColumnResize(table, cols, card);
    addRowResize(table);
    table.classList.add('xl-sized');
  }

  function init(panel) {
    if (!panel || panel.dataset.xlGridInit) return;
    var table = panel.querySelector('table.xl-table');
    var card = panel.classList.contains('xl-card') ? panel : panel.closest('.xl-card');
    if (!table || !card) return;

    if (table.getBoundingClientRect().width) {
      reallyInit(panel, table, card);
      return;
    }

    // Not painted yet (still hidden, fonts/layout not settled, tab opened
    // in the background, etc). A one-shot width check here used to just
    // give up permanently for whichever sheet happens to be the default
    // active tab, since nothing else ever re-triggers it — a tab switch
    // never happens if the user never leaves that sheet. Watch for it to
    // actually gain a size instead of guessing when that'll be.
    if (panel.dataset.xlGridWatching) return;
    panel.dataset.xlGridWatching = '1';
    if (typeof ResizeObserver !== 'undefined') {
      var ro = new ResizeObserver(function () {
        if (panel.dataset.xlGridInit) { ro.disconnect(); return; }
        if (table.getBoundingClientRect().width) {
          ro.disconnect();
          reallyInit(panel, table, card);
        }
      });
      ro.observe(panel);
    } else {
      // Very old browser without ResizeObserver — fall back to polling for
      // a couple of seconds, which comfortably covers slow font/layout
      // settling without polling forever.
      var attempts = 0;
      var poll = setInterval(function () {
        attempts++;
        if (panel.dataset.xlGridInit || attempts > 40) { clearInterval(poll); return; }
        if (table.getBoundingClientRect().width) {
          clearInterval(poll);
          reallyInit(panel, table, card);
        }
      }, 50);
    }
  }

  function initVisible() {
    document.querySelectorAll('.xl-tabpanel, .xl-card').forEach(function (panel) {
      init(panel);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initVisible();
    // Tab switches just toggle inline display:none — watch for that too,
    // since a panel that was genuinely display:none (not just unpainted)
    // won't fire ResizeObserver until it's shown.
    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        var el = m.target;
        if (el.offsetParent !== null) init(el);
      });
    });
    document.querySelectorAll('.xl-tabpanel, .xl-card').forEach(function (panel) {
      observer.observe(panel, { attributes: true, attributeFilter: ['style'] });
    });
  });
})();
