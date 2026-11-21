// Pane handles (D-46): drag a handle to resize a pane, keep the widths of a page in the browser
// (localStorage), and reset them with the sidebar button. Events are delegated on `document`,
// so a handle that HTMX swaps in works at once.

const STORAGE_PREFIX = "design-kb.panes.";
const DEFAULT_PANE_MIN = 240;

let keptWidths = {};
let drag = null;

/** Return the localStorage key of this page. */
function storageKey() {
  return STORAGE_PREFIX + document.body.dataset.page;
}

/** Return the saved widths of this page, or an empty object when the storage is blocked or empty. */
function loadWidths() {
  try {
    return JSON.parse(window.localStorage.getItem(storageKey())) || {};
  } catch (error) {
    return {};
  }
}

/** Save the widths of this page; a blocked storage is ignored, so the widths last for the visit. */
function saveWidths() {
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify(keptWidths));
  } catch (error) {
    // No storage: keptWidths in memory is all there is.
  }
}

/** Delete the saved widths of this page. */
function deleteWidths() {
  try {
    window.localStorage.removeItem(storageKey());
  } catch (error) {
    // No storage: nothing to delete.
  }
}

/** Return the smallest width of a pane in pixels, read from --pane-min on :root. */
function paneMin() {
  const value = getComputedStyle(document.documentElement).getPropertyValue("--pane-min");
  return parseFloat(value) || DEFAULT_PANE_MIN;
}

/** Put the kept widths on the panes of the page; a flexible pane ignores --pane-width. */
function applyWidths() {
  document.querySelectorAll("[data-pane]").forEach(setKeptWidth);
}

/** Put the kept width on one pane, if the page kept one for it. */
function setKeptWidth(pane) {
  const width = keptWidths[pane.dataset.pane];
  if (typeof width === "number") {
    pane.style.setProperty("--pane-width", width + "px");
  }
}

/** Show the reset button only when the page has a handle. */
function updateResetButton() {
  const button = document.querySelector("[data-pane-reset]");
  if (button !== null) {
    button.hidden = document.querySelector("[data-pane-handle]") === null;
  }
}

/** Return the pane left of a handle; a handle in a slot (display: contents) looks past the slot. */
function paneLeftOf(handle) {
  return handle.previousElementSibling || handle.parentElement.previousElementSibling;
}

/** Return the pane right of a handle. */
function paneRightOf(handle) {
  return handle.nextElementSibling || handle.parentElement.nextElementSibling;
}

/** Return true when the pane takes the free width, as its computed style says. */
function isFlexible(pane) {
  return parseFloat(getComputedStyle(pane).flexGrow) > 0;
}

/** Return the pane that a handle resizes: the left one, or the right one when the left is flexible. */
function paneToResize(handle) {
  const left = paneLeftOf(handle);
  return isFlexible(left) ? paneRightOf(handle) : left;
}

/** Start a drag when the pointer goes down on a handle. */
function onPointerDown(event) {
  const handle = event.target.closest("[data-pane-handle]");
  if (handle === null) {
    return;
  }
  const target = paneToResize(handle);
  const onLeft = target === paneLeftOf(handle);
  const other = onLeft ? paneRightOf(handle) : paneLeftOf(handle);
  drag = {
    handle: handle,
    target: target,
    startX: event.clientX,
    startWidth: target.getBoundingClientRect().width,
    otherWidth: other.getBoundingClientRect().width,
    direction: onLeft ? 1 : -1,
  };
  handle.setPointerCapture(event.pointerId);
  handle.classList.add("dragging");
  event.preventDefault();
}

/** Move the edge of the pane with the pointer, and stop where a neighbour gets narrower than --pane-min. */
function onPointerMove(event) {
  if (drag === null) {
    return;
  }
  const min = paneMin();
  const wanted = drag.startWidth + (event.clientX - drag.startX) * drag.direction;
  const largest = drag.startWidth + drag.otherWidth - min;
  const width = Math.max(min, Math.min(wanted, largest));
  drag.target.style.setProperty("--pane-width", width + "px");
}

/** End the drag and keep the new width of the pane. */
function onPointerUp() {
  if (drag === null) {
    return;
  }
  const width = parseFloat(drag.target.style.getPropertyValue("--pane-width"));
  if (!Number.isNaN(width)) {
    keptWidths[drag.target.dataset.pane] = Math.round(width);
    saveWidths();
  }
  drag.handle.classList.remove("dragging");
  drag = null;
}

/** Remove the dragged width of one pane, so that the default of app.css applies. */
function clearPaneWidth(pane) {
  pane.style.removeProperty("--pane-width");
}

/** Reset the widths of the page to the defaults when the reset button is clicked. */
function onClick(event) {
  if (event.target.closest("[data-pane-reset]") === null) {
    return;
  }
  keptWidths = {};
  deleteWidths();
  document.querySelectorAll("[data-pane]").forEach(clearPaneWidth);
}

/** Mark one row as selected when it is the row of the given engineer ID. */
function markRow(row, selectedId) {
  row.classList.toggle("selected", row.dataset.engineerId === selectedId);
}

/** Mark the row of the engineer whose detail pane is open, and no other row. */
function markSelectedRow() {
  const detail = document.querySelector('[data-pane="engineer-detail"]');
  const selectedId = detail === null ? null : detail.dataset.engineerId;
  for (const row of document.querySelectorAll('[data-pane="engineers"] [data-engineer-id]')) {
    markRow(row, selectedId);
  }
}

/** Apply the kept widths, show the reset button and mark the selected row, at load and after an HTMX swap. */
function refreshPanes() {
  applyWidths();
  updateResetButton();
  markSelectedRow();
}

keptWidths = loadWidths();
refreshPanes();
document.addEventListener("pointerdown", onPointerDown);
document.addEventListener("pointermove", onPointerMove);
document.addEventListener("pointerup", onPointerUp);
document.addEventListener("pointercancel", onPointerUp);
document.addEventListener("click", onClick);
document.addEventListener("htmx:afterSwap", refreshPanes);
